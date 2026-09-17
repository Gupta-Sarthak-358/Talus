"""Ingest pass 16: Tsong promotion (Phase IV-A).

  PROMOTE 1 championship (pool 22 -> 23): Tsong-20190916.
    govt IPR Tier-1 + EastMojo Sep-19 (Tsong-named) + TNT Sep-18 (cloudburst,
    100+ homeless) + EastMojo Sep-20 (CM visit Tsong/Mangtabung, ex-gratia,
    deceased Buddhi Subba 81) + NewsClick Sep-28 (8km Yuksom, 30-45min, bridges).
    Mangtabung kept as same-episode context, not a row.
  HOLD: MyongKyong (detail richer, still single-outlet).
  NOTED: Oct-19-2021 South Sikkim govt damage aggregate (multi-point, no incident).
Run: mnemo-venv python scripts/trackA_mining17.py
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
CHAMP = REPO / "data/sih26001/evidence/championship_events_v1.csv"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    setrow(d["slide_no"] == "NEWS-TSONG-20190916",
           source_2="EastMojo Sep-19 (Tsong-named) + TNT Sep-18 (Sep-16 cloudburst, 100+ homeless) "
                    "+ EastMojo Sep-20 (CM Tsong/Mangtabung visit, ex-gratia, Buddhi Subba 81) "
                    "+ NewsClick Sep-28 (30-45min, 5 Rangeet bridges)",
           source_convergence="multi (5 outlets incl Tier-1 govt)",
           time="Sep-16 evening cloudburst (30-45min)",
           fatalities="1 (Buddhi Subba 81, died after 2 days)",
           status="mined-exact", precision_status="EXACT_MULTI_SOURCE",
           exactness_status="EXACT_MULTI_SOURCE",
           event_identity="single-event: Tsong cloudburst mass-evacuation (300 homeless, whole village); "
                          "Mangtabung = same-episode context, not a row",
           event_definition="evening cloudburst, village washout",
           event_type="fatal cloudburst mass-evacuation",
           ceiling="n/a-eligible")
    d.loc[d["slide_no"] == "NEWS-TSONG-20190916", "eligible_for_championship"] = "True"
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
