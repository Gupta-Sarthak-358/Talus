"""E13: strict regional calibration (SIH26001).

Per branch (Global backbone / South specialist), per seed (5):
  train (60% clusters) -> fit model (+ isotonic on CALIB partition predictions)
  calib (20% clusters) -> out-of-sample calibration predictions, fit isotonic
  test  (20% clusters) -> UNTOUCHED until final eval
Report: ROC-AUC, PR-AUC, Brier, ECE, sens50, reliability bins; raw vs calibrated.
Regional separation: G-north-cal, G-south-cal, S-south-cal (never one global curve).
Prod weights/models UNTOUCHED (experiment fits only).

Outputs: runs/e13.json. Run: mnemo-venv python scripts/e13_calibration.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "runs" / "e13.json"

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


def reliability(y, p, bins=10) -> list:
    edges = np.linspace(0.0, 1.0, bins + 1)
    out = []
    for b in range(bins):
        m = (p >= edges[b]) & (p <= edges[b + 1]) if b else (p >= edges[0]) & (p <= edges[1])
        if m.sum() == 0:
            continue
        out.append({"bin": [round(float(edges[b]), 2), round(float(edges[b + 1]), 2)],
                    "mean_pred": round(float(p[m].mean()), 3),
                    "frac_pos": round(float(y[m].mean()), 3), "n": int(m.sum())})
    return out


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
    else:
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


def split_60_20_20(coords_r, y_r, seed):
    """Cluster region coords (k=10) -> train/calib/test cluster sets with both classes each."""
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=10, random_state=seed, n_init=10).fit_predict(coords_r)
    # greedy: sort clusters by size desc, deal into test(2)/calib(2)/train(6) balanced by positives
    order = sorted(range(10), key=lambda c: (km == c).sum(), reverse=True)
    buckets: dict[str, list] = {"test": [], "calib": [], "train": []}
    poscount = {k: 0 for k in buckets}
    for c in order:
        # put cluster where positives are currently scarcest (test/calib need >=30 pos)
        k = min(("test", "calib", "train"), key=lambda k: (poscount[k], len(buckets[k])))
        buckets[k].append(c)
        poscount[k] += int(y_r[km == c].sum())
    # enforce quotas: test 2, calib 2, train 6 clusters
    if sorted(len(v) for v in buckets.values()) != [2, 2, 6]:
        buckets = {"test": order[0:2], "calib": order[2:4], "train": order[4:10]}
    out = {}
    for k, cl in buckets.items():
        idx = np.where(np.isin(km, cl))[0]
        assert len(np.unique(y_r[idx])) == 2 and len(idx) >= 50, f"{k} degenerate"
        out[k] = idx
    return out


def main() -> int:
    t0 = time.time()
    from sklearn.isotonic import IsotonicRegression
    m0 = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    s0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    extras_m, extras_s = [], []
    for tag in ("e15", "e15c"):
        mm = pd.read_csv(REPO / "data/sih26001/processed" / f"{tag}_negatives.csv")
        ss = pd.read_csv(REPO / "data/sih26001/processed" / f"{tag}_sidecar.csv")
        keep = (mm["distance_to_road"] < 1000).to_numpy()
        extras_m.append(mm[keep])
        extras_s.append(ss[keep])
    mat = pd.concat([m0] + extras_m, ignore_index=True)
    side = pd.concat([s0] + extras_s, ignore_index=True)
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    lat = side["lat"].to_numpy()
    district = side["district"].to_numpy()
    south = ((side["district"] == "Darjeeling").to_numpy()
             | ((district == "background") & (lat < LAT_SPLIT)))
    north = ~south
    log(f"pool n={len(y)} pos={int(y.sum())} south={int(south.sum())} north={int(north.sum())}")

    res: dict = {"seeds": SEEDS, "per_seed": []}
    for seed in SEEDS:
        sp = split_60_20_20(coords[south], y[south], seed)
        no = split_60_20_20(coords[north], y[north], seed + 1)
        S = {k: np.where(south)[0][v] for k, v in sp.items()}
        N = {k: np.where(north)[0][v] for k, v in no.items()}
        entry: dict = {"seed": seed,
                       "sizes": {k: {"S": int(len(v)), "N": int(len(N[k]))} for k, v in S.items()}}
        for fam in ("rf", "xgb"):
            f = {}
            # M0 global backbone: train north-train + south-train
            tr = np.concatenate([N["train"], S["train"]])
            p_nte = fit_predict(X.iloc[tr], y[tr], X.iloc[N["test"]], fam, seed)
            p_ste = fit_predict(X.iloc[tr], y[tr], X.iloc[S["test"]], fam, seed)
            p_nca = fit_predict(X.iloc[tr], y[tr], X.iloc[N["calib"]], fam, seed)
            p_sca = fit_predict(X.iloc[tr], y[tr], X.iloc[S["calib"]], fam, seed)
            # M1 south specialist: train south-train only
            q_ste = fit_predict(X.iloc[S["train"]], y[S["train"]], X.iloc[S["test"]], fam, seed)
            q_sca = fit_predict(X.iloc[S["train"]], y[S["train"]], X.iloc[S["calib"]], fam, seed)
            # M2: regional isotonic on out-of-sample calib predictions
            iso_n = IsotonicRegression(out_of_bounds="clip").fit(p_nca, y[N["calib"]])
            iso_s0 = IsotonicRegression(out_of_bounds="clip").fit(p_sca, y[S["calib"]])
            iso_s1 = IsotonicRegression(out_of_bounds="clip").fit(q_sca, y[S["calib"]])
            f["G_north_raw"] = metrics(y[N["test"]], p_nte)
            f["G_north_cal"] = metrics(y[N["test"]], iso_n.predict(p_nte))
            f["G_south_raw"] = metrics(y[S["test"]], p_ste)
            f["G_south_cal"] = metrics(y[S["test"]], iso_s0.predict(p_ste))
            f["S_south_raw"] = metrics(y[S["test"]], q_ste)
            f["S_south_cal"] = metrics(y[S["test"]], iso_s1.predict(q_ste))
            f["rel_G_south_cal"] = reliability(y[S["test"]], iso_s0.predict(p_ste))
            f["rel_S_south_cal"] = reliability(y[S["test"]], iso_s1.predict(q_ste))
            entry[fam] = f
        res["per_seed"].append(entry)
        r = entry["rf"]
        log(f"seed {seed}: S_raw G {r['G_south_raw']['brier']}/{r['G_south_raw']['ece10']} vs "
            f"S {r['S_south_raw']['brier']}/{r['S_south_raw']['ece10']} | "
            f"S_cal {r['S_south_cal']['brier']}/{r['S_south_cal']['ece10']} | "
            f"G_cal {r['G_south_cal']['brier']}/{r['G_south_cal']['ece10']}")

    import math
    res["summary"] = {}
    for fam in ("rf", "xgb"):
        for key in ("G_north_raw", "G_north_cal", "G_south_raw", "G_south_cal",
                    "S_south_raw", "S_south_cal"):
            for met in ("pr_auc", "auc", "brier", "ece10", "sens50"):
                vals = np.array([s[fam][key][met] for s in res["per_seed"]], dtype=float)
                vals = vals[~np.isnan(vals)]
                if len(vals) == 0:
                    continue
                m, sd = float(vals.mean()), float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
                res["summary"][f"{fam}_{key}_{met}"] = {
                    "mean": round(m, 4), "std": round(sd, 4),
                    "ci95": round(2.776 * sd / math.sqrt(len(vals)), 4) if len(vals) > 1 else 0.0}
    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")
    print("\n===== E13 SUMMARY (mean over 5 seeds) =====")
    for k, v in res["summary"].items():
        if k.endswith(("_brier", "_ece10", "_pr_auc", "_sens50")):
            print(f"{k:28s} {v['mean']:.4f} ±{v['ci95']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
