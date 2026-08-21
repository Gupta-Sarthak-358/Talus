"""Experiment F2 (Member 2 Phase 5 extension): do trend features help FORECASTING?

Experiment F showed V2 trends do NOT improve nowcasting (t) — consistent with
the generator's memoryless FoS. The proper test for 'predictive' features is
forecasting: predict instability_score at t+H from observations at t only.
H in {1, 7}. Same frozen protocol and splits; last H days per group dropped.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\features")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from temporal_features import build_v2, V1, V2_TEMPORAL
from experiment_f import get_internal_states, encode_fit, metrics, LGBM_PARAMS
from config import TRAIN_SEEDS, VAL_SEEDS, TEST_SEEDS

SCRATCH = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe")
OUT = SCRATCH / "experiment_f2_forecast.json"


def shift_target(df, horizon):
    """y(t) = instability_score(t+horizon) within each (seed, zone); drops tail."""
    parts = []
    for _, g in df.groupby(["seed", "zone_id"], sort=False):
        g = g.sort_values("timestamp").copy() if "timestamp" in g.columns else g.copy()
        g = g.reset_index(drop=True)
        if len(g) <= horizon:
            continue
        g["y_future"] = g["instability_score"].shift(-horizon)
        parts.append(g.iloc[:-horizon])
    return pd.concat(parts, ignore_index=True)


def main():
    d = get_internal_states()
    v2 = build_v2(d)

    tr = v2[v2.seed.isin(TRAIN_SEEDS)].reset_index(drop=True)
    va = v2[v2.seed.isin(VAL_SEEDS)].reset_index(drop=True)
    te = v2[v2.seed.isin(TEST_SEEDS)].reset_index(drop=True)

    RES = {"runs": {}}
    for H in [1, 7]:
        trh, vah, teh = shift_target(tr, H), shift_target(va, H), shift_target(te, H)
        for tag, feats in [("V1", V1 + ["zone_id"]), ("V2", V1 + V2_TEMPORAL + ["zone_id"])]:
            pre = encode_fit(trh, feats)
            m = LGBMRegressor(**LGBM_PARAMS)
            m.fit(pre.transform(trh[feats]), trh["y_future"].values.astype(float))
            pv = m.predict(pre.transform(vah[feats]))
            pt = m.predict(pre.transform(teh[feats]))
            RES["runs"][f"H={H}::{tag}"] = {
                "val": metrics(vah["y_future"].values.astype(float), pv),
                "test": metrics(teh["y_future"].values.astype(float), pt)}
            print(f"[H={H}] {tag}: val R2={RES['runs'][f'H={H}::{tag}']['val']['r2']:.3f} "
                  f"test R2={RES['runs'][f'H={H}::{tag}']['test']['r2']:.3f}", flush=True)
        # persistence baseline: predict y(t+H) = instability_score(t)
        p_persist = teh["instability_score"].values.astype(float)
        RES["runs"][f"H={H}::persistence"] = {"test": metrics(teh["y_future"].values.astype(float), p_persist)}
        print(f"[H={H}] persistence: test R2={RES['runs'][f'H={H}::persistence']['test']['r2']:.3f}", flush=True)

    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()