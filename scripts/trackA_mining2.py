"""Ingest external mining pass 2 into Track A census (SIH26001 Phase IV-A).

Pass-2 verdicts (10-point checklist per candidate):
  ELIGIBLE 3: Rongey-20220628 (dual), Yumthang-20220831 (triple), 20Mile-20220901 (triple)
  PROVISIONAL 3: Pubung source-leg passed (still edge); 17Mile-20220615 (single);
                 BirikDara-20220802 (single); 29Mile-20210906 (geo unresolved)
  GUARDS 2: Jun17-2022 aggregate (dedup, absorbs Jun15 deaths); Chungthang-20231004 (mechanism reject)
Run: mnemo-venv python scripts/trackA_mining2.py
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

    # Pubung: source leg PASSED (6 sources), geography leg still EDGE
    setrow(d["slide_no"] == "NEWS-PUBUNG-20190708",
           source_2="IndiaToday+Zee+DNA+MillenniumPost+SaveTheHills-field-report Jul 8-9 2019",
           source_convergence="multi (6 outlets, ground detail + IMD 172mm/24h)",
           exactness_status="EXACT_MULTI_SOURCE",
           event_identity="single-event: Chatai Dhura below Pubung Fatak, house buried ~0130-0230")
    # Oct-2021 pooled event: corroboration strengthened
    setrow(d["slide_no"] == "NEWS-NH10-20211020",
           source_2="TOI Oct 20 + NDTV Oct 20 + ET + Firstpost (29th-Mile + Pani House + Rangpo bridge)",
           source_convergence="multi (5 outlets)")

    new_rows = [
        {"slide_no": "NEWS-RONGEY-20220628", "district": "Gangtok", "lat": 27.30, "lon": 88.65,
         "year": 2022, "month_hint": "June 2022", "exact_date": "2022-06-28", "time": "~01:00 Tue",
         "source": "Hindustan Times Jun 28 2022 (Doma Sherpa + 2 children, Rongey Dokan Dara)",
         "source_url": "hindustantimes.com Jun 28 2022",
         "source_2": "NorthEast Chronicle Jun 28 2022 (same hut, same 1am timing)",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Rongey Dokan Dara hut, near Gangtok (APPROX)",
         "fatalities": "3", "road_association": "", "status": "mined-exact",
         "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event", "related_episode_id": "EP-JUN2022-SIKKIM",
         "exactness_status": "EXACT_MULTI_SOURCE", "geography_status": "IN_DOMAIN",
         "DEM_status": "COVERED", "rainfall_status": "AVAILABLE", "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-YUMTHANG-20220831", "district": "Mangan", "lat": 27.70, "lon": 88.68,
         "year": 2022, "month_hint": "August 2022", "exact_date": "2022-08-31", "time": "~16:00 Wed",
         "source": "Northeast Live Sep 1 2022 (Aug 31 4pm, 8 vehicles, Yumthang valley)",
         "source_url": "northeastlivetv.com Sep 1 2022",
         "source_2": "The Hindu/PTI Sep 1 + NDTV Sep 1 (Army Trishakti rescue, 74 tourists, 19km from Yumthang)",
         "source_convergence": "triple", "date_precision": "exact",
         "location_precision": "landslip 19km from Yumthang on Chungthang road (APPROX)",
         "fatalities": "0 (74 stranded, Army rescue)", "road_association": "Yumthang road closed",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event, no deaths but road-closure + mass exposure",
         "related_episode_id": "EP-SEP2022-SIKKIM", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-20MILE-20220901", "district": "Gangtok/Pakyong", "lat": 27.17, "lon": 88.51,
         "year": 2022, "month_hint": "September 2022", "exact_date": "2022-09-01",
         "time": "overnight Aug 31-Sep 1",
         "source": "India.com Sep 1 2022 (20 Mile NH20, Gangtok cut off, 2nd time that week)",
         "source_url": "india.com Sep 1 2022",
         "source_2": "Sentinel Assam Sep 1 + Pratidin Time Sep 1 (same spot, same night)",
         "source_convergence": "triple", "date_precision": "exact",
         "location_precision": "20 Mile, Singtam-Rangpo highway (APPROX)",
         "fatalities": "0 reported", "road_association": "NH20 blocked, Gangtok cut off; Pakyong/Pandam alternates also blocked",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "chronic 19/20-Mile site, DISTINCT date from Oct-9-2022 pooled event (T-30 windows do not overlap)",
         "related_episode_id": "EP-SEP2022-SIKKIM", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-17MILE-20220615", "district": "Gangtok", "lat": 27.28, "lon": 88.62,
         "year": 2022, "month_hint": "June 2022", "exact_date": "2022-06-15", "time": "Wednesday",
         "source": "Telegraph/PTI Jun 16 2022 (Army Black Cat rescue, 8 buried, 1 died, 17th Mile E.Sikkim)",
         "source_url": "telegraphindia.com Jun 16 2022", "source_2": "",
         "source_convergence": "single (wire)", "date_precision": "exact-provisional",
         "location_precision": "17th Mile, East Sikkim (APPROX)", "fatalities": "1 (8 buried)",
         "road_association": "", "status": "provisional-exact", "precision_status": "EXACT_VERIFIED",
         "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event", "related_episode_id": "EP-JUN2022-SIKKIM",
         "exactness_status": "EXACT_PROVISIONAL", "geography_status": "IN_DOMAIN",
         "DEM_status": "COVERED", "rainfall_status": "AVAILABLE", "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-BIRIKDARA-20220802", "district": "Pakyong/Kalimpong border", "lat": 27.14,
         "lon": 88.52, "year": 2022, "month_hint": "August 2022", "exact_date": "2022-08-02",
         "time": "", "source": "Northeast Live Aug 2 2022 (NH10 Birik Dara, state cut off)",
         "source_url": "northeastlivetv.com Aug 2 2022", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Birik Dara, NH10 near state border (APPROX)", "fatalities": "",
         "road_association": "NH10 blocked", "status": "provisional-exact",
         "precision_status": "EXACT_VERIFIED", "priority": "mined", "source_tier": "Tier3",
         "event_identity": "single-event", "related_episode_id": "EP-AUG2022-SIKKIM",
         "exactness_status": "EXACT_PROVISIONAL", "geography_status": "IN_DOMAIN?",
         "DEM_status": "COVERED?", "rainfall_status": "AVAILABLE", "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-29MILE-20210906", "district": "Kalimpong", "lat": 27.06, "lon": 88.44,
         "year": 2021, "month_hint": "September 2021", "exact_date": "2021-09-06",
         "time": "overnight Sun-Mon",
         "source": "Business Standard Sep 6 2021 (70m debris, 29 Mile, NH10 cut, 4th blockage of monsoon)",
         "source_url": "business-standard.com Sep 6 2021",
         "source_2": "LatestLY/PTI Sep 6 2021 (same 70m/29-Mile detail)",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "29 Mile NH10 Kalimpong: mile-marker vs 60km-from-Rangpo CONFLICT (~10km)",
         "fatalities": "0 reported", "road_association": "NH10 cut, Darjeeling-hills diversion",
         "status": "provisional-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "chronic 29-Mile site (also hit Oct-20-2021); point unresolved",
         "related_episode_id": "EP-SEP2021-NE", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "UNRESOLVED (box-edge conflict)", "DEM_status": "TBD",
         "rainfall_status": "AVAILABLE", "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-SIKKIM-20220617", "district": "Mangan (aggregate)", "lat": 27.50, "lon": 88.55,
         "year": 2022, "month_hint": "June 2022", "exact_date": "2022-06-17", "time": "Friday (aggregate)",
         "source": "Hindustan Times Jun 18 2022 (5 dead incl 3 policemen, Friday)",
         "source_url": "hindustantimes.com Jun 18 2022", "source_2": "",
         "source_convergence": "n/a-aggregate", "date_precision": "aggregate",
         "location_precision": "statewide aggregate incl Jun-15 Lingzya/17th-Mile deaths: NOT a point event",
         "fatalities": "5 (likely includes Jun-15 deaths)", "road_association": "",
         "status": "aggregate-duplicate", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "AGGREGATE of Jun-15 incidents re-reported Friday: NOT a new sample",
         "related_episode_id": "EP-JUN2022-SIKKIM", "exactness_status": "EXACT_VERIFIED",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "n/a"},
        {"slide_no": "NEWS-CHUNGTHANG-20231004", "district": "Mangan", "lat": 27.61, "lon": 88.66,
         "year": 2023, "month_hint": "October 2023", "exact_date": "2023-10-04", "time": "~01:30",
         "source": "The Hindu Oct 4 + IE Oct 4 + peer-reviewed (Sattar et al 2025, Petley)",
         "source_url": "thehindu.com Oct 4 2023", "source_2": "multi",
         "source_convergence": "multi", "date_precision": "exact",
         "location_precision": "South Lhonak -> Teesta cascade, Chungthang dam",
         "fatalities": "40+", "road_association": "11 bridges, NH10",
         "status": "rejected", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "REJECTED: GLOF cascade, trigger at 5200m outside regime; not a rainfall-triggered slope failure",
         "related_episode_id": "EP-OCT2023-GLOF", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_REGIME", "DEM_status": "n/a", "rainfall_status": "n/a",
         "satellite_status": "n/a"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)

    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["precision_status"].str.startswith("EXACT").fillna(False)].iterrows():
        if str(r.get("eligible_for_championship", "")) in ("True", "False") and r["slide_no"] not in \
                {n["slide_no"] for n in new_rows} | {"NEWS-PUBUNG-20190708", "NEWS-NH10-20211020"}:
            continue
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
        d.loc[idx, "contam_soil"] = "daily-CCI"
        d.loc[idx, "contam_sat"] = str(r["satellite_status"])
        st = str(r["status"])
        if not isinstance(d.loc[idx, "contam_prox_m"], str):
            d.loc[idx, "contam_prox_m"] = round(sep, 1)
        else:
            try:
                d.loc[idx, "contam_prox_m"] = round(sep, 1)
            except Exception:
                pass
        elig = bool(geo and st == "mined-exact"
                    and str(r["exactness_status"]).startswith("EXACT_")
                    and "PROVISIONAL" not in str(r["exactness_status"])
                    and "DUPLICATE" not in str(r["event_identity"])
                    and "AGGREGATE" not in str(r["event_identity"])
                    and "REJECTED" not in str(r["event_identity"]))
        d.loc[idx, "eligible_for_championship"] = str(elig)
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    elig[["slide_no", "district", "lat", "lon", "year", "exact_date", "source",
          "precision_status"]].to_csv(CHAMP, index=False)
    log(f"rows={len(d)} eligible={len(elig)} (gap {30 - len(elig)})")
    for _, r in d[d["slide_no"].str.startswith("NEWS-", na=False)].iterrows():
        log(f"  {r['slide_no']}: elig={r['eligible_for_championship']} status={r['status']} prox={r['contam_prox_m']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
