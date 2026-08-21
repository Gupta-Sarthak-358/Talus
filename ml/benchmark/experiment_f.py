"""Experiment F (Member 2 Phases 5-8): does temporal observability help?

Baseline (frozen, 50 worlds): LightGBM abs R2=0.901 / d-inst 0.847 / d-fos 0.845.
Protocol unchanged: train 42-81, val 82-86 (selection only), test 87-91 once.
Model A = V1 (12 snapshot features). Model B = V2 (V1 + 20 causal trend features).
Ablation by feature group. Final model selection on the winning feature set.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\features")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from generator_v1 import build_timeline, build_internal_state
from temporal_features import (build_v2, selftest_causality, V1, V2_TEMPORAL, GROUPS,
                               TEMPORAL_RAIN, TEMPORAL_GW, TEMPORAL_CRACK, TEMPORAL_BLAST)
from config import TRAIN_SEEDS, VAL_SEEDS, TEST_SEEDS

DEVICE_FREE = True
SCRATCH = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe")
CACHE = SCRATCH / "internal_states_42_91.csv"
OUT = SCRATCH / "experiment_f_results.json"
SEED = 0
np.random.seed(SEED)

LGBM_PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                   random_state=SEED, n_jobs=-1, verbose=-1)


def get_internal_states():
    if CACHE.exists():
        d = pd.read_csv(CACHE)
        return d.rename(columns={"material_class": "rock_type"})
    frames = []
    t0 = time.time()
    for seed in range(42, 92):
        tl = build_timeline("2024-01-01", 365)
        df = build_internal_state(tl, seed)
        df["seed"] = seed
        frames.append(df)
    d = pd.concat(frames, ignore_index=True)
    d.to_csv(CACHE, index=False)
    print(f"internal states cached: {len(d)} rows ({time.time()-t0:.0f}s)", flush=True)
    return d.rename(columns={"material_class": "rock_type"})


def metrics(y, p):
    return {"mae": round(float(mean_absolute_error(y, p)), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y, p))), 3),
            "r2": round(float(r2_score(y, p)), 3)}


def encode_fit(df, feats):
    cats = [c for c in ["rock_type", "crack_severity", "zone_id"] if c in feats]
    nums = [c for c in feats if c not in cats]
    pre = ColumnTransformer([("n", StandardScaler(), nums),
                             ("c", OneHotEncoder(handle_unknown="ignore"), cats)])
    pre.fit(df[feats])
    return pre


def main():
    d = get_internal_states()
    v2 = build_v2(d)

    ok, fails = selftest_causality(d, n_checks=20)
    print(f"causality gate: {'PASS' if ok else 'FAIL ' + str(fails[:3])}", flush=True)
    if not ok:
        sys.exit(1)

    tr = v2[v2.seed.isin(TRAIN_SEEDS)].reset_index(drop=True)
    va = v2[v2.seed.isin(VAL_SEEDS)].reset_index(drop=True)
    te = v2[v2.seed.isin(TEST_SEEDS)].reset_index(drop=True)
    base = tr.groupby("zone_id").agg(baseline_inst=("instability_score", "min"),
                                     baseline_fos=("fos", "max")).reset_index()
    for part in (tr, va, te):
        part.merge(base, on="zone_id", how="left") if False else None
    tr = tr.merge(base, on="zone_id"); va = va.merge(base, on="zone_id"); te = te.merge(base, on="zone_id")
    TARGETS = {"abs_instability": "instability_score",
               "delta_instability": "delta_instability",
               "delta_fos": "delta_fos"}
    tr["delta_instability"] = tr["instability_score"] - tr["baseline_inst"]
    va["delta_instability"] = va["instability_score"] - va["baseline_inst"]
    te["delta_instability"] = te["instability_score"] - te["baseline_inst"]
    tr["delta_fos"] = tr["fos"] - tr["baseline_fos"]
    va["delta_fos"] = va["fos"] - va["baseline_fos"]
    te["delta_fos"] = te["fos"] - te["baseline_fos"]

    RES = {"causality_gate": "PASS", "runs": {}}

    def run_lgbm(feats, tag):
        pre = encode_fit(tr, feats)
        Xtr = pre.transform(tr[feats])
        Xva = pre.transform(va[feats])
        Xte = pre.transform(te[feats])
        block = {}
        for tname, ycol in TARGETS.items():
            m = LGBMRegressor(**LGBM_PARAMS)
            m.fit(Xtr, tr[ycol].values.astype(float))
            pv = m.predict(Xva)
            pt = m.predict(Xte)
            block[tname] = {"val": metrics(va[ycol].values.astype(float), pv),
                            "test": metrics(te[ycol].values.astype(float), pt)}
            print(f"[{tag}] {tname}: val R2={block[tname]['val']['r2']:.3f} "
                  f"test R2={block[tname]['test']['r2']:.3f}", flush=True)
        return block

    RES["runs"]["A_V1_baseline"] = run_lgbm(V1 + ["zone_id"], "A_V1")
    RES["runs"]["B_V2_full"] = run_lgbm(V1 + V2_TEMPORAL + ["zone_id"], "B_V2")

    ablations = {
        "V1+rain": TEMPORAL_RAIN, "V1+gw": TEMPORAL_GW,
        "V1+crack": TEMPORAL_CRACK, "V1+blast": TEMPORAL_BLAST,
        "V1+rain+gw": TEMPORAL_RAIN + TEMPORAL_GW,
        "V1+rain+crack": TEMPORAL_RAIN + TEMPORAL_CRACK,
        "V1+gw+crack": TEMPORAL_GW + TEMPORAL_CRACK,
        "V1+crack+blast": TEMPORAL_CRACK + TEMPORAL_BLAST,
    }
    for tag, extra in ablations.items():
        RES["runs"][tag] = run_lgbm(V1 + extra + ["zone_id"], tag)

    best_by_target = {}
    for tname in TARGETS:
        ranked = sorted(((tag, blk[tname]["val"]["r2"]) for tag, blk in RES["runs"].items()),
                        key=lambda kv: -kv[1])
        best_by_target[tname] = ranked[0]
        print(f"[best-val] {tname}: {ranked[0][0]} (val R2={ranked[0][1]:.3f})", flush=True)
    RES["best_by_validation"] = best_by_target

    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()