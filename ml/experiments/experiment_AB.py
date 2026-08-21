import json
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

d = pd.read_csv(r"C:\Users\satvi\Desktop\Talus\data\processed\generator_v1\ml_handoff\synthetic_ml_dataset_seeds_42_46.csv")

STATIC = ["slope_angle_deg", "slope_height_m", "rock_type"]
DYNAMIC = ["rainfall_24h_mm", "rainfall_7d_mm", "crack_density", "crack_severity",
           "blast_frequency_per_week", "blast_vibration_ppv_mms", "days_since_inspection",
           "prior_incident", "groundwater_proxy"]
ALL = STATIC + DYNAMIC
CATS = ["rock_type", "crack_severity"]


def mkpipe(features):
    cats = [c for c in CATS if c in features]
    pre = ColumnTransformer([("num", "passthrough", [c for c in features if c not in CATS]),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), cats)])
    return Pipeline([("pre", pre), ("m", RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=0))])


def evals(p, Xte, yte):
    pr = p.predict(Xte)
    return {"mae": round(float(mean_absolute_error(yte, pr)), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(yte, pr))), 3),
            "r2": round(float(r2_score(yte, pr)), 3)}


out = {}

# ============ EXPERIMENT A: single seed 42, chronological split ============
# Jan-Sep -> train (days 0-272), Oct-Nov -> val (273-334), Dec -> test (335-364)
seed42 = d[d.seed == 42].copy()
day = seed42.groupby(["zone_id"]).cumcount()
seed42["day"] = day
tr = seed42[seed42.day <= 272].drop(columns=["zone_id", "seed", "day", "instability_score", "risk_label", "fos"])
va = seed42[(seed42.day > 272) & (seed42.day <= 334)].drop(columns=["zone_id", "seed", "day", "instability_score", "risk_label", "fos"])
te = seed42[seed42.day > 334].drop(columns=["zone_id", "seed", "day", "instability_score", "risk_label", "fos"])
ytr, yva, yte = seed42[seed42.day <= 272]["instability_score"], seed42[(seed42.day > 272) & (seed42.day <= 334)]["instability_score"], seed42[seed42.day > 334]["instability_score"]

pA = mkpipe(ALL)
pA.fit(tr, ytr)
out["A_singleseed_seed42_chrono"] = {
    "train": {"days": "0-272", "rows": len(tr), "mean_y": round(float(ytr.mean()), 2),
              "test_mean_y": round(float(yte.mean()), 2)},
    "val": evals(pA, va, yva),
    "test": evals(pA, te, yte),
}

# also per-zone within seed42 chrono (controls per zone)
per_zone = {}
for z in seed42.zone_id.unique():
    sz = seed42[seed42.zone_id == z]
    dcol = sz.groupby("zone_id").cumcount()
    sz = sz.assign(day=dcol)
    trz = sz[sz.day <= 272].drop(columns=["zone_id", "seed", "day", "instability_score", "risk_label", "fos"])
    tez = sz[sz.day > 334].drop(columns=["zone_id", "seed", "day", "instability_score", "risk_label", "fos"])
    ytrz, ytez = sz[sz.day <= 272]["instability_score"], sz[sz.day > 334]["instability_score"]
    pz = mkpipe(ALL)
    pz.fit(trz, ytrz)
    per_zone[z] = {**evals(pz, tez, ytez),
                   "train_mean": round(float(ytrz.mean()), 2), "test_mean": round(float(ytez.mean()), 2)}
out["A_seed42_chrono_per_zone"] = per_zone

# ============ EXPERIMENT B: static vs dynamic, honest unseen-seed split ============
m = d.seed != 46
Xtr, Xte = d[m], d[d.seed == 46]
ytr, yte = d[m]["instability_score"], d[d.seed == 46]["instability_score"]

for name, feats in [("static_geometry_geology", STATIC), ("dynamic_env_ops", DYNAMIC), ("all_features", ALL)]:
    p = mkpipe(feats)
    p.fit(Xtr[feats], ytr)
    out[f"B_unseenseed46_{name}"] = evals(p, Xte[feats], yte)

with open(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\experiment_AB_report.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))