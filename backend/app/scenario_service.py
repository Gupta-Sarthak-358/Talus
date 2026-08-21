"""Bridge between the TALUS backend and the frozen Scenario Engine v1.5.

Causal physics What-If: scenarios modify CAUSES (rain realization, blast
schedule); the frozen generator v1.4.0 chain propagates them
(rain -> groundwater -> cracks -> FoS -> score -> label). This module never
writes fos/instability_score/risk_label directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "ml" / "scenario", REPO / "ml" / "data_generation"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import Scenario, run_scenario, TEMPLATES  # noqa: E402
from generator_schema import GENERATOR_VERSION  # noqa: E402

ZONE_MAP = {"A": "ZONE_A", "B": "ZONE_B", "C": "ZONE_C", "D": "ZONE_D"}
IMD_CSV = REPO / "data" / "processed" / "imd" / "neyveli_rainfall_1901_2024.csv"


def template_provenance(template_id: str | None) -> dict | None:
    if not template_id or template_id not in TEMPLATES:
        return None
    a, b = TEMPLATES[template_id]
    imd = pd.read_csv(IMD_CSV, parse_dates=["timestamp"])
    w = imd[(imd.timestamp >= a) & (imd.timestamp <= b)]
    return {"template_id": template_id, "imd_window": [a, b],
            "window_total_mm": round(float(w["rainfall_mm"].sum()), 1),
            "window_max_day_mm": round(float(w["rainfall_mm"].max()), 1),
            "source": "IMD 0.25deg Neyveli grid 11.5N 79.5E"}


def list_templates() -> list[dict]:
    return [template_provenance(t) for t in TEMPLATES]


def _trajectory(df: pd.DataFrame, base_fos: np.ndarray, max_points: int = 400) -> list[dict]:
    n = len(df)
    step = max(1, int(np.ceil(n / max_points)))
    pts = []
    for i in range(0, n, step):
        pts.append({"day": int(i),
                    "fos": round(float(df["fos"].iloc[i]), 4),
                    "instability_score": float(df["instability_score"].iloc[i]),
                    "risk_label": str(df["risk_label"].iloc[i]),
                    "baseline_fos": round(float(base_fos[i]), 4)})
    last = n - 1
    if (n - 1) % step != 0:
        pts.append({"day": int(last),
                    "fos": round(float(df["fos"].iloc[last]), 4),
                    "instability_score": float(df["instability_score"].iloc[last]),
                    "risk_label": str(df["risk_label"].iloc[last]),
                    "baseline_fos": round(float(base_fos[last]), 4)})
    return pts


def evidence_timeline(df: pd.DataFrame, min_score_jump: float = 3.0,
                      max_events: int = 25) -> list[dict]:
    """FR-10 Risk Evidence Timeline: state changes + their causes.

    Derived from the causal trajectory (NOT from SHAP): each event is a
    day where instability moved >= min_score_jump, with causes attributed
    from the physical state variables that changed that day.
    """
    events = []
    for i in range(1, len(df)):
        s_prev = float(df["instability_score"].iloc[i - 1])
        s_cur = float(df["instability_score"].iloc[i])
        if abs(s_cur - s_prev) < min_score_jump:
            continue
        causes = []
        d_rain = float(df["rainfall_mm"].iloc[i]) - float(df["rainfall_mm"].iloc[i - 1])
        if d_rain >= 10.0:
            causes.append(f"heavy rainfall (+{d_rain:.0f} mm/24h)")
        d_gw = float(df["groundwater_proxy"].iloc[i]) - float(df["groundwater_proxy"].iloc[i - 1])
        if d_gw >= 15.0:
            causes.append(f"groundwater proxy rose (+{d_gw:.0f} mm)")
        sev_prev, sev_cur = str(df["crack_severity"].iloc[i - 1]), str(df["crack_severity"].iloc[i])
        if sev_prev != sev_cur:
            causes.append(f"crack severity {sev_prev} -> {sev_cur}")
        if bool(df["blast_occurs"].iloc[i]):
            causes.append(f"blast event (PPV {float(df['blast_vibration_ppv_mms'].iloc[i]):.1f} mm/s)")
        wf_prev = bool(df["water_filled"].iloc[i - 1])
        wf_cur = bool(df["water_filled"].iloc[i])
        if wf_cur and not wf_prev:
            causes.append("cracks became water-filled")
        if not causes:
            continue
        events.append({"day": int(i),
                       "score_from": round(s_prev, 1),
                       "score_to": round(s_cur, 1),
                       "fos": round(float(df["fos"].iloc[i]), 3),
                       "causes": causes})
        if len(events) >= max_events:
            break
    return events


def run_causal(zone_letter: str, kind: str, start_day: int, duration_days: int,
               params: dict, horizon_days: int, seed: int) -> dict:
    zid = ZONE_MAP[zone_letter]
    name = f"api_{kind}_{start_day}_{duration_days}"
    sc = Scenario(name=name, kind=kind, zone_id=zid, seed=seed,
                  start_day=start_day, duration_days=duration_days,
                  params=dict(params))
    b = run_scenario(Scenario(name=f"base_{zid}_{seed}", kind="none",
                              zone_id=zid, seed=seed), days=horizon_days)
    m = run_scenario(sc, days=horizon_days)

    diff = m["instability_score"].values - b["instability_score"].values
    onset = int(np.argmax(np.abs(diff) > 1.0)) if (np.abs(diff) > 1.0).any() else None
    worst = int(np.argmax(m["instability_score"].values))
    crit_m = (m["crack_severity"].astype(str) == "critical")
    filled_crit = int((crit_m & m["water_filled"].astype(bool)).sum())

    diff_fos = m["fos"].values - b["fos"].values
    hi = ["high", "critical"]
    summary = {
        "baseline_min_fos": round(float(b["fos"].min()), 3),
        "scenario_min_fos": round(float(m["fos"].min()), 3),
        "delta_min_fos": round(float(m["fos"].min() - b["fos"].min()), 3),
        "fos_divergence_min": round(float(diff_fos.min()), 3),
        "divergence_day": int(np.argmin(diff_fos)),
        "days_diverging_gt_001": int((np.abs(diff_fos) > 0.01).sum()),
        "baseline_peak_instability": float(b["instability_score"].max()),
        "scenario_peak_instability": float(m["instability_score"].max()),
        "delta_peak_instability": round(float(m["instability_score"].max()
                                              - b["instability_score"].max()), 1),
        "baseline_days_high_or_critical": int(b["risk_label"].astype(str).isin(hi).sum()),
        "scenario_days_high_or_critical": int(m["risk_label"].astype(str).isin(hi).sum()),
        "first_response_day": onset,
        "worst_day": worst,
        "worst_day_risk": str(m.loc[worst, "risk_label"]),
        "max_groundwater_proxy_mm": round(float(m["groundwater_proxy"].max()), 1),
        "open_crack_branch_fired": bool(filled_crit > 0),
    }
    return {"zone_id": zone_letter,
            "scenario_name": name,
            "mode": "causal_physics",
            "generator_version": GENERATOR_VERSION,
            "summary": summary,
            "provenance": template_provenance(params.get("template_id")),
            "evidence_timeline": evidence_timeline(m),
            "trajectory": _trajectory(m, b["fos"].values)}