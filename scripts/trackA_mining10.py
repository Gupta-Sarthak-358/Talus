"""Ingest mining pass 9: steer-test + post-archive consistency (Phase IV-A).

  PROVENANCE (no new samples):
    DARJ-20150701 += TOI Jul-1-2 2015 ground detail (36 dead, Saureni 20, rain gauges);
      notes Saureni-2015 vs Soureni-2025 same-area 10yr recurrence (observation, not a row).
    MAJWA-20240610 += Telegraph Jun-11-2024 (Majuwa Yangang Monday: 2 dead + 1 missing,
      8 houses) — confirms duplicate-guard.
  NEW PROVISIONAL 1: SadaPhamtam-20260725 (in-box, dual, post-archive rain pending).
  NEW REJECTED 1: Samardung-20260720 (Teesta-VI under-construction TUNNEL, BhaluKhola rule).
  NOTED-NOT-ADDED: Yuksam-Sep-2019 (no exact date), NH10-Jul-2019 40h blockade (aggregate),
    Rangma-Sep-2012 (single + unlocalizable + pre-S2), Ravangla-Sep-2026 (single, post-archive).
  Championship unchanged at 20.
Run: mnemo-venv python scripts/trackA_mining10.py
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    _s2 = d.loc[d["slide_no"] == "NEWS-DARJ-20150701", "source_2"].iloc[0]
    _s2 = "" if pd.isna(_s2) else str(_s2)
    setrow(d["slide_no"] == "NEWS-DARJ-20150701",
           source_2=(_s2 + " + TOI Jul-1-2 2015 (Saureni 20/Mirik 7/Kalimpong 7/Rangbang, gauges Kurseong 185mm)").strip(" +"),
           event_identity="multi-slide episode Jul-1-2015 night (Saureni/Mirik/Kalimpong): ONE sample; "
                          "OBS: Saureni-2015 vs Soureni-2025 same area, 10yr recurrence")
    setrow(d["slide_no"] == "NEWS-MAJWA-20240610",
           source_2="HT Jun 2024 + Telegraph Jun-11-2024 (Majuwa Yangang Monday: 2 dead + 1 missing, 8 houses, flash flood)",
           source_convergence="dual (duplicate confirmed)")

    new_rows = [
        {"slide_no": "NEWS-SADAPHAMTAM-20260725", "district": "Namchi", "lat": 27.16,
         "lon": 88.36, "year": 2026, "month_hint": "July 2026", "exact_date": "2026-07-25",
         "time": "Saturday afternoon (secondary slide on clearance crew)",
         "source": "IndiaTodayNE Jul 25 2026 (Sada-Phamtam Rd, Lal Bahadur Rai 18 + Man Bahadur Gurung 61, 4 injured)",
         "source_url": "indiatodayne.in Jul 25 2026",
         "source_2": "NEWire Jul 25 2026 (same names/crew/secondary-slide detail)",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Sada-Phamtam road, Namchi (APPROX)",
         "fatalities": "2 + 4 injured", "road_association": "clearance-crew secondary failure",
         "status": "provisional-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2/3",
         "event_identity": "genuine secondary slope failure; POST-ARCHIVE (no IMD-2026) -> feature-pending",
         "related_episode_id": "EP-JUL2026-NAMCHI", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED",
         "rainfall_status": "PENDING (ind2026?)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal?"},
        {"slide_no": "NEWS-SAMARDUNG-20260720", "district": "Namchi", "lat": 27.20, "lon": 88.40,
         "year": 2026, "month_hint": "July 2026", "exact_date": "2026-07-20", "time": "~15:09 Mon",
         "source": "HT Jul 21 + Swarajya Jul 21 2026 (Samardung Teesta-VI tunnel, 8-10 dead, 19 trapped, methane leak)",
         "source_url": "hindustantimes.com Jul 21 2026", "source_2": "multi",
         "source_convergence": "multi", "date_precision": "exact",
         "location_precision": "Samardung tunnel, Jholungey, Teesta Stage-VI (APPROX)",
         "fatalities": "8-10 + trapped", "road_association": "",
         "status": "rejected", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "REJECTED: under-construction TUNNEL collapse 3km inside (BhaluKhola precedent), 4th application of excavation rule",
         "related_episode_id": "EP-JUL2026-NAMCHI", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "n/a", "rainfall_status": "n/a",
         "satellite_status": "n/a", "event_type": "rejected (mechanism)"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["slide_no"].isin({n["slide_no"] for n in new_rows})].iterrows():
        la, lo = float(r["lat"]), float(r["lon"])
        geo = bool(LON0 <= lo <= LON1 and LAT0 <= la <= LAT1)
        try:
            rain = (REPO / f"data/raw/imd/ind{int(str(r['exact_date'])[:4])}_rfp25.nc").exists()
        except Exception:
            rain = False
        sep = float(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
            * np.sin(np.radians(plo - lo) / 2) ** 2)).min())
        d.loc[idx, "contam_geo"] = str(geo)
        d.loc[idx, "contam_rain"] = str(rain)
        d.loc[idx, "contam_prox_m"] = round(sep, 1)
        elig = bool(geo and rain and str(r["status"]) == "mined-exact"
                    and "PROVISIONAL" not in str(r["exactness_status"])
                    and "REJECTED" not in str(r["event_identity"]))
        d.loc[idx, "eligible_for_championship"] = str(elig)
        log(f"  {r['slide_no']}: geo={geo} rain={rain} elig={elig}")
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
