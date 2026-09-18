"""VI-T0 matrix v1 (frozen recipe): positives-trainable + N0/N1 -> features.

Engineered strictly backward-looking (groupby-shift within trajectory, safe).
Missingness: NaN + <f>_miss flags in matrix; trainers median-impute from
TRAIN folds only (policy frozen in recipe JSON). Folds: GroupKFold(5) by site,
seed 42, fold ids stored so T0A/T0B share splits. No held-out anywhere.
Outputs data/vit/matrix_v1.csv + matrix_v1_recipe.json.
Run: mnemo-venv python scripts/vit_matrix.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "data" / "vit"

LEVEL = ["r24", "r3", "r7", "r30", "d_r24_1d", "d_r7_3d", "accel", "dryspell",
         "soil", "d_soil_3d", "d_soil_7d", "fos_med", "d_fos_7d",
         "seis_n50", "seis_dist", "seis_yrs", "susceptibility",
         "slope", "elev", "aspect", "curv", "twi", "spi", "draind",
         "ndvi", "d_road", "d_river"]
DYN = ["r24", "r3", "r7", "r30", "d_r24_1d", "d_r7_3d", "accel", "dryspell",
       "soil", "d_soil_3d", "d_soil_7d", "fos_med", "d_fos_7d",
       "seis_n50", "seis_dist", "seis_yrs"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    pos = pd.read_csv(OUTDIR / "traj_dev_positives.csv")
    pos = pos[pos["train_exclude"] == 0].copy()
    pos["stratum"] = "POS"
    pos["traj_id"] = pos["slide_no"]
    neg = pd.read_csv(OUTDIR / "traj_dev_negatives.csv")
    neg["traj_id"] = neg["slide_no"] + "_" + neg["stratum"] + "_" + neg["window_year"].astype(str)
    neg["region"] = neg["stratum"]
    d = pd.concat([pos, neg], ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["traj_id", "date"]).reset_index(drop=True)
    assert len(d) == 780 + 793 + 403
    g = d.groupby("traj_id", group_keys=False)

    d["r7_lag3"] = g["r7"].shift(3)
    d["r7_lag7"] = g["r7"].shift(7)
    d["r30_lag7"] = g["r30"].shift(7)
    d["soil_lag3"] = g["soil"].shift(3)
    d["fos_lag7"] = g["fos_med"].shift(7)
    d["r24max7"] = g["r24"].rolling(7, min_periods=1).max().reset_index(level=0, drop=True)
    d["wetdays7"] = (g["r24"].rolling(7, min_periods=1)
                     .apply(lambda s: (s >= 10).sum(), raw=False).reset_index(level=0, drop=True))
    d["fos_min14"] = g["fos_med"].rolling(14, min_periods=1).min().reset_index(level=0, drop=True)
    d["r7slope7"] = (g["r7"].rolling(7, min_periods=4)
                     .apply(lambda s: float(np.polyfit(np.arange(len(s)), s, 1)[0]), raw=False)
                     .reset_index(level=0, drop=True))
    d["soil_miss"] = d["soil"].isna().astype(int)
    d["fos_miss"] = d["fos_med"].isna().astype(int)

    FEAT = LEVEL + ["r7_lag3", "r7_lag7", "r30_lag7", "soil_lag3", "fos_lag7",
                    "r24max7", "wetdays7", "fos_min14", "r7slope7",
                    "soil_miss", "fos_miss"]
    # lulc fixed one-hot from frozen training levels (dev-visible static attr)
    lvls = sorted(pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
                  ["lulc"].astype(str).unique().tolist())
    for lv in lvls:
        d[f"lulc_{lv}"] = (d["lulc"].astype(str) == lv).astype(int)
    FEAT += [f"lulc_{lv}" for lv in lvls]

    gkf = GroupKFold(n_splits=5)
    d["fold"] = -1
    for i, (_, te) in enumerate(gkf.split(d, d["y14"], groups=d["slide_no"])):
        d.loc[te, "fold"] = i
    assert (d["fold"] >= 0).all()
    # every fold must contain both classes
    for i in range(5):
        f = d[d["fold"] == i]
        assert f["y14"].sum() > 0 and (f["y14"] == 0).sum() > 0, f"fold {i} degenerate"

    d.to_csv(OUTDIR / "matrix_v1.csv", index=False)
    recipe = {"features": FEAT, "dyn": DYN + ["r7_lag3", "r7_lag7", "r30_lag7",
                                              "soil_lag3", "fos_lag7", "r24max7", "wetdays7",
                                              "fos_min14", "r7slope7", "soil_miss", "fos_miss"],
              "static": ["susceptibility", "slope", "elev", "aspect", "curv", "twi",
                         "spi", "draind", "ndvi", "d_road", "d_river"] + [f"lulc_{lv}" for lv in lvls],
              "imputation": "train-fold median + miss flags (soil_miss, fos_miss); "
                            "computed inside CV, never global",
              "folds": "GroupKFold(5) by slide_no, seed-free deterministic",
              "n": len(d), "positives": int(d["y14"].sum()),
              "note": "shifts/rolling strictly backward-looking; row d uses only rows <= d"}
    json.dump(recipe, open(OUTDIR / "matrix_v1_recipe.json", "w"), indent=2)
    log(f"matrix {len(d)} rows x {len(FEAT)} feats; y14+={int(d['y14'].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
