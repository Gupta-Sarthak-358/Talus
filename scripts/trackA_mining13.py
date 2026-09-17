"""Ingest mining pass 12: Sokpay promotion + onset schema (Phase IV-A).

  PROMOTE 1 championship (pool 21 -> 22): Sokpay-20230326 (EastMojo ground + ANI +
  NE NOW + NERising + SikkimExpress; Sunday ~0230; 4 houses, 18 families, NH cut).
  First MARCH (pre-monsoon) championship event.
  PROVENANCE: SadaPhamtam += NE NOW Jul-25 + NewsOnAir (triple; still post-archive).
  SCHEMA: onset_start/onset_end/event_definition/date_conflict/resolution_basis
  columns added; Mantam populated (progressive-onset precedent).
Run: mnemo-venv python scripts/trackA_mining13.py
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
CHAMP = REPO / "data/sih26001/evidence/championship_events_v1.csv"
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)
    for c in ("onset_start", "onset_end", "event_definition", "date_conflict",
              "resolution_basis"):
        if c not in d.columns:
            d[c] = ""

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    setrow(d["slide_no"] == "NEWS-MANTAM-20160813",
           onset_start="2016-08-02", onset_end="2016-08-08",
           event_definition="catastrophic Kanaka-damming collapse",
           date_conflict="NESAC inventory Aug-3 (early-phase onset)",
           resolution_basis="contemporaneous + institutional (SANDRP/TOI/DC-quotes/GSI/CWC/NRSC/HC-PIL)")
    setrow(d["slide_no"] == "NEWS-SADAPHAMTAM-20260725",
           source_2=d.loc[d["slide_no"] == "NEWS-SADAPHAMTAM-20260725", "source_2"].iloc[0]
           + " + NE NOW Jul-25 + NewsOnAir (Phamtam, triple)")

    new_rows = [
        {"slide_no": "NEWS-SOKPAY-20230326", "district": "Gangtok", "lat": 27.40,
         "lon": 88.53, "year": 2023, "month_hint": "March 2023", "exact_date": "2023-03-26",
         "time": "~02:30-03:00 Sun",
         "source": "EastMojo Mar 27 2023 ground (4 houses, 18 families, 2km scar, DM/resident names, 'every monsoon since 2016')",
         "source_url": "eastmojo.com Mar 27 2023",
         "source_2": "ThePrint/ANI Mar 27 + NE NOW Mar 27 + NortheastRising Mar 27 + SikkimExpress headline",
         "source_convergence": "multi (5 outlets)", "date_precision": "exact",
         "location_precision": "Sokpay village, Dikchu block (APPROX)",
         "fatalities": "0 (18 families evacuated)", "road_association": "NH Dikchu-Rakdong cut, Samdong alternate",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "single-event; FIRST MARCH/pre-monsoon championship event; chronic since 2016",
         "related_episode_id": "EP-MAR2023-SOKPAY", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "non-fatal mass-evacuation",
         "ceiling": "n/a-eligible", "onset_start": "", "onset_end": "",
         "event_definition": "overnight slope collapse", "date_conflict": "",
         "resolution_basis": ""},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    la, lo = 27.40, 88.53
    geo = bool(LON0 <= lo <= LON1 and LAT0 <= la <= LAT1)
    rain = (REPO / "data/raw/imd/ind2023_rfp25.nc").exists()
    sep = float(2 * 6371000.0 * np.arcsin(np.sqrt(
        np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
        * np.sin(np.radians(plo - lo) / 2) ** 2)).min())
    idx = d[d["slide_no"] == "NEWS-SOKPAY-20230326"].index[0]
    for k, v in {"contam_geo": str(geo), "contam_dem": "True", "contam_rain": str(rain),
                 "contam_soil": "daily-CCI", "contam_sat": "S2-check-at-replay",
                 "contam_prox_m": round(sep, 1),
                 "eligible_for_championship": str(bool(geo and rain))}.items():
        d.loc[idx, k] = v
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    log(f"Sokpay: geo={geo} rain={rain} prox={round(sep,1)}m")
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
