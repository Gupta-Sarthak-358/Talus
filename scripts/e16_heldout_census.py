"""E16 census: inventory positives EXCLUDED from training (out-of-study-bbox).

Training kept study bbox lon[88.06,88.96] lat[27.00,27.999]; everything else the
loader saw is a natural held-out set. Characterize: counts, states, dates,
DEM-tile and IMD coverage for potential daily replay.
Outputs: runs/e16_census.json. Run: mnemo-venv python scripts/e16_heldout_census.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "runs" / "e16_census.json"

LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import build_training_matrix as B
    pos = B.load_positives()
    inside = ((pos["lon"] >= LON0) & (pos["lon"] <= LON1)
              & (pos["lat"] >= LAT0) & (pos["lat"] <= LAT1)).to_numpy()
    held = pos[~inside].reset_index(drop=True)
    log(f"loaded positives={len(pos)} in-study={int(inside.sum())} HELD-OUT={len(held)}")
    res: dict = {"n_loaded": int(len(pos)), "n_in_study": int(inside.sum()),
                 "n_heldout": int(len(held))}

    if len(held):
        res["by_source"] = {str(k): int(v) for k, v in held["source"].value_counts().items()}
        res["by_district"] = {str(k): int(v) for k, v in held["district"].value_counts().head(20).items()}
        dated = held[held["year"] > 0]
        res["dated"] = int(len(dated))
        res["dated_years"] = sorted(int(v) for v in dated["year"].unique().tolist()) if len(dated) else []
        res["latlon_bbox"] = [round(float(held["lat"].min()), 3), round(float(held["lat"].max()), 3),
                              round(float(held["lon"].min()), 3), round(float(held["lon"].max()), 3)]
        # DEM tile n27_e088 covers lon 88-89 / lat 27-28
        in_tile = ((held["lon"] >= 88.0) & (held["lon"] <= 89.0)
                   & (held["lat"] >= 27.0) & (held["lat"] <= 28.0)).to_numpy()
        res["in_dem_tile"] = int(in_tile.sum())
        # IMD archive: check yearly files for dated held-out years
        imd_ok, imd_missing = [], []
        for yy in sorted(set(int(v) for v in dated["year"].tolist())) if len(dated) else []:
            ((imd_ok if (REPO / f"data/raw/imd/ind{yy}_rfp25.nc").exists() else imd_missing).append(yy))
        res["imd_years_present"] = imd_ok
        res["imd_years_missing"] = imd_missing
        res["dated_in_tile"] = int(((held["year"] > 0).to_numpy() & in_tile).sum())
        # sample rows for the record
        res["sample"] = held[["slide_no", "district", "lat", "lon", "year", "source"]].head(15).to_dict("records")
        for r in res["sample"]:
            r["lat"] = round(float(r["lat"]), 4)
            r["lon"] = round(float(r["lon"]), 4)
            r["year"] = int(r["year"])
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT}")
    print(json.dumps({k: v for k, v in res.items() if k != "sample"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
