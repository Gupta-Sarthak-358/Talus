"""E1.5c verification: north SMD before/after top-up + north matched-eval on the
expanded pool. Cleanup metric only — NOT an architecture rerun (no specialists,
no debate). Run: mnemo-venv python scripts/e15c_check.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "runs" / "e15c_check.json"
SEED = 42
N_TREES = 200
LAT_SPLIT = 27.15
NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def metrics(y, p) -> dict:
    from sklearn.metrics import roc_auc_score
    return {"auc": round(float(roc_auc_score(y, p)), 4),
            "brier": round(float(np.mean((p - y) ** 2)), 4),
            "n": int(len(y))}


def smd(a, b) -> float:
    s = np.sqrt((np.var(a) + np.var(b)) / 2)
    return round(float((np.mean(a) - np.mean(b)) / s) if s > 0 else 0.0, 3)


def build_X(mat: pd.DataFrame) -> pd.DataFrame:
    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "seismic_dist_km", "seismic_n50_rate",
             "seismic_years_since", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    return X.drop(columns=["spi"])


def make_pre():
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]),
    ])


def main() -> int:
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupKFold
    from sklearn.neighbors import NearestNeighbors
    m0 = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    s0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    m1 = pd.read_csv(REPO / "data/sih26001/processed/e15_negatives.csv")
    s1 = pd.read_csv(REPO / "data/sih26001/processed/e15_sidecar.csv")
    m2 = pd.read_csv(REPO / "data/sih26001/processed/e15c_negatives.csv")
    s2 = pd.read_csv(REPO / "data/sih26001/processed/e15c_sidecar.csv")
    keep = (m2["distance_to_road"] < 1000).to_numpy()
    m2, s2 = m2[keep].reset_index(drop=True), s2[keep].reset_index(drop=True)
    assert (m2["recent_disturbance"] == 0).all()
    mat = pd.concat([m0, m1[m1["distance_to_road"] < 1000], m2], ignore_index=True)
    side = pd.concat([s0, s1[m1["distance_to_road"] < 1000], s2], ignore_index=True)
    y = mat["event"].to_numpy().astype(int)
    lat = side["lat"].to_numpy()
    district = side["district"].to_numpy()
    north = ((district != "Darjeeling") & (district != "background")) | ((district == "background") & (lat >= LAT_SPLIT))
    log(f"expanded pool n={len(y)} pos={int(y.sum())} north_bg={int(((y == 0) & north).sum())}")

    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    g8 = KMeans(n_clusters=8, random_state=SEED, n_init=10).fit_predict(coords)
    oof = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=8).split(X, y, g8):
        pre = make_pre()
        clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
        clf.fit(pre.fit_transform(X.iloc[tr]), y[tr])
        oof[te] = clf.predict_proba(pre.transform(X.iloc[te]))[:, 1]

    res: dict = {}
    # SMD before (without e15c) vs after, north positives vs north BG
    npos = (y == 1) & north
    nbg_old = (y == 0) & north & (np.arange(len(y)) < len(m0) + (m1["distance_to_road"] < 1000).sum())
    nbg_all = (y == 0) & north
    for feat, col in (("elev", "elevation"), ("road", "distance_to_road"), ("slope", "slope_angle")):
        v = mat[col].to_numpy()
        res[feat] = {"smd_before": smd(v[npos], v[nbg_old]), "smd_after": smd(v[npos], v[nbg_all])}
    # greedy 1:1 matched north eval (with top-up) on frozen-expanded OOF
    feats = np.column_stack([mat["elevation"].to_numpy(), mat["distance_to_road"].to_numpy()])
    mu, sd = feats[npos].mean(0), feats[npos].std(0)
    z = (feats - mu) / sd
    p_idx = np.where(npos)[0]
    b_idx = np.where(nbg_all)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(z[b_idx])
    dd, _ = nn.kneighbors(z[p_idx])
    order = np.argsort(dd.ravel())
    taken, pairs = set(), []
    for oi in order:
        drow = np.sqrt(((z[b_idx] - z[p_idx[oi]]) ** 2).sum(1))
        for bi in np.argsort(drow):
            if bi not in taken:
                taken.add(bi)
                pairs.append((p_idx[oi], b_idx[bi]))
                break
    mp = np.array([a for a, _ in pairs])
    mb = np.array([b for _, b in pairs])
    midx = np.concatenate([mp, mb])
    res["north_matched_eval"] = {"pairs": len(mp), **metrics(y[midx], oof[midx])}
    for feat, col in (("elev", "elevation"), ("road", "distance_to_road"), ("slope", "slope_angle")):
        v = mat[col].to_numpy()
        res[f"matched_smd_{feat}"] = smd(v[mp], v[mb])
    log(f"SMD north: {res}")
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("E1.5c:", json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
