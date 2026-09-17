"""Region-specialist vs generalist experiment (SIH26001).

Question: do local rain/EQ thresholds + per-area models beat one global model,
or does generalisation win? (User hypothesis: generalisation costs speciality.)

Ladder:
  L1 global: RF200, GroupKFold(8) on KMeans-8 coords (trainer protocol, fewer trees for speed).
  L2 two-region: SOUTH=DARJ (district Darjeeling + background lat<27.15)
                 NORTH=SK (all other districts + rest of background).
       - global-sliced AUC per region (same L1 OOF, sliced)
       - specialist within-region OOF AUC (GroupKFold-4 inside each region)
       - ensemble pooled OOF (concat specialist OOFs) vs global pooled
       - cross-region: fit full NORTH -> test SOUTH, fit full SOUTH -> test NORTH
  L4 four-region: KMeans-4 geographic blocks, same specialist/ensemble procedure.
Thresholds: per-region positive rain (24h/7d/30d, effective=7d+0.3*30d) medians/p90
  + seismic means -> local-threshold proposal vs warning_thresholds.json scale.
Importances: top-5 permutation (3 repeats, screening) for global vs N vs S.

Outputs: stdout tables + runs/region_specialist.json (git-ignored runs/).
Run: mnemo-venv python scripts/exp_region_specialist.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDECAR = REPO / "data/sih26001/processed/training_sidecar.csv"
OUT = REPO / "runs" / "region_specialist.json"

SEED = 42
N_TREES = 200  # screening (prod=500); relative deltas are the claim, not absolutes
LAT_SPLIT = 27.15  # 95% of DARJ positives <27.15, 89% of SK positives >=27.15; lon overlaps

NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since", "recent_disturbance"]


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
    if len(np.unique(y)) < 2:
        return None
    return round(float(roc_auc_score(y, p)), 4)


def build_X(mat: pd.DataFrame) -> pd.DataFrame:
    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "seismic_dist_km", "seismic_n50_rate",
             "seismic_years_since", "recent_disturbance", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    return X.drop(columns=["spi"])


def make_pre():
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]),
    ])


def fit_rf(Xtr: pd.DataFrame, ytr: np.ndarray):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.base import clone
    pre = make_pre()
    Xt = pre.fit_transform(Xtr)
    clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
    clf.fit(Xt, ytr)
    return pre, clf


def group_oof(X, y, groups, n_splits, tag: str):
    """Spatial GroupKFold OOF with RF200. Single-class folds: AUC n/a, kept pooled."""
    from sklearn.model_selection import GroupKFold
    from sklearn.ensemble import RandomForestClassifier
    gkf = GroupKFold(n_splits=n_splits)
    oof = np.full(len(y), np.nan)
    fold_auc = {}
    for tr, te in gkf.split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            # single-class train fold (tiny/pure spatial pocket): constant fallback
            oof[te] = float(np.unique(y[tr])[0])
            fold_auc[int(np.unique(groups[te])[0])] = auc(y[te], oof[te])
            continue
        pre = make_pre()
        Xt = pre.fit_transform(X.iloc[tr])
        Xe = pre.transform(X.iloc[te])
        clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
        clf.fit(Xt, y[tr])
        proba = clf.predict_proba(Xe)
        if proba.shape[1] == 1:
            oof[te] = float(clf.classes_[0] == 1)
        else:
            oof[te] = proba[:, list(clf.classes_).index(1)]
        fold_auc[int(np.unique(groups[te])[0])] = auc(y[te], oof[te])
    assert not np.isnan(oof).any(), f"{tag}: NaN in OOF"
    return oof, fold_auc


def metrics(y, p) -> dict:
    return {"auc": auc(y, p), "brier": brier(y, p), "ece10": ece(y, p),
            "acc50": round(float(((p >= 0.5) == y).mean()), 4), "n": int(len(y)),
            "pos_rate": round(float(y.mean()), 4)}


def main() -> int:
    t0 = time.time()
    mat = pd.read_csv(MATRIX)
    side = pd.read_csv(SIDECAR)
    assert len(mat) == len(side) and (mat["zone_id"] == side["zone_id"]).all()
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    district = side["district"].to_numpy()
    lat = side["lat"].to_numpy()

    is_bg = district == "background"
    is_darj = district == "Darjeeling"
    is_sk = ~(is_bg | is_darj)

    # L2 regions: positives by district, background by geography
    reg = np.where(is_darj | (is_bg & (lat < LAT_SPLIT)), "SOUTH_DARJ",
           np.where(is_sk | (is_bg & (lat >= LAT_SPLIT)), "NORTH_SK", "?"))
    assert set(np.unique(reg)) == {"SOUTH_DARJ", "NORTH_SK"}
    for r in ("SOUTH_DARJ", "NORTH_SK"):
        m = reg == r
        log(f"{r}: n={m.sum()} pos={int(y[m].sum())} "
            f"pos_rate={y[m].mean():.3f} lat_med={np.median(lat[m]):.3f}")

    # ---------- L1 global ----------
    from sklearn.cluster import KMeans
    g8 = KMeans(n_clusters=8, random_state=SEED, n_init=10).fit_predict(coords)
    oof_g, _ = group_oof(X, y, g8, 8, "global")
    res: dict = {"seed": SEED, "trees": N_TREES, "lat_split": LAT_SPLIT,
                 "global_pooled": metrics(y, oof_g)}

    # ---------- global sliced by region ----------
    res["global_sliced"] = {}
    for r in ("SOUTH_DARJ", "NORTH_SK"):
        m = reg == r
        res["global_sliced"][r] = metrics(y[m], oof_g[m])
        log(f"global-sliced {r}: {res['global_sliced'][r]}")

    # ---------- L2 specialists ----------
    res["specialist"] = {}
    oof_ens = np.full(len(y), np.nan)
    for r in ("SOUTH_DARJ", "NORTH_SK"):
        m = np.where(reg == r)[0]
        Xr, yr = X.iloc[m], y[m]
        cr = coords[m]
        k = 4
        gr = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit_predict(cr)
        oof_r, _ = group_oof(Xr, yr, gr, k, r)
        oof_ens[m] = oof_r
        res["specialist"][r] = {"within_oof": metrics(yr, oof_r),
                                "global_sliced_same_pts": metrics(yr, oof_g[m])}
        log(f"specialist {r} within-OOF: {res['specialist'][r]['within_oof']}")
    res["ensemble_L2_pooled"] = metrics(y, oof_ens)
    log(f"ensemble L2 pooled: {res['ensemble_L2_pooled']} vs global {res['global_pooled']}")

    # ---------- cross-region ----------
    res["cross_region"] = {}
    for tr_r, te_r in (("NORTH_SK", "SOUTH_DARJ"), ("SOUTH_DARJ", "NORTH_SK")):
        tr = np.where(reg == tr_r)[0]
        te = np.where(reg == te_r)[0]
        pre, clf = fit_rf(X.iloc[tr], y[tr])
        p = clf.predict_proba(pre.transform(X.iloc[te]))[:, 1]
        res["cross_region"][f"{tr_r}->{te_r}"] = metrics(y[te], p)
        log(f"cross {tr_r}->{te_r}: {res['cross_region'][f'{tr_r}->{te_r}']}")

    # ---------- L4 KMeans-4 blocks ----------
    g4 = KMeans(n_clusters=4, random_state=SEED, n_init=10).fit_predict(coords)
    res["L4_blocks"] = {}
    oof_l4 = np.full(len(y), np.nan)
    for c in range(4):
        m = np.where(g4 == c)[0]
        maj = pd.Series(district[m]).value_counts().head(2).to_dict()
        res["L4_blocks"][f"block_{c}"] = {
            "n": int(len(m)), "pos": int(y[m].sum()),
            "centroid": [round(float(coords[m, 0].mean()), 3),
                         round(float(coords[m, 1].mean()), 3)],
            "top_districts": {str(k): int(v) for k, v in maj.items()},
            "global_sliced": metrics(y[m], oof_g[m])}
        if len(np.unique(y[m])) < 2 or len(m) < 60:
            log(f"L4 block_{c} too pure/small for specialist (n={len(m)} pos={y[m].sum()}) — skipped")
            oof_l4[m] = oof_g[m]  # fall back to global for pooled comparison
            res["L4_blocks"][f"block_{c}"]["specialist"] = None
            continue
        gr = KMeans(n_clusters=3, random_state=SEED, n_init=10).fit_predict(coords[m])
        oof_r, _ = group_oof(X.iloc[m], y[m], gr, 3, f"L4-{c}")
        oof_l4[m] = oof_r
        res["L4_blocks"][f"block_{c}"]["specialist"] = metrics(y[m], oof_r)
        log(f"L4 block_{c}: specialist {res['L4_blocks'][f'block_{c}']['specialist']} "
            f"vs global-sliced {res['L4_blocks'][f'block_{c}']['global_sliced']}")
    res["ensemble_L4_pooled"] = metrics(y, oof_l4)

    # ---------- thresholds (positives only) ----------
    pos = y == 1
    res["thresholds"] = {}
    for r, m in (("SOUTH_DARJ", (reg == "SOUTH_DARJ") & pos),
                 ("NORTH_SK", (reg == "NORTH_SK") & pos)):
        rain24 = mat.loc[m, "rainfall_24h_mm"].to_numpy()
        rain7 = mat.loc[m, "rainfall_7d_mm"].to_numpy()
        rain30 = mat.loc[m, "rainfall_30d_mm"].to_numpy()
        eff = rain7 + 0.3 * rain30
        sm = mat.loc[m, "soil_moisture"].to_numpy()
        seis = mat.loc[m, "seismic_n50_rate"].to_numpy()
        res["thresholds"][r] = {
            "n_pos": int(m.sum()),
            "rain24_med": round(float(np.median(rain24)), 1),
            "rain24_p90": round(float(np.quantile(rain24, 0.9)), 1),
            "rain7_med": round(float(np.median(rain7)), 1),
            "rain30_med": round(float(np.median(rain30)), 1),
            "eff_med": round(float(np.median(eff)), 1),
            "eff_p90": round(float(np.quantile(eff, 0.9)), 1),
            "soil_med": round(float(np.median(sm)), 3),
            "seis_rate_mean": round(float(seis.mean()), 4)}
        log(f"thresholds {r}: {res['thresholds'][r]}")

    # ---------- importances (screening, 3 repeats) ----------
    from sklearn.inspection import permutation_importance
    res["importance_top5"] = {}
    for tag, idx in (("global", np.arange(len(y))),
                     ("NORTH_SK", np.where(reg == "NORTH_SK")[0]),
                     ("SOUTH_DARJ", np.where(reg == "SOUTH_DARJ")[0])):
        pre, clf = fit_rf(X.iloc[idx], y[idx])
        Xt = pre.transform(X.iloc[idx])
        try:
            names = [n.split("__")[-1] for n in pre.get_feature_names_out()]
        except Exception:
            names = NUMERIC
        perm = permutation_importance(clf, Xt, y[idx], n_repeats=3,
                                      random_state=SEED, scoring="roc_auc", n_jobs=-1)
        order = np.argsort(perm.importances_mean)[::-1][:5]
        res["importance_top5"][tag] = [
            {"feature": names[i], "drop": round(float(perm.importances_mean[i]), 4)}
            for i in order]
        log(f"importance {tag}: {res['importance_top5'][tag]}")

    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")

    print("\n===== SPECIALIST vs GENERALIST (RF200 screening) =====")
    print(f"global pooled        : {res['global_pooled']}")
    print(f"global sliced SOUTH  : {res['global_sliced']['SOUTH_DARJ']}")
    print(f"global sliced NORTH  : {res['global_sliced']['NORTH_SK']}")
    print(f"specialist SOUTH     : {res['specialist']['SOUTH_DARJ']['within_oof']}")
    print(f"specialist NORTH     : {res['specialist']['NORTH_SK']['within_oof']}")
    print(f"ensemble L2 pooled   : {res['ensemble_L2_pooled']}")
    print(f"ensemble L4 pooled   : {res['ensemble_L4_pooled']}")
    print(f"cross N->S           : {res['cross_region']['NORTH_SK->SOUTH_DARJ']}")
    print(f"cross S->N           : {res['cross_region']['SOUTH_DARJ->NORTH_SK']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
