"""Ingest external mining pass 1 into Track A census (SIH26001 Phase IV-A).

- Adds episode/dedup schema columns.
- Upgrades DipuDara-20240820 (peer-reviewed corroboration) + Mangan-20240613 (episode).
- Adds Majwa-20240610 as duplicate-of-existing (no new sample).
- Adds 3 out-of-domain candidates (transfer cohort) + 1 provisional (domain edge).
- Runs contamination checks on every exact row; eligibility is computed, never asserted.
Run: mnemo-venv python scripts/trackA_mining1.py
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


NEW_COLS = ["source_2", "source_convergence", "event_identity", "related_episode_id",
            "exactness_status", "geography_status", "DEM_status", "rainfall_status",
            "satellite_status", "eligible_for_championship"]


def main() -> int:
    d = pd.read_csv(TRACKER)
    for c in NEW_COLS:
        if c not in d.columns:
            d[c] = ""

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    E = d["precision_status"].str.startswith("EXACT").fillna(False)
    # defaults for existing exact rows: single-event identity, eligibility computed later
    setrow(E & (d["event_identity"] == ""), event_identity="single-event")
    setrow(d["slide_no"] == "NEWS-MANGAN-20240613",
           source_2="Financial Express + NE NOW + DD News Jun 13-14 2024",
           source_convergence="multi",
           event_identity="multi-slide cluster Mangan/Pakshep/Ambithang/Geythang/Nampathang/NH-10: ONE sample",
           related_episode_id="EP-JUN2024-SIKKIM", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="S2-2024-05-03")
    setrow(d["slide_no"] == "NEWS-DIPUDARA-20240820",
           source_2="Natural Hazards Research peer-reviewed paper (Aug 20 2024)",
           source_convergence="dual (press + peer-reviewed)",
           related_episode_id="EP-AUG2024-EASTSIKKIM", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="S2-2024-08-16")
    setrow(d["slide_no"] == "NEWS-DIPUDARA-20240821",
           related_episode_id="EP-AUG2024-EASTSIKKIM", exactness_status="EXACT_VERIFIED",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="S2-2024-08-16")
    setrow(d["slide_no"] == "NEWS-NH10-20221009",
           related_episode_id="EP-OCT2022-NE", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="S2-2022-10-01")
    setrow(d["slide_no"] == "NEWS-DARJ-20150701",
           related_episode_id="EP-JUL2015-DARJ", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="L8-available-check-at-replay")
    setrow(d["slide_no"] == "NEWS-NH10-20150709",
           related_episode_id="EP-JUL2015-DARJ", exactness_status="EXACT_VERIFIED",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="L8-available-check-at-replay")
    setrow(d["slide_no"] == "NEWS-NH10-20211020",
           related_episode_id="EP-OCT2021-NE", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED", rainfall_status="AVAILABLE",
           satellite_status="S2-2021-10-check-at-replay")

    new_rows = [
        # --- out-of-domain transfer cohort (Meghalaya/Assam, same monsoon episode) ---
        {"slide_no": "NEWS-GARO-20220609", "district": "West/SW Garo Hills, Meghalaya",
         "lat": 25.47, "lon": 90.12, "year": 2022, "month_hint": "June 2022",
         "exact_date": "2022-06-09", "time": "", "source": "NDTV Jun 9 2022 (4 killed)",
         "source_url": "ndtv.com Jun 9 2022", "source_2": "NE NOW Jun 9 2022 (Jebalgre/Gambegre, Samati)",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Jebalgre/Gambegre + Samati, SW Garo Hills (APPROX)",
         "fatalities": "4", "road_association": "", "status": "mined-exact",
         "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event", "related_episode_id": "EP-JUN2022-NE",
         "exactness_status": "EXACT_MULTI_SOURCE", "geography_status": "OUT_OF_DOMAIN_TRANSFER",
         "DEM_status": "FETCH_REQUIRED", "rainfall_status": "AVAILABLE (IMD national)",
         "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-GUWAHATI-20220614", "district": "Kamrup Metro, Assam",
         "lat": 26.10, "lon": 91.71, "year": 2022, "month_hint": "June 2022",
         "exact_date": "2022-06-14", "time": "~01:00", "source": "Indian Express Jun 2022 (Nijarapar Boragaon)",
         "source_url": "indianexpress.com Jun 2022", "source_2": "TOI same event/location",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Nijarapar, Boragaon, Guwahati (APPROX)",
         "fatalities": "4 buried alive", "road_association": "", "status": "mined-exact",
         "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event (urban slope-cut)", "related_episode_id": "EP-JUN2022-NE",
         "exactness_status": "EXACT_MULTI_SOURCE", "geography_status": "OUT_OF_DOMAIN_TRANSFER",
         "DEM_status": "FETCH_REQUIRED", "rainfall_status": "AVAILABLE (IMD national)",
         "satellite_status": "S2-check-at-replay"},
        {"slide_no": "NEWS-LAITLAREM-20220617", "district": "East Khasi Hills, Meghalaya",
         "lat": 25.34, "lon": 91.86, "year": 2022, "month_hint": "June 2022",
         "exact_date": "2022-06-17", "time": "", "source": "Highland Post Jun 2022 (date/time/location)",
         "source_url": "highlandpost.com Jun 2022", "source_2": "TOI same-day Meghalaya deaths",
         "source_convergence": "dual", "date_precision": "exact",
         "location_precision": "Laitlarem, East Khasi Hills (APPROX)",
         "fatalities": "5 (mudslides incl. NH-6)", "road_association": "NH-6 caved in",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "single-event", "related_episode_id": "EP-JUN2022-NE",
         "exactness_status": "EXACT_MULTI_SOURCE", "geography_status": "OUT_OF_DOMAIN_TRANSFER",
         "DEM_status": "FETCH_REQUIRED", "rainfall_status": "AVAILABLE (IMD national)",
         "satellite_status": "S2-check-at-replay"},
        # --- provisional: in-domain edge, single+weak corroboration ---
        {"slide_no": "NEWS-PUBUNG-20190708", "district": "Darjeeling",
         "lat": 26.99, "lon": 88.16, "year": 2019, "month_hint": "July 2019",
         "exact_date": "2019-07-08", "time": "early Monday", "source": "TOI Jul 8 2019 (couple killed)",
         "source_url": "timesofindia Jul 8 2019", "source_2": "Jul 10 report placing incident on Monday (weak)",
         "source_convergence": "single+weak", "date_precision": "exact-provisional",
         "location_precision": "Pubung Phatak, Sukhiapokhri block (APPROX)",
         "fatalities": "2", "road_association": "", "status": "provisional-exact",
         "precision_status": "EXACT_VERIFIED", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "single-event", "related_episode_id": "EP-JUL2019-DARJ",
         "exactness_status": "EXACT_PROVISIONAL", "geography_status": "EDGE (0.01deg S of box)",
         "DEM_status": "COVERED?", "rainfall_status": "AVAILABLE", "satellite_status": "L8/S2-check-at-replay"},
        # --- duplicate guard: Majwa Jun 10 already represented ---
        {"slide_no": "NEWS-MAJWA-20240610", "district": "South Sikkim",
         "lat": 27.23, "lon": 88.42, "year": 2024, "month_hint": "June 2024",
         "exact_date": "2024-06-10", "time": "", "source": "Hindustan Times Jun 2024 (3 die, Majwa)",
         "source_url": "hindustantimes.com Jun 2024", "source_2": "",
         "source_convergence": "n/a-duplicate", "date_precision": "exact",
         "location_precision": "Majwa, Rangang-Yangang (APPROX)",
         "fatalities": "3", "road_association": "", "status": "duplicate-existing",
         "precision_status": "EXACT_VERIFIED", "priority": "mined", "source_tier": "Tier2",
         "event_identity": "DUPLICATE of existing Jun-10 Tier-1 replay evidence: NOT a new sample",
         "related_episode_id": "EP-JUN2024-SIKKIM", "exactness_status": "EXACT_VERIFIED",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)

    # contamination checks on every exact row
    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["precision_status"].str.startswith("EXACT").fillna(False)].iterrows():
        la, lo = float(r["lat"]), float(r["lon"])
        geo = bool(LON0 <= lo <= LON1 and LAT0 <= la <= LAT1)
        dem = bool(88.0 <= lo <= 89.0 and 27.0 <= la <= 28.0)
        rain = True
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
        d.loc[idx, "contam_prox_m"] = round(sep, 1)
        elig = bool(geo and r["status"] == "mined-exact"
                    and str(r["exactness_status"]).startswith("EXACT_")
                    and "PROVISIONAL" not in str(r["exactness_status"])
                    and "DUPLICATE" not in str(r["event_identity"]))
        d.loc[idx, "eligible_for_championship"] = str(elig)
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"] == "True"]
    log(f"rows={len(d)} eligible={len(elig)} transfer={(d['geography_status'] == 'OUT_OF_DOMAIN_TRANSFER').sum()} "
        f"provisional={(d['exactness_status'] == 'EXACT_PROVISIONAL').sum()}")
    for _, r in d[d["precision_status"].str.startswith("EXACT").fillna(False)].iterrows():
        log(f"  {r['slide_no']}: geo={r['contam_geo']} elig={r['eligible_for_championship']} ep={r['related_episode_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
