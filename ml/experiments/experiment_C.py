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

FEATURES = ["rainfall_24h_mm", "rainfall_7d_mm", "slope_angle_deg", "slope_height_m", "rock_type",
            "crack_density", "crack_severity", "blast_frequency_per_week", "blast_vibration_ppv_mms",
            "days_since_inspection", "prior_incident", "groundwater_proxy", "zone_id"]
CATS = ["rock_type", "crack_severity", "zone_id"]

train = d[d.seed != 46].copy()
test = d[d.seed == 46].copy()


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

# ---------- baseline derivation (TRAIN ONLY, per zone) ----------
# intact/dry structural state = most stable condition seen in train.
# FoS higher = more stable -> max FoS  ;  instability lower = more stable -> min instability.
base = train.groupby("zone_id").agg(baseline_fos=("fos", "max"),
                                    baseline_inst=("instability_score", "min")).reset_index()
out["baselines"] = {r.zone_id: {"fos": round(float(r.baseline_fos), 3),
                                "instability": round(float(r.baseline_inst), 3)} for r in base.itertuples()}

tr = train.merge(base, on="zone_id")
te = test.merge(base, on="zone_id")

Xtr, Xte = tr[FEATURES], te[FEATURES]

# ---------- Target 1: absolute instability (reference, from baseline.py) ----------
from baseline import build_pipeline as _bp  # noqa
p1 = Pipeline([("pre", mkpipe().named_steps["pre"]), ("m", RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=0))])
p1.fit(Xtr, tr["instability_score"])
out["C_target_abs_instability"] = evals(p1, Xte, te["instability_score"])

# ---------- Target 2: delta instability (deviation from intact baseline) ----------
y_dinst_tr = tr["instability_score"] - tr["baseline_inst"]
y_dinst_te = te["instability_score"] - te["baseline_inst"]
p2 = mkpipe()
p2.fit(Xtr, y_dinst_tr)
out["C_target_delta_instability"] = evals(p2, Xte, y_dinst_te)
out["C_target_delta_instability"]["test_mean_delta"] = round(float(y_dinst_te.mean()), 3)
out["C_target_delta_instability"]["train_mean_delta"] = round(float(y_dinst_tr.mean()), 3)

# ---------- Target 3: delta FoS (deviation from intact structural FoS) ----------
y_dfos_tr = tr["fos"] - tr["baseline_fos"]
y_dfos_te = te["fos"] - te["baseline_fos"]
p3 = mkpipe()
p3.fit(Xtr, y_dfos_tr)
out["C_target_delta_fos"] = evals(p3, Xte, y_dfos_te)
out["C_target_delta_fos"]["test_mean_delta_fos"] = round(float(y_dfos_te.mean()), 3)
out["C_target_delta_fos"]["train_mean_delta_fos"] = round(float(y_dfos_tr.mean()), 3)

with open(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\experiment_C_report.json", "w") as f:
    json.dump(out, f, indent=2, default=str)
print(json.dumps(out, indent=2, default=str))