"""Gate B/C on the E1.5b-corrected pool (SIH26001).

Pool: 1468 positives + 1468 original BG + 1114 new southern road<1km BG (E1.5b).
recent_disturbance REMOVED from X (E8). Train/eval disjointness via spatial
GroupKFold (new negatives cluster geographically automatically).
Gate B: global vs SOUTH/NORTH specialists, same corrected splits.
Gate C: matched-negative eval, NO_BOTH/NO_MEMORY/NO_SEISMIC ablations,
  sensitivity@0.5 per region, SMD audit (pos vs all-BG vs matched-BG).

Outputs: runs/gates_e15.json. Run: mnemo-venv python scripts/gates_e15.py
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
OUT = REPO / "runs" / "gates_e15.json"

SEED = 42
N_TREES = 200
LAT_SPLIT = 27.15
NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since"]  # recent_disturbance REMOVED (E8)


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


def sens50(y, p) -> float:
    return round(float((p[y == 1] >= 0.5).mean()), 4) if (y == 1).any() else None


def metrics(y, p) -> dict:
    return {"auc": auc(y, p), "pr_auc": pr_auc(y, p), "brier": brier(y, p),
            "ece10": ece(y, p), "acc50": round(float(((p >= 0.5) == y).mean()), 4),
            "sens50": sens50(y, p), "n": int(len(y)),
            "pos_rate": round(float(y.mean()), 4)}


def build_X(mat: pd.DataFrame, num_cols) -> pd.DataFrame:
    keep = [c for c in ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
                        "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
                        "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
                        "drain_density", "seismic_dist_km", "seismic_n50_rate",
                        "seismic_years_since", "recent_disturbance", "lulc"]
            if c == "lulc" or c in num_cols or c == "spi"]
    X = mat[keep].copy()
    if "spi" in X.columns:
        X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
        X = X.drop(columns=["spi"])
    return X


def make_pre(num_cols):
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    return ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]),
    ])


def group_oof(X, y, groups, n_splits, num_cols, tag=""):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupKFold
    gkf = GroupKFold(n_splits=n_splits)
    oof = np.full(len(y), np.nan)
    for tr, te in gkf.split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            oof[te] = float(np.unique(y[tr])[0])
            continue
        pre = make_pre(num_cols)
        clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
        clf.fit(pre.fit_transform(X.iloc[tr]), y[tr])
        proba = clf.predict_proba(pre.transform(X.iloc[te]))
        oof[te] = proba[:, list(clf.classes_).index(1)] if proba.shape[1] > 1 else float(clf.classes_[0] == 1)
    assert not np.isnan(oof).any(), f"{tag}: NaN in OOF"
    return oof


def fit_predict(Xtr, ytr, Xte, num_cols):
    from sklearn.ensemble import RandomForestClassifier
    pre = make_pre(num_cols)
    clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
    clf.fit(pre.fit_transform(Xtr), ytr)
    proba = clf.predict_proba(pre.transform(Xte))
    return proba[:, list(clf.classes_).index(1)] if proba.shape[1] > 1 else np.full(len(Xte), float(clf.classes_[0] == 1))


def smd(a: np.ndarray, b: np.ndarray) -> float:
    s = np.sqrt((np.var(a) + np.var(b)) / 2)
    return round(float((np.mean(a) - np.mean(b)) / s) if s > 0 else 0.0, 3)


def main() -> int:
    t0 = time.time()
    from sklearn.cluster import KMeans
    m0 = pd.read_csv(MAT0)
    s0 = pd.read_csv(SIDE0)
    m1 = pd.read_csv(MAT1)
    s1 = pd.read_csv(SIDE1)
    assert list(m1.columns) == list(m0.columns) and list(s1.columns) == list(s0.columns)
    assert (m1["recent_disturbance"] == 0).all() and (m1["event"] == 0).all()
    # design filter (logged): road<1km survivors only
    keep = (m1["distance_to_road"] < 1000).to_numpy()
    log(f"road<1km filter: {int(keep.sum())}/{len(m1)} survivors")
    assert keep.sum() >= 450, "shortfall: extend candidates"
    m1 = m1[keep].reset_index(drop=True)
    s1 = s1[keep].reset_index(drop=True)

    mat = pd.concat([m0, m1], ignore_index=True)
    side = pd.concat([s0, s1], ignore_index=True)
    y = mat["event"].to_numpy().astype(int)
    coords = side[["lat", "lon"]].to_numpy()
    district = side["district"].to_numpy()
    lat = side["lat"].to_numpy()
    is_new = np.arange(len(y)) >= len(m0)
    log(f"corrected pool: n={len(y)} pos={int(y.sum())} new_bg={int(is_new.sum())} "
        f"(orig_bg={(y == 0).sum() - is_new.sum()})")

    X = build_X(mat, NUMERIC)
    g8 = KMeans(n_clusters=8, random_state=SEED, n_init=10).fit_predict(coords)
    res: dict = {"n": len(y), "n_pos": int(y.sum()), "n_new_bg": int(is_new.sum()),
                 "wound_removed": True}

    # ---- Gate B ----
    oof_g = group_oof(X, y, g8, 8, NUMERIC, "global-corrected")
    res["B_global_pooled"] = metrics(y, oof_g)
    log(f"B global pooled: {res['B_global_pooled']}")
    res["B_regions"] = {}
    oof_ens = np.full(len(y), np.nan)
    for r, rm in (("SOUTH", (side["district"] == "Darjeeling").to_numpy() | ((district == "background") & (lat < LAT_SPLIT))),
                  ("NORTH", ((district != "Darjeeling") & (district != "background")) | ((district == "background") & (lat >= LAT_SPLIT)))):
        m = np.where(rm)[0]
        gs = KMeans(n_clusters=4, random_state=SEED, n_init=10).fit_predict(coords[m])
        oof_r = group_oof(X.iloc[m], y[m], gs, 4, NUMERIC, r)
        oof_ens[m] = oof_r
        res["B_regions"][r] = {"n": int(len(m)), "pos": int(y[m].sum()),
                               "specialist": metrics(y[m], oof_r),
                               "global_sliced": metrics(y[m], oof_g[m])}
        log(f"B {r}: specialist {res['B_regions'][r]['specialist']} "
            f"vs global-sliced {res['B_regions'][r]['global_sliced']}")
    res["B_ensemble_pooled"] = metrics(y, oof_ens)

    # ---- Gate C: matched eval + ablations ----
    # greedy 1:1 match per region on standardized (elev, road); slope diagnostic
    feats = np.column_stack([mat["elevation"].to_numpy(), mat["distance_to_road"].to_numpy()])
    mu, sd = feats[y == 1].mean(0), feats[y == 1].std(0)
    z = (feats - mu) / sd
    from sklearn.neighbors import NearestNeighbors
    matched_idx = []
    res["C_smd"] = {}
    south_m = (side["district"] == "Darjeeling").to_numpy() | ((district == "background") & (lat < LAT_SPLIT))
    north_m = ((district != "Darjeeling") & (district != "background")) | ((district == "background") & (lat >= LAT_SPLIT))
    for r, rm in (("SOUTH", south_m), ("NORTH", north_m)):
        p_idx = np.where((y == 1) & rm)[0]
        b_idx = np.where((y == 0) & rm)[0]
        nn = NearestNeighbors(n_neighbors=1).fit(z[b_idx])
        dd, _ = nn.kneighbors(z[p_idx])
        # greedy without replacement
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
        for feat, col in (("elev", "elevation"), ("road", "distance_to_road"), ("slope", "slope_angle")):
            v = mat[col].to_numpy()
            res["C_smd"].setdefault(r, {})[feat] = {
                "pos_med": round(float(np.median(v[mp])), 1),
                "allbg_med": round(float(np.median(v[(y == 0) & rm])), 1),
                "matched_med": round(float(np.median(v[mb])), 1),
                "smd_all": smd(v[mp], v[(y == 0) & rm]),
                "smd_matched": smd(v[mp], v[mb])}
        midx = np.concatenate([mp, mb])
        res["C_smd"][r]["matched_eval"] = metrics(y[midx], oof_g[midx])
        matched_idx.append(midx)
        log(f"C {r}: matched {len(mp)} pairs; SMD elev {res['C_smd'][r]['elev']['smd_all']}->{res['C_smd'][r]['elev']['smd_matched']}, "
            f"road {res['C_smd'][r]['road']['smd_all']}->{res['C_smd'][r]['road']['smd_matched']}; "
            f"matched-eval {res['C_smd'][r]['matched_eval']}")
    midx_all = np.concatenate(matched_idx)
    res["C_matched_pooled"] = metrics(y[midx_all], oof_g[midx_all])

    res["C_ablations_corrected"] = {}
    for name, drop in (("FULL", []), ("NO_BOTH", ["elevation", "distance_to_road"]),
                       ("NO_MEMORY", ["rainfall_7d_mm", "rainfall_30d_mm", "soil_moisture"]),
                       ("NO_SEISMIC", ["seismic_dist_km", "seismic_n50_rate", "seismic_years_since"])):
        num = [c for c in NUMERIC if c not in drop]
        oof = group_oof(X, y, g8, 8, num, f"C-{name}")
        res["C_ablations_corrected"][name] = {"drop": drop, **metrics(y, oof)}
        log(f"C {name}: {res['C_ablations_corrected'][name]}")

    # ---- temporal on corrected pool (E4 repeat; dated positives all Sikkim) ----
    yr = side["year"].to_numpy().astype(int)
    rng = np.random.default_rng(SEED)
    neg_idx = np.where(y == 0)[0].copy()
    rng.shuffle(neg_idx)
    half = len(neg_idx) // 2
    all_idx = np.arange(len(y))
    in_tr = np.isin(all_idx, neg_idx[:half])
    in_te = np.isin(all_idx, neg_idx[half:])
    tr_m = ((yr > 0) & (yr <= 2018)) | in_tr
    te_m = ((yr > 0) & (yr >= 2019)) | in_te
    p_te = fit_predict(X.iloc[tr_m], y[tr_m], X.iloc[te_m], NUMERIC)
    res["temporal_corrected"] = {"test_n": int(te_m.sum()),
                                 "test_pos_dated": int((((yr > 0) & (yr >= 2019)) & (y == 1)).sum()),
                                 **metrics(y[te_m], p_te)}
    log(f"temporal corrected: {res['temporal_corrected']}")

    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")
    print("\n===== GATES =====")
    print("B global:", res["B_global_pooled"], "| ens:", res["B_ensemble_pooled"])
    for r in ("SOUTH", "NORTH"):
        print(f"B {r}:", res["B_regions"][r]["specialist"], "vs global-sliced:", res["B_regions"][r]["global_sliced"])
    print("C matched pooled:", res["C_matched_pooled"])
    for k, v in res["C_ablations_corrected"].items():
        print(f"C {k}:", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
