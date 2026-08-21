"""Section 6a: default-parameter baselines (frozen protocol v1).

Each model in the frozen registry is fit on TRAIN and evaluated on
VALIDATION (diagnostic) and TEST (headline). Predictions and metrics are
saved as JSON so the report is reproducible.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from config import default_models, FEATURES, ZONE_COL, CATEGORICAL_FEATURES, RANDOM_STATE
from prepare import (load_corpus, partition, zone_baselines, add_delta_targets,
                     target_vector, X_matrix, categorical_columns)
from metrics import evaluate, TARGET_UNIT


def make_pipeline(estimator, include_zone=True):
    cats = categorical_columns(include_zone)
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    pre = ColumnTransformer([
        ("num_norm", StandardScaler(), nums),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cats),
    ], remainder="drop")
    return Pipeline([("pre", pre), ("est", estimator)])


def run(args):
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    d = load_corpus()
    parts = partition(d)
    baselines = zone_baselines(parts["train"])
    for name, df in parts.items():
        parts[name] = add_delta_targets(df, baselines)

    include_zone = not args.drop_zone

    Xtr = X_matrix(parts["train"], include_zone)
    Xva = X_matrix(parts["validation"], include_zone)
    Xte = X_matrix(parts["test"], include_zone)

    target_names = args.targets
    models = default_models()
    n_train = len(set(parts["train"]["seed"].values))

    result = {
        "protocol": "v1",
        "n_train_seeds": n_train,
        "corpus": str(CORPUS_PATH),
        "include_zone": include_zone,
        "baselines_zone": baselines.to_dict("records"),
        "targets": {},
    }

    for tname in target_names:
        ytr = target_vector(parts["train"], tname)
        yva = target_vector(parts["validation"], tname)
        yte = target_vector(parts["test"], tname)
        seed_te = parts["test"]["seed"].values
        target_block = {"unit": TARGET_UNIT[tname], "models": {}}
        for name, factory in models.items():
            pipe = make_pipeline(factory(), include_zone)
            t0 = time.time()
            pipe.fit(Xtr, ytr)
            pva = pipe.predict(Xva)
            pte = pipe.predict(Xte)
            dt = round(time.time() - t0, 2)
            target_block["models"][name] = {
                "valid": evaluate(yva, pva, parts["validation"]["seed"].values),
                "test": evaluate(yte, pte, seed_te),
                "fit_sec": dt,
            }
            print(f"[baseline] target={tname:18s} model={name:20s} "
                  f"R2_test={target_block['models'][name]['test']['r2']:.3f} (fit {dt}s)",
                  flush=True)
        result["targets"][tname] = target_block

    out_path = out_dir / "baselines_default.json"
    out_path.write_text(json.dumps(result, indent=2),
                        encoding="utf-8")
    print(f"\nwrote {out_path}")


# the corpus path needed by a couple of prints only; import here
from config import CORPUS_PATH  # noqa: E402


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "results"))
    ap.add_argument("--drop-zone", action="store_true",
                    help="exclude zone_id from features (grouping key removed)")
    ap.add_argument("--targets", nargs="+",
                    default=["abs_instability", "delta_instability", "delta_fos"])
    args = ap.parse_args()
    run(args)