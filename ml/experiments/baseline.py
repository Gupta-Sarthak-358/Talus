import json
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                             f1_score, precision_recall_fscore_support,
                             confusion_matrix, balanced_accuracy_score)
from sklearn.inspection import permutation_importance
from xgboost import XGBRegressor, XGBClassifier

warnings.filterwarnings("ignore")

DATA = r"C:\Users\satvi\Desktop\Talus\data\processed\generator_v1\ml_handoff\synthetic_ml_dataset_seeds_42_46.csv"
OUT = r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe"

FEATURES = ["rainfall_24h_mm", "rainfall_7d_mm", "slope_angle_deg", "slope_height_m",
            "rock_type", "crack_density", "crack_severity", "blast_frequency_per_week",
            "blast_vibration_ppv_mms", "days_since_inspection", "prior_incident",
            "groundwater_proxy"]
CATS = ["rock_type", "crack_severity"]
REGR_TARGET = "instability_score"
CLASS_TARGET = "risk_label"
LABEL_ORDER = ["very_low", "low", "moderate", "high", "critical"]


def build_pipeline(kind):
    pre = ColumnTransformer([
        ("num", "passthrough", [c for c in FEATURES if c not in CATS]),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATS),
    ])
    if kind == "dummy_reg":
        return kind, pre, DummyRegressor(strategy="mean"), "reg"
    if kind == "dummy_clf":
        return kind, pre, DummyClassifier(strategy="most_frequent"), "clf"
    if kind == "rf_reg":
        return kind, pre, RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=0), "reg"
    if kind == "gb_reg":
        return kind, pre, GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=0), "reg"
    if kind == "xgb_reg":
        return kind, pre, XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.06, reg_lambda=1.0,
                                       subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=0), "reg"
    if kind == "rf_clf":
        return kind, pre, RandomForestClassifier(n_estimators=400, max_depth=18, min_samples_leaf=2, class_weight="balanced",
                                                 n_jobs=-1, random_state=0), "clf"
    if kind == "gb_clf":
        return kind, pre, GradientBoostingClassifier(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=0), "clf"
    if kind == "xgb_clf":
        return kind, pre, XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.06, reg_lambda=1.0,
                                        subsample=0.8, colsample_bytree=0.8, eval_metric="mlogloss", random_state=0), "clf"
    raise ValueError(kind)


def run():
    d = pd.read_csv(DATA)
    X = d[FEATURES]
    y_reg = d[REGR_TARGET].astype(float)
    y_clf = le = LabelEncoder().fit_transform(d[CLASS_TARGET])

    report = {
        "row_count": len(d),
        "features": FEATURES,
        "seed_heldout": True,
        "target_dist_reg": {
            "min": float(y_reg.min()), "mean": float(y_reg.mean()), "std": float(y_reg.std()),
            "max": float(y_reg.max()), "p25": float(y_reg.quantile(.25)), "p50": float(y_reg.median()), "p75": float(y_reg.quantile(.75)),
        },
        "target_dist_clf": {k: int(v) for k, v in sorted(d[CLASS_TARGET].value_counts().items())},
    }

    # ---- Split strategy: temporal hold-out of the LAST SEED (seed 46) ----
    train_mask = d["seed"] != 46
    test_mask = d["seed"] == 46
    report["split"] = {
        "train_rows": int(train_mask.sum()),
        "test_rows": int(test_mask.sum()),
        "rule": "train=seeds 42,43,44,45; test=seed 46. Rows within a seed are 4 zones x 365 days; no seed skips.",
    }

    results = {}
    for kind in ["dummy_reg", "rf_reg", "gb_reg", "xgb_reg"]:
        name, pre, model, _ = build_pipeline(kind)
        t0 = time.time()
        pipe = Pipeline([("pre", pre), ("model", model)])
        pipe.fit(X[train_mask], y_reg[train_mask])
        pred = pipe.predict(X[test_mask])
        yt = y_reg[test_mask].values
        dt = time.time() - t0
        results[name] = {
            "mae": float(mean_absolute_error(yt, pred)),
            "rmse": float(np.sqrt(mean_squared_error(yt, pred))),
            "r2": float(r2_score(yt, pred)),
            "train_sec": round(dt, 2),
        }

    for kind in ["dummy_clf", "rf_clf", "gb_clf", "xgb_clf"]:
        name, pre, model, _ = build_pipeline(kind)
        t0 = time.time()
        pipe = Pipeline([("pre", pre), ("model", model)])
        pipe.fit(X[train_mask], y_clf[train_mask])
        pred = pipe.predict(X[test_mask])
        yt = y_clf[test_mask]
        dt = time.time() - t0
        cm = confusion_matrix(yt, pred, labels=np.arange(5))
        pr, rec, f1, supp = precision_recall_fscore_support(yt, pred, labels=np.arange(5), zero_division=0)
        results[name] = {
            "macro_f1": float(f1_score(yt, pred, average="macro", zero_division=0)),
            "balanced_acc": float(balanced_accuracy_score(yt, pred)),
            "accuracy": float((yt == pred).mean()),
            "per_class": {
                LABEL_ORDER[i]: {
                    "precision": round(float(pr[i]), 3),
                    "recall": round(float(rec[i]), 3),
                    "f1": round(float(f1[i]), 3),
                    "support": int(supp[i]),
                }
                for i in range(5)
            },
            "confusion_matrix": cm.tolist(),
            "train_sec": round(dt, 2),
        }

    # ---- Feature importance (permutation, seeded on the strongest regressor for clarity) ----
    pipe = Pipeline([("pre", pre), ("model", RandomForestRegressor(n_estimators=400, max_depth=18, min_samples_leaf=2, n_jobs=-1, random_state=0))])
    pipe.fit(X[train_mask], y_reg[train_mask])
    pi = permutation_importance(pipe, X[test_mask], y_reg[test_mask], n_repeats=10, random_state=0, n_jobs=-1)
    results["permutation_importance_reg"] = {
        f: round(float(pi.importances_mean[i]), 4) for i, f in enumerate(FEATURES)
    }

    report["results"] = results
    report["label_order"] = LABEL_ORDER

    with open(f"{OUT}/baseline_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()