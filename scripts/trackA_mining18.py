"""Ingest pass 17: final-sweep verdicts (Phase IV-A).

  +1 PROVISIONAL: 29MILE-20200827 (TT Aug-28-2020 mirror: Thursday wee hours, truck
  buried + 4 houses, 18h cut; single-source; T-30 overlaps Sep-23-2020 same site ->
  same-side split law pre-applied in identity).
  CLOSE Dentam lead: 2023 flood-dominant, 2024 aggregate-no-incident, 2012 pre-S2 aggregate.
  NOTED: Sichey-20250512 substation slide (dual, exact, but minor + post-archive — docs only);
  SetiJhora Sep-23-2023 recurrence (toe-erosion ambiguity — docs only).
  Pool holds 23 -> FREEZE per evidence-ceiling decision.
Run: mnemo-venv python scripts/trackA_mining18.py
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)
    new_rows = [
        {"slide_no": "NEWS-29MILE-20200827", "district": "Kalimpong", "lat": 27.0144,
         "lon": 88.4359, "year": 2020, "month_hint": "August 2020", "exact_date": "2020-08-27",
         "time": "Thursday wee hours",
         "source": "Telegraph TT Aug-28-2020 via mirror (29th Mile, truck buried + 4 houses, 18h NH10 cut)",
         "source_url": "newsmaxtobago mirror Aug 28 2020", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "29th Mile NH10 (same field-GPS site)",
         "fatalities": "0", "road_association": "NH10 cut 18h, single-file by evening",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "chronic 29-Mile site, 5th dated hit; T-30 overlaps Sep-23-2020 same site -> "
                          "same-side split law applies if promoted; needs corroboration",
         "related_episode_id": "EP-AUG2020-NE", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "road-block chronic-site?",
         "ceiling": "YES-corroboration", "onset_start": "", "onset_end": "",
         "event_definition": "wee-hours debris, truck buried", "date_conflict": "",
         "resolution_basis": ""},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    d.loc[d["slide_no"] == "NEWS-29MILE-20200827",
          ["contam_geo", "contam_dem", "contam_rain", "contam_prox_m",
           "eligible_for_championship"]] = ["True", "True", "True", 412.4, "False"]
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    log(f"rows={len(d)} championship={len(elig)} -> FREEZE at {len(elig)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
