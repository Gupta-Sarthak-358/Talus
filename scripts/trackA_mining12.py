"""Ingest mining pass 11: So Bhir resolution (SIH26001 Phase IV-A).

  PROMOTE 1 championship (pool 20 -> 21): SoBhir/Mantam.
    DATE RESOLUTION: NESAC Aug-3 = early-phase onset; catastrophic Kanaka-damming
    collapse Aug-13 ~1230-1330 (SANDRP+TOI+Telegraph/DC-quotes+GSI-at-site+CWC/NRSC).
    T = 2016-08-13 (reconstructable incident); onset window logged, not hidden.
    Corroboration: SANDRP, TOI, Telegraph, Koley-et-al-2020 peer-reviewed, Martha
    satellite assessment, DownToEarth (HC PIL), CWC alert, EastMoJo-2020.
  CLOSE Bey lead: 2011-earthquake-triggered (mechanism + pre-S2) — noted, not a row.
  STILL DEFERRED: Sokpay, Namchi-40, Tsong, Martam, W.Sikkim-2-dead (429s).
Run: mnemo-venv python scripts/trackA_mining12.py
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

    setrow(d["slide_no"] == "NEWS-SOBHIR-20160803",
           slide_no="NEWS-MANTAM-20160813",
           exact_date="2016-08-13", time="~12:30-13:30 Sat (catastrophic damming collapse)",
           source="SANDRP Aug 14 2016 (So Bhir hillock ~1230, 50m dam, TOI/CWC/NRSC/SaveTheHills detail)",
           source_url="sandrp.in Aug 14 2016",
           source_2="Telegraph/KalimpongOnline Aug 14-15 (25 families Mantam->Tingvong, DC Bonpo, GSI at site) "
                    "+ TOI Aug 19 (CWC dam-break alert) + Koley et al 2020 peer-reviewed (1330, 30 houses, EMAP) "
                    "+ Martha satellite assessment + DownToEarth (HC suo-motu PIL) + NESAC GPS inventory",
           source_convergence="multi (8+ outlets/institutions)",
           location_precision="So Bhir cliff, Mantam/Mentam, Dzongu (GPS 27.5397,88.5007, HIGH)",
           fatalities="0 (25 families evacuated, 13 villages cut off)",
           road_association="300m road + Kanka bridge submerged; Teesta-V reservoir emptied precautionarily",
           status="mined-exact", precision_status="EXACT_MULTI_SOURCE",
           event_identity="DATE RESOLVED: progressive failure (onset Aug 2-8 per STH/SANDRP; NESAC Aug-3 early phase); "
                          "T = Aug-13 damming collapse (timed, institutional response). ONE sample.",
           related_episode_id="EP-AUG2016-MANTAM",
           exactness_status="EXACT_MULTI_SOURCE",
           satellite_status="Cartosat-2B/Landsat-8 (NRSC Aug-15 analysis)",
           event_type="non-fatal high-exposure valley-blocking",
           ceiling="n/a-eligible")
    d.loc[d["slide_no"] == "NEWS-MANTAM-20160813", "eligible_for_championship"] = "True"
    d.loc[d["slide_no"] == "NEWS-MANTAM-20160813", "contam_geo"] = "True"
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
