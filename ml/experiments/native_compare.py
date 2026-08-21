import json
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, f1_score, balanced_accuracy_score

warnings.filterwarnings("ignore")

d = pd.read_csv(r"C:\Users\satvi\Desktop\Talus\data\processed\generator_v1\ml_handoff\synthetic_ml_dataset_seeds_42_46.csv")
FEATURES = ["rainfall_24h_mm", "rainfall_7d_mm", "slope_angle_deg", "slope_height_m", "rock_type",
            "crack_density", "crack_severity", "blast_frequency_per_week", "blast_vibration_ppv_mms",
            "days_since_inspection", "prior_incident", "groundwater_proxy"]
CATS = ["rock_type", "crack_severity"]
X = d[FEATURES]
pre = ColumnTransformer([("num", "passthrough", [c for c in FEATURES if c not in CATS]),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CATS)])


def run_reg(Xtr, Xte, ytr, yte):
    p = Pipeline([("pre", pre), ("m", RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=0))])
    p.fit(Xtr, ytr)
    pr = p.predict(Xte)
    mae = mean_absolute_error(yte, pr)
    rmse = np.sqrt(mean_squared_error(yte, pr))
    r2 = r2_score(yte, pr)
    return [round(float(mae), 3), round(float(rmse), 3), round(float(r2), 3)]


def run_clf(ytr, yte):
    p = Pipeline([("pre", pre), ("m", RandomForestClassifier(n_estimators=400, max_depth=18, min_samples_leaf=2, class_weight="balanced", n_jobs=-1, random_state=0))])
    p.fit(Xtr_clf, ytr)
    pr = p.predict(Xte_clf)
    return [round(float(f1_score(yte, pr, average="macro", zero_division=0)), 3),
            round(float(balanced_accuracy_score(yte, pr)), 3),
            round(float((yte == pr).mean()), 3)]


out = {}

# A) random split WITHIN seeds 42-45 (seed 46 excluded entirely)
m = d.seed != 46
Xtr_c, Xte_c, ytr_c, yte_c = train_test_split(X[m], d[m]["instability_score"], test_size=0.2, random_state=0)
out["random_split_within_seeds_42_45"] = {
    "reg_rf": {"mae_rmse_r2": run_reg(Xtr_c, Xte_c, ytr_c, yte_c)},
    "note": "random split restricted to seeds 42-45; seed 46 excluded",
}

# B) naive random split across ALL 7,300 (leak-inflated reference)
Xtr_a, Xte_a, ytr_a, yte_a = train_test_split(X, d["instability_score"], test_size=0.2, random_state=0)
Xtr_f = Xtr_a; Xte_f = Xte_a
out["random_split_ALL_7300_naive"] = {
    "reg_rf": {"mae_rmse_r2": run_reg(Xtr_a, Xte_a, ytr_a, yte_a)},
    "note": "NAIVE reference: random split includes seed 46 rows in train -> band-leakage inflation",
}

# classification for both: use the same masks
def clf_on(Xtr, Xte, yall):
    split = train_test_split(d["seed"] != 46, np.arange(len(d)), test_size=0.2, random_state=0)
    p = Pipeline([("pre", pre), ("m", RandomForestClassifier(n_estimators=400, max_depth=18, min_samples_leaf=2, class_weight="balanced", n_jobs=-1, random_state=0))])
    p.fit(Xtr, yall[0])
    pr = p.predict(Xte)
    yte = yall[1]
    return [round(float(f1_score(yte, pr, average="macro", zero_division=0)), 3),
            round(float(balanced_accuracy_score(yte, pr)), 3),
            round(float((yte == pr).mean()), 3)]

# A clf
m_idx = d.seed[m].index
idx = np.where(m)[0]
ti, tei = train_test_split(idx, test_size=0.2, random_state=0)
p = Pipeline([("pre", pre), ("m", RandomForestClassifier(n_estimators=400, max_depth=18, min_samples_leaf=2, class_weight="balanced", n_jobs=-1, random_state=0))])
p.fit(X.iloc[ti], d.iloc[ti]["risk_label"])
pr = p.predict(X.iloc[tei])
yte = d.iloc[tei]["risk_label"]
out["random_split_within_seeds_42_45"]["clf_rf"] = {
    "macroF1_balAcc_acc": [round(float(f1_score(yte, pr, average="macro", zero_division=0)), 3),
                           round(float(balanced_accuracy_score(yte, pr)), 3),
                           round(float((yte == pr).mean()), 3)]}

# B clf
idxa = np.arange(len(d))
tia, tea = train_test_split(idxa, test_size=0.2, random_state=0)
p2 = Pipeline([("pre", pre), ("m", RandomForestClassifier(n_estimators=400, max_depth=18, min_samples_leaf=2, class_weight="balanced", n_jobs=-1, random_state=0))])
p2.fit(X.iloc[tia], d.iloc[tia]["risk_label"])
pr2 = p2.predict(X.iloc[tea])
yte2 = d.iloc[tea]["risk_label"]
out["random_split_ALL_7300_naive"]["clf_rf"] = {
    "macroF1_balAcc_acc": [round(float(f1_score(yte2, pr2, average="macro", zero_division=0)), 3),
                           round(float(balanced_accuracy_score(yte2, pr2)), 3),
                           round(float((yte2 == pr2).mean()), 3)]}

with open(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\native_split_compare.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))