"""FR-03 calibration layer: isotonic P(elevated risk) around the frozen RF.

Contract (designed before coding, per review):
  Quantity : P(instability_score >= 75) -- i.e. High/Critical bands (FoS < 1.0),
             called "calibrated probability of elevated synthetic risk".
  Input    : frozen RF mean prediction (raw 0-100 score). Univariate.
  Fit      : isotonic regression on OUT-OF-FOLD train-seed predictions
             (GroupKFold k=5, groups=seed -> no seed crosses folds,
             no validation/test rows used).
  Evaluate : validation seeds 82-86 only -- Brier, ECE (10 bins),
             reliability table. Test seeds 87-91 remain untouched.
  Artifact : ml/models/talus_calibration_v1.joblib
             {isotonic, threshold, version, fit_metadata}
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from config import TRAIN_SEEDS, VAL_SEEDS, FEATURES, CATEGORICAL_FEATURES as CATS

REPO = Path(r"C:\Users\satvi\Desktop\Talus")
CORPUS = REPO / "data" / "processed" / "generator_v1" / "ml_handoff" / "synthetic_ml_dataset_seeds_42_91.csv"
ARTIFACT = REPO / "ml" / "models" / "talus_calibration_v1.joblib"
RESULTS = Path(r"C:\Users\satvi\Desktop\Talus\ml\benchmark\results\calibration.json")
THRESHOLD = 75.0
SEED = 0


def make_rf():
    return RandomForestRegressor(n_estimators=500, max_depth=12, min_samples_leaf=1,
                                 random_state=SEED, n_jobs=-1)


def encode_fit(df):
    nums = [c for c in FEATURES if c not in CATS]
    pre = ColumnTransformer([("n", StandardScaler(), nums),
                             ("c", OneHotEncoder(handle_unknown="ignore"), CATS)])
    pre.fit(df[FEATURES + ["zone_id"]])
    return pre


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def ece(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    total, n = 0.0, len(p)
    table = []
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        if m.sum() == 0:
            continue
        conf, freq = float(p[m].mean()), float(y[m].mean())
        total += m.sum() / n * abs(conf - freq)
        table.append({"bin": f"[{edges[i]:.1f},{edges[i+1]:.1f}]", "n": int(m.sum()),
                      "mean_predicted": round(conf, 3), "observed_frequency": round(freq, 3)})
    return float(total), table


def main():
    d = pd.read_csv(CORPUS)
    d["elevated"] = (d["instability_score"] >= THRESHOLD).astype(int)
    tr = d[d.seed.isin(TRAIN_SEEDS)].reset_index(drop=True)
    va = d[d.seed.isin(VAL_SEEDS)].reset_index(drop=True)

    pre = encode_fit(tr)
    Xtr = pre.transform(tr[FEATURES + ["zone_id"]])
    ytr_score = tr["instability_score"].values.astype(float)
    groups = tr["seed"].values

    # out-of-fold predictions on train seeds (no seed crosses folds)
    oof = np.zeros(len(tr))
    gkf = GroupKFold(n_splits=5)
    for fit_idx, pred_idx in gkf.split(Xtr, ytr_score, groups):
        rf = make_rf()
        rf.fit(Xtr[fit_idx], ytr_score[fit_idx])
        oof[pred_idx] = rf.predict(Xtr[pred_idx])
        print(f"fold done ({len(fit_idx)} train rows)", flush=True)

    ytr_event = (ytr_score >= THRESHOLD).astype(int)
    iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
    iso.fit(oof, ytr_event)

    # freeze the production RF on ALL train seeds (the frozen Model v1 config)
    rf_full = make_rf()
    rf_full.fit(Xtr, ytr_score)

    # evaluate on VALIDATION seeds only
    Xva = pre.transform(va[FEATURES + ["zone_id"]])
    va_scores = rf_full.predict(Xva)
    yva_event = (va["instability_score"].values.astype(float) >= THRESHOLD).astype(int)
    p_iso = iso.predict(va_scores)
    p_naive = np.clip(va_scores / 100.0, 0, 1)

    brier_iso, table = ece(p_iso, yva_event)[:2] if False else (brier(p_iso, yva_event), None)
    ece_iso, table = ece(p_iso, yva_event)
    ece_naive, _ = ece(p_naive, yva_event)
    res = {
        "threshold_score": THRESHOLD,
        "event_definition": "instability_score >= 75 (High/Critical bands, FoS < 1.0)",
        "meaning": "calibrated probability of elevated SYNTHETIC risk under the prototype target definition",
        "fit": {"method": "isotonic", "data": "out-of-fold predictions, train seeds 42-81",
                "cv": "GroupKFold(k=5, groups=seed)", "n_train": int(len(tr))},
        "validation": {
            "seeds": VAL_SEEDS, "n": int(len(va)),
            "base_rate": round(float(yva_event.mean()), 4),
            "brier_isotonic": round(brier_iso, 4),
            "brier_naive_score_over_100": round(brier(p_naive, yva_event), 4),
            "ece_isotonic": round(ece_iso, 4),
            "ece_naive": round(ece_naive, 4),
            "reliability_table": table,
        },
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"isotonic": iso, "threshold": THRESHOLD, "version": "v1"}, ARTIFACT, compress=3)
    RESULTS.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res["validation"], indent=2))
    print(f"\nartifact -> {ARTIFACT}")
    print(f"results  -> {RESULTS}")


if __name__ == "__main__":
    main()