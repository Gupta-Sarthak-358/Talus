"""Ingest mining pass 5 into Track A census (SIH26001 Phase IV-A).

  29-MILE RESOLVED: 3 outlets + mile-marker math place it between Teesta and Rambi
  (~27.05,88.43, in-box); the lone '60km-from-Rangpo' is outweighed reporter error.
  PROMOTE 2 championship: 29Mile-20210711 (quad) + 29Mile-20210906 (dual).
  PROVISIONAL 1 in-domain: 29Mile-20200923 (single Morung/PTI).
  TRANSFER-ELIGIBLE 3: Tripura May-18 pair (two points, one morning) + Nongstoin-20230617.
  PROVISIONAL-TRANSFER 5: Tripura May-20 pair, Lumshong-20220616, Pynthor-20231008, Rngain-20230414.
  SKIPPED with reason: Mawsynram truck gorge (road accident), Guwahati guard-wall (structural).
  DEFERRED (429): Mizoram, Jul-2020-Sikkim windows.
Run: mnemo-venv python scripts/trackA_mining6.py
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

    setrow(d["slide_no"] == "NEWS-29MILE-20210906",
           lat=27.05, lon=88.43,
           location_precision="29th Mile NH10 between Teesta and Rambi (3 outlets + mile-marker math; lone 60km-from-Rangpo outweighd as reporter error)",
           status="mined-exact",
           geography_status="IN_DOMAIN", DEM_status="COVERED",
           event_identity="chronic 29-Mile site, DISTINCT date (3rd of 4: Jul-11-21, Sep-6-21, Oct-20-21, +Sep-23-20 prov)",
           event_type="non-fatal road-block chronic-site")

    new_rows = [
        {"slide_no": "NEWS-29MILE-20210711", "district": "Kalimpong", "lat": 27.05, "lon": 88.43,
         "year": 2021, "month_hint": "July 2021", "exact_date": "2021-07-11",
         "time": "Sunday morning major (Sat-night minors)",
         "source": "HT Jul 11 + NDTV Jul 11 + ET/PTI Jul 11 (29th Mile Teesta-Rambi, NH10 fully blocked)",
         "source_url": "hindustantimes.com Jul 11 2021",
         "source_2": "Sikkim Today Jul 11 (0700 block, orange alert) + BRO clearing detail",
         "source_convergence": "quad", "date_precision": "exact",
         "location_precision": "29th Mile NH10 between Teesta and Rambi (APPROX, resolved)",
         "fatalities": "0 reported", "road_association": "NH10 fully blocked, 1km+ queues both sides",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "chronic 29-Mile site, DISTINCT date (1st of dated series); T-30 clear of Sep-6",
         "related_episode_id": "EP-JUL2021-NE", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "non-fatal road-block chronic-site"},
        {"slide_no": "NEWS-29MILE-20200923", "district": "Kalimpong", "lat": 27.05, "lon": 88.43,
         "year": 2020, "month_hint": "September 2020", "exact_date": "2020-09-23",
         "time": "Wednesday morning",
         "source": "Morung Express/PTI Sep 23 2020 (major slide, 29 Mile WB, Sikkim cut off)",
         "source_url": "morungexpress.com 2020", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "29 Mile NH10 West Bengal (same resolved site, APPROX)",
         "fatalities": "", "road_association": "NH10 cut",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "chronic 29-Mile site, earliest dated hit; needs corroboration",
         "related_episode_id": "EP-SEP2020-NE", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "road-block chronic-site?"},
        {"slide_no": "NEWS-SUBALSINGH-20180518", "district": "Khowai, Tripura", "lat": 23.99,
         "lon": 91.55, "year": 2018, "month_hint": "May 2018", "exact_date": "2018-05-18",
         "time": "05:30 Fri",
         "source": "Firstpost/PTI May 18 2018 (Subal Singh Para family of 3, SP + CM quotes)",
         "source_url": "firstpost.com May 18 2018",
         "source_2": "NE NOW May 18 (same names/timing) + HT May 21 six-toll aggregate",
         "source_convergence": "multi", "date_precision": "exact",
         "location_precision": "Subal Singh Para, ~35km Agartala/10km Khowai foothills (APPROX)",
         "fatalities": "3 (family) + 1 child injured", "road_association": "",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event (point 1 of 2 Friday morning)",
         "related_episode_id": "EP-MAY2018-TRIPURA", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-KAMBUK-20180518", "district": "Khowai, Tripura", "lat": 24.00, "lon": 91.56,
         "year": 2018, "month_hint": "May 2018", "exact_date": "2018-05-18", "time": "~05:30 Fri",
         "source": "Firstpost/PTI May 18 2018 (Malendra Debbarma 65, Kambukcherra)",
         "source_url": "firstpost.com May 18 2018",
         "source_2": "NE NOW May 18 (Belfungpara variant name, same toll)",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Kambukcherra/Belfungpara near Kambhukcherra, W.Tripura (APPROX)",
         "fatalities": "1", "road_association": "",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event (point 2 of 2 Friday morning, ~10km from point 1)",
         "related_episode_id": "EP-MAY2018-TRIPURA", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-PALKU-20180520", "district": "Gomati, Tripura", "lat": 23.90, "lon": 91.50,
         "year": 2018, "month_hint": "May 2018", "exact_date": "2018-05-20", "time": "Sunday",
         "source": "India.com/PTI May 20 2018 (18yo woman, Palku Gomati)",
         "source_url": "india.com May 20 2018", "source_2": "HT May 21 six-toll (aggregate support)",
         "source_convergence": "single+aggregate", "date_precision": "exact-provisional",
         "location_precision": "Palku village, Gomati (APPROX)", "fatalities": "1",
         "road_association": "", "status": "provisional-exact",
         "precision_status": "EXACT_VERIFIED", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event; needs direct corroboration",
         "related_episode_id": "EP-MAY2018-TRIPURA", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal?"},
        {"slide_no": "NEWS-BELBARI-20180520", "district": "West Tripura", "lat": 23.95, "lon": 91.35,
         "year": 2018, "month_hint": "May 2018", "exact_date": "2018-05-20", "time": "Sunday",
         "source": "India.com/PTI May 20 2018 (60yo man, Belbari block, 25km Agartala)",
         "source_url": "india.com May 20 2018", "source_2": "HT May 21 six-toll (aggregate support)",
         "source_convergence": "single+aggregate", "date_precision": "exact-provisional",
         "location_precision": "Belbari block, 25km from Agartala (APPROX)", "fatalities": "1",
         "road_association": "", "status": "provisional-exact",
         "precision_status": "EXACT_VERIFIED", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event; needs direct corroboration",
         "related_episode_id": "EP-MAY2018-TRIPURA", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal?"},
        {"slide_no": "NEWS-NONGSTOIN-20230617", "district": "West Khasi Hills, Meghalaya",
         "lat": 25.51, "lon": 91.27, "year": 2023, "month_hint": "June 2023",
         "exact_date": "2023-06-17", "time": "03:30-04:30 Sat",
         "source": "ET/PTI Jun 17 2023 (Mawiong-Pyndengrei, 2 sisters 10+15)",
         "source_url": "economictimes Jun 17 2023",
         "source_2": "HT Jun 17 + Meghalaya Monitor Jun 17 (names Cafinia/Maya Nongsiej) + TOI Jun 18",
         "source_convergence": "multi (4 outlets)", "date_precision": "exact",
         "location_precision": "Mawiong-Pyndengrei/Dommawlein, Nongstoin (APPROX)",
         "fatalities": "2", "road_association": "local roads cut (Nondein river)",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event",
         "related_episode_id": "EP-JUN2023-MEGHALAYA", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-LUMSHONG-20220616", "district": "East Jaintia Hills, Meghalaya",
         "lat": 25.35, "lon": 92.50, "year": 2022, "month_hint": "June 2022",
         "exact_date": "2022-06-16", "time": "Thursday",
         "source": "EastMojo Jun 17 2022 (NH6 Lumshong, Tripura cut off rail+road)",
         "source_url": "eastmojo.com Jun 17 2022", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Lumshong, E.Jaintia Hills, NH6 (APPROX)", "fatalities": "0",
         "road_association": "NH6 cut, Tripura isolated (Agartala-Dhaka-Kolkata buses added)",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "EP-JUN2022-NE Meghalaya pulse; needs corroboration",
         "related_episode_id": "EP-JUN2022-NE", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "road-block high-exposure?"},
        {"slide_no": "NEWS-PYNTHOR-20231008", "district": "West Jaintia Hills, Meghalaya",
         "lat": 25.55, "lon": 92.15, "year": 2023, "month_hint": "October 2023",
         "exact_date": "2023-10-08", "time": "early Sunday",
         "source": "Sentinel Assam/IANS Oct 9 2023 (Pynthor Langtein, family of 4 incl 2 minors)",
         "source_url": "sentinelassam.com Oct 9 2023", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Pynthor Langtein village, W.Jaintia Hills (APPROX)",
         "fatalities": "4", "road_association": "",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier3",
         "event_identity": "single-event; needs corroboration",
         "related_episode_id": "EP-OCT2023-MEGHALAYA", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal?"},
        {"slide_no": "NEWS-RNGAIN-20230414", "district": "East Khasi Hills, Meghalaya",
         "lat": 25.25, "lon": 91.95, "year": 2023, "month_hint": "April 2023",
         "exact_date": "2023-04-14", "time": "Friday night",
         "source": "NE Live Apr 15 2023 (Shillong-Dawki Rngain Pynursla, 2 dead incl Rangbah Shnong, 50 stranded)",
         "source_url": "northeastlivetv.com Apr 15 2023", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Rngain near Pynursla, Shillong-Dawki Rd Pkg-II (APPROX)",
         "fatalities": "2", "road_association": "Shillong-Dawki road cut",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier3",
         "event_identity": "road-cut construction slope (NHIDCL Pkg-II, FIR + IIT-G study ordered); include per road-cut rule, needs corroboration",
         "related_episode_id": "EP-APR2023-MEGHALAYA", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal road-cut?"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    ids = {n["slide_no"] for n in new_rows} | {"NEWS-29MILE-20210906"}
    for idx, r in d[d["slide_no"].isin(ids)].iterrows():
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
        log(f"  {r['slide_no']}: geo={geo} rain={rain} elig={elig}")
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    tr = d[(d["geography_status"] == "OUT_OF_DOMAIN_TRANSFER") & (d["status"] == "mined-exact")]
    log(f"rows={len(d)} championship={len(elig)} transfer={len(tr)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
