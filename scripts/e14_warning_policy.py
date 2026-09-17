"""E14: warning-policy comparison on calibrated outputs (SIH26001).

South test: Global+South-cal vs Specialist+South-cal. North test: global only.
Operating point: smallest threshold with CALIB-positive recall >= 0.80,
transferred fixed to TEST. Plus full 0.05-0.95 sweep curves (diagnostic).
Decision rule (pre-registered in EXPERIMENTS_E_LADDER.md): keep South branch iff
FAR lower by >=0.02 absolute in >=4/5 seeds (RF primary, XGB agrees in direction),
no worse road-event recall; else collapse.

Outputs: runs/e14.json. Run: mnemo-venv python scripts/e14_warning_policy.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "runs" / "e14.json"

SEEDS = [42, 7, 123, 2024, 999]
LAT_SPLIT = 27.15
RECALL_TARGET = 0.80
FAR_MARGIN = 0.02
GRID = np.round(np.arange(0.05, 0.96, 0.05), 2)
NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since"]  # wound REMOVED (E8)


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


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


def op_metrics(y, p, t: float, road=None) -> dict:
    flag = p >= t
    pos, neg = y == 1, y == 0
    road_pos = pos & (road < 200) if road is not None else np.zeros_like(pos)
    tp, fp = int((flag & pos).sum()), int((flag & neg).sum())
    return {"thr": round(float(t), 2),
            "recall": round(tp / max(int(pos.sum()), 1), 4),
            "missed": int(pos.sum()) - tp,
            "far": round(fp / max(int(neg.sum()), 1), 4),
            "far_per_1000": round(1000 * fp / max(int(neg.sum()), 1), 1),
            "precision": round(tp / max(tp + fp, 1), 4),
            "road_recall": round(float((flag & road_pos).sum()) / max(int(road_pos.sum()), 1), 4),
            "road_n": int(road_pos.sum()),
            "flagged_frac": round(float(flag.mean()), 4)}


def split_60_20_20(coords_r, y_r, seed):
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=10, random_state=seed, n_init=10).fit_predict(coords_r)
    order = sorted(range(10), key=lambda c: (km == c).sum(), reverse=True)
    buckets: dict[str, list] = {"test": [], "calib": [], "train": []}
    poscount = {k: 0 for k in buckets}
    for c in order:
        k = min(("test", "calib", "train"), key=lambda k: (poscount[k], len(buckets[k])))
        buckets[k].append(c)
        poscount[k] += int(y_r[km == c].sum())
    if sorted(len(v) for v in buckets.values()) != [2, 2, 6]:
        buckets = {"test": order[0:2], "calib": order[2:4], "train": order[4:10]}
    out = {}
    for k, cl in buckets.items():
        idx = np.where(np.isin(km, cl))[0]
        assert len(np.unique(y_r[idx])) == 2 and len(idx) >= 50, f"{k} degenerate"
        out[k] = idx
    return out


ROAD = np.array([])


def main() -> int:
    global ROAD
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
    ROAD = mat["distance_to_road"].to_numpy()
    coords = side[["lat", "lon"]].to_numpy()
    lat = side["lat"].to_numpy()
    district = side["district"].to_numpy()
    south = ((side["district"] == "Darjeeling").to_numpy()
             | ((district == "background") & (lat < LAT_SPLIT)))
    north = ~south
    log(f"pool n={len(y)} south={int(south.sum())} north={int(north.sum())}")

    res: dict = {"seeds": SEEDS, "recall_target": RECALL_TARGET,
                 "far_margin": FAR_MARGIN, "per_seed": []}
    for seed in SEEDS:
        sp = split_60_20_20(coords[south], y[south], seed)
        no = split_60_20_20(coords[north], y[north], seed + 1)
        S = {k: np.where(south)[0][v] for k, v in sp.items()}
        N = {k: np.where(north)[0][v] for k, v in no.items()}
        entry: dict = {"seed": seed}
        for fam in ("rf", "xgb"):
            f: dict = {}
            tr = np.concatenate([N["train"], S["train"]])
            # raw probs on calib (threshold transfer) + test
            p_sca = fit_predict(X.iloc[tr], y[tr], X.iloc[S["calib"]], fam, seed)
            p_ste = fit_predict(X.iloc[tr], y[tr], X.iloc[S["test"]], fam, seed)
            p_nte = fit_predict(X.iloc[tr], y[tr], X.iloc[N["test"]], fam, seed)
            q_sca = fit_predict(X.iloc[S["train"]], y[S["train"]], X.iloc[S["calib"]], fam, seed)
            q_ste = fit_predict(X.iloc[S["train"]], y[S["train"]], X.iloc[S["test"]], fam, seed)
            iso_s0 = IsotonicRegression(out_of_bounds="clip").fit(p_sca, y[S["calib"]])
            iso_s1 = IsotonicRegression(out_of_bounds="clip").fit(q_sca, y[S["calib"]])
            iso_n = IsotonicRegression(out_of_bounds="clip").fit(
                fit_predict(X.iloc[tr], y[tr], X.iloc[N["calib"]], fam, seed), y[N["calib"]])
            c_ste, c_qte = iso_s0.predict(p_ste), iso_s1.predict(q_ste)
            c_nte = iso_n.predict(p_nte)
            # operating thresholds from CALIB (recall>=0.80), fixed to TEST
            yc = y[S["calib"]]
            # smallest GRID threshold with calib recall>=target on calibrated calib preds
            c_sca = iso_s0.predict(p_sca)
            c_qca = iso_s1.predict(q_sca)
            t_g = next((float(t) for t in GRID[::-1] if (c_sca >= t)[yc == 1].mean() >= RECALL_TARGET), 0.05)
            t_s = next((float(t) for t in GRID[::-1] if (c_qca >= t)[yc == 1].mean() >= RECALL_TARGET), 0.05)
            r_ste = ROAD[S["test"]]
            f["G_op"] = {**op_metrics(y[S["test"]], c_ste, t_g, r_ste), "thr_from": "calib"}
            f["S_op"] = {**op_metrics(y[S["test"]], c_qte, t_s, r_ste), "thr_from": "calib"}
            f["G_sweep"] = [op_metrics(y[S["test"]], c_ste, float(t), r_ste) for t in GRID]
            f["S_sweep"] = [op_metrics(y[S["test"]], c_qte, float(t), r_ste) for t in GRID]
            f["N_op_global"] = op_metrics(y[N["test"]], c_nte,
                                          next((float(t) for t in GRID[::-1]
                                                if (iso_n.predict(fit_predict(X.iloc[tr], y[tr], X.iloc[N["calib"]], fam, seed)) >= t)[y[N["calib"]] == 1].mean() >= RECALL_TARGET), 0.05),
                                          ROAD[N["test"]])
            entry[fam] = f
        res["per_seed"].append(entry)
        log(f"seed {seed}: RF G {entry['rf']['G_op']} | S {entry['rf']['S_op']}")

    # ---- apply pre-registered rule ----
    import math
    rule = {"wins_rf": 0, "road_worse": False, "xgb_sign": []}
    for s in res["per_seed"]:
        if s["rf"]["S_op"]["far"] <= s["rf"]["G_op"]["far"] - FAR_MARGIN:
            rule["wins_rf"] += 1
        if s["rf"]["S_op"]["road_recall"] < s["rf"]["G_op"]["road_recall"] - 0.02:
            rule["road_worse"] = True
        rule["xgb_sign"].append(float(s["xgb"]["S_op"]["far"] - s["xgb"]["G_op"]["far"]))
    xgb_agree = sum(1 for d in rule["xgb_sign"] if d < 0)
    rule["xgb_agree_count"] = int(xgb_agree)
    rule["keep_branch"] = bool(rule["wins_rf"] >= 4 and xgb_agree >= 3 and not rule["road_worse"])
    rule["verdict"] = ("KEEP South specialist branch" if rule["keep_branch"]
                       else "COLLAPSE to global + regional calibration")
    res["rule"] = rule
    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min :: {rule['verdict']} "
        f"(RF wins {rule['wins_rf']}/5, XGB agree {xgb_agree}/5, road_worse={rule['road_worse']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
