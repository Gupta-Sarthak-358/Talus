"""Dataset preparation for the benchmark (protocol v1).

Loads the v2 corpus, derives zone baselines from TRAIN rows only, builds the
seed-aware partition (train/validation/test), and exposes a tiny preprocessing
pipeline: categorical one-hot for linear models + lightgbm/xgb categorical
handling is left to their native params.
"""
import numpy as np
import pandas as pd

from config import (CORPUS_PATH, TRAIN_SEEDS, VAL_SEEDS, TEST_SEEDS,
                    FEATURES, CATEGORICAL_FEATURES, ZONE_COL, SEED_COL,
                    TARGET_COLS)


def load_corpus():
    d = pd.read_csv(CORPUS_PATH)
    d[SEED_COL] = d[SEED_COL].astype(int)
    return d


def partition(d):
    """Return dict of DataFrames keyed by 'train'/'validation'/'test'."""
    tr = d[d[SEED_COL].isin(TRAIN_SEEDS)]
    va = d[d[SEED_COL].isin(VAL_SEEDS)]
    te = d[d[SEED_COL].isin(TEST_SEEDS)]
    return {"train": tr, "validation": va, "test": te}


def zone_baselines(train):
    """Baseline per zone from TRAIN rows only (never peek at val/test)."""
    return train.groupby(ZONE_COL).agg(
        baseline_inst=("instability_score", "min"),
        baseline_fos=("fos", "max"),
    ).reset_index()


def add_delta_targets(df, baselines):
    df = df.merge(baselines, on=ZONE_COL, how="left")
    df["delta_instability"] = df["instability_score"] - df["baseline_inst"]
    df["delta_fos"] = df["fos"] - df["baseline_fos"]
    return df


def target_vector(df, tname):
    if tname == "abs_instability":
        return df["instability_score"].values.astype(float)
    if tname == "delta_instability":
        return df["delta_instability"].values.astype(float)
    if tname == "delta_fos":
        return df["delta_fos"].values.astype(float)
    raise ValueError(tname)


def X_matrix(df, include_zone=True):
    cols = list(FEATURES)
    if include_zone:
        cols = cols + [ZONE_COL]
    return df[cols].copy()


def categorical_columns(include_zone=True):
    cols = list(CATEGORICAL_FEATURES)
    if include_zone:
        cols = cols + [ZONE_COL]
    return cols