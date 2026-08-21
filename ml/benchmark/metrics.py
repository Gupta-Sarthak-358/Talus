"""Frozen metric helpers for the benchmark (protocol v1).

Metrics per the protocol: MAE, RMSE, R2 plus a per-seed bootstrap CI of R2
to respect the fact that test WORLDS (not rows) are the unit of evaluation.
"""
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

TARGET_UNIT = {
    "abs_instability": "0-100 score",
    "delta_instability": "score units (deviation)",
    "delta_fos": "FoS units (deviation)",
}


def seed_meta_r2(truth, pred, seed_labels, n_boot=2000, random_state=0):
    """Per-seed-seeded bootstrap: resample whole seeds, recompute R2."""
    seeds = np.unique(seed_labels)
    rng = np.random.default_rng(random_state)
    boots = []
    for _ in range(n_boot):
        picked = rng.choice(seeds, size=len(seeds), replace=True)
        idx = np.concatenate([np.where(seed_labels == s)[0] for s in picked])
        y, p = truth[idx], pred[idx]
        if y.std() <= 1e-12:
            continue
        boots.append(r2_score(y, p))
    boots = np.array(boots)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def evaluate(y_true, y_pred, seed_labels):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    lo, hi = seed_meta_r2(y_true, y_pred, seed_labels)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "r2_seed_boot_2.5": lo,
        "r2_seed_boot_97.5": hi,
    }