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

    hi = ["high", "critical"]
    summary = {
        "baseline_min_fos": round(float(b["fos"].min()), 3),
        "scenario_min_fos": round(float(m["fos"].min()), 3),
        "delta_min_fos": round(float(m["fos"].min() - b["fos"].min()), 3),
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
            "trajectory": _trajectory(m, b["fos"].values)}