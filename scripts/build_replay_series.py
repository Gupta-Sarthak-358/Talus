"""Temporal-replay bundle for the judge demo: daily model state before each past event.

Reads the per-case daily CSVs + committed summary produced by
scripts/counterfactual_past_events.py and emits ONE committed bundle:

  data/sih26001/evidence/replay_series.json

  {cases: [{id, title, site_name, event_date, event_date_fuzzy, event_note,
            sources, analogue:{row, distance_m, lulc},
            series: [{date, score, band, rain_24h, rain_7d, rain_30d,
                      soil_moisture, ndvi, drivers:[...]}]}],
   ledger: [{id, title, event_date, first_moderate, first_high,
             first_critical, lead_high_days, lead_critical_days,
             false_alarm_episodes}]}

Causality rule (NON-NEGOTIABLE, asserted here): every series row's inputs
are information available ON that date — rainfall trailing sums ending that
day (IMD archive), soil on/before that day (daily CCI or quasi-static
fallback), ONE pre-event satellite scene, static terrain. Series dates must
be <= event_date or the build FAILS.

Drivers (honest, no per-day SHAP theatre): week-over-week input deltas
(rain_7d jump, soil jump) + the analogue row's static context. The why-panel
says "rainfall accumulation rose Xmm in 7 days", never invented attribution.

False-alarm episodes: contiguous High-or-worse runs separated by >=3 calm
days; episodes strictly before the final pre-event episode. Definition is
logged in the bundle.

Run (mnemo venv): python scripts/build_replay_series.py  (after replays)
"""
from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PROCDIR = REPO / "data/sih26001/processed"
EVIDDIR = REPO / "data/sih26001/evidence"
OUT = EVIDDIR / "replay_series.json"
SUMMARY = EVIDDIR / "counterfactual_summary.json"
BANDS = ["Very Low", "Low", "Moderate", "High", "Critical"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def drivers_for(df: pd.DataFrame, i: int) -> list[str]:
    """Week-over-week input deltas in plain words (inputs, not attribution)."""
    if i < 7:
        return ["window opening — accumulating baseline"]
    d7 = float(df["rain_7d"].iloc[i] - df["rain_7d"].iloc[i - 7])
    dsoil = float(df["soil_moisture"].iloc[i] - df["soil_moisture"].iloc[i - 7])
    out = []
    if d7 >= 50:
        out.append(f"antecedent rainfall +{d7:.0f}mm in 7 days")
    elif d7 >= 15:
        out.append(f"antecedent rainfall +{d7:.0f}mm in 7 days (building)")
    elif d7 <= -50:
        out.append(f"rainfall easing {d7:.0f}mm over 7 days")
    if dsoil >= 0.03:
        out.append(f"soil wetness rising (+{dsoil:.3f})")
    elif dsoil <= -0.03:
        out.append(f"soil drying ({dsoil:.3f})")
    if not out:
        out.append("steady antecedent conditions")
    return out


def episodes(dates: list[str], hot: list[bool], gap: int = 3) -> list[tuple[str, str]]:
    """Contiguous hot runs separated by >=gap calm days -> [(start, end)]."""
    eps: list[tuple[str, str]] = []
    start = None
    calm = 0
    for d, h in zip(dates, hot):
        if h:
            if start is None:
                start = d
            calm = 0
        else:
            if start is not None:
                calm += 1
                if calm >= gap:
                    eps.append((start, dates[dates.index(d) - gap]))
                    start = None
                    calm = 0
    if start is not None:
        eps.append((start, dates[-1]))
    return eps


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    cases_out = []
    ledger = []
    for c in summary["cases"]:
        cid = c["id"]
        csv = PROCDIR / f"counterfactual_{cid}.csv"
        assert csv.exists(), f"missing daily series {csv} — rerun counterfactual_past_events.py"
        df = pd.read_csv(csv, parse_dates=["date"])
        ev = pd.Timestamp(c["event_date"])
        # CAUSALITY ASSERTS
        assert (df["date"] <= ev).all(), f"{cid}: series leaks past event date"
        assert df["date"].is_monotonic_increasing, f"{cid}: series not chronological"
        dates = df["date"].dt.strftime("%Y-%m-%d").tolist()
        hot = [b in ("High", "Critical") for b in df["band"]]
        eps = episodes(dates, hot)
        false_alarms = max(0, len(eps) - (1 if eps and eps[-1][1] >= dates[-7:][0] else 0))
        # first crossings
        first = {}
        for band in ("Moderate", "High", "Critical"):
            hit = df.index[df["band"] == band].tolist() or \
                df.index[df["band"].isin(BANDS[BANDS.index(band):])].tolist()
            first[band] = dates[hit[0]] if hit else None

        def lead(d):
            return (ev - pd.Timestamp(d)).days if d else None

        series = []
        for i, r in df.iterrows():
            series.append({
                "date": dates[i], "score": round(float(r["score"]), 1), "band": r["band"],
                "rain_24h": round(float(r["rain_24h"]), 1),
                "rain_7d": round(float(r["rain_7d"]), 1),
                "rain_30d": round(float(r["rain_30d"]), 1),
                "soil_moisture": round(float(r["soil_moisture"]), 4),
                "ndvi": round(float(r["ndvi"]), 3),
                "drivers": drivers_for(df, i),
            })
        cases_out.append({
            "id": cid, "title": c["title"], "site_name": c.get("site"),
            "event_date": c["event_date"], "event_date_fuzzy": c.get("event_date_fuzzy"),
            "event_note": c.get("event_note"), "sources": c.get("sources", []),
            "analogue": {"row": c.get("terrain_analogue_row"),
                         "distance_m": c.get("analogue_distance_m"),
                         "lulc": c.get("analogue_lulc")},
            "soil_source": c.get("soil_source"), "ndvi_source": c.get("ndvi_source"),
            "series": series,
        })
        ledger.append({
            "id": cid, "title": c["title"], "event_date": c["event_date"],
            "event_date_fuzzy": c.get("event_date_fuzzy"),
            "first_moderate": first["Moderate"], "first_high": first["High"],
            "first_critical": first["Critical"],
            "lead_high_days": lead(first["High"]),
            "lead_critical_days": lead(first["Critical"]),
            "early_hot_episodes": false_alarms,
        })
        log(f"{cid}: {len(series)} days, High {first['High']} ({lead(first['High'])}d lead), "
            f"Critical {first['Critical']}, early hot episodes {false_alarms}")

    bundle = {
        "causality": "every row uses inputs available ON that date only: trailing IMD sums, "
                     "same/prior-day soil (daily CCI or quasi-static fallback), one pre-event "
                     "S2 scene, static terrain; asserted (series <= event_date) at build.",
        "early_episode_definition": "contiguous High-or-worse runs separated by >=3 calm days, "
                                    "counting runs before the final pre-event run. These are EARLY hot episodes, "
                                    "not necessarily false: cf. Dipudara, where precursor slides a month before "
                                    "the collapse triggered the evacuation that saved lives.",
        "model": summary.get("model"), "generated": summary.get("generated"),
        "cases": cases_out, "ledger": ledger,
    }
    OUT.write_text(json.dumps(bundle, indent=1), encoding="utf-8")
    log(f"bundle -> {OUT} ({OUT.stat().st_size/1024:.0f} KB, "
        f"{sum(len(c['series']) for c in cases_out)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
