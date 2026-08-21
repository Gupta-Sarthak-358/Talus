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

d = pd.read_csv(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\seeds_42_61.csv")

FEATURES = ["rainfall_24h_mm", "rainfall_7d_mm", "slope_angle_deg", "slope_height_m", "rock_type",
            "crack_density", "crack_severity", "blast_frequency_per_week", "blast_vibration_ppv_mms",
            "days_since_inspection", "prior_incident", "groundwater_proxy", "zone_id"]
CATS = ["rock_type", "crack_severity", "zone_id"]


def mkpipe():
    pre = ColumnTransformer([("num", "passthrough", [c for c in FEATURES if c not in CATS]),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CATS)])
    return Pipeline([("pre", pre), ("m", RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=0))])


def evals(p, X, y):
    pr = p.predict(X)
    return {"mae": round(float(mean_absolute_error(y, pr)), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y, pr))), 3),
            "r2": round(float(r2_score(y, pr)), 3)}


out = {}


def run_coverage(tag, train_seeds, test_seeds):
    train = d[d.seed.isin(train_seeds)]
    test = d[d.seed.isin(test_seeds)]
    base = train.groupby("zone_id").agg(baseline_fos=("fos", "max"),
                                        baseline_inst=("instability_score", "min")).reset_index()
    tr = train.merge(base, on="zone_id")
    te = test.merge(base, on="zone_id")
    Xtr, Xte = tr[FEATURES], te[FEATURES]

    res = {"train_seeds": sorted(train_seeds), "test_seeds": sorted(test_seeds),
           "train_rows": int(len(tr)), "test_rows": int(len(te))}

    # delta FoS (primary scientific target)
    ytr = tr["fos"] - tr["baseline_fos"]
    yte = te["fos"] - te["baseline_fos"]
    p = mkpipe(); p.fit(Xtr, ytr)
    res["delta_fos"] = evals(p, Xte, yte)
    res["delta_fos"]["train_mean_delta_fos"] = round(float(ytr.mean()), 3)
    res["delta_fos"]["test_mean_delta_fos"] = round(float(yte.mean()), 3)

    # delta instability (ML target)
    ytr2 = tr["instability_score"] - tr["baseline_inst"]
    yte2 = te["instability_score"] - te["baseline_inst"]
    p2 = mkpipe(); p2.fit(Xtr, ytr2)
    res["delta_instability"] = evals(p2, Xte, yte2)
    res["delta_instability"]["train_mean_delta"] = round(float(ytr2.mean()), 3)
    res["delta_instability"]["test_mean_delta"] = round(float(yte2.mean()), 3)

    # absolute instability reference
    p3 = mkpipe(); p3.fit(Xtr, tr["instability_score"])
    res["abs_instability"] = evals(p3, Xte, te["instability_score"])
    return res


# 5-seed equivalent (train 42-45, test 46) for direct comparison
out["n5_seed46_holdout"] = run_coverage("5", [42, 43, 44, 45], [46])

# 20-seed: train 42-56, val 57-58, test 59-61
out["n20_train4256_val5758_test5961"] = run_coverage("20", list(range(42, 57)), list(range(59, 62)))

with open(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\experiment_D_report.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))