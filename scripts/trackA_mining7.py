"""Ingest mining pass 6 into Track A census (SIH26001 Phase IV-A).

  PROMOTE 1 championship: 29Mile-20200923 (now 5 outlets: Morung+IE+TOI+NELive+IndiaTodayNE).
  HOLD 2: SeesaGolai (follow-ups same-outlet, mechanism still subsidence-flavored);
          Sichey (Telegraph dead page; +InSAR chronic-slope context, event still single-source).
  TRANSFER-ELIGIBLE 1: Hlimen-20240528 (houses-collapsed point inside Remal toll).
  PROVISIONAL-TRANSFER 1: Hunthar-NH6-20240528.
  REJECTED 1: Melthum quarry-20240528 (excavation-site collapse, BhaluKhola precedent).
  NOTED-NOT-SPLIT: other Remal village tolls (Salem/Falkawn/Aibawk/Lungsei/Kelsih/Chawnpui)
  stay aggregate context, not rows. Mirik/Kurseong deferred (429).
Run: mnemo-venv python scripts/trackA_mining7.py
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

    setrow(d["slide_no"] == "NEWS-29MILE-20200923",
           source_2="IE/PTI + TOI/PTI + NE Live + IndiaTodayNE Sep 23 2020 (all: Wed morning, 29 Mile WB)",
           source_convergence="multi (5 outlets)",
           status="mined-exact", exactness_status="EXACT_MULTI_SOURCE",
           event_identity="chronic 29-Mile site, EARLIEST dated hit (1st of 4); T-30 clear of Jul-11-21",
           event_type="non-fatal road-block chronic-site")
    setrow(d["slide_no"] == "NEWS-SEESAGOLAI-20210601",
           source_2="EastMojo follow-ups Jun 30 + Jul 11 (SAME outlet: month closure, Jul-12 two-way reopen)",
           source_convergence="single-outlet (follow-ups are not independent corroboration)",
           event_identity="MECHANISM CAVEAT stands: caved-in/sinking; needs second outlet addressing cause")
    setrow(d["slide_no"] == "NEWS-SICHEY-20210609",
           source_2="Dehls&Bhasin EGU22 InSAR: Upper/Lower Sichey 3-7cm/yr monsoon-linked (slope context, NOT event corroboration)",
           source_convergence="single (event); chronic-slope context only",
           event_identity="single-event; event itself still needs corroboration + time resolution")

    new_rows = [
        {"slide_no": "NEWS-HLIMEN-20240528", "district": "Aizawl, Mizoram", "lat": 23.68,
         "lon": 92.72, "year": 2024, "month_hint": "May 2024", "exact_date": "2024-05-28",
         "time": "Tuesday (Remal aftermath)",
         "source": "Hindu/PTI May 28-29 2024 (Hlimen houses collapsed, 5 dead + 4 missing, MSDMA)",
         "source_url": "thehindu.com May 28 2024",
         "source_2": "NDTV May 29 + TOI May 30 (Hlimen 5-6 recovered, SP Alwal) + ET (8 killed other incidents)",
         "source_convergence": "multi (4 outlets)", "date_precision": "exact",
         "location_precision": "Hlimen, southern outskirts Aizawl (APPROX)",
         "fatalities": "5-6 + missing", "road_association": "NH6 Hunthar cut (separate provisional)",
         "status": "mined-exact", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "houses-collapsed natural-slope point; other Remal village tolls stay aggregate context, NOT rows",
         "related_episode_id": "EP-MAY2024-REMAL", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "fatal"},
        {"slide_no": "NEWS-HUNTHAR-20240528", "district": "Aizawl, Mizoram", "lat": 23.75,
         "lon": 92.70, "year": 2024, "month_hint": "May 2024", "exact_date": "2024-05-28",
         "time": "Tuesday",
         "source": "Outlook May 28 2024 (NH6 Hunthar, Aizawl cut off)",
         "source_url": "outlookindia.com May 28 2024",
         "source_2": "ET May 29 (Aizawl cut off, NH6) — same-wire facts",
         "source_convergence": "dual-weak", "date_precision": "exact-provisional",
         "location_precision": "Hunthar, NH6 (APPROX)", "fatalities": "0",
         "road_association": "NH6 cut, Aizawl isolated",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier2",
         "event_identity": "road-block point; needs location precision + independent corroboration",
         "related_episode_id": "EP-MAY2024-REMAL", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "FETCH_REQUIRED",
         "rainfall_status": "AVAILABLE (IMD national)", "satellite_status": "S2-check-at-replay",
         "event_type": "road-block?"},
        {"slide_no": "NEWS-MELTHUM-20240528", "district": "Aizawl, Mizoram", "lat": 23.69,
         "lon": 92.72, "year": 2024, "month_hint": "May 2024", "exact_date": "2024-05-28",
         "time": "~06:00 Tue",
         "source": "Hindu/PTI + NDTV + Tribune + TOI May 28-30 2024 (Melthum-Hlimen quarry, ~15 dead)",
         "source_url": "thehindu.com May 28 2024", "source_2": "multi",
         "source_convergence": "multi", "date_precision": "exact",
         "location_precision": "Melthum-Hlimen stone quarry, S.Aizawl (APPROX)",
         "fatalities": "~15 + missing", "road_association": "",
         "status": "rejected", "precision_status": "EXACT_MULTI_SOURCE", "priority": "mined",
         "source_tier": "Tier1/2",
         "event_identity": "REJECTED: stone-quarry excavation-site collapse amid rain (BhaluKhola precedent) — occupational, not slope failure",
         "related_episode_id": "EP-MAY2024-REMAL", "exactness_status": "EXACT_MULTI_SOURCE",
         "geography_status": "OUT_OF_DOMAIN_TRANSFER", "DEM_status": "n/a",
         "rainfall_status": "n/a", "satellite_status": "n/a", "event_type": "rejected (mechanism)"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    ids = {n["slide_no"] for n in new_rows} | {"NEWS-29MILE-20200923", "NEWS-SEESAGOLAI-20210601",
                                              "NEWS-SICHEY-20210609"}
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
