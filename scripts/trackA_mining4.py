"""Ingest mining pass 3 into Track A census (SIH26001 Phase IV-A).

  ELIGIBLE 1: Pathing/Gaguney-20221124 (PTI rescue + field GPS + peer paper).
  PROVISIONAL 2: SeesaGolai-20210601 (single + subsidence-mechanism caveat);
                 Sichey-20210609 (single-source, time conflict in article).
  REJECTED 1: BhaluKhola-20210617 (tunnel-face collapse, construction accident).
  PROVENANCE: pooled Oct-2021 event gains EastMojo Oct-20 ground report (16 slides, 20th Mile, Rangpo bridge 2am).
  DEFERRED (429): Jul-2020, May-2020-North, Sep-2021-Gangtok windows.
Run: mnemo-venv python scripts/trackA_mining4.py
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

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    setrow(d["slide_no"] == "NEWS-NH10-20211020",
           source_2=d.loc[d["slide_no"] == "NEWS-NH10-20211020", "source_2"].iloc[0]
           + " + EastMojo Oct-20 ground report (16 slides NH10, 20th-Mile cutoff, Rangpo bridge pillars 2am)")

    new_rows = [
        {"slide_no": "NEWS-PATHING-20221124", "district": "Namchi", "lat": 27.2955, "lon": 88.3924,
         "year": 2022, "month_hint": "November 2022", "exact_date": "2022-11-24",
         "time": "Thursday (rescue day; activity through Nov 27-28)",
         "source": "PTI/ThePrint Nov 24 2022 (60 families rescued, relief camp, Pathing S.Sikkim)",
         "source_url": "theprint.in Nov 24 2022",
         "source_2": "IndiaTodayNE Nov 27 (50+ houses) + SaveTheHills field GPS Nov 27-28 + peer paper (Gaguney N27d18.235 E88d23.797)",
         "source_convergence": "multi (wire + press + field GPS + peer-reviewed)",
         "date_precision": "exact",
         "location_precision": "Gaguney slide, Pathing Yangang (field GPS 27.2955,88.3924; paper 27.3039,88.3966)",
         "fatalities": "0 (60-76 families evacuated)", "road_association": "only village road blocked",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "reactivating chronic slide (29yr; Oct-2021 onset, Nov-2022 pulse): ONE sample at Nov-24 evacuation pulse",
         "related_episode_id": "EP-NOV2022-PATHING", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "non-fatal mass-evacuation chronic-slide"},
        {"slide_no": "NEWS-SEESAGOLAI-20210601", "district": "Gangtok", "lat": 27.324, "lon": 88.613,
         "year": 2021, "month_hint": "June 2021", "exact_date": "2021-06-01", "time": "Tuesday morning",
         "source": "EastMojo Jun 1 2021 (photos, 40m cave-in, Deorali-Titanic closure ~1 month)",
         "source_url": "eastmojo.com Jun 1 2021", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Seesa Golai NH10, Gangtok (APPROX)",
         "fatalities": "0", "road_association": "NH10 Deorali-Titanic barred ~1 month",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "MECHANISM CAVEAT: sinking/subsidence (construction/seepage/tremors per MLA), may not be a rainfall slide",
         "related_episode_id": "EP-JUN2021-GANGTOK", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "road-block (subsidence?)"},
        {"slide_no": "NEWS-SICHEY-20210609", "district": "Gangtok", "lat": 27.31, "lon": 88.60,
         "year": 2021, "month_hint": "June 2021", "exact_date": "2021-06-09",
         "time": "conflicting (wee hours vs 7PM in same article)",
         "source": "Sikkim Today Jun 9 2021 (house buried, Sichey Tamang Gumpa, 1 dead 1 injured)",
         "source_url": "thesikkimtoday.com Jun 9 2021", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Sichey near Tamang Gumpa, Gangtok (APPROX)",
         "fatalities": "1 + 1 injured", "road_association": "",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier3",
         "event_identity": "single-event; needs corroboration + time resolution",
         "related_episode_id": "EP-JUN2021-GANGTOK", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "fatal"},
        {"slide_no": "NEWS-BHALUKHOLA-20210617", "district": "Kalimpong", "lat": 27.09, "lon": 88.45,
         "year": 2021, "month_hint": "June 2021", "exact_date": "2021-06-17", "time": "Thursday night",
         "source": "HT Jun 18 + NewsBytes Jun 18 2021 (tunnel No.10 face, Bhalu Khola, 2 Jharkhand labourers)",
         "source_url": "hindustantimes.com Jun 18 2021", "source_2": "dual (but same wire facts)",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Tunnel No.10 Bhalu Khola-Tar Khola, Sevoke-Rangpo rail (APPROX)",
         "fatalities": "2 + 5 injured", "road_association": "",
         "status": "rejected", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "REJECTED: underground tunnel-face strata collapse (construction accident), not an open-slope landslide",
         "related_episode_id": "EP-JUN2021-RAIL", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "n/a", "rainfall_status": "n/a",
         "satellite_status": "n/a", "event_type": "rejected (mechanism)"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)

    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["slide_no"].isin(
            {"NEWS-PATHING-20221124", "NEWS-SEESAGOLAI-20210601", "NEWS-SICHEY-20210609",
             "NEWS-BHALUKHOLA-20210617", "NEWS-NH10-20211020"})].iterrows():
        la, lo = float(r["lat"]), float(r["lon"])
        geo = bool(LON0 <= lo <= LON1 and LAT0 <= la <= LAT1)
        dem = bool(88.0 <= lo <= 89.0 and 27.0 <= la <= 28.0)
        try:
            rain = (REPO / f"data/raw/imd/ind{int(str(r['exact_date'])[:4])}_rfp25.nc").exists()
        except Exception:
            rain = False
        sep = float(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
            * np.sin(np.radians(plo - lo) / 2) ** 2)).min())
        d.loc[idx, "contam_geo"] = str(geo)
        d.loc[idx, "contam_dem"] = str(d.loc[idx, "DEM_status"] == "COVERED" and dem)
        d.loc[idx, "contam_rain"] = str(rain)
        d.loc[idx, "contam_prox_m"] = round(sep, 1)
        elig = bool(geo and str(r["status"]) == "mined-exact"
                    and str(r["exactness_status"]).startswith("EXACT_")
                    and "PROVISIONAL" not in str(r["exactness_status"])
                    and "REJECTED" not in str(r["event_identity"]))
        d.loc[idx, "eligible_for_championship"] = str(elig)
        log(f"  {r['slide_no']}: geo={geo} rain={rain} prox={round(sep,1)}m elig={elig}")
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    log(f"rows={len(d)} eligible={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
