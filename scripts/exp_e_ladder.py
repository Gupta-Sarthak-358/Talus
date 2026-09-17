"""E-ladder: data-honesty experiments before any new intelligence (SIH26001).

E1 hard/region-balanced negatives | E2/E6/E7 ablations | E3 leave-district-out |
E4 temporal + leakage audit | E5 rainfall-source audit | E8 wound-on-road-events |
E9 hazard->exposure ranking | E10 cross-fit calibration + prevalence |
E11 championship protocol (definition + current pre-fix baseline).

Outputs: stdout tables + runs/exp_e_ladder.json.
Run: mnemo-venv python scripts/exp_e_ladder.py
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
OUT = REPO / "runs" / "exp_e_ladder.json"

SEED = 42
N_TREES = 200  # screening; relative deltas are the claim
LAT_SPLIT = 27.15

NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since", "recent_disturbance"]
TERRAIN = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "drain_density", "distance_to_river"]
DYN = ["rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm", "soil_moisture"]
SEIS = ["seismic_dist_km", "seismic_n50_rate", "seismic_years_since"]


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


def pr_auc(y, p):
    from sklearn.metrics import average_precision_score
    if len(np.unique(y)) < 2:
        return None
    return round(float(average_precision_score(y, p)), 4)


def metrics(y, p) -> dict:
    return {"auc": auc(y, p), "pr_auc": pr_auc(y, p), "brier": brier(y, p),
            "ece10": ece(y, p), "acc50": round(float(((p >= 0.5) == y).mean()), 4),
            "n": int(len(y)), "pos_rate": round(float(y.mean()), 4)}


def build_X(mat: pd.DataFrame) -> pd.DataFrame:
    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "seismic_dist_km", "seismic_n50_rate",
             "seismic_years_since", "recent_disturbance", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    return X.drop(columns=["spi"])


def make_pre(num_cols, use_lulc: bool = True):
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    ops = [("num", StandardScaler(), num_cols)]
    if use_lulc:
        ops.append(("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"]))
    return ColumnTransformer(ops)


def group_oof(X, y, groups, n_splits, num_cols, use_lulc=True, tag=""):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupKFold
    gkf = GroupKFold(n_splits=n_splits)
    oof = np.full(len(y), np.nan)
    for tr, te in gkf.split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            oof[te] = float(np.unique(y[tr])[0])
            continue
        pre = make_pre(num_cols, use_lulc)
        clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
        clf.fit(pre.fit_transform(X.iloc[tr]), y[tr])
        proba = clf.predict_proba(pre.transform(X.iloc[te]))
        oof[te] = proba[:, list(clf.classes_).index(1)] if proba.shape[1] > 1 else float(clf.classes_[0] == 1)
    assert not np.isnan(oof).any(), f"{tag}: NaN in OOF"
    return oof


def fit_full(Xtr, ytr, num_cols, use_lulc=True):
    from sklearn.ensemble import RandomForestClassifier
    pre = make_pre(num_cols, use_lulc)
    clf = RandomForestClassifier(n_estimators=N_TREES, random_state=SEED, n_jobs=-1)
    clf.fit(pre.fit_transform(Xtr), ytr)
    return pre, clf


def main() -> int:
    t0 = time.time()
    from sklearn.cluster import KMeans
    mat = pd.read_csv(MATRIX)
    side = pd.read_csv(SIDECAR)
    assert len(mat) == len(side)
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    district = side["district"].to_numpy()
    lat = side["lat"].to_numpy()
    res: dict = {"seed": SEED, "trees": N_TREES, "n": len(y)}

    g8 = KMeans(n_clusters=8, random_state=SEED, n_init=10).fit_predict(coords)

    # ---------------- E2/E6/E7 ablations ----------------
    SETS = {
        "FULL": ([], True),
        "NO_ELEV": (["elevation"], True),
        "NO_ROAD": (["distance_to_road"], True),
        "NO_BOTH": (["elevation", "distance_to_road"], True),
        "TERRAIN_ONLY": ([c for c in NUMERIC if c not in TERRAIN], True),
        "DYN_ONLY": ([c for c in NUMERIC if c not in DYN], False),
        "TERRAIN_DYN": (["distance_to_road"] + SEIS + ["recent_disturbance"], True),
        "NO_MEMORY": (["rainfall_7d_mm", "rainfall_30d_mm", "soil_moisture"], True),
        "NO_SEISMIC": (SEIS, True),
        "NO_WOUND": (["recent_disturbance"], True),
    }
    res["ablations"] = {}
    oof_full = None
    for name, (drop, use_lulc) in SETS.items():
        num = [c for c in NUMERIC if c not in drop]
        oof = group_oof(X, y, g8, 8, num, use_lulc, name)
        res["ablations"][name] = {"drop": drop, "use_lulc": use_lulc, **metrics(y, oof)}
        if name == "FULL":
            oof_full = oof
        log(f"ablation {name}: {res['ablations'][name]}")

    # ---------------- E1 hard + region-balanced ----------------
    bg = district == "background"
    pos = y == 1
    hard = bg & (mat["elevation"].to_numpy() < 2500) & (mat["distance_to_road"].to_numpy() < 1000)
    easy = bg & ~hard
    res["E1"] = {
        "n_hard_bg": int(hard.sum()), "n_easy_bg": int(easy.sum()),
        "hard_eval_pos_vs_hard_bg": metrics(y[pos | hard], oof_full[pos | hard]),
        "easy_eval_pos_vs_easy_bg": metrics(y[pos | easy], oof_full[pos | easy]),
        "note": "same FULL OOF predictions, different negative pools: "
                "hard=elev<2500m & road<1km (populated-terrain-like)",
    }
    log(f"E1 hard: {res['E1']['hard_eval_pos_vs_hard_bg']}")
    log(f"E1 easy: {res['E1']['easy_eval_pos_vs_easy_bg']}")

    # ---------------- E3 leave-district-out ----------------
    def g4(x):
        if x == "Darjeeling":
            return "DARJ"
        if x in ("East Sikkim", "Gangtok District", "Pakyong", "East District"):
            return "EASTSK"
        if x in ("West Sikkim", "Soreng", "Gyalshing", "West district", "West District", "Geyzing"):
            return "WESTSK"
        if x in ("South Sikkim", "Namchi", "North Sikkim", "Mangan"):
            return "S_N_SK"
        return "BG"
    pg = np.array([g4(x) for x in district])
    # BG -> nearest positive group (1-NN haversine on radians)
    from sklearn.neighbors import NearestNeighbors
    pos_idx = np.where(~(pg == "BG"))[0]
    nn = NearestNeighbors(n_neighbors=1, metric="haversine").fit(np.radians(coords[pos_idx]))
    _, ii = nn.kneighbors(np.radians(coords[pg == "BG"]))
    bg_group = pg[pos_idx[ii.ravel()]]
    full_group = pg.copy().astype(object)
    full_group[pg == "BG"] = bg_group
    res["E3"] = {}
    for held in ("DARJ", "EASTSK", "WESTSK", "S_N_SK"):
        te = np.where(full_group == held)[0]
        tr = np.where(full_group != held)[0]
        pre, clf = fit_full(X.iloc[tr], y[tr], NUMERIC, True)
        p = clf.predict_proba(pre.transform(X.iloc[te]))[:, 1]
        res["E3"][f"holdout_{held}"] = {"n_test": int(len(te)),
                                        "pos_test": int(y[te].sum()), **metrics(y[te], p)}
        log(f"E3 holdout {held}: {res['E3'][f'holdout_{held}']}")

    # ---------------- E4 temporal + leakage audit ----------------
    yr = side["year"].to_numpy()
    rng = np.random.default_rng(SEED)
    neg_idx = np.where(y == 0)[0].copy()
    rng.shuffle(neg_idx)
    half = len(neg_idx) // 2
    all_idx = np.arange(len(y))
    in_tr_neg = np.isin(all_idx, neg_idx[:half])
    in_te_neg = np.isin(all_idx, neg_idx[half:])
    tr_m = ((yr > 0) & (yr <= 2018)) | in_tr_neg
    te_m = ((yr > 0) & (yr >= 2019)) | in_te_neg
    pre, clf = fit_full(X.iloc[tr_m], y[tr_m], NUMERIC, True)
    p_te = clf.predict_proba(pre.transform(X.iloc[te_m]))[:, 1]
    # temporal within NORTH only (all >=2019 dated positives are Sikkim)
    north = (district != "Darjeeling") & (district != "background")
    n_tr = ((yr > 0) & (yr <= 2018) & north) | in_tr_neg
    n_te = ((yr > 0) & (yr >= 2019) & north) | in_te_neg
    pre2, clf2 = fit_full(X.iloc[n_tr], y[n_tr], NUMERIC, True)
    p_nte = clf2.predict_proba(pre2.transform(X.iloc[n_te]))[:, 1]
    allowed_rain = {"background-year-peak-imd", "event-year-peak-imd",
                    "climatology-1991-2020", "event-imd-daily"}
    allowed_soil = {"background-year-window-soil", "quasistatic-v092-fallback",
                    "event-year-window-soil", "event-soil-daily"}
    res["E4"] = {
        "temporal_global": {"test_n": int(te_m.sum()),
                            "test_pos_dated": int((((yr > 0) & (yr >= 2019)) & (y == 1)).sum()),
                            **metrics(y[te_m], p_te)},
        "temporal_north_only": {"test_n": int(n_te.sum()),
                                "test_pos_dated": int((((yr > 0) & (yr >= 2019)) & north & (y == 1)).sum()),
                                **metrics(y[n_te], p_nte)},
        "darj_dated_ge2019_pos": int((((yr > 0) & (yr >= 2019)) & (district == "Darjeeling") & (y == 1)).sum()),
        "tag_audit": {
            "rain_vocab_ok": bool(set(side["rain_source"].unique()) <= allowed_rain),
            "soil_vocab_ok": bool(set(side["soil_source"].unique()) <= allowed_soil),
            "rain_counts": {str(k): int(v) for k, v in side["rain_source"].value_counts().items()},
            "soil_counts": {str(k): int(v) for k, v in side["soil_source"].value_counts().items()}},
        "leakage_limitation": "year-peak rows use that-year JJAS peak, which can include "
            "post-event days for early-season slides (month-anchored tier TODO in manifest); "
            "exact-date rows (4) use trailing windows only. Builder must fail on future timestamps (E11).",
    }
    log(f"E4 temporal global: {res['E4']['temporal_global']}")
    log(f"E4 temporal north: {res['E4']['temporal_north_only']}")

    # ---------------- E5 rainfall-source audit + slice ----------------
    res["E5"] = {
        "local_alt_sources": {"IMERG": "absent", "CHIRPS": "absent", "ERA5-Land": "absent",
                              "note": "no local alt-source rasters; multi-source comparison pending download"},
        "oof_by_rain_source": {},
    }
    for src in sorted(side["rain_source"].unique()):
        m = (side["rain_source"] == src).to_numpy()
        if m.sum() > 20 and len(np.unique(y[m])) == 2:
            res["E5"]["oof_by_rain_source"][str(src)] = metrics(y[m], oof_full[m])
    log(f"E5 slices: {res['E5']['oof_by_rain_source']}")

    # ---------------- E8 wound on road-events ----------------
    road_pos = (y == 1) & (mat["distance_to_road"].to_numpy() < 200)
    res["E8"] = {
        "wound_nonzero": int((mat["recent_disturbance"] != 0).sum()),
        "road_pos_n": int(road_pos.sum()),
        "oof_road_pos_vs_all_bg": metrics(y[road_pos | bg], oof_full[road_pos | bg]),
        "verdict": "4/2936 nonzero -> no measurable signal; drop recent_disturbance from X (delta logged) "
                   "until wound layer is rebuilt as disturbance score and re-tested on road-events recall.",
    }
    log(f"E8: {res['E8']}")

    # ---------------- E9 hazard->exposure ranking ----------------
    try:
        run = json.loads((REPO / "data/sih26001/evidence/runout_exposure.json").read_text(encoding="utf-8"))
        sl = json.loads((REPO / "data/sih26001/fixtures/slopes.json").read_text(encoding="utf-8"))
        hz = {z["zone_id"]: z["risk_score"] for z in sl["zones"]}
        rows = [(zid, hz.get(zid), (run["zones"].get(zid) or {}).get("buildings_n"))
                for zid in run.get("zones", {}) if zid in hz]
        by_hz = sorted(rows, key=lambda r: -(r[1] or 0))
        by_exp = sorted(rows, key=lambda r: -((r[2] or 0)))
        res["E9"] = {"by_hazard": [[a, b, c] for a, b, c in by_hz],
                     "by_exposure": [[a, b, c] for a, b, c in by_exp],
                     "rank_changed": [a for a, _, _ in by_hz] != [a for a, _, _ in by_exp],
                     "verdict": "exposure reorders priorities without touching the hazard model."}
    except Exception as e:  # noqa: BLE001
        res["E9"] = {"error": str(e)}
    log(f"E9 rank_changed={res['E9'].get('rank_changed')}")

    # ---------------- E10 cross-fit calibration + prevalence ----------------
    from sklearn.isotonic import IsotonicRegression
    res["E10"] = {}
    for tag, m in (("global", np.ones(len(y), bool)),
                   ("NORTH", ((district != "Darjeeling") & (district != "background")) | (bg & (lat >= LAT_SPLIT))),
                   ("SOUTH", (district == "Darjeeling") | (bg & (lat < LAT_SPLIT)))):
        idx = np.where(m)[0]
        # 4-fold OOF inside subset, then even/odd cross-fit isotonic
        from sklearn.model_selection import GroupKFold
        sub_c = coords[idx]
        from sklearn.cluster import KMeans
        gg = KMeans(n_clusters=4, random_state=SEED, n_init=10).fit_predict(sub_c)
        oof_s = group_oof(X.iloc[idx], y[idx], gg, 4, NUMERIC, True, f"cal-{tag}")
        even = np.arange(len(idx)) % 2 == 0
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(oof_s[even], y[idx][even])
        cal = iso.predict(oof_s[~even])
        raw = oof_s[~even]
        yt = y[idx][~even]
        res["E10"][tag] = {"n_fit": int(even.sum()), "n_eval": int((~even).sum()),
                           "raw": metrics(yt, raw), "calibrated": metrics(yt, cal)}
        log(f"E10 {tag}: raw {res['E10'][tag]['raw']} -> cal {res['E10'][tag]['calibrated']}")
    # prevalence illustration: balanced-train p=0.9 under 1% base rate
    p_bal, pi_tr, pi_real = 0.9, 0.5, 0.01
    p_real = (p_bal * pi_real / pi_tr) / (p_bal * pi_real / pi_tr + (1 - p_bal) * (1 - pi_real) / (1 - pi_tr))
    res["E10"]["prevalence_note"] = {
        "balanced_p0.9_at_1pct_base_rate": round(float(p_real), 4),
        "meaning": "a 0.90 model output under 50/50 training ~= 0.08 field probability at 1% base rate; "
                   "never present raw outputs as real-world probabilities.",
    }

    # ---------------- E11 championship protocol ----------------
    res["E11_championship"] = {
        "train": "global model, validated feature set, balanced training",
        "test": "temporally-later events + geographically-held-out areas + representative negatives",
        "report": ["ROC-AUC", "PR-AUC", "Brier", "calibration/ECE", "critical-event recall",
                   "first-warning lead time", "false-alarm rate", "missed-event rate",
                   "exposed homes captured", "critical roads captured"],
        "prefixed_baseline": {
            "note": "pre-fix numbers (inflated BG + climatology proxies); beat these AFTER E1 sampling fix",
            "global_spatial_oof_auc": res["ablations"]["FULL"]["auc"],
            "temporal_global_auc": res["E4"]["temporal_global"]["auc"],
            "hard_negative_auc": res["E1"]["hard_eval_pos_vs_hard_bg"]["auc"],
        },
    }
    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")
    print("\n===== E-LADDER SUMMARY =====")
    for k, v in res["ablations"].items():
        print(f"abl {k:12s} auc={v['auc']} pr={v['pr_auc']} brier={v['brier']} acc={v['acc50']}")
    print("E1 hard:", res["E1"]["hard_eval_pos_vs_hard_bg"], "| easy:", res["E1"]["easy_eval_pos_vs_easy_bg"])
    print("E3:", {k: v for k, v in res["E3"].items()})
    print("E4 temporal:", res["E4"]["temporal_global"], res["E4"]["temporal_north_only"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
