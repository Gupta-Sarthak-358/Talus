"""VI-T0A: LR/RF/XGB on frozen matrix_v1. Fixed hyperparams (baseline, NO tuning).

Outer: stored grouped folds (5, by site). Imputation: train-fold medians.
Calibration: isotonic on INNER GroupKFold(4) OOF train preds, refit on full
train, apply to test fold. Metrics pooled over test folds: AUC/AP/Brier/ECE
for y14 (primary) and y7 (secondary, same scores). Dev only. No held-out.
Outputs runs/phase_v/vit0a/. Run: mnemo-venv python scripts/train_vit_t0a.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "runs" / "phase_v" / "vit0a"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def brier(y, p) -> float:
    return round(float(np.mean((p - y) ** 2)), 4)


def ece(y, p, bins=10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p <= edges[b + 1])
        if m.sum() == 0:
            continue
        e += (m.sum() / len(p)) * abs(y[m].mean() - p[m].mean())
    return round(float(e), 4)


def metrics(y, p) -> dict:
    return {"auc": round(float(roc_auc_score(y, p)), 4),
            "ap": round(float(average_precision_score(y, p)), 4),
            "brier": brier(y, p), "ece": ece(y, p)}


def make_models():
    return {
        "lr": make_pipeline(StandardScaler(),
                            LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)),
        "rf": RandomForestClassifier(n_estimators=500, min_samples_leaf=5,
                                     class_weight="balanced_subsample", n_jobs=-1, random_state=42),
        "xgb": XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8, reg_lambda=2.0,
                             scale_pos_weight=8.0, n_jobs=-1, random_state=42,
                             tree_method="hist"),
    }


def main() -> int:
    d = pd.read_csv(REPO / "data/vit/matrix_v1.csv")
    recipe = json.load(open(REPO / "data/vit/matrix_v1_recipe.json"))
    FEAT = recipe["features"]
    X = d[FEAT].to_numpy(float)
    groups = d["slide_no"].to_numpy()
    res: dict = {}
    pooled: dict = {}
    oof_store: dict = {}
    for name, proto in make_models().items():
        all_raw, all_cal, all_y14, all_y7, folds = [], [], [], [], []
        cal_series = pd.Series(index=d.index, dtype=float)
        for fold in sorted(d["fold"].unique()):
            te = (d["fold"] == fold).to_numpy()
            tr = ~te
            med = np.nanmedian(X[tr], axis=0)
            Xtr = np.where(np.isnan(X[tr]), med, X[tr])
            Xte = np.where(np.isnan(X[te]), med, X[te])
            ytr = d.loc[tr, "y14"].to_numpy()
            # inner OOF on train for isotonic
            inner = GroupKFold(n_splits=4)
            oof = np.zeros(tr.sum())
            gtr = groups[tr]
            for itr, iva in inner.split(Xtr, ytr, groups=gtr):
                from sklearn.base import clone
                m = clone(proto).fit(Xtr[itr], ytr[itr])
                oof[iva] = m.predict_proba(Xtr[iva])[:, 1]
            iso = IsotonicRegression(out_of_bounds="clip").fit(oof, ytr)
            from sklearn.base import clone
            m = clone(proto).fit(Xtr, ytr)
            raw = m.predict_proba(Xte)[:, 1]
            cal = iso.predict(raw)
            cal_series.loc[d[te].index] = cal
            all_raw.append(raw)
            all_cal.append(cal)
            all_y14.append(d.loc[te, "y14"].to_numpy())
            all_y7.append(d.loc[te, "y7"].to_numpy())
            folds.append({"fold": int(fold),
                          "raw14": metrics(d.loc[te, "y14"].to_numpy(), raw),
                          "cal14": metrics(d.loc[te, "y14"].to_numpy(), cal)})
        y14 = np.concatenate(all_y14)
        y7 = np.concatenate(all_y7)
        raw = np.concatenate(all_raw)
        cal = np.concatenate(all_cal)
        res[name] = {"folds": folds,
                     "pooled_raw14": metrics(y14, raw), "pooled_cal14": metrics(y14, cal),
                     "pooled_raw7": metrics(y7, raw), "pooled_cal7": metrics(y7, cal)}
        pooled[name] = res[name]["pooled_cal14"]
        oof_store[name] = cal_series
        log(f"{name}: cal14 AUC={res[name]['pooled_cal14']['auc']} "
            f"Brier={res[name]['pooled_cal14']['brier']} | "
            f"cal7 AUC={res[name]['pooled_cal7']['auc']}")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(OUTDIR / "vit0a_cv.json", "w"), indent=2)
    oof = d[["slide_no", "traj_id", "stratum", "date", "y14", "y7", "fold"]].copy()
    for name, s in oof_store.items():
        oof[name] = s
    oof.to_csv(OUTDIR / "oof_preds.csv", index=False)
    d[["slide_no", "traj_id", "stratum", "date", "y14", "y7", "fold"]].to_csv(
        OUTDIR / "keys.csv", index=False)
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
