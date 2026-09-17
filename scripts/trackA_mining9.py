"""Ingest mining pass 8: mechanism verdicts (SIH26001 Phase IV-A).

  PROMOTE 2 championship (pool 18 -> 20):
    ManganChungthang-20200627 (Telegraph + ANI + Federal: active slides + washout, include-rule)
    Apdara-20200627 (NHPC own PR: 0020 hillside slide 40m above dam + SANDRP/Gaon/EastMojo/PTI)
  HOLD: MyongKyong (still single-source).
  RECLASS: Soureni/Dilaram geography -> POST_CHAMPIONSHIP_STUDY (frozen NGEN-box rule).
Run: mnemo-venv python scripts/trackA_mining9.py
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

    setrow(d["slide_no"] == "NEWS-MANGANCHUNG-20200627",
           source_2="ANI Jun 29 (two road formations washed away in landslides, Mangan-PS + Lanthey) + Federal Jul 3 (BRO: boulders still falling, small slides active)",
           source_convergence="multi (3 outlets)",
           status="mined-exact", exactness_status="EXACT_MULTI_SOURCE",
           event_identity="MECHANISM PASS: documented active slope failures + road destruction (washout component does not disqualify per include-rule)",
           event_type="road-block strategic-corridor")
    setrow(d["slide_no"] == "NEWS-APDARA-20200627",
           source_2="NHPC own PR Jun 29 (Ministry of Power: 0020 slide, left-abutment hillside 40m above dam top) + SANDRP + GaonConnection + EastMojo Jun 27 (Lum/Lingtyang cut)",
           source_convergence="multi (5 outlets incl operator admission)",
           time="00:20 Sat",
           status="mined-exact", exactness_status="EXACT_MULTI_SOURCE",
           event_identity="MECHANISM PASS: genuine hillside slope failure above dam (operator-attested); dam-damage dispute irrelevant to event identity; negligence allegation logged not hidden",
           event_type="infrastructure-adjacent slope failure")
    for s in ("NEWS-SOURENI-20251005", "NEWS-DILARAM-20251005"):
        setrow(d["slide_no"] == s,
               geography_status="POST_CHAMPIONSHIP_STUDY",
               event_identity=d.loc[d["slide_no"] == s, "event_identity"].iloc[0]
               + " | FROZEN 2026-09-18: NGEN-box rule excludes from championship; support-envelope study later")

    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    for idx, r in d[d["slide_no"].isin(
            {"NEWS-MANGANCHUNG-20200627", "NEWS-APDARA-20200627"})].iterrows():
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
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
