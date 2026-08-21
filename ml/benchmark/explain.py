"""Section 6c: explainability on the validation-selected Random Forest.

Model selection rule (protocol 6b / project decision): model is chosen by
seed-aware VALIDATION performance, never by test. RF is the validation winner
on all three targets, so RF is the primary model here. XGBoost/LightGBM/
HistGB stay as comparative baselines; their test scores are already recorded
in the tuned_*.json reports and are NOT used for any further selection.

Runs three explanation families on RF:
  1. permutation importance (test seeds, RMSE drop)
  2. Tree SHAP (global mean|SHAP|, on a test-subset of rows)
  3. monotonicity / counterfactual checks (sweep one environmental variable
     holding others fixed; verify predicted instability moves in the
     physics-expected direction)
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from config import FEATURES, CATEGORICAL_FEATURES, RANDOM_STATE
from prepare import (load_corpus, partition, zone_baselines, add_delta_targets,
                     target_vector, X_matrix, categorical_columns)

OUT = Path(__file__).parent / "results"
N_SHAP_ROWS = 2000


def build_rf_pipeline(include_zone=True):
    cats = categorical_columns(include_zone)
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    pre = ColumnTransformer([
        ("num_norm", StandardScaler(), nums),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cats),
    ], remainder="drop")
    model = RandomForestRegressor(n_estimators=500, max_depth=12, min_samples_leaf=1,
                                  random_state=RANDOM_STATE, n_jobs=-1)
    return Pipeline([("pre", pre), ("est", model)]), pre


def encoded_names(pre, include_zone):
    """Full encoded feature names after the ColumnTransformer is fitted.

    ColumnTransformer().get_feature_names_out() returns e.g.
    'num_norm__rainfall_24h_mm', 'cat__rock_type_sandstone',
    'cat__zone_id_ZONE_A'. We keep the post-underscore segment.
    """
    raw = pre.get_feature_names_out()
    return [n.split("__")[-1] for n in raw]


def fit_pre(pre, Xdf):
    pre.fit(Xdf)
    return pre


def monotonicity_sweep(pipe, base_row, feats_orig, include_zone):
    """Sweep one numeric environmental feature while holding the row fixed.

    Returns dict feature -> (preds ascending over a sweep grid, direction_ok).
    Physics expectation (higher value -> higher instability):
      rainfall_24h_mm, rainfall_7d_mm, groundwater_proxy, crack_density,
      blast_vibration_ppv_mms, slope_angle_deg, slope_height_m
    """
    expect_up = ["rainfall_24h_mm", "rainfall_7d_mm", "groundwater_proxy",
                 "crack_density", "blast_vibration_ppv_mms", "slope_angle_deg",
                 "slope_height_m"]
    grid = np.linspace(0.01, 1.0, 12)
    out = {}
    for feat in expect_up:
        lo = feats_orig[feat].quantile(0.02)
        hi = feats_orig[feat].quantile(0.98)
        if hi <= lo:
            continue
        preds = []
        for frac in grid:
            row = base_row.copy()
            row[feat] = lo + frac * (hi - lo)
            Xr = pd.DataFrame([row])
            if include_zone:
                Xr["zone_id"] = base_row["zone_id"]
            else:
                Xr = Xr[FEATURES]
            preds.append(float(pipe.predict(Xr)[0]))
        preds = np.array(preds)
        # direction check: is the last-20% prediction above the first-20%?
        up = float(preds[-3:].mean() - preds[:3].mean())
        out[feat] = {"pred_min": float(preds.min()), "pred_max": float(preds.max()),
                     "delta_over_sweep": round(up, 3),
                     "direction_ok": bool(up > 0)}
    return out


def run():
    include_zone = True
    d = load_corpus()
    parts = partition(d)
    baselines = zone_baselines(parts["train"])
    for name, df in parts.items():
        parts[name] = add_delta_targets(df, baselines)
    all_df = pd.concat([parts["train"], parts["validation"]], ignore_index=True)
    Xall = X_matrix(all_df, include_zone)
    Xte = X_matrix(parts["test"], include_zone)
    seed_te = parts["test"]["seed"].values
    feats_orig = all_df[FEATURES]

    report = {"primary_model": "random_forest (validation-selected)",
              "note": ("test results from tuned_*.json are recorded evidence; "
                       "NOT used for selection"),
              "targets": {}}

    for tname in ["abs_instability", "delta_instability", "delta_fos"]:
        yall = target_vector(all_df, tname)
        yte = target_vector(parts["test"], tname)

        pipe, pre = build_rf_pipeline(include_zone)
        pipe.fit(Xall, yall)
        fit_pre(pre, Xall)

        # 1) permutation importance on test seeds (RMSE drop)
        t0 = time.time()
        pi = permutation_importance(pipe, Xte, yte, n_repeats=10,
                                    random_state=RANDOM_STATE, n_jobs=-1)
        raw_names = list(Xte.columns)
        perm = {raw_names[i]: round(float(pi.importances_mean[i]), 4)
                for i in range(len(raw_names))}
        print(f"[explain] {tname}: permutation done in {time.time()-t0:.0f}s", flush=True)

        # 2) SHAP (TreeExplainer) on a test subset
        rng = np.random.default_rng(0)
        idx = rng.choice(len(Xte), size=min(N_SHAP_ROWS, len(Xte)), replace=False)
        Xshap = Xte.iloc[idx]
        Xenc = pipe.named_steps["pre"].transform(Xshap)
        names = encoded_names(pre, include_zone)
        explainer = shap.TreeExplainer(pipe.named_steps["est"])
        sv = explainer.shap_values(Xenc)
        mean_abs = np.abs(sv).mean(axis=0)
        shap_rank = {names[i]: round(float(mean_abs[i]), 4) for i in range(len(names))}
        print(f"[explain] {tname}: SHAP done ({len(idx)} rows)", flush=True)

        # 3) monotonicity: pick a median test row per zone, sweep dynamics
        mono = {}
        for z in parts["test"]["zone_id"].unique():
            zrow = parts["test"][parts["test"]["zone_id"] == z].sample(1, random_state=0).iloc[0]
            mono[z] = monotonicity_sweep(pipe, zrow, feats_orig, include_zone)

        report["targets"][tname] = {
            "permutation_importance": perm,
            "shap_mean_abs": shap_rank,
            "monotonicity_by_zone": mono,
        }

    out_path = OUT / "explainability.json"
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    run()