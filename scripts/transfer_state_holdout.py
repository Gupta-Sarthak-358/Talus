"""Leave-one-state-out transfer test: train on Sikkim, test on Darjeeling (WB) and vice versa.

Why: GroupKFold-8 already guards geographic leakage, but a state holdout is
the harshest honest test — different inventory (GSI-SK vs GSI-WB), different
terrain, different monsoon exposure. If the model transfers, the learned
physics is real, not inventory memorization.

Assignment: positives by sidecar district (Darjeeling vs all Sikkim labels);
negatives (district='background') by nearest-positive district (seed-free,
deterministic). Same 14-num + lulc pipeline as the trainer, RF500 + LR.

Output: ml/sih26001/reports/transfer.md + transfer.json
Run (mnemo venv): python scripts/transfer_state_holdout.py
"""
from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDECAR = REPO / "data/sih26001/processed/training_sidecar.csv"
REPORTDIR = REPO / "ml/sih26001/reports"
SEED = 42
BASE_NUM = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
            "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
            "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
            "drain_density"]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build_X(mat: pd.DataFrame):
    X = mat[[c for c in BASE_NUM if c != "spi_log"] + ["spi", "lulc"]].copy()
    X["spi_log"] = np.log1p(X.pop("spi").clip(lower=0))
    num = [c for c in X.columns if c != "lulc"]
    return X, num


def main() -> int:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, brier_score_loss
    from sklearn.neighbors import NearestNeighbors
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    mat = pd.read_csv(MATRIX)
    side = pd.read_csv(SIDECAR)
    y = mat["event"].to_numpy().astype(int)
    pos = y == 1
    is_wb_pos = (side["district"] == "Darjeeling").to_numpy() & pos
    # negatives -> nearest positive's state (deterministic, no seed needed)
    nn = NearestNeighbors(n_neighbors=1).fit(side.loc[pos, ["lat", "lon"]].to_numpy())
    _, idx = nn.kneighbors(side.loc[~pos, ["lat", "lon"]].to_numpy())
    wb_of_pos = is_wb_pos[pos]
    neg_wb = np.zeros(len(mat), dtype=bool)
    neg_wb[np.where(~pos)[0]] = wb_of_pos[idx[:, 0]]
    wb = is_wb_pos | neg_wb
    log(f"WB rows: {int(wb.sum())} (pos {int((wb & pos).sum())}), "
        f"SK rows: {int((~wb).sum())} (pos {int(((~wb) & pos).sum())})")

    X, num = build_X(mat)
    pre = ColumnTransformer([("num", StandardScaler(), num),
                             ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"])])
    out = {}
    for name, tr, te in [("train-SK_test-WB", ~wb, wb), ("train-WB_test-SK", wb, ~wb)]:
        rf = Pipeline([("pre", pre), ("clf", RandomForestClassifier(
            n_estimators=500, random_state=SEED, n_jobs=-1))])
        rf.fit(X.iloc[tr], y[tr])
        p_rf = rf.predict_proba(X.iloc[te])[:, 1]
        lr = Pipeline([("pre", ColumnTransformer(
            [("num", StandardScaler(), num),
             ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"])])),
            ("clf", LogisticRegression(max_iter=5000))])
        lr.fit(X.iloc[tr], y[tr])
        p_lr = lr.predict_proba(X.iloc[te])[:, 1]
        out[name] = {
            "n_train": int(tr.sum()), "n_test": int(te.sum()),
            "rf_auc": round(float(roc_auc_score(y[te], p_rf)), 4),
            "rf_brier": round(float(brier_score_loss(y[te], p_rf)), 4),
            "lr_auc": round(float(roc_auc_score(y[te], p_lr)), 4),
            "lr_brier": round(float(brier_score_loss(y[te], p_lr)), 4),
        }
        log(f"{name}: train={tr.sum()} test={te.sum()} "
            f"RF auc={out[name]['rf_auc']} brier={out[name]['rf_brier']} | "
            f"LR auc={out[name]['lr_auc']} brier={out[name]['lr_brier']}")

    lines = ["# Leave-one-state-out transfer (train-SK/test-WB and reverse, RF500+LR, seed 42)",
             "",
             "Hardest honest test: different inventory, terrain, monsoon exposure per side.",
             "Reference: pooled GroupKFold-8 OOF RF 0.9308 / LR 0.8945.",
             "",
             "| direction | train n | test n | RF AUC | RF Brier | LR AUC | LR Brier |",
             "|---|---|---|---|---|---|---|"]
    for name, r in out.items():
        lines.append(f"| {name} | {r['n_train']} | {r['n_test']} | {r['rf_auc']} | "
                     f"{r['rf_brier']} | {r['lr_auc']} | {r['lr_brier']} |")
    REPORTDIR.mkdir(parents=True, exist_ok=True)
    (REPORTDIR / "transfer.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTDIR / "transfer.json").write_text(json.dumps(
        {"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
         "seed": SEED, "reference_oof": {"rf_auc": 0.9308, "lr_auc": 0.8945},
         "directions": out}, indent=2), encoding="utf-8")
    log("reports -> ml/sih26001/reports/transfer.{md,json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
