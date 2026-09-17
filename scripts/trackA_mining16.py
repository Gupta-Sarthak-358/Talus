"""Ingest pass 15: Mamkhola verdict + 29-Mile GPS refinement (Phase IV-A).

  REJECT 1: Mamkhola-20210730 (5 outlets but flash-flood rivulet washaway of a
  construction labour camp + boulders — flood-dominant, occupational setting;
  Melli Bazaar houses kept as same-episode context, not a row).
  REFINE 3: 29-Mile eligible rows (20200923/20210711/20210906) adopt SaveTheHills
  field GPS 27.0144,88.4359 (documented refinement, ~4km from approx).
  HOLD: Sichey (press budget exhausted; admin-archive avenue remains).
  NOTED: SetiJhora Sep-23-2020 = toe erosion, explicitly not a slide.
Run: mnemo-venv python scripts/trackA_mining16.py
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
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

    for s in ("NEWS-29MILE-20200923", "NEWS-29MILE-20210711", "NEWS-29MILE-20210906"):
        setrow(d["slide_no"] == s, lat=27.0144, lon=88.4359,
               location_precision="29th Mile NH10 (SaveTheHills field GPS 27.0144,88.4359, Sep-2020 site visit; Rambi town itself 26.98 out-of-box)",
               contam_geo="True", contam_dem="True")
    setrow(d["slide_no"] == "NEWS-SICHEY-20210609",
           ceiling="YES-corroboration (press budget exhausted; admin-archive avenue remains)",
           event_identity="single-event; press re-searches exhausted over 4 rounds; Sikkim Express "
                          "print-archive / DDMA record is the remaining avenue")

    new_rows = [
        {"slide_no": "NEWS-MAMKHOLA-20210730", "district": "Kalimpong", "lat": 27.15,
         "lon": 88.50, "year": 2021, "month_hint": "July 2021", "exact_date": "2021-07-30",
         "time": "early Friday morning",
         "source": "India Today Jul 30 + Hindu/PTI Jul 31 + NIEP/PTI Jul 31 (Mamkhola ITDCL camp, 1 dead + 5 missing)",
         "source_url": "indiatoday.in Jul 30 2021",
         "source_2": "NE24 Jul 30 + IndiaTodayNE Jul 30 + Arunachal24 (same wire facts; Melli Bazaar 10 houses same episode context)",
         "source_convergence": "multi (5 outlets, same-wire)", "date_precision": "exact",
         "location_precision": "Mamkhola ITDCL rail camp near Rangpo, Kalimpong PS (APPROX)",
         "fatalities": "1 + 5 missing (Dhan Singh Bhandari 35)", "road_association": "NH10 Rangpo-Melli cut, Mamkhola culvert",
         "status": "rejected", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "REJECTED 2026-09-18: flash-flood rivulet washaway of construction labour camp "
                          "(flood-dominant + occupational); boulders secondary. Melli Bazaar houses = context.",
         "related_episode_id": "EP-JUL2021-MAMKHOLA", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "n/a", "rainfall_status": "n/a",
         "satellite_status": "n/a", "event_type": "rejected (mechanism)",
         "ceiling": "NO-mechanism", "onset_start": "", "onset_end": "",
         "event_definition": "rivulet washaway of camp", "date_conflict": "",
         "resolution_basis": ""},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["slide_no"].isin(
            {"NEWS-MAMKHOLA-20210730", "NEWS-29MILE-20200923", "NEWS-29MILE-20210711",
             "NEWS-29MILE-20210906"})].iterrows():
        la, lo = float(r["lat"]), float(r["lon"])
        sep = float(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
            * np.sin(np.radians(plo - lo) / 2) ** 2)).min())
        d.loc[idx, "contam_prox_m"] = round(sep, 1)
    d.loc[d["slide_no"] == "NEWS-MAMKHOLA-20210730", "contam_geo"] = "True"
    d.loc[d["slide_no"] == "NEWS-MAMKHOLA-20210730", "contam_rain"] = "True"
    d.loc[d["slide_no"] == "NEWS-MAMKHOLA-20210730", "eligible_for_championship"] = "False"
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
