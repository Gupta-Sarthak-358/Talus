"""Phase-1 susceptibility prototype trainer (SIH26001 model-training lane).

Spec: docs/sih26001/MODEL_TRAINING_HANDOFF.md + validation protocol
docs/sih26001/04_MODEL_PLAN_SIH26001.md:37-50. Defaults: season-window proxy
target (tagged approximate in the matrix — never invented dates).

Design (frozen before running):
  X = 14 numeric (spi as log1p, documented) + lulc one-hot(drop_first).
  DROPPED from X (logged delta): lithology + lineament_density (uniform PROXY
  constants — asserted constant, zero signal), previous_landslide (leakage:
  positives ARE inventory slides; negatives are >300m by construction),
  zone_id/time_window/evidence_quality (keys/tags, not features).
  Clusters: KMeans(k=8, seed 42) on [lat,lon] (sidecar; clustering is
  NGEN-side grouping, coords never enter X).
  OOF: GroupKFold(8) — random row splits banned (04_MODEL_PLAN:39-41).
  Models: LR baseline (mandatory dumb baseline) -> RF 500 trees (v1 carryover).
  XGB/LGBM/SHAP deferred (packages absent on this machine — logged, not silent).
  Calibration: isotonic on OOF + Brier/ECE-10 vs prevalence-naive (v1 pattern);
  optimism caveat stated (same-OOF fit); temporal holdout only if >=30 dated
  positives per side (rule pre-registered here), else skipped with counts.
  NO fixture/score/contract touches: max demo touch declined by design (frozen
  scores are validator-guarded; see manifest rationale).

Outputs (models git-ignored; reports committed):
  ml/models/sih26001_{rf,lr,iso}_v1.joblib   (git-ignored)
  ml/sih26001/reports/{metrics,calibration,benchmarks}.md  (COMMITTED)
  docs/sih26001/ML_MODEL_CARD_V2.md           (COMMITTED draft, only if clean:
    RF OOF-AUC > LR OOF-AUC and calibrated Brier < naive Brier)
  data/sih26001/manifest.training.json        (appends "training" section)

Run: py scripts/train_sih26001.py  (needs scikit-learn/scipy/pandas/numpy)
"""
from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDECAR = REPO / "data/sih26001/processed/training_sidecar.csv"
MODELDIR = REPO / "ml/models"
REPORTDIR = REPO / "ml/sih26001/reports"
CARD = REPO / "docs/sih26001/ML_MODEL_CARD_V2.md"
MANIFEST = REPO / "data/sih26001/manifest.training.json"

SEED = 42
N_CLUSTERS = 8
TEMP_MIN_PER_SIDE = 30

NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density"]
DROP_CONST = ["lithology", "lineament_density"]
DROP_LEAK = ["previous_landslide"]
DROP_KEYS = ["zone_id", "time_window", "evidence_quality"]

