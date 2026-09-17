"""Ingest mining pass 4: NER-wide search, support-constrained classification (Phase IV-A).

  TRANSFER-ELIGIBLE 3: Tigdo-20200710 + ModiRijo-20200710 (same Itanagar episode, two points),
                       Tupul-20220630 (GSI three-phase, ONE sample).
  PROVISIONAL-TRANSFER 4: Sood-20220619, Hollongi-20200923, ItanagarNH415-20190717, NH29-20190704.
  NOTED-NOT-ADDED: Nagaland Jul-Aug-2018 statewide aggregate (no exact date/point — phantom class).
  DEFERRED (429): Mizoram, Tripura, Meghalaya-2023 windows.
  Championship pool expected UNCHANGED (all out-of-box); the classifier proves itself.
Run: mnemo-venv python scripts/trackA_mining5.py
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
        {"slide_no": "NEWS-TIGDO-20200710", "district": "Papum Pare, Arunachal", "lat": 27.14,
         "lon": 93.70, "year": 2020, "month_hint": "July 2020", "exact_date": "2020-07-10",
         "time": "02:30 Fri",
         "source": "Arunachal Times Jul 10-11 2020 (Tigdo Yupia, 4 dead incl 8-month infant, names, DC/SP visit)",
         "source_url": "archive.arunachaltimes.in Jul 11 2020",
         "source_2": "NewsMill Jul 10 (Tigdo family as 1st of 2 Friday slides) + CM Khandu tweet",
         "source_convergence": "multi", "date_precision": "exact",
         "location_precision": "Tigdo village near Yupia (APPROX)",
         "fatalities": "4 + house hit thrice before (ignored warnings)", "road_association": "",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event (point 1 of 2 in Friday Itanagar episode)",
         "related_episode_id": "EP-JUL2020-ITANAGAR", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-MODIRIJO-20200710", "district": "Papum Pare, Arunachal", "lat": 27.10,
         "lon": 93.62, "year": 2020, "month_hint": "July 2020", "exact_date": "2020-07-10",
         "time": "11:30 Fri",
         "source": "Arunachal Times Jul 10-11 2020 (Modi Rijo 6 Kilo NH415, 3 dead + 1 missing, SDRF/police/CRPF search)",
         "source_url": "archive.arunachaltimes.in Jul 11 2020",
         "source_2": "NewsMill Jul 10 (2nd Friday slide) + CM Khandu tweet + IMD Guwahati Wed warning for Thu-Fri",
         "source_convergence": "multi", "date_precision": "exact",
         "location_precision": "Modi Rijo near 6 Kilo, NH415 Itanagar-Naharlagun (APPROX)",
         "fatalities": "3 + 1 missing (Lokam Minu 22)", "road_association": "NH415 corridor",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event (point 2 of 2, 9h after Tigdo, ~10km apart); mudslide from dumping site",
         "related_episode_id": "EP-JUL2020-ITANAGAR", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-TUPUL-20220630", "district": "Noney, Manipur", "lat": 24.94, "lon": 93.66,
         "year": 2022, "month_hint": "June 2022", "exact_date": "2022-06-30", "time": "00:30 Thu (night Jun 29-30)",
         "source": "The Hindu Jul 1 + Telegraph Jul 1 + IE Jul 3-19 2022 (Tupul rail camp, 56-58 dead)",
         "source_url": "thehindu.com Jul 1 2022",
         "source_2": "GSI preliminary report Jul 8 (three phases 0030/0600 + Part C, 0.6 sq km, unprotected slope cut) + Wikipedia",
         "source_convergence": "multi + GSI", "date_precision": "exact",
         "location_precision": "Tupul station yard, Maranching hill, Noney (APPROX)",
         "fatalities": "56-58 (29 TA + 29 civilians) + 3 missing", "road_association": "Imphal-Jiribam rail",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "GSI three phases SAME night = ONE sample (explicit anti-split guard); rain + weak soil + slope-cut",
         "related_episode_id": "EP-JUN2022-TUPUL", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal mass-casualty"},
        {"slide_no": "NEWS-SOOD-20220619", "district": "Papum Pare, Arunachal", "lat": 27.13,
         "lon": 93.72, "year": 2022, "month_hint": "June 2022", "exact_date": "2022-06-19",
         "time": "Sunday morning",
         "source": "NE NOW Jun 19 2022 (boxer Rage Hilli 16, Sood village, bike to trials)",
         "source_url": "nenow.in Jun 19 2022", "source_2": "CM Khandu condolence tweet (weak)",
         "source_convergence": "single+weak", "date_precision": "exact-provisional",
         "location_precision": "Sood village, Yupia side (APPROX)", "fatalities": "1",
         "road_association": "", "status": "provisional-exact", "precision_status": "EXACT_VERIFIED",
         "priority": "mined", "source_tier": "Tier3",
         "event_identity": "single-event; needs press corroboration",
         "related_episode_id": "EP-JUN2022-ITANAGAR", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-HOLLONGI-20200923", "district": "Papum Pare, Arunachal", "lat": 27.08,
         "lon": 93.70, "year": 2020, "month_hint": "September 2020", "exact_date": "2020-09-23",
         "time": "Wednesday (~0845-1145 block)",
         "source": "Arunachal Times Sep 23-24 2020 (NH415 Hollongi-Chimpu 6KM, 3h block, EE quotes)",
         "source_url": "archive.arunachaltimes.in Sep 24 2020", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "6KM Hollongi checkgate-Chimpu, NH415 (APPROX)", "fatalities": "0",
         "road_association": "NH415 3h block", "status": "provisional-exact",
         "precision_status": "EXACT_VERIFIED", "priority": "mined", "source_tier": "Tier3",
         "event_identity": "single-event; needs corroboration",
         "related_episode_id": "EP-SEP2020-ITANAGAR", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "road-block"},
        {"slide_no": "NEWS-ITANAGAR-20190717", "district": "Papum Pare, Arunachal", "lat": 27.101,
         "lon": 93.623, "year": 2019, "month_hint": "July 2019", "exact_date": "2019-07-17",
         "time": "Wednesday",
         "source": "NE NOW Jul 17 2019 (NH415 police HQ, 2 seriously injured, vehicles destroyed)",
         "source_url": "nenow.in Jul 17 2019", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "NH415 near police HQ, Itanagar (APPROX)",
         "fatalities": "0 (2 seriously injured)", "road_association": "NH415 blocked, vehicles destroyed",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier3",
         "event_identity": "single-event; needs corroboration",
         "related_episode_id": "EP-JUL2019-ITANAGAR", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "road-block"},
        {"slide_no": "NEWS-NH29-20190704", "district": "Kohima, Nagaland", "lat": 25.66, "lon": 94.09,
         "year": 2019, "month_hint": "July 2019", "exact_date": "2019-07-04",
         "time": "Thursday morning (sinking since Wed 11pm)",
         "source": "EastMojo Jul 4 2019 (NH29 KMC dumping site, 15m sunk 2m, 100+ vehicles, PWD EE quotes)",
         "source_url": "eastmojo.com Jul 4 2019", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "NH29 near old KMC dumping site, Kohima (APPROX)",
         "fatalities": "0", "road_association": "NH29 Kohima-Dimapur cut, chronic site (400m Jul-2018, reopened Sep-29)",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "chronic NH29 sinking site; needs corroboration",
         "related_episode_id": "EP-JUL2019-KOHIMA", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "road-block chronic-site"},
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
        d.loc[idx, "contam_dem"] = str(False)
        d.loc[idx, "contam_rain"] = str(rain)
        d.loc[idx, "contam_prox_m"] = round(sep, 1)
        elig = bool(geo and str(r["status"]) == "mined-exact"
                    and str(r["exactness_status"]).startswith("EXACT_")
                    and "PROVISIONAL" not in str(r["exactness_status"]))
        d.loc[idx, "eligible_for_championship"] = str(elig)
        log(f"  {r['slide_no']}: geo={geo} rain={rain} prox={round(sep/1000,0)}km transfer_elig={str(r['status'])=='mined-exact'}")
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    tr = d[(d["geography_status"] == "OUT_OF_DOMAIN_TRANSFER") & (d["status"] == "mined-exact")]
    log(f"rows={len(d)} championship={len(elig)} transfer_eligible={len(tr)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
