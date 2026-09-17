"""Feature/group ablation for SIH26001 Phase-1 model (finals deep-dive).

Same protocol as scripts/train_sih26001.py: KMeans-8 spatial groups (seed 42),
GroupKFold OOF, RF500 + LR, AUC/Brier. Compares:

  Groups: full | no_rain | no_dem6 | no_soil | no_ndvi | no_osm | no_drain
          | no_lulc | static_only | trigger_only
  Singles (LOO): elevation | distance_to_road | ndvi | rainfall_7d_mm | twi
  Leakage demo: +previous_landslide (proves the exclusion was right)
  Null test: +lithology +lineament_density uniforms (proves omission cost ~0)
  Candidates: aspect_sincos (circular encoding) | +twi_x_rain7 | +slope_x_rain7

Outputs (committed): ml/sih26001/reports/ablation.md + ablation.json
Run (mnemo venv): C:\\Users\\satvi\\Desktop\\mnemo\\.venv\\Scripts\\python.exe scripts/ablate_features.py
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
N_CLUSTERS = 8

BASE_NUM = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
            "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
            "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
            "drain_density", "seismic_dist_km", "seismic_n50_rate",
            "seismic_years_since"]
RAIN = ["rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm"]
DEM6 = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log"]
OSM = ["distance_to_road", "distance_to_river"]
SEISMIC = ["seismic_dist_km", "seismic_n50_rate", "seismic_years_since"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build_X(mat: pd.DataFrame, drop=(), add_prev=False, add_const=False,
            aspect_sincos=False, interactions=()):
    cols = [c for c in BASE_NUM if c not in drop]
    raw = [c for c in cols if c != "spi_log"]
    if "spi_log" in cols:
        raw = raw + ["spi"]
    X = mat[raw + ["lulc"]].copy()
    if "spi_log" in cols:
        X["spi_log"] = np.log1p(X.pop("spi").clip(lower=0))
    if aspect_sincos and "aspect" not in drop:
        rad = np.radians(X.pop("aspect").to_numpy())
        X["aspect_sin"], X["aspect_cos"] = np.sin(rad), np.cos(rad)
    for a, b, name in interactions:
        if a in X.columns and b in X.columns:
            s1, s2 = X[a].std(), X[b].std()
            X[name] = (X[a] / (s1 or 1.0)) * (X[b] / (s2 or 1.0))
    const_cols = []
    if add_prev:
        X["previous_landslide"] = mat["previous_landslide"].to_numpy()
    if add_const:
        X["_lith"] = 1.0
        X["_lin"] = 1.0
        const_cols = ["_lith", "_lin"]
    num = [c for c in X.columns if c != "lulc" and c not in const_cols]
    return X, num, const_cols


CONFIGS = [
    ("full", {}),
    ("no_rain", {"drop": tuple(RAIN)}),
    ("no_dem6", {"drop": tuple(DEM6)}),
    ("no_soil", {"drop": ("soil_moisture",)}),
    ("no_ndvi", {"drop": ("ndvi",)}),
    ("no_osm", {"drop": tuple(OSM)}),
    ("no_seismic", {"drop": tuple(SEISMIC)}),
    ("no_drain", {"drop": ("drain_density",)}),
    ("no_lulc", {"drop_lulc": True}),
    ("static_only", {"drop": tuple(RAIN + ["soil_moisture", "ndvi"])}),
    ("trigger_only", {"keep": tuple(RAIN + ["soil_moisture", "ndvi"])}),
    ("loo_elevation", {"drop": ("elevation",)}),
    ("loo_distance_to_road", {"drop": ("distance_to_road",)}),
    ("loo_ndvi", {"drop": ("ndvi",)}),
    ("loo_rainfall_7d", {"drop": ("rainfall_7d_mm",)}),
    ("loo_twi", {"drop": ("twi",)}),
    ("LEAK_prev_slide", {"add_prev": True}),
    ("NULL_lith_lineament", {"add_const": True}),
    ("CAND_aspect_sincos", {"aspect_sincos": True}),
    ("CAND_+twi_x_rain7", {"interactions": (("twi", "rainfall_7d_mm", "twi_x_rain7"),)}),
    ("CAND_+slope_x_rain7", {"interactions": (("slope_angle", "rainfall_7d_mm", "slope_x_rain7"),)}),
]


def run_config(name, cfg, mat, y, groups, gkf):
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, brier_score_loss
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    drop = set(cfg.get("drop", ()))
    keep = cfg.get("keep")
    use_lulc = not cfg.get("drop_lulc", False)
    if keep is not None:
        drop = set(BASE_NUM) - set(keep)
    X, num, const_cols = build_X(
        mat, drop=drop, add_prev=cfg.get("add_prev", False),
        add_const=cfg.get("add_const", False),
        aspect_sincos=cfg.get("aspect_sincos", False),
        interactions=cfg.get("interactions", ()))
    transformers = [("num", StandardScaler(), num)]
    if use_lulc:
        transformers.append(("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]))
    else:
        X = X.drop(columns=["lulc"])
    pre = ColumnTransformer(transformers)
    oof_rf = np.full(len(y), np.nan)
    oof_lr = np.full(len(y), np.nan)
    for tr, te in gkf.split(X, y, groups):
        rf = RandomForestClassifier(n_estimators=500, random_state=SEED, n_jobs=-1)
        Xt_tr = pre.fit_transform(X.iloc[tr])
        # constants bypass the scaler (zero-variance guard), reattached post-transform
        if const_cols:
            import scipy.sparse as _sp
            Ctr = X.iloc[tr][const_cols].to_numpy()
            Cte = X.iloc[te][const_cols].to_numpy()
            Xt_tr = _sp.hstack([Xt_tr, Ctr]).tocsr() if _sp.issparse(Xt_tr) else np.hstack([Xt_tr, Ctr])
            Xt_te = pre.transform(X.iloc[te])
            Xt_te = _sp.hstack([Xt_te, Cte]).tocsr() if _sp.issparse(Xt_te) else np.hstack([Xt_te, Cte])
        else:
            Xt_te = pre.transform(X.iloc[te])
        rf.fit(Xt_tr, y[tr])
        oof_rf[te] = rf.predict_proba(Xt_te)[:, 1]
        lr = Pipeline([("pre", ColumnTransformer(transformers)),
                       ("clf", LogisticRegression(max_iter=5000))])
        lr.fit(X.iloc[tr], y[tr])
        oof_lr[te] = lr.predict_proba(X.iloc[te])[:, 1]
    out = {
        "rf_auc": round(float(roc_auc_score(y, oof_rf)), 4),
        "rf_brier": round(float(brier_score_loss(y, oof_rf)), 4),
        "lr_auc": round(float(roc_auc_score(y, oof_lr)), 4),
        "lr_brier": round(float(brier_score_loss(y, oof_lr)), 4),
        "n_features": int(len(num) + (len(pre.named_transformers_["cat"].categories_[0]) - 1) if use_lulc else len(num)),
    }
    return out


def main() -> int:
    from sklearn.cluster import KMeans
    from sklearn.model_selection import GroupKFold

    mat = pd.read_csv(MATRIX)
    side = pd.read_csv(SIDECAR)
    y = mat["event"].to_numpy().astype(int)
    groups = KMeans(n_clusters=N_CLUSTERS, random_state=SEED, n_init=10).fit_predict(
        side[["lat", "lon"]].to_numpy())
    gkf = GroupKFold(n_splits=N_CLUSTERS)
    log(f"n={len(mat)} pos={int(y.sum())}; configs={len(CONFIGS)}")
    results = {}
    for name, cfg in CONFIGS:
        r = run_config(name, cfg, mat, y, groups, gkf)
        results[name] = r
        log(f"{name:22s} RF auc={r['rf_auc']} brier={r['rf_brier']} | LR auc={r['lr_auc']} brier={r['lr_brier']}")
    base = results["full"]
    lines = [
        "# SIH26001 ablation study (same protocol as train: KMeans-8 groups, GroupKFold OOF, RF500+LR, seed 42)",
        "",
        f"Baseline `full`: RF AUC {base['rf_auc']} / Brier {base['rf_brier']}; "
        f"LR AUC {base['lr_auc']} / Brier {base['lr_brier']}. Deltas below are RF-AUC vs full.",
        "",
        "| config | RF AUC (Δ) | RF Brier | LR AUC (Δ) | LR Brier | n_feat |",
        "|---|---|---|---|---|---|",
    ]
    for name, _ in CONFIGS:
        r = results[name]
        lines.append(f"| {name} | {r['rf_auc']} ({r['rf_auc']-base['rf_auc']:+.4f}) | {r['rf_brier']} | "
                     f"{r['lr_auc']} ({r['lr_auc']-base['lr_auc']:+.4f}) | {r['lr_brier']} | {r['n_features']} |")
    lines += [
        "",
        "## Reading",
        "- LEAK_prev_slide quantifies why previous_landslide stays excluded (label construction leaks).",
        "- NULL_lith_lineament quantifies the omission cost of the two uniform PROXY constants.",
        "- CAND_* test skipped/improved encodings; adopted only if they beat full honestly.",
        "- static_only vs trigger_only splits the trigger-vs-terrain debate with numbers.",
    ]
    REPORTDIR.mkdir(parents=True, exist_ok=True)
    (REPORTDIR / "ablation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTDIR / "ablation.json").write_text(json.dumps(
        {"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"), "seed": SEED,
         "baseline": base, "configs": results}, indent=2), encoding="utf-8")
    log("reports -> ml/sih26001/reports/ablation.{md,json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
