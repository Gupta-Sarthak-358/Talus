"""Experiment G: can real DEM-derived spatial context improve prediction?

Zones have no geo-coordinates, so curvature/aspect/flow-accumulation would
require inventing locations (rejected). But the frozen terrain sampler already
exposes two REAL DEM-derived fields that the V1 contract never ships:
elevation_m and regional_slope_deg. This experiment adds exactly those.

Protocol unchanged: train 42-81 / val 82-86 / test 87-91, LightGBM frozen
config, three targets. Kill criterion: no meaningful improvement => dead.
"""
import json
import sys

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from config import TRAIN_SEEDS, VAL_SEEDS, TEST_SEEDS

SCRATCH = r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe"
V1 = ["rainfall_24h_mm", "rainfall_7d_mm", "slope_angle_deg", "slope_height_m",
      "rock_type", "crack_density", "crack_severity", "blast_frequency_per_week",
      "blast_vibration_ppv_mms", "days_since_inspection", "prior_incident",
      "groundwater_proxy"]
DEM = ["elevation_m", "regional_slope_deg"]
CATS = ["rock_type", "crack_severity", "zone_id"]


def metrics(y, p):
    return {"mae": round(float(mean_absolute_error(y, p)), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y, p))), 3),
            "r2": round(float(r2_score(y, p)), 3)}


def main():
    d = pd.read_csv(rf"{SCRATCH}\internal_states_42_91.csv")
    d = d.rename(columns={"material_class": "rock_type", "rainfall_mm": "rainfall_24h_mm"})
    tr = d[d.seed.isin(TRAIN_SEEDS)].reset_index(drop=True)
    va = d[d.seed.isin(VAL_SEEDS)].reset_index(drop=True)
    te = d[d.seed.isin(TEST_SEEDS)].reset_index(drop=True)
    base = tr.groupby("zone_id").agg(bi=("instability_score", "min"), bf=("fos", "max")).reset_index()
    for part in (tr, va, te):
        part.merge(base, on="zone_id", how="left")
    tr = tr.merge(base, on="zone_id"); va = va.merge(base, on="zone_id"); te = te.merge(base, on="zone_id")
    for part in (tr, va, te):
        part["delta_instability"] = part["instability_score"] - part["bi"]
        part["delta_fos"] = part["fos"] - part["bf"]

    out = {}
    for tag, feats in [("V1", V1 + ["zone_id"]), ("V1+DEM", V1 + DEM + ["zone_id"])]:
        nums = [c for c in feats if c not in CATS]
        pre = ColumnTransformer([("n", StandardScaler(), nums),
                                 ("c", OneHotEncoder(handle_unknown="ignore"), CATS)])
        pre.fit(tr[feats])
        Xtr, Xva, Xte = (pre.transform(p[feats]) for p in (tr, va, te))
        for tname, ycol in [("abs", "instability_score"), ("d_inst", "delta_instability"), ("d_fos", "delta_fos")]:
            m = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                              random_state=0, n_jobs=-1, verbose=-1)
            m.fit(Xtr, tr[ycol].values.astype(float))
            out.setdefault(tname, {})[tag] = metrics(te[ycol].values.astype(float), m.predict(Xte))
        print(f"[{tag}] done", flush=True)

    print("\n=== Experiment G: V1 vs V1+real DEM context ===")
    verdicts = {}
    for tname, blk in out.items():
        v1, dem = blk["V1"], blk["V1+DEM"]
        delta = round(dem["r2"] - v1["r2"], 4)
        verdicts[tname] = {"V1": v1, "V1+DEM": dem, "delta_r2": delta}
        print(f"{tname:6s} V1 R2={v1['r2']:.3f}  V1+DEM R2={dem['r2']:.3f}  delta={delta:+.4f}")
    out["verdict"] = ("KILL: no meaningful improvement" if all(abs(v["delta_r2"]) < 0.01 for v in verdicts.values())
                      else "KEEP: improvement >= 0.01 on at least one target")
    print("\n" + out["verdict"])
    with open(rf"{SCRATCH}\experiment_G_dem.json", "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()