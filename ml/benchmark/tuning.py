"""Section 6b: hyperparameter tuning (frozen protocol v1).

Rules locked in protocol.md:
- Search is randomized over TRAIN seeds ONLY.
- GroupKFold(k=5) has groups = train seed, so a seed never crosses folds.
- Validation set is used ONLY for model selection after tuning.
- TEST is touched exactly once, after refit on TRAIN+VALIDATION seeds 42-86.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GroupKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from config import (default_models, tuning_spaces, production_sizes, FEATURES,
                    CATEGORICAL_FEATURES, RANDOM_STATE)
from prepare import (load_corpus, partition, zone_baselines, add_delta_targets,
                     target_vector, X_matrix, categorical_columns)
from metrics import evaluate

SESSION = Path(__file__).parent / "results"


def build_pipe(estimator, include_zone):
    cats = categorical_columns(include_zone)
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    pre = ColumnTransformer([
        ("num_norm", StandardScaler(), nums),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cats),
    ], remainder="drop")
    return Pipeline([("pre", pre), ("est", estimator)])


def run(args):
    d = load_corpus()
    parts = partition(d)
    baselines = zone_baselines(parts["train"])
    for name, df in parts.items():
        parts[name] = add_delta_targets(df, baselines)

    include_zone = not args.drop_zone
    train_df = parts["train"]
    val_df = parts["validation"]
    all_df = pd_concat(train_df, val_df)
    Xtr = X_matrix(train_df, include_zone)
    Xva = X_matrix(val_df, include_zone)
    Xall = X_matrix(all_df, include_zone)
    groups_tr = train_df["seed"].values
    seed_va = val_df["seed"].values
    seed_te = parts["test"]["seed"].values

    result = {"protocol": "v1", "targets": {}, "tuned_params": {}}

    for tname in args.targets:
        ytr = target_vector(train_df, tname)
        yva = target_vector(val_df, tname)
        yall = target_vector(all_df, tname)
        target_block = {}
        for model_name in args.models:
            if model_name not in tuning_spaces():
                print(f"  skip {model_name}: no tuning space defined")
                continue
            space = tuning_spaces()[model_name]
            est = default_models()[model_name]()
            # pipeline estimator slot is named "est" -> remap keys to est__*
            full = {f"est__{k}": v for k, v in space.items()}
            pipe = build_pipe(est, include_zone)
            gkf = GroupKFold(n_splits=5)
            search = RandomizedSearchCV(
                pipe, full, scoring="neg_root_mean_squared_error",
                cv=gkf, n_iter=args.n_iter, n_jobs=-1,
                random_state=RANDOM_STATE, error_score="raise", refit=False,
            )
            t0 = time.time()
            search.fit(Xtr, ytr, groups=groups_tr)
            best = search.best_params_
            dt = round(time.time() - t0, 2)

            # refit on TRAIN+VALIDATION at PRODUCTION sizes (cheap-search
            # sizes were proxies; protocol 6b says full model for final eval)
            final_params = dict(best)
            for key, val in production_sizes().get(model_name, {}).items():
                final_params[f"est__{key}"] = val
            best_pipe = build_pipe(est, include_zone)
            best_pipe.set_params(**final_params)
            best_pipe.fit(Xall, yall)

            pva = best_pipe.predict(Xva)
            pte = best_pipe.predict(X_matrix(parts["test"], include_zone))
            target_block[model_name] = {
                "best_params_search": best,
                "final_params_production": final_params,
                "valid_after_refit_train_val": evaluate(yva, pva, seed_va),
                "test_after_refit_train_val": evaluate(
                    target_vector(parts["test"], tname), pte, seed_te),
                "cv_search_sec": dt,
            }
            result["tuned_params"][f"{tname}::{model_name}"] = best
            print(f"[tune] target={tname:18s} model={model_name:20s} "
                  f"R2_test={target_block[model_name]['test_after_refit_train_val']['r2']:.3f} "
                  f"(cv {dt}s)", flush=True)
        result["targets"][tname] = target_block

    out_path = SESSION / f"tuned_{'_'.join(args.models)}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out_path}")


def pd_concat(a, b):
    import pandas as pd
    return pd.concat([a, b], ignore_index=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SESSION))
    ap.add_argument("--drop-zone", action="store_true")
    ap.add_argument("--targets", nargs="+",
                    default=["abs_instability", "delta_instability", "delta_fos"])
    ap.add_argument("--models", nargs="+",
                    default=["ridge", "random_forest", "hist_gradient_boost", "xgboost", "lightgbm"])
    ap.add_argument("--n-iter", type=int, default=20)
    args = ap.parse_args()
    run(args)