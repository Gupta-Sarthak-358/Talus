"""E1.5a: negative difficulty ladder N0-N5 on FROZEN global OOF + match-feasibility.

N0 random BG | N1 low-elev BG | N2 near-road BG | N3 elev+road | N4 +slope |
N5 region + elev + road + slope (pooled concat of within-region N4 evals).
Plus: >=300m separation check, per-positive nearest-BG match audit (feasibility
of a matched *training* set from the existing pool), LULC mix per tier.

Run: mnemo-venv python scripts/exp_e15_ladder.py
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
OUT = REPO / "runs" / "exp_e15_ladder.json"

SEED = 42
N_TREES = 200
LAT_SPLIT = 27.15
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


def metrics(y, p) -> dict:
    return {"auc": auc(y, p), "brier": brier(y, p), "ece10": ece(y, p),
            "acc50": round(float(((p >= 0.5) == y).mean()), 4),
            "n": int(len(y)), "pos_rate": round(float(y.mean()), 4)}


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


def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    R = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def main() -> int:
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupKFold
    mat = pd.read_csv(MATRIX)
    side = pd.read_csv(SIDECAR)
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    lat = side["lat"].to_numpy()
    district = side["district"].to_numpy()
    bg = district == "background"
    pos = y == 1
    elev = mat["elevation"].to_numpy()
    road = mat["distance_to_road"].to_numpy()
    slope = mat["slope_angle"].to_numpy()

    # frozen global OOF (same protocol as E-ladder FULL)
    g8 = KMeans(n_clusters=8, random_state=SEED, n_init=10).fit_predict(coords)
    oof = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=8).split(X, y, g8):
        pre = make_pre()
        clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
        clf.fit(pre.fit_transform(X.iloc[tr]), y[tr])
        proba = clf.predict_proba(pre.transform(X.iloc[te]))
        oof[te] = proba[:, list(clf.classes_).index(1)]
    assert not np.isnan(oof).any()

    # ---- separation check (Gate A): BG >=300m from every positive? ----
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=1, metric="haversine").fit(np.radians(coords[pos]))
    d_bg, _ = nn.kneighbors(np.radians(coords[bg]))
    d_bg_m = (d_bg.ravel() * 6371000.0)
    res: dict = {"separation_m": {"min": round(float(d_bg_m.min()), 1),
                                  "median": round(float(np.median(d_bg_m)), 1),
                                  "frac_ge_300m": round(float((d_bg_m >= 300).mean()), 4)}}
    log(f"BG-to-nearest-positive: min {res['separation_m']['min']}m, "
        f"frac>=300m {res['separation_m']['frac_ge_300m']}")

    # ---- difficulty tiers ----
    slo_lo, slo_hi = np.quantile(slope[pos], [0.10, 0.90])
    tiers = {
        "N0_random": bg,
        "N1_lowelev": bg & (elev < 2500),
        "N2_nearroad": bg & (road < 1000),
        "N3_elev_road": bg & (elev < 2500) & (road < 1000),
        "N4_plus_slope": bg & (elev < 2500) & (road < 1000)
        & (slope >= slo_lo) & (slope <= slo_hi),
    }
    res["tiers"] = {}
    for name, mask in tiers.items():
        idx = np.where(pos | mask)[0]
        m = {"n_bg": int(mask.sum()), **metrics(y[idx], oof[idx]),
             "bg_elev_med": round(float(np.median(elev[mask])), 0),
             "bg_road_med": round(float(np.median(road[mask])), 0),
             "bg_lulc_top": {str(k): int(v) for k, v in
                             pd.Series(mat.loc[mask, "lulc"]).value_counts().head(3).items()}}
        res["tiers"][name] = m
        log(f"{name}: bg={m['n_bg']} auc={m['auc']} "
            f"(elev_med {m['bg_elev_med']}, road_med {m['bg_road_med']})")
    # N5: within-region N4 evals, pooled concat
    n5_parts = []
    res["tiers"]["N5_region_matched"] = {}
    for r, rm in (("SOUTH", (district == "Darjeeling") | (bg & (lat < LAT_SPLIT))),
                  ("NORTH", (district != "Darjeeling") & (district != "background") | (bg & (lat >= LAT_SPLIT)))):
        pm = pos & rm
        nm = bg & (elev < 2500) & (road < 1000) & (slope >= slo_lo) & (slope <= slo_hi) & rm
        idx = np.where(pm | nm)[0]
        res["tiers"]["N5_region_matched"][r] = {"n_pos": int(pm.sum()), "n_bg": int(nm.sum()),
                                               **metrics(y[idx], oof[idx])}
        n5_parts.append(idx)
        log(f"N5 {r}: pos={pm.sum()} bg={nm.sum()} auc={res['tiers']['N5_region_matched'][r]['auc']}")
    n5_idx = np.concatenate(n5_parts)
    res["tiers"]["N5_region_matched"]["POOLED"] = metrics(y[n5_idx], oof[n5_idx])
    log(f"N5 pooled: {res['tiers']['N5_region_matched']['POOLED']}")

    # ---- match-feasibility: nearest BG in standardized (elev, slope, road) space ----
    feats = np.column_stack([elev, slope, np.log1p(road)])
    mu, sd = feats[pos].mean(0), feats[pos].std(0)
    z = (feats - mu) / sd
    from sklearn.neighbors import NearestNeighbors as NN2
    out = {}
    for r, rm in (("SOUTH", (lat < LAT_SPLIT)), ("NORTH", (lat >= LAT_SPLIT))):
        p_idx = np.where(pos & rm)[0]
        b_idx = np.where(bg & rm)[0]
        if len(b_idx) == 0:
            out[r] = {"n_pos": int(len(p_idx)), "n_bg": 0, "feasible": False}
            continue
        nn2 = NN2(n_neighbors=1).fit(z[b_idx])
        dd, _ = nn2.kneighbors(z[p_idx])
        dd = dd.ravel()
        # greedy 1:1 without replacement
        order = np.argsort(dd)
        used, matched = set(), 0
        dists = []
        taken = set()
        for oi in order:
            drow = np.sqrt(((z[b_idx] - z[p_idx[oi]]) ** 2).sum(1))
            for bi in np.argsort(drow):
                if bi not in taken:
                    taken.add(bi)
                    matched += 1
                    dists.append(float(drow[bi]))
                    break
        out[r] = {"n_pos": int(len(p_idx)), "n_bg": int(len(b_idx)),
                  "greedy_1to1_matched": int(matched),
                  "coverage": round(matched / max(len(p_idx), 1), 3),
                  "nn_dist_med": round(float(np.median(dd)), 3),
                  "nn_dist_p90": round(float(np.quantile(dd, 0.9)), 3),
                  "frac_nn_lt_0.5": round(float((dd < 0.5).mean()), 3)}
        log(f"match {r}: pos={len(p_idx)} bg={len(b_idx)} "
            f"nn_med={out[r]['nn_dist_med']} frac<0.5={out[r]['frac_nn_lt_0.5']}")
    res["match_feasibility"] = out
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT}")
    print("\n===== N-LADDER =====")
    for k, v in res["tiers"].items():
        print(k, v if k != "N5_region_matched" else v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