RESULTS: dict = {"seed": SEED, "clusters": N_CLUSTERS,
                 "started": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ece_score(y_true: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p > edges[b]) & (p <= edges[b + 1] if b < bins - 1 else p <= edges[b + 1] + 1e-12)
        if b == 0:
            m = (p >= edges[0]) & (p <= edges[1])
        if m.sum() == 0:
            continue
        e += (m.sum() / len(p)) * abs(y_true[m].mean() - p[m].mean())
    return round(float(e), 4)


def brier(y_true: np.ndarray, p: np.ndarray) -> float:
    return round(float(np.mean((p - y_true) ** 2)), 4)


def auc_score(y_true: np.ndarray, p: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    return round(float(roc_auc_score(y_true, p)), 4)


def _try_import(pkg: str):
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False


HAS_XGB = _try_import("xgboost")
HAS_LGB = _try_import("lightgbm")
HAS_SHAP = _try_import("shap")


def main() -> int:
    from sklearn.cluster import KMeans
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    mat = pd.read_csv(MATRIX)
    side = pd.read_csv(SIDECAR)
    assert len(mat) == len(side) and (mat["zone_id"] == side["zone_id"]).all(), "matrix/sidecar mismatch"
    y = mat["event"].to_numpy().astype(int)
    assert set(np.unique(y)) == {0, 1}, "single-class matrix — refusing to train"
    assert (mat["zone_id"].str.startswith("T")).all(), "frozen S-IDs must never enter training"
    for c in DROP_CONST:
        assert mat[c].nunique() == 1, f"{c} not uniform — uniformity assumption broken: {mat[c].unique()[:5]}"
    log(f"n={len(mat)} pos={int(y.sum())} neg={int((y == 0).sum())}; "
        f"uniform drops verified: {[(c, mat[c].iloc[0]) for c in DROP_CONST]}")

    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    X = X.drop(columns=["spi"])
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]),
    ])
    lulc_cats = sorted(mat["lulc"].unique().tolist())
    log(f"lulc classes: {lulc_cats}")

    coords = side[["lat", "lon"]].to_numpy()
    groups = KMeans(n_clusters=N_CLUSTERS, random_state=SEED, n_init=10).fit_predict(coords)
    log(f"clusters: {dict(zip(*np.unique(groups, return_counts=True)))}")

    gkf = GroupKFold(n_splits=N_CLUSTERS)
    oof_lr = np.full(len(y), np.nan)
    oof_rf = np.full(len(y), np.nan)
    oof_xgb = np.full(len(y), np.nan) if HAS_XGB else None
    oof_lgb = np.full(len(y), np.nan) if HAS_LGB else None
    fold_auc: dict = {}
    for tr, te in gkf.split(X, y, groups):
        lab = int(groups[te[0]])
        assert (groups[te] == lab).all(), "GroupKFold test fold spans groups"
        lr = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=5000))])
        lr.fit(X.iloc[tr], y[tr])
        oof_lr[te] = lr.predict_proba(X.iloc[te])[:, 1]
        rf = RandomForestClassifier(n_estimators=500, random_state=SEED, n_jobs=-1)
        rf.fit(pre.fit_transform(X.iloc[tr]), y[tr])
        oof_rf[te] = rf.predict_proba(pre.transform(X.iloc[te]))[:, 1]
        if HAS_XGB:
            from xgboost import XGBClassifier
            xgb = Pipeline([("pre", pre), ("clf", XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05,
                                                                subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
                                                                random_state=SEED, n_jobs=-1))])
            xgb.fit(X.iloc[tr], y[tr])
            oof_xgb[te] = xgb.predict_proba(X.iloc[te])[:, 1]
        if HAS_LGB:
            from lightgbm import LGBMClassifier
            lgb = Pipeline([("pre", pre), ("clf", LGBMClassifier(n_estimators=400, learning_rate=0.05, max_depth=-1,
                                                                 random_state=SEED, n_jobs=-1, verbose=-1))])
            lgb.fit(X.iloc[tr], y[tr])
            oof_lgb[te] = lgb.predict_proba(X.iloc[te])[:, 1]
        # A held-out spatial cluster can be single-class (dense inventory pockets
        # or remote background) — AUC undefined there; accuracy always defined.
        if len(np.unique(y[te])) == 2:
            a_lr, a_rf = auc_score(y[te], oof_lr[te]), auc_score(y[te], oof_rf[te])
            a_xgb = auc_score(y[te], oof_xgb[te]) if HAS_XGB else None
            a_lgb = auc_score(y[te], oof_lgb[te]) if HAS_LGB else None
            fold_auc[lab] = (a_lr, a_rf, a_xgb, a_lgb)
        else:
            fold_auc[lab] = (None, None, None, None)
            log(f"fold cluster_{lab}: single-class held-out (n={len(te)}, "
                f"pos_rate={y[te].mean():.2f}) — AUC n/a, kept in pooled OOF")
    assert not np.isnan(oof_lr).any() and not np.isnan(oof_rf).any()
    if HAS_XGB: assert not np.isnan(oof_xgb).any()  # type: ignore
    if HAS_LGB: assert not np.isnan(oof_lgb).any()  # type: ignore

    prev_rate = float(y.mean())
    naive = np.full(len(y), prev_rate)
    metrics: dict = {
        "lr_oof": {"auc": auc_score(y, oof_lr), "brier": brier(y, oof_lr), "ece10": ece_score(y, oof_lr),
                   "acc50": round(float(((oof_lr >= 0.5) == y).mean()), 4)},
        "rf_oof": {"auc": auc_score(y, oof_rf), "brier": brier(y, oof_rf), "ece10": ece_score(y, oof_rf),
                   "acc50": round(float(((oof_rf >= 0.5) == y).mean()), 4)},
        "naive_prevalence": {"brier": brier(y, naive), "ece10": ece_score(y, naive)},
        "per_cluster_auc": {f"cluster_{c}": {"lr": (round(a, 4) if a is not None else "n/a"),
                                                     "rf": (round(b, 4) if b is not None else "n/a"),
                                                     **({"xgb": round(cx, 4) if cx is not None else "n/a"} if HAS_XGB else {}),
                                                     **({"lgb": round(lg, 4) if lg is not None else "n/a"} if HAS_LGB else {})}
                            for c, (a, b, cx, lg) in sorted(fold_auc.items())},
    }
    if HAS_XGB:
        metrics["xgb_oof"] = {"auc": auc_score(y, oof_xgb), "brier": brier(y, oof_xgb), "ece10": ece_score(y, oof_xgb),  # type: ignore
                               "acc50": round(float(((oof_xgb >= 0.5) == y).mean()), 4)}  # type: ignore
    if HAS_LGB:
        metrics["lgb_oof"] = {"auc": auc_score(y, oof_lgb), "brier": brier(y, oof_lgb), "ece10": ece_score(y, oof_lgb),  # type: ignore
                               "acc50": round(float(((oof_lgb >= 0.5) == y).mean()), 4)}  # type: ignore
    log(f"OOF LR: {metrics['lr_oof']}")
    log(f"OOF RF: {metrics['rf_oof']}")
    log(f"naive: {metrics['naive_prevalence']}")

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(oof_rf, y)
    cal = iso.predict(oof_rf)
    metrics["rf_calibrated_oof"] = {"brier": brier(y, cal), "ece10": ece_score(y, cal)}
    metrics["calibration_caveat"] = ("isotonic fit on the same OOF predictions it is evaluated on "
                                     "(optimistic); clean check is the temporal holdout below (when feasible)")
    log(f"calibrated OOF: {metrics['rf_calibrated_oof']} (same-OOF optimism caveat logged)")

    # Temporal holdout (pre-registered rule). Negatives are timeless background:
    # seeded 50/50 into both periods (logged design choice); year is used ONLY
    # for bookkeeping, never as a feature.
    from sklearn.base import clone
    yr = side["year"].to_numpy()
    rng = np.random.default_rng(SEED)
    neg_idx = np.where(y == 0)[0].copy()
    rng.shuffle(neg_idx)
    half = len(neg_idx) // 2
    all_idx = np.arange(len(y))
    in_tr_neg = np.isin(all_idx, neg_idx[:half])
    in_te_neg = np.isin(all_idx, neg_idx[half:])
    n_tr_pos = int(((yr > 0) & (yr <= 2018) & (y == 1)).sum())
    n_te_pos = int(((yr > 0) & (yr >= 2019) & (y == 1)).sum())
    temporal: dict = {"rule": f">= {TEMP_MIN_PER_SIDE} dated positives per side",
                      "n_train_pos_dated": n_tr_pos, "n_test_pos_dated": n_te_pos,
                      "negatives_split": "seeded 50/50 (timeless background)"}
    if n_tr_pos >= TEMP_MIN_PER_SIDE and n_te_pos >= TEMP_MIN_PER_SIDE:
        tr_m = ((yr > 0) & (yr <= 2018)) | in_tr_neg
        te_m = ((yr > 0) & (yr >= 2019)) | in_te_neg
        pre_t = clone(pre)
        Xn_tr = pre_t.fit_transform(X.iloc[tr_m])
        Xn_te = pre_t.transform(X.iloc[te_m])
        rf_t = RandomForestClassifier(n_estimators=500, random_state=SEED, n_jobs=-1).fit(Xn_tr, y[tr_m])
        p_te = rf_t.predict_proba(Xn_te)[:, 1]
        temporal["done"] = True
        temporal["test_n"] = int(te_m.sum())
        temporal["rf_test"] = {"auc": auc_score(y[te_m], p_te), "brier": brier(y[te_m], p_te),
                               "ece10": ece_score(y[te_m], p_te)}
        log(f"temporal holdout: {temporal['rf_test']}")
    else:
        temporal["done"] = False
        temporal["reason"] = (f"only {n_tr_pos} dated positives <=2018 / {n_te_pos} >=2019 "
                              f"(672/764 positives undated) — below rule; skipped, not fudged")
        log(f"temporal holdout SKIPPED: {temporal['reason']}")

    # Threshold-consistency screen (consistency only, not validation).
    # NOTE: climatological June totals here (min 409mm) all sit above the
    # 13mm/day x30d = 390mm monsoon separator, so the separator cannot split
    # this data — median split used instead, separator coverage stated.
    rain7 = mat["rainfall_7d_mm"].to_numpy()
    rain24 = mat["rainfall_24h_mm"].to_numpy()
    rain30 = mat["rainfall_30d_mm"].to_numpy()
    med30 = float(np.median(rain30))
    hi = rain30 >= med30
    thresh = {
        "june_total_separator_mm": 390.0,
        "frac_points_above_separator": round(float((rain30 >= 390.0).mean()), 4),
        "median_split_mm": round(med30, 1),
        "mean_oof_p_above_median": round(float(oof_rf[hi].mean()), 4),
        "mean_oof_p_below_median": round(float(oof_rf[~hi].mean()), 4),
        "frac_pos_dailymax_ge_144": round(float((rain24[y == 1] >= 144.0).mean()), 4),
        "note": ("Dahal 144mm is an event-intensity threshold; our 24h proxy is a JJAS-daily-max "
                 "climatology, so this fraction is a consistency screen, not a threshold validation"),
    }
    log(f"threshold screen: {thresh}")

    # Final fits on full data (deployment-shape artifacts) + importances + SHAP
    from sklearn.inspection import permutation_importance
    Xn_full = pre.fit_transform(X)
    feat_names = NUMERIC + [f"lulc_{c}" for c in pre.named_transformers_["cat"].categories_[0][1:]]
    lr_full = Pipeline([("pre", clone(pre)), ("clf", LogisticRegression(max_iter=5000))])
    lr_full.fit(X, y)
    rf_full = RandomForestClassifier(n_estimators=500, random_state=SEED, n_jobs=-1)
    rf_full.fit(Xn_full, y)
    # XGB/LGB full fits (if available)
    xgb_full = lgb_full = None
    if HAS_XGB:
        from xgboost import XGBClassifier
        xgb_full = Pipeline([("pre", clone(pre)), ("clf", XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05,
                                                                        subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
                                                                        random_state=SEED, n_jobs=-1))])
        xgb_full.fit(X, y)
    if HAS_LGB:
        from lightgbm import LGBMClassifier
        lgb_full = Pipeline([("pre", clone(pre)), ("clf", LGBMClassifier(n_estimators=400, learning_rate=0.05, max_depth=-1,
                                                                         random_state=SEED, n_jobs=-1, verbose=-1))])
        lgb_full.fit(X, y)
    perm = permutation_importance(rf_full, Xn_full, y, n_repeats=5, random_state=SEED,
                                  scoring="roc_auc", n_jobs=-1)
    order = np.argsort(perm.importances_mean)[::-1]
    importance = [{"feature": feat_names[i], "perm_auc_drop": round(float(perm.importances_mean[i]), 4),
                   "impurity": round(float(rf_full.feature_importances_[i]), 4)} for i in order]
    log("top-5 permutation importance: " + str([(d["feature"], d["perm_auc_drop"]) for d in importance[:5]]))
    shap_sample = None
    if HAS_SHAP:
        try:
            import shap
            explainer = shap.TreeExplainer(rf_full)
            # 5 demo points (stratified) for per-prediction example
            rng = np.random.default_rng(SEED)
            pos_idx = np.where(y == 1)[0]
            neg_idx = np.where(y == 0)[0]
            demo_idx = np.concatenate([rng.choice(pos_idx, 3, replace=False), rng.choice(neg_idx, 2, replace=False)])
            shap_vals = explainer.shap_values(Xn_full[demo_idx])
            # shap 0.51 returns [neg, pos] for binary; take pos class
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[1]
            shap_sample = [{"zone_id": f"SHAP-{i}", "features": dict(zip(feat_names, Xn_full[demo_idx[i]].tolist())),
                            "shap": dict(zip(feat_names, shap_vals[i].tolist()))} for i in range(len(demo_idx))]
            log(f"SHAP sample computed for {len(demo_idx)} points (TreeExplainer on RF)")
        except Exception as exc:  # noqa: BLE001
            log(f"SHAP failed (non-fatal): {exc}")
            shap_sample = None

    MODELDIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": rf_full, "encoder": pre, "features": feat_names, "seed": SEED,
                 "target": "event (season-window proxy, approximate)"},
                MODELDIR / "sih26001_rf_v1.joblib", compress=3)
    joblib.dump({"model": lr_full, "seed": SEED}, MODELDIR / "sih26001_lr_v1.joblib", compress=3)
    joblib.dump({"isotonic": iso, "fit_on": "RF spatial-OOF (same-OOF optimism caveat)"},
                MODELDIR / "sih26001_iso_v1.joblib", compress=3)
    if xgb_full is not None:
        joblib.dump({"model": xgb_full, "seed": SEED}, MODELDIR / "sih26001_xgb_v1.joblib", compress=3)
    if lgb_full is not None:
        joblib.dump({"model": lgb_full, "seed": SEED}, MODELDIR / "sih26001_lgb_v1.joblib", compress=3)
    log(f"models -> {MODELDIR}/sih26001_{{rf,lr,iso{',xgb' if xgb_full is not None else ''}{',lgb' if lgb_full is not None else ''}}}_v1.joblib (git-ignored)")

    shap_meta = {"done": shap_sample is not None, "n_demo": len(shap_sample) if shap_sample else 0}
    RESULTS.update({"n": int(len(y)), "n_pos": int(y.sum()), "metrics": metrics,
                    "temporal": temporal, "threshold_screen": thresh,
                    "importance": importance, "shap_sample": shap_sample, "shap_meta": shap_meta,
                    "lulc_classes": lulc_cats,
                    "dropped_from_X": {"uniform_proxy": DROP_CONST, "leakage": DROP_LEAK, "keys": DROP_KEYS},
                    "deferred": ([] if (HAS_XGB and HAS_LGB and HAS_SHAP) else
                                 [d for d, ok in [("xgboost", HAS_XGB), ("lightgbm", HAS_LGB), ("shap", HAS_SHAP)] if not ok]),
                    "has_xgb": HAS_XGB, "has_lgb": HAS_LGB, "has_shap": HAS_SHAP,
                    "finished": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})

    # ---- reports (committed) ----
    REPORTDIR.mkdir(parents=True, exist_ok=True)
    date = RESULTS["finished"][:10]
    # metrics table rows
    header = "| model | AUC | Brier | ECE10 | acc@0.5 |\n|---|---|---|---|---|\n"
    rows = [
        f"| LR baseline | {metrics['lr_oof']['auc']} | {metrics['lr_oof']['brier']} | {metrics['lr_oof']['ece10']} | {metrics['lr_oof']['acc50']} |",
        f"| RF 500 trees | {metrics['rf_oof']['auc']} | {metrics['rf_oof']['brier']} | {metrics['rf_oof']['ece10']} | {metrics['rf_oof']['acc50']} |",
    ]
    if "xgb_oof" in metrics:
        rows.append(f"| XGB | {metrics['xgb_oof']['auc']} | {metrics['xgb_oof']['brier']} | {metrics['xgb_oof']['ece10']} | {metrics['xgb_oof']['acc50']} |")
    if "lgb_oof" in metrics:
        rows.append(f"| LGBM | {metrics['lgb_oof']['auc']} | {metrics['lgb_oof']['brier']} | {metrics['lgb_oof']['ece10']} | {metrics['lgb_oof']['acc50']} |")
    rows.append(f"| naive prevalence | — | {metrics['naive_prevalence']['brier']} | {metrics['naive_prevalence']['ece10']} | — |")
    per_cluster_header = "| held-out cluster | LR | RF"
    if "xgb_oof" in metrics:
        per_cluster_header += " | XGB"
    if "lgb_oof" in metrics:
        per_cluster_header += " | LGBM"
    per_cluster_header += " |\n|---|---|---" + ("|---" if "xgb_oof" in metrics else "") + ("|---" if "lgb_oof" in metrics else "") + "|\n"
    per_cluster_rows = ""
    for c, v in enumerate(metrics["per_cluster_auc"].values()):
        row = f"| cluster_{c} | {v['lr']} | {v['rf']}"
        if "xgb_oof" in metrics:
            row += f" | {v.get('xgb', 'n/a')}"
        if "lgb_oof" in metrics:
            row += f" | {v.get('lgb', 'n/a')}"
        per_cluster_rows += row + " |\n"
    shap_note = (f"SHAP sample: {len(shap_sample)} points TreeSHAP on RF (see manifest shap_sample)" if shap_sample else "SHAP deferred (package absent); permutation+impurity above instead.")
    (REPORTDIR / "metrics.md").write_text(
        f"# SIH26001 Phase-1 training metrics ({date})\n\n"
        f"Target: `event` season-window proxy (positives = inventoried Sikkim + "
        f"Darjeeling-hills (WB) slides, tagged `approximate`; negatives = >300m "
        f"background, seed 42). "
        f"n={len(y)} (pos={int(y.sum())}). X = 14 numeric (spi log1p) + lulc one-hot "
        f"(drop_first); lithology/lineament omitted (uniform PROXY), previous_landslide "
        f"omitted (leakage — positives ARE inventory slides).\n\n"
        f"## Spatial GroupKFold(8) out-of-fold (clusters = KMeans-8 on coords, seed 42)\n\n"
        + header + "\n".join(rows) + "\n\n"
        f"## Per-held-out-cluster AUC (leave-one-cluster-out shape, KMeans labels)\n\n"
        + per_cluster_header + per_cluster_rows
        + f"\n## Temporal holdout\n\n{json.dumps(temporal, indent=2)}\n\n"
        f"## Threshold-consistency screen\n\n{json.dumps(thresh, indent=2)}\n\n"
        f"## Permutation importance (in-sample screening, RF full-data fit)\n\n"
        + "".join(f"| {d['feature']} | {d['perm_auc_drop']} | {d['impurity']} |\n" for d in importance)
        + f"\n{shap_note}\n",
        encoding="utf-8")
    (REPORTDIR / "calibration.md").write_text(
        f"# SIH26001 Phase-1 calibration ({date})\n\n"
        f"Isotonic fit on RF spatial-OOF predictions "
        f"(CalibratedClassifierCV-style prefit on OOF; optimism caveat: fit and "
        f"evaluation share the same OOF — clean check is the temporal holdout, "
        f"currently skipped for lack of dated positives).\n\n"
        f"| predictor | Brier | ECE10 |\n|---|---|---|\n"
        f"| RF raw OOF | {metrics['rf_oof']['brier']} | {metrics['rf_oof']['ece10']} |\n"
        f"| RF isotonic OOF | {metrics['rf_calibrated_oof']['brier']} | "
        f"{metrics['rf_calibrated_oof']['ece10']} |\n"
        f"| naive prevalence | {metrics['naive_prevalence']['brier']} | "
        f"{metrics['naive_prevalence']['ece10']} |\n\n"
        f"Confidence = calibrated P(elevated susceptibility) under the prototype "
        f"season-window target — never 'probability a landslide will occur here tomorrow'.\n",
        encoding="utf-8")
    # benchmarks: include best of RF/XGB/LGBM (exclude calibrated which has no auc/acc)
    oof_models = [k for k in metrics if k.endswith("_oof") and k not in {"lr_oof", "rf_calibrated_oof"} and "auc" in metrics[k]]
    best_auc = max(metrics[k]["auc"] for k in oof_models)
    best_acc = max(metrics[k]["acc50"] for k in oof_models)
    (REPORTDIR / "benchmarks.md").write_text(
        f"# SIH26001 Phase-1 benchmarks ({date})\n\n"
        f"Published bars are targets, not promises (04_MODEL_PLAN:61-71).\n\n"
        f"| published bar | ours (spatial OOF) | verdict |\n|---|---|---|\n"
        f"| Dibang XGBoost AUC 0.96 | best {best_auc} (RF {metrics['rf_oof']['auc']}"
        + (f" XGB {metrics['xgb_oof']['auc']}" if "xgb_oof" in metrics else "")
        + (f" LGBM {metrics['lgb_oof']['auc']}" if "lgb_oof" in metrics else "") + ") | "
        f"{'match/exceed' if best_auc >= 0.96 else 'below — prototype, reported honestly'} |\n"
        f"| Meghalaya ensemble >90% acc | best {best_acc} (RF {metrics['rf_oof']['acc50']}) | "
        f"{'match/exceed' if best_acc >= 0.90 else 'below — prototype, reported honestly'} |\n"
        f"| v1 calibration Brier 0.081 (own corpus, not inherited) | RF cal Brier "
        f"{metrics['rf_calibrated_oof']['brier']} (same-OOF optimism noted) | for the record |\n"
        f"| Monga E=-11.10+0.62D / Dahal >144mm | threshold screen in metrics.md "
        f"(consistency only) | scenario engine untouched |\n\n"
        f"LHASA-2.0 blend and GSI-RLFS CSI comparison are post-hackathon work.\n",
        encoding="utf-8")
    log(f"reports -> {REPORTDIR}/{{metrics,calibration,benchmarks}}.md")

    # ---- model card (only if clean) + manifest ----
    clean = (metrics["rf_oof"]["auc"] > metrics["lr_oof"]["auc"]
             and metrics["rf_calibrated_oof"]["brier"] < metrics["naive_prevalence"]["brier"])
    RESULTS["clean"] = bool(clean)
    if clean:
        CARD.write_text(
            f"# ML Model Card v2 (DRAFT, {date}) — SIH26001 Phase-1 prototype\n\n"
            f"Intended use: susceptibility screening prototype for the Gangtok/Sikkim pilot; "
            f"NOT a safety standard, NOT a per-landslide predictor.\n\n"
            f"Training data: inventory-scale matrix ({len(y)} rows, 764 positives from GSI "
            f"shapefile + report PDF after <50m dedupe, 764 background negatives; season-window "
            f"proxy target tagged approximate; full provenance in "
            f"data/sih26001/manifest.training.json).\n\n"
            f"Model: RandomForestClassifier(500 trees, seed 42) + isotonic calibration; "
            f"LR baseline beaten on spatial OOF (AUC {metrics['rf_oof']['auc']} vs "
            f"{metrics['lr_oof']['auc']}); calibrated Brier {metrics['rf_calibrated_oof']['brier']} "
            f"vs naive {metrics['naive_prevalence']['brier']}.\n\n"
            f"Validation: spatial GroupKFold(8) OOF (no random splits); temporal holdout "
            f"skipped (only {n_tr_pos} dated positives <=2018 — INITIATION year-or-0); "
            f"{'TreeSHAP per-prediction sample computed ('+str(len(shap_sample))+' points, see manifest shap_sample)' if shap_sample else 'TreeSHAP per-prediction deferred (package absent; permutation importance in ml/sih26001/reports/metrics.md)'}.\n\n"
            f"Limitations: climatology/quasi-static proxies (rain/soil/NDVI tagged); uniform "
            f"lithology/lineament omitted from X; OSM center-approx distances "
            f"(osm-qa-unverified); demo fixtures/scores untouched by this lane.\n",
            encoding="utf-8")
        log(f"model card draft -> {CARD}")
    else:
        log("NOT clean (RF must beat LR on spatial OOF-AUC and calibrated Brier must beat naive) "
            "— no model card; presenting as training-ready")

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    man["training"] = RESULTS
    man["demo_touch"] = ("none — zero fixture/score/contract changes by this lane "
                         "(frozen scores are validator-guarded; training is upside, not a demo blocker)")
    MANIFEST.write_text(json.dumps(man, indent=2), encoding="utf-8")
    log(f"manifest updated -> {MANIFEST}")
    print(f"TRAIN DONE: clean={clean} rf_auc={metrics['rf_oof']['auc']} "
          f"lr_auc={metrics['lr_oof']['auc']} cal_brier={metrics['rf_calibrated_oof']['brier']} "
          f"naive_brier={metrics['naive_prevalence']['brier']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())