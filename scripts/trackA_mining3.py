"""Ingest mining pass 2b: provisional resolutions (SIH26001 Phase IV-A).

  PROMOTE 3: Pubung-20190708 (Chataidhura GPS 27.0044 in-box, edge-flagged),
             17Mile-20220615 (Hindu/Outlook/Pratidin corroborate Telegraph),
             BirikDara-20220802 (TOI/TNN ground detail corroborates NE Live).
  PROVENANCE: pooled Oct-2021 event gains peer-reviewed scar study (Das et al Curr Sci 2022).
  HOLD: 29Mile-20210906 (localization search 429; stays provisional).
  Adds event_type metadata column (fatal/non-fatal/road-block/high-exposure/multi-slide).
Run: mnemo-venv python scripts/trackA_mining3.py
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


TYPES = {
    "NEWS-DARJ-20150701": "fatal multi-slide episode", "NEWS-NH10-20150709": "fatal road-block",
    "NEWS-NH10-20211020": "road-block high-exposure", "NEWS-MANGAN-20240613": "fatal multi-slide episode",
    "NEWS-DIPUDARA-20240820": "non-fatal high-exposure", "NEWS-DIPUDARA-20240821": "non-fatal",
    "NEWS-NH10-20221009": "road-block high-exposure", "NEWS-RONGEY-20220628": "fatal",
    "NEWS-YUMTHANG-20220831": "non-fatal high-exposure", "NEWS-20MILE-20220901": "road-block high-exposure",
    "NEWS-PUBUNG-20190708": "fatal", "NEWS-17MILE-20220615": "non-fatal (1 death post-rescue) road-block",
    "NEWS-BIRIKDARA-20220802": "non-fatal road-block",
}


def main() -> int:
    d = pd.read_csv(TRACKER)
    if "event_type" not in d.columns:
        d["event_type"] = ""
    for k, v in TYPES.items():
        d.loc[d["slide_no"] == k, "event_type"] = v

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    setrow(d["slide_no"] == "NEWS-PUBUNG-20190708",
           lat=27.0044, lon=88.2165,
           source_2="IndiaToday+Zee+DNA+MillenniumPost+SaveTheHills-field-report + Chataidhura Sub-Center GPS",
           location_precision="Chatai Dhura village (health-facility GPS 27.0044,88.2165); scar 'below Pubung Fatak', ~0.5km box margin",
           status="mined-exact", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN_EDGE (0.5km margin, proxy coordinate)",
           DEM_status="COVERED", rainfall_status="AVAILABLE", satellite_status="L8-check-at-replay",
           event_identity="single-event: Chatai Dhura below Pubung Fatak, house buried ~0130-0230; IMD Darjeeling 172mm/24h")
    setrow(d["slide_no"] == "NEWS-17MILE-20220615",
           source_2="The Hindu/PTI Jun 15 + Outlook/PTI + PratidinTime Jun 16 (all: 8 buried, Black Cat, 17th Mile, 1 died)",
           source_convergence="multi (4 outlets)", date_precision="exact",
           location_precision="17th Mile, Gangtok JN Road (APPROX)",
           status="mined-exact", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED",
           event_identity="single-event; note Apr-2023 avalanche same mile-marker (different mechanism/year)")
    setrow(d["slide_no"] == "NEWS-BIRIKDARA-20220802",
           lat=27.10, lon=88.48,
           source_2="TOI/TNN Aug 3 2022 ground detail (0830 Tue Birik Dara + 1330 Gelle Khola, Kalimpong 62.6mm, SP/EE quotes)",
           source_convergence="dual", date_precision="exact", time="08:30 Tue",
           location_precision="Birik Dara NH10, Kalimpong, Sevoke-Rangpo stretch (APPROX)",
           status="mined-exact", exactness_status="EXACT_MULTI_SOURCE",
           geography_status="IN_DOMAIN", DEM_status="COVERED",
           event_identity="chronic Birik Dara site: peer-reviewed Oct-20-2021 slide SAME site (Das et al); distinct date, separate sample")
    setrow(d["slide_no"] == "NEWS-NH10-20211020",
           source_2="TOI Oct 20 + NDTV Oct 20 + ET + Firstpost + Das et al Curr Sci 2022 peer-reviewed scar study (Birik Dara, 10pm Oct 20 2021)",
           source_convergence="multi (5 outlets + peer-reviewed geotech study)")

    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["slide_no"].isin(
            {"NEWS-PUBUNG-20190708", "NEWS-17MILE-20220615", "NEWS-BIRIKDARA-20220802",
             "NEWS-NH10-20211020"})].iterrows():
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
                    and "PROVISIONAL" not in str(r["exactness_status"]))
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
