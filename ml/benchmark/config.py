"""Frozen configuration for the TALUS ML benchmark (protocol v1).

See protocol.md for the frozen rules. Change here only to record a new
frozen revision, never silently.
"""
from pathlib import Path

from sklearn.ensemble import (RandomForestRegressor, HistGradientBoostingRegressor)
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

REPO = Path(r"C:\Users\satvi\Desktop\Talus")
CORPUS_PATH = REPO / "data" / "processed" / "generator_v1" / "ml_handoff" / "synthetic_ml_dataset_seeds_42_91.csv"

RANDOM_STATE = 0
N_JOBS = -1

FEATURES = [
    "rainfall_24h_mm",
    "rainfall_7d_mm",
    "slope_angle_deg",
    "slope_height_m",
    "rock_type",
    "crack_density",
    "crack_severity",
    "blast_frequency_per_week",
    "blast_vibration_ppv_mms",
    "days_since_inspection",
    "prior_incident",
    "groundwater_proxy",
]
ZONE_COL = "zone_id"
CATEGORICAL_FEATURES = ["rock_type", "crack_severity"]
SEED_COL = "seed"
TARGET_COLS = ["fos", "instability_score", "risk_label"]

# partition: seeds 42-81 train, 82-86 validation, 87-91 test
TRAIN_SEEDS = list(range(42, 82))
VAL_SEEDS = list(range(82, 87))
TEST_SEEDS = list(range(87, 92))

TARGET_DEFS = ["abs_instability", "delta_instability", "delta_fos"]


def default_models():
    """(name, estimator_factory) for section 6a default-param baselines."""
    return {
        "dummy": lambda: DummyRegressor(strategy="mean"),
        "ridge": lambda: Ridge(alpha=1.0, random_state=RANDOM_STATE),
        "random_forest": lambda: RandomForestRegressor(
            n_estimators=300, max_depth=None, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=N_JOBS),
        "hist_gradient_boost": lambda: HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.05, max_depth=6,
            random_state=RANDOM_STATE),
        "xgboost": lambda: XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE,
            n_jobs=N_JOBS, eval_metric="rmse"),
        "lightgbm": lambda: LGBMRegressor(
            n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
            subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_STATE,
            n_jobs=N_JOBS, verbose=-1),
    }


def tuning_spaces():
    """Hyperparameter search spaces for section 6b (RandomizedSearchCV).

    Keys match default_models(). Sizes are deliberately REDUCED during
    search: trees/iterations are a cheap proxy to find promising
    hyperparameters, not the final model. After search, the best config is
    refit at PRODUCTION_SIZES (full estimators) on TRAIN+VALIDATION and
    evaluated ONCE on TEST. See protocol.md 6b.
    """
    return {
        "ridge": {"alpha": [1e-2, 1e-1, 1.0, 10.0, 100.0]},
        "random_forest": {
            "n_estimators": [100, 150, 200],
            "max_depth": [12, 18, None],
            "min_samples_leaf": [1, 2, 4],
        },
        "hist_gradient_boost": {
            "max_iter": [100, 200, 300],
            "learning_rate": [0.02, 0.05, 0.1],
            "max_depth": [4, 6, 8],
            "l2_regularization": [0.0, 1.0, 10.0],
        },
        "xgboost": {
            "n_estimators": [100, 200, 300],
            "learning_rate": [0.02, 0.05, 0.1],
            "max_depth": [4, 6, 8],
            "subsample": [0.7, 0.8, 1.0],
            "colsample_bytree": [0.7, 0.8, 1.0],
            "reg_lambda": [0.1, 1.0, 10.0],
        },
        "lightgbm": {
            "n_estimators": [100, 200, 300],
            "learning_rate": [0.02, 0.05, 0.1],
            "num_leaves": [15, 31, 63],
            "max_depth": [4, 6, 8],
            "subsample": [0.7, 0.8, 1.0],
            "colsample_bytree": [0.7, 0.8, 1.0],
            "reg_lambda": [0.1, 1.0, 10.0],
        },
    }


def production_sizes():
    """Full estimator sizes for the FINAL refit after tuning (protocol 6b).

    During search we used reduced n_estimators/max_iter; the winning config
    is then refit with these full sizes on TRAIN+VALIDATION before the single
    TEST evaluation. Tuned values for the estimator-size key are replaced by
    the full size; all other tuned hyperparameters are kept.
    """
    return {
        "ridge": {},
        "random_forest": {"n_estimators": 500},
        "hist_gradient_boost": {"max_iter": 400},
        "xgboost": {"n_estimators": 500},
        "lightgbm": {"n_estimators": 500},
    }