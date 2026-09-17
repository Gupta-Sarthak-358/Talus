"""Ingest mining pass 7 into Track A census (SIH26001 Phase IV-A).

  PROMOTE 1 championship: Lingchom-20200524 (govt IPR + PTI/FloodList + IndiaTodayNE).
  PROVISIONAL 3 in-domain: MyongKyong-20200524, ManganChungthang-20200627, Apdara-20200627.
  PROVISIONAL 2 Darjeeling-south (METHODOLOGY FORK: box-edge, support-check pending,
  IMD-2025 pending): Soureni-20251005 + Dilaram-20251005 (Oct-2025 Remal-class cloudburst).
  PROVENANCE: Tigdo/ModiRijo gain IE-Jul-10 + Scroll + AP triple corroboration.
  DEFERRED (429): Kurseong-solo, Kalimpong-2020 windows.
Run: mnemo-venv python scripts/trackA_mining8.py
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

    for s in ("NEWS-TIGDO-20200710", "NEWS-MODIRIJO-20200710"):
        setrow(d["slide_no"] == s,
               source_2=d.loc[d["slide_no"] == s, "source_2"].iloc[0]
               + " + IE Jul-10 (8-toll, CM 142mm tweet, RMC red alert) + Scroll + AP")

    new_rows = [
        {"slide_no": "NEWS-LINGCHOM-20200524", "district": "Mangan", "lat": 27.38, "lon": 88.55,
         "year": 2020, "month_hint": "May 2020", "exact_date": "2020-05-24", "time": "~13:00 Sun",
         "source": "sikkim.gov.in IPR May 24 (SDM Kabi: Phu Phu Sherpa 50 dead, 2 injured, 3 houses, evacuations)",
         "source_url": "sikkim.gov.in May 24 2020",
         "source_2": "FloodList/PTI May 25 (woman + 2 injured, N.district May-24) + IndiaTodayNE May 26 (Lingchom woman 12:30)",
         "source_convergence": "multi (Tier-1 govt + wire + press)", "date_precision": "exact",
         "location_precision": "Upper Lingchom, Kabi-Tingda (APPROX)",
         "fatalities": "1 + 2 injured", "road_association": "Upper Lingchom approach cut; Gangtok-Mangan blocks Phensong/Kabi",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "single-event (post-Amphan pre-monsoon)",
         "related_episode_id": "EP-MAY2020-NSIKKIM", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "fatal"},
        {"slide_no": "NEWS-MYONGKYONG-20200524", "district": "Mangan", "lat": 27.48, "lon": 88.52,
         "year": 2020, "month_hint": "May 2020", "exact_date": "2020-05-24", "time": "evening Sun",
         "source": "IndiaTodayNE May 26 2020 (Myong Kyong U.Dzongu: 2 dead, 3 houses washed + 11 partial)",
         "source_url": "indiatodayne.in May 26 2020", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Myong Kyong, Upper Dzongu (APPROX)",
         "fatalities": "2", "road_association": "",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier3",
         "event_identity": "distinct point from Lingchom same day (~15km); needs corroboration",
         "related_episode_id": "EP-MAY2020-NSIKKIM", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "fatal?"},
        {"slide_no": "NEWS-MANGANCHUNG-20200627", "district": "Mangan", "lat": 27.51, "lon": 88.53,
         "year": 2020, "month_hint": "June 2020", "exact_date": "2020-06-27", "time": "Saturday",
         "source": "Telegraph Jun 28 2020 (Mangan-Chungthang washed out Mangan-PS + Lanthey Khola, BRO quotes)",
         "source_url": "telegraphindia.com Jun 28 2020", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Mangan PS + Lanthey Khola, Mangan-Chungthang highway (APPROX)",
         "fatalities": "0", "road_association": "strategic border highway cut, Passingdang flash flood same episode",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "strategic-road point; needs corroboration",
         "related_episode_id": "EP-JUN2020-NSIKKIM", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "road-block?"},
        {"slide_no": "NEWS-APDARA-20200627", "district": "Gangtok", "lat": 27.35, "lon": 88.53,
         "year": 2020, "month_hint": "June 2020", "exact_date": "2020-06-27", "time": "Saturday",
         "source": "Statesman/PTI Jun 28 2020 (Apdara Teesta-V dam damage + Gangtok-Mangan multi-blocks, Mangan 500mm/4d)",
         "source_url": "thestatesman.com Jun 28 2020", "source_2": "",
         "source_convergence": "single", "date_precision": "exact-provisional",
         "location_precision": "Apdara, Teesta Stage-V site, E.Sikkim (APPROX)",
         "fatalities": "0", "road_association": "Mangan-Gangtok/Phamtam/Ambithang, Dikchu routes blocked",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "infrastructure-damage point, same episode as Mangan-Chungthang; needs corroboration",
         "related_episode_id": "EP-JUN2020-NSIKKIM", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "S2-check-at-replay", "event_type": "infrastructure-damage?"},
        {"slide_no": "NEWS-SOURENI-20251005", "district": "Darjeeling", "lat": 26.91, "lon": 88.18,
         "year": 2025, "month_hint": "October 2025", "exact_date": "2025-10-05",
         "time": "Saturday night-Sunday (cloudburst, 300mm/12h)",
         "source": "ET Oct 9-10 2025 (Soureni 24 families, Tingling cloudburst 23 dead, village buried)",
         "source_url": "economictimes Oct 2025",
         "source_2": "TOI Oct 5-6 (Mirik 11 dead, iron bridge) + Telegraph/PTI + Rediff/NDRF + ANI (Mirik house, Rai family)",
         "source_convergence": "multi (5+ outlets)", "date_precision": "exact",
         "location_precision": "Soureni, Mirik (APPROX)",
         "fatalities": "11+ Mirik (children incl)", "road_association": "Mirik-Sukhiapokhri buried, Balasun iron bridge washed",
         "status": "provisional-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "FORK: lat 26.91 south of NGEN box; Darjeeling-hills terrain, support-check + IMD-2025 pending",
         "related_episode_id": "EP-OCT2025-MIRIK", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "DARJEELING-SOUTH-PENDING-SUPPORT", "DEM_status": "TBD (N26 tile?)",
         "rainfall_status": "PENDING (ind2025?)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal multi-slide episode?"},
        {"slide_no": "NEWS-DILARAM-20251005", "district": "Darjeeling", "lat": 26.95, "lon": 88.25,
         "year": 2025, "month_hint": "October 2025", "exact_date": "2025-10-05", "time": "Sunday",
         "source": "News24 Oct 5 2025 (Dilaram Kurseong-Darjeeling Rd: 7 recovered + 2 missing, Addl SP quote)",
         "source_url": "news24online.com Oct 5 2025",
         "source_2": "TOI Oct 5 (Dilaram + Whistle Khola blocks, SP Prakash) + ThePrint (Dilaram-Kurseong blocked)",
         "source_convergence": "multi (3 outlets)", "date_precision": "exact",
         "location_precision": "Dilaram, Kurseong-Darjeeling road (APPROX)",
         "fatalities": "7 + 2 missing", "road_association": "Kurseong-Darjeeling Rd + Rohini/Gourishankar blocked",
         "status": "provisional-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "FORK: distinct point ~30km from Soureni same night; support-check + IMD-2025 pending",
         "related_episode_id": "EP-OCT2025-MIRIK", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "DARJEELING-SOUTH-PENDING-SUPPORT", "DEM_status": "TBD (N26 tile?)",
         "rainfall_status": "PENDING (ind2025?)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal road-block?"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["slide_no"].isin({n["slide_no"] for n in new_rows})].iterrows():
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
