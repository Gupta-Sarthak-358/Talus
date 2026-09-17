"""Ingest pass 14: admin sweep verdicts (Phase IV-A).

  +2 PROVISIONAL: Tsong-20190916 (Tier-1 govt IPR, needs Tsong-specific corroboration;
  EastMojo Sep-19 supports episode only); UpperRimbi-20250912 (6 outlets, post-archive
  rain pending; Sardong Sep-13 kept as same-episode context, not a row).
  NOTED: Martam slide GPS 27.2596,88.5506 (academic, no exact event date — context only).
  DEFERRED (429): Sichey-final, West-2-dead-3-injured, Melli-2021, Kalimpong-2020.
  Pool holds 22.
Run: mnemo-venv python scripts/trackA_mining15.py
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
    new_rows = [
        {"slide_no": "NEWS-TSONG-20190916", "district": "Gyalshing", "lat": 27.35, "lon": 88.20,
         "year": 2019, "month_hint": "September 2019", "exact_date": "2019-09-16",
         "time": "evening (rescue since 16th eve, reported 17th)",
         "source": "sikkim.gov.in IPR Sep 17 2019 (Tsong evacuation + relief, Yuksam camp, lady rescued)",
         "source_url": "sikkim.gov.in Sep 17 2019", "source_2": "EastMojo Sep 19 (Yuksam episode support, not Tsong-specific)",
         "source_convergence": "single-Tier1 (event); episode corroborated",
         "date_precision": "exact-provisional",
         "location_precision": "Tsong village, Yuksam-Tashiding (APPROX)",
         "fatalities": "0 reported (1 rescued)", "road_association": "roads washed, power/water cut (Tsong unrestored longest)",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier1",
         "event_identity": "single-event; needs Tsong-specific second source",
         "related_episode_id": "EP-SEP2019-YUKSAM", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "mass-evacuation?",
         "ceiling": "YES-corroboration", "onset_start": "", "onset_end": "",
         "event_definition": "evening mudslides, village evacuation", "date_conflict": "",
         "resolution_basis": ""},
        {"slide_no": "NEWS-UPPERRIMBI-20250912", "district": "Gyalshing", "lat": 27.29,
         "lon": 88.23, "year": 2025, "month_hint": "September 2025", "exact_date": "2025-09-12",
         "time": "~midnight Thu-Fri",
         "source": "TOI Sep 12 2025 (Upper Rimbi Yangthang: 4 dead + 3 missing, SP Sherpa, log bridge)",
         "source_url": "timesofindia Sep 12 2025",
         "source_2": "ET + Zee/ANI + Daijiworld (named victims) + NE Live (7yo survivor) + IE Sep 14 (Sardong same-episode context)",
         "source_convergence": "multi (6 outlets)", "date_precision": "exact",
         "location_precision": "Upper Rimbi, Yangthang, W.Sikkim (APPROX)",
         "fatalities": "4 + 3 missing", "road_association": "access cut, Hume river flooded",
         "status": "provisional-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "POST-ARCHIVE (no ind2025); Sardong Sep-13 kept as context not a row",
         "related_episode_id": "EP-SEP2025-RIMBI", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED",
         "rainfall_status": "PENDING (ind2025?)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal?", "ceiling": "YES-IF-ARCHIVE(ind2025)",
         "onset_start": "", "onset_end": "", "event_definition": "midnight hillside collapse",
         "date_conflict": "", "resolution_basis": ""},
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
        d.loc[idx, "eligible_for_championship"] = "False"
        log(f"  {r['slide_no']}: geo={geo} rain={rain} (provisional)")
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
