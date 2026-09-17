"""E12: South Specialist Confirmation (SIH26001).

Frozen dataset: E1.5b corrected pool (4050 rows). No sampling changes herein.
Models: M0 global RF500/XGB, M1 south RF500/XGB, M2 global+isotonic (M0c) and
  south+isotonic (M1c) for RF500 (symmetric inner-2-fold cross-fit on train half).
Protocol per seed (5 seeds): KMeans-2 spatial split of SOUTH -> train/eval halves;
  M0 trains NORTH+S-train, M1 trains S-train only; eval on S-eval (all + hard-only).
Primary: PR-AUC on South eval; then sens50 (critical-recall proxy), Brier, ECE,
  ROC-AUC. Report mean/median/std/95% CI of specialist-minus-global deltas.
Feature audit: permutation (3x) + SHAP top-10, global vs south RF500.

Outputs: runs/e12.json. Run: mnemo-venv python scripts/e12_south_confirmation.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MAT0 = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDE0 = REPO / "data/sih26001/processed/training_sidecar.csv"
MAT1 = REPO / "data/sih26001/processed/e15_negatives.csv"
SIDE1 = REPO / "data/sih26001/processed/e15_sidecar.csv"
OUT = REPO / "runs" / "e12.json"

SEEDS = [42, 7, 123, 2024, 999]
LAT_SPLIT = 27.15
NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since"]  # wound REMOVED (E8)


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def brier(y, p) -> float:
    return round(float(np.mean((p - y) ** 2)), 4)


def ece(y, p, bins=10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p <= edges[b + 1])
        if m.sum() == 0:
            continue
        e += (m.sum() / len(p)) * abs(y[m].mean() - p[m].mean())
    return round(float(e), 4)


def auc(y, p):
    from sklearn.metrics import roc_auc_score
    return round(float(roc_auc_score(y, p)), 4) if len(np.unique(y)) == 2 else None


def pr_auc(y, p):
    from sklearn.metrics import average_precision_score
    return round(float(average_precision_score(y, p)), 4) if len(np.unique(y)) == 2 else None


def sens50(y, p):
    return round(float((p[y == 1] >= 0.5).mean()), 4) if (y == 1).any() else None


def metrics(y, p) -> dict:
    return {"pr_auc": pr_auc(y, p), "sens50": sens50(y, p), "brier": brier(y, p),
            "ece10": ece(y, p), "auc": auc(y, p),
            "acc50": round(float(((p >= 0.5) == y).mean()), 4),
            "n": int(len(y)), "pos_rate": round(float(y.mean()), 4)}


def build_X(mat: pd.DataFrame) -> pd.DataFrame:
    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "seismic_dist_km", "seismic_n50_rate",
             "seismic_years_since", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    return X.drop(columns=["spi"])


def make_xy(family: str, seed: int):
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]),
    ])
    if family == "rf":
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators=500, random_state=seed, n_jobs=-1)
        return pre, clf
    from xgboost import XGBClassifier
    clf = XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
                        random_state=seed, n_jobs=-1)
    return pre, clf


def fit_predict(Xtr, ytr, Xte, family, seed):
    pre, clf = make_xy(family, seed)
    clf.fit(pre.fit_transform(Xtr), ytr)
    proba = clf.predict_proba(pre.transform(Xte))
    return proba[:, list(clf.classes_).index(1)] if proba.shape[1] > 1 else np.full(len(Xte), float(clf.classes_[0] == 1))


def inner_oof(Xtr, ytr, family, seed):
    """2-fold OOF over train half (for symmetric cross-fit calibration)."""
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=seed)
    oof = np.full(len(ytr), np.nan)
    for a, b in skf.split(Xtr, ytr):
        oof[b] = fit_predict(Xtr.iloc[a], ytr[a], Xtr.iloc[b], family, seed)
    return oof


def main() -> int:
    t0 = time.time()
    from sklearn.cluster import KMeans
    from sklearn.isotonic import IsotonicRegression
    m0 = pd.read_csv(MAT0)
    s0 = pd.read_csv(SIDE0)
    m1 = pd.read_csv(MAT1)
    s1 = pd.read_csv(SIDE1)
    keep = (m1["distance_to_road"] < 1000).to_numpy()
    m1, s1 = m1[keep].reset_index(drop=True), s1[keep].reset_index(drop=True)
    mat = pd.concat([m0, m1], ignore_index=True)
    side = pd.concat([s0, s1], ignore_index=True)
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    district = side["district"].to_numpy()
    lat = side["lat"].to_numpy()
    south = ((side["district"] == "Darjeeling").to_numpy()
             | ((district == "background") & (lat < LAT_SPLIT)))
    north = ~south
    log(f"pool n={len(y)} pos={int(y.sum())} south={int(south.sum())} north={int(north.sum())}")

    res: dict = {"seeds": SEEDS, "per_seed": [], "families": ["rf", "xgb"]}
    s_idx = np.where(south)[0]
    s_coords = coords[s_idx]
    for seed in SEEDS:
        # spatial halving of SOUTH (KMeans-2); assert both classes each half
        km = KMeans(n_clusters=2, random_state=seed, n_init=10).fit_predict(s_coords)
        h0 = s_idx[km == 0]
        h1 = s_idx[km == 1]
        assert len(np.unique(y[h0])) == 2 and len(np.unique(y[h1])) == 2, f"seed {seed}: degenerate half"
        tr_half, te_half = (h0, h1) if len(h0) >= len(h1) else (h1, h0)
        n_idx = np.where(north)[0]
        ev = mat["distance_to_road"].to_numpy()[te_half] < 1000
        ev &= mat["elevation"].to_numpy()[te_half] < 2500
        hard = te_half[ev]
        entry: dict = {"seed": seed, "n_train_half": int(len(tr_half)),
                       "n_eval_half": int(len(te_half)), "n_eval_hard": int(len(hard))}
        for fam in ("rf", "xgb"):
            p_m0 = fit_predict(X.iloc[np.concatenate([n_idx, tr_half])], y[np.concatenate([n_idx, tr_half])],
                               X.iloc[te_half], fam, seed)
            p_m1 = fit_predict(X.iloc[tr_half], y[tr_half], X.iloc[te_half], fam, seed)
            entry[fam] = {"M0_all": metrics(y[te_half], p_m0),
                          "M1_south": metrics(y[te_half], p_m1),
                          "M0_hard": metrics(y[hard], p_m0[ev]),
                          "M1_hard": metrics(y[hard], p_m1[ev])}
            if fam == "rf":
                # M2: symmetric cross-fit isotonic on train half
                o_tr_m0 = inner_oof(X.iloc[np.concatenate([n_idx, tr_half])],
                                    y[np.concatenate([n_idx, tr_half])], fam, seed)
                # inner_oof indexes the concatenated frame; take south-half rows
                iso0 = IsotonicRegression(out_of_bounds="clip")
                iso0.fit(o_tr_m0[len(n_idx):], y[tr_half])
                o_tr_m1 = inner_oof(X.iloc[tr_half], y[tr_half], fam, seed)
                iso1 = IsotonicRegression(out_of_bounds="clip")
                iso1.fit(o_tr_m1, y[tr_half])
                entry[fam]["M0c_cal"] = metrics(y[te_half], iso0.predict(p_m0))
                entry[fam]["M1c_cal"] = metrics(y[te_half], iso1.predict(p_m1))
        res["per_seed"].append(entry)
        log(f"seed {seed}: RF dPR={entry['rf']['M1_south']['pr_auc'] - entry['rf']['M0_all']['pr_auc']:+.4f} "
            f"dAUC={entry['rf']['M1_south']['auc'] - entry['rf']['M0_all']['auc']:+.4f} | "
            f"XGB dPR={entry['xgb']['M1_south']['pr_auc'] - entry['xgb']['M0_all']['pr_auc']:+.4f}")

    # ---- deltas with 95% CI (t, df=4) ----
    import math
    res["deltas"] = {}
    for fam in ("rf", "xgb"):
        for subset in ("all", "hard"):
            for met in ("pr_auc", "auc", "brier", "sens50"):
                ds = np.array([s[fam][f"M1_{'south' if subset == 'all' else subset}"][met]
                               - s[fam][f"M0_{'all' if subset == 'all' else 'hard'}"][met]
                               for s in res["per_seed"]], dtype=float)
                # sign convention: brier lower-is-better -> report global-minus-specialist
                if met == "brier":
                    ds = -ds
                m, sd = float(ds.mean()), float(ds.std(ddof=1))
                ci = 2.776 * sd / math.sqrt(len(ds))
                res["deltas"][f"{fam}_{subset}_{met}"] = {
                    "mean": round(m, 4), "median": round(float(np.median(ds)), 4),
                    "std": round(sd, 4), "ci95": round(ci, 4),
                    "all_positive": bool((ds > 0).all())}
    # M2 calibration comparison (RF)
    res["M2"] = {}
    for tag in ("M0c_cal", "M1c_cal"):
        for met in ("brier", "ece10"):
            vals = np.array([s["rf"][tag][met] for s in res["per_seed"]])
            res["M2"][f"{tag}_{met}"] = {"mean": round(float(vals.mean()), 4),
                                         "std": round(float(vals.std(ddof=1)), 4)}

    # ---- feature audit: permutation (3x) + SHAP, global vs south RF500 ----
    from sklearn.inspection import permutation_importance
    res["audit"] = {}
    for tag, idx in (("global", np.arange(len(y))), ("south", s_idx)):
        pre, clf = make_xy("rf", SEEDS[0])
        Xt = pre.fit_transform(X.iloc[idx])
        if hasattr(Xt, "toarray"):
            Xt = Xt.toarray()
        clf.fit(Xt, y[idx])
        try:
            names = [n.split("__")[-1] for n in pre.get_feature_names_out()]
        except Exception:
            names = NUMERIC
        perm = permutation_importance(clf, Xt, y[idx], n_repeats=3,
                                      random_state=SEEDS[0], scoring="roc_auc", n_jobs=-1)
        order = np.argsort(perm.importances_mean)[::-1][:10]
        res["audit"][tag] = [{"feature": names[i],
                              "drop": round(float(perm.importances_mean[i]), 4)}
                             for i in order]
        log(f"audit {tag}: {res['audit'][tag][:5]}")
    try:
        import shap
        rng = np.random.default_rng(SEEDS[0])
        pos_i = np.where(y == 1)[0]
        neg_i = np.where(y == 0)[0]
        demo = np.concatenate([rng.choice(pos_i, 60, replace=False),
                               rng.choice(neg_i, 40, replace=False)])
        res["audit"]["shap"] = {}
        for tag, idx in (("global", np.arange(len(y))), ("south", s_idx)):
            pre, clf = make_xy("rf", SEEDS[0])
            Xt = pre.fit_transform(X.iloc[idx])
            if hasattr(Xt, "toarray"):
                Xt = Xt.toarray()
            clf.fit(Xt, y[idx])
            names = [n.split("__")[-1] for n in pre.get_feature_names_out()]
            ex = shap.TreeExplainer(clf)
            Xd = Xt[demo] if tag == "global" else pre.transform(X.iloc[demo])
            if hasattr(Xd, "toarray"):
                Xd = Xd.toarray()
            sv = ex.shap_values(Xd)
            if isinstance(sv, list):
                sv = sv[1] if len(sv) > 1 else sv[0]
            sv = np.asarray(sv)
            if sv.ndim == 3:  # (n, f, classes) in some shap builds -> positive class
                sv = sv[..., 1]
            mean_abs = np.abs(np.atleast_2d(sv)).mean(axis=0)
            top = np.argsort(mean_abs)[::-1][:10]
            res["audit"]["shap"][tag] = [{"feature": names[i],
                                          "mean_abs": round(float(mean_abs[i]), 4)} for i in top]
            log(f"SHAP {tag}: {[d['feature'] for d in res['audit']['shap'][tag][:5]]}")
    except Exception as e:  # noqa: BLE001
        res["audit"]["shap"] = {"error": str(e)}
        log(f"SHAP failed (non-fatal): {e}")

    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")
    print("\n===== E12 DELTAS (specialist - global; brier sign-flipped so + is better) =====")
    for k, v in res["deltas"].items():
        print(f"{k:22s} mean={v['mean']:+.4f} median={v['median']:+.4f} ±{v['ci95']:.4f} all_pos={v['all_positive']}")
    print("M2:", res["M2"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
