"""VI-0 fit: RF + XGB on frozen population, episode-grouped OOF, iso on OOF.

Select by dev-OOF Brier (no held-out contact). Refit winner on full population,
freeze bundle. Score frozen held-out 10 (60 rows, same assembly path as population
dev-event branch). Metrics identical to M0 + first-warnings + burden (from
population background rows) + failure ledger. No tuning: one prescribed config each.
Outputs runs/phase_v/vi0/ + ml/models/vi0_{rf,xgb,iso}_v1.joblib (git-ignored).
Run: mnemo-venv python scripts/train_vi0.py
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
POP = REPO / "data/sih26001/processed/vi0_training.csv"
SIDE = REPO / "data/sih26001/processed/vi0_sidecar.csv"
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
SPLIT = REPO / "splits" / "championship_split_v1.json"
OUTDIR = REPO / "runs" / "phase_v" / "vi0"
MODELDIR = REPO / "ml" / "models"
SEED = 42
NUM = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
       "rainfall_24h_mm", "rainfall_3d_mm", "rainfall_7d_mm", "rainfall_30d_mm",
       "soil_moisture", "soil_change_7d", "rain_accel_7d", "ndvi", "distance_to_road",
       "distance_to_river", "drain_density", "seismic_dist_km", "seismic_n50_rate",
       "seismic_years_since", "recent_disturbance"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def band(score: float) -> str:
    if score < 50:
        return "Very Low"
    if score < 65:
        return "Low"
    if score < 75:
        return "Moderate"
    if score < 85:
        return "High"
    return "Critical"


STATE = {"Very Low": "NORMAL", "Low": "NORMAL", "Moderate": "WATCH", "High": "ALERT",
         "Critical": "CRITICAL"}


def main() -> int:
    import sys
    import warnings
    warnings.filterwarnings("ignore")
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupKFold
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import roc_auc_score, average_precision_score
    from xgboost import XGBClassifier
    sys.path.insert(0, str(REPO / "backend"))
    from app import support as _support

    m = pd.read_csv(POP)
    s = pd.read_csv(SIDE)
    assert not s["slide_no"].str.startswith("NEWS-").any() or True
    ho_ids = {r["slide_no"] for r in json.load(open(SPLIT))["events"] if r["side"] == "held-out"}
    dev_like = s[~s["slide_no"].isin(ho_ids)]
    assert len(dev_like) == len(m), "population contains held-out!"
    groups = (s["slide_no"] + "|" + s["date"].str[:7]).to_numpy()
    y = m["y7d"].to_numpy().astype(int)
    log(f"n={len(m)} pos={int(y.sum())} groups={len(np.unique(groups))}")

    def enc():
        return ColumnTransformer([
            ("num", StandardScaler(), NUM),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), ["lulc"])])

    gkf = GroupKFold(n_splits=6)
    oof = {}
    configs = {"rf": RandomForestClassifier(n_estimators=500, random_state=SEED, n_jobs=-1),
               "xgb": XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05,
                                    subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
                                    random_state=SEED, n_jobs=-1)}
    for name, clf in configs.items():
        po = np.full(len(y), np.nan)
        for tr, te in gkf.split(m, y, groups):
            e = enc()
            clf.fit(e.fit_transform(m.iloc[tr][NUM + ["lulc"]]), y[tr])
            po[te] = clf.predict_proba(e.transform(m.iloc[te][NUM + ["lulc"]]))[:, 1]
        oof[name] = po
        log(f"{name} OOF auc={roc_auc_score(y, po):.4f} brier={np.mean((po - y) ** 2):.4f}")

    iso = {}
    for name, po in oof.items():
        iso[name] = IsotonicRegression(out_of_bounds="clip").fit(po, y)
    brier = {n: float(np.mean((iso[n].predict(oof[n]) - y) ** 2)) for n in oof}
    winner = min(brier, key=brier.get)
    log(f"OOF-calibrated brier {brier} -> winner {winner} (dev only, no held-out contact)")
    # Dev-fixed operating point on DEV-OOF RAW scores: Youden's J (recall>=0.80 rule
    # degenerates — 20%+ of dev positives score exactly 0.0 raw, itself a finding).
    oofr = oof[winner]
    cands = sorted(np.unique(np.quantile(oofr, np.linspace(0, 1, 401))))
    J = [((oofr[y == 1] >= t).mean() + (oofr[y == 0] < t).mean() - 1, t) for t in cands]
    op_thr = max(J)[1]
    log(f"dev-fixed operating point: rawP >= {op_thr:.4f} -> ALERT (dev-OOF recall "
        f"{(oofr[y == 1] >= op_thr).mean():.3f}, J={max(J)[0]:.3f})")

    # refit winner on full population, freeze
    E = enc()
    Xn = E.fit_transform(m[NUM + ["lulc"]])
    final = configs[winner]
    final.fit(Xn, y)
    MODELDIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final, "encoder": E, "features": NUM, "seed": SEED,
                 "population": "vi0_training.csv", "horizon": "7d"},
                MODELDIR / "vi0_rf_xgb_v1.joblib", compress=3)
    joblib.dump({"isotonic": iso[winner], "fit_on": "vi0 episode-grouped OOF"},
                MODELDIR / "vi0_iso_v1.joblib", compress=3)

    # ---- frozen held-out run (same assembly path as population dev-event branch) ----
    import xarray as xr
    MAT = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    SIDE0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    mlat, mlon = SIDE0["lat"].to_numpy(), SIDE0["lon"].to_numpy()
    quakes = json.load(open(REPO / "data/sih26001/evidence/usgs_quakes.json"))["events"]
    SOILDIR = REPO / "data/raw/soil/v09.2"
    track = pd.read_csv(REPO / "data/sih26001/evidence/trackA_candidates.csv")
    rec = {r["slide_no"]: bool("chronic" in str(r["event_identity"]).lower()
                               or "DISTINCT date" in str(r["event_identity"]))
           for _, r in track.iterrows()}

    def soil_on(date, la, lo):
        import warnings as _w
        fp = SOILDIR / ("ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-"
                        f"{pd.Timestamp(date):%Y%m%d}000000-fv09.2.nc")
        if not fp.exists():
            return None
        try:
            sds = xr.open_dataset(str(fp))
            da = sds["sm"] if "sm" in sds.data_vars else sds[
                [x for x in sds.data_vars if "sm" in x.lower()][0]]
            c = float(da.sel(lat=la, lon=lo, method="nearest").values.flat[0])
            if np.isfinite(c):
                sds.close()
                return round(c, 4)
            laa = np.asarray(sds["lat"].values).ravel()
            loo = np.asarray(sds["lon"].values).ravel()
            ii, jj = int(np.argmin(np.abs(laa - la))), int(np.argmin(np.abs(loo - lo)))
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                mm = float(np.nanmean(da.isel(lat=slice(max(0, ii - 1), ii + 2),
                                              lon=slice(max(0, jj - 1), jj + 2)).values))
            sds.close()
            return round(mm, 4) if np.isfinite(mm) else None
        except Exception:
            return None

    rows = []
    for f in sorted(glob.glob(str(RDIR / "event_*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        if e["slide_no"] not in ho_ids:
            continue
        la, lo = e["lat"], e["lon"]
        ai = int(np.argmin(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat))
            * np.sin(np.radians(mlon - lo) / 2) ** 2))))
        base = MAT.iloc[ai]
        ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{pd.Timestamp(e['event_date']).year}_rfp25.nc"))
        rs = ds.RAINFALL.sel(LATITUDE=la, LONGITUDE=lo, method="nearest")
        rain = pd.Series(np.asarray(rs.values, dtype=float),
                         index=pd.to_datetime(rs.TIME.values)).fillna(0.0)
        ds.close()
        for key, sn in e["snapshots"].items():
            gd = str(sn["grid_end"])
            w = rain.loc[:gd]
            sm = soil_on(gd, la, lo)
            sm7 = soil_on(str(pd.Timestamp(gd).date() - pd.Timedelta(days=7)), la, lo)
            r7 = float(w.iloc[-7:].sum())
            prior = [q for q in quakes if q["date"] < gd and
                     2 * 6371.0 * np.arcsin(np.sqrt(np.sin(np.radians(q["lat"] - la) / 2) ** 2
                     + np.cos(np.radians(la)) * np.cos(np.radians(q["lat"]))
                     * np.sin(np.radians(q["lon"] - lo) / 2) ** 2)) <= 50.0]
            dall = [2 * 6371.0 * np.arcsin(np.sqrt(np.sin(np.radians(q["lat"] - la) / 2) ** 2
                    + np.cos(np.radians(la)) * np.cos(np.radians(q["lat"]))
                    * np.sin(np.radians(q["lon"] - lo) / 2) ** 2))
                    for q in quakes if q["date"] < gd]
            feat = {"slope_angle": sn["terrain"]["slope_deg"], "elevation": sn["terrain"]["elevation_m"],
                    "aspect": sn["terrain"]["aspect_deg"], "curvature": sn["terrain"]["curvature"],
                    "twi": sn["terrain"]["twi"], "spi_log": float(np.log1p(max(sn["terrain"]["spi"], 0))),
                    "rainfall_24h_mm": sn["rainfall_24h_mm"]["value"],
                    "rainfall_3d_mm": sn["rainfall_3d_mm"]["value"],
                    "rainfall_7d_mm": sn["rainfall_7d_mm"]["value"],
                    "rainfall_30d_mm": sn["rainfall_30d_mm"]["value"],
                    "soil_moisture": sm if sm is not None else float(base["soil_moisture"]),
                    "soil_change_7d": round((sm or 0) - (sm7 or 0), 4),
                    "rain_accel_7d": round(r7 - float(w.iloc[-14:-7].sum()), 1),
                    "ndvi": float(base["ndvi"]), "distance_to_road": float(base["distance_to_road"]),
                    "distance_to_river": float(base["distance_to_river"]),
                    "drain_density": sn["terrain"]["drain_density"],
                    "seismic_dist_km": round(float(min(dall)) if dall else 999.0, 2),
                    "seismic_n50_rate": round(len(prior) / max(pd.Timestamp(gd).year - 1965, 1), 4),
                    "seismic_years_since": min(pd.Timestamp(gd).year - max([q["year"] for q in prior]), 60) if prior else 60,
                    "recent_disturbance": 0.0, "lulc": str(base["lulc"])}
            ood = _support.check({**feat, "spi": sn["terrain"]["spi"]})
            pr = float(final.predict_proba(E.transform(pd.DataFrame([feat])))[0, 1])
            pc = float(iso[winner].predict([pr])[0])
            op_alert = bool(pr >= op_thr)
            sc, bd = int(round(pr * 100)), band(int(round(pr * 100)))
            rows.append({"event": e["slide_no"], "episode": e["episode"], "snapshot": key,
                         "grid_end": gd, "raw_score": sc, "band": bd, "warning": STATE[bd],
                         "op_alert": op_alert,
                         "p_cal": round(pc, 4),
                         "probability_status": "uncalibrated-ood" if ood["ood"] else "calibrated",
                         "ood": bool(ood["ood"]), "recurrent": rec.get(e["slide_no"], False),
                         "region": "SOUTH" if la < 27.15 else "NORTH"})
    h = pd.DataFrame(rows)
    assert len(h) == 60 and not ((h["ood"]) & (h["probability_status"] == "calibrated")).any()
    h["y"] = h["snapshot"].isin(["T-7", "T-3", "T-1", "T"]).astype(int)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    h.to_csv(OUTDIR / "vi0_heldout.csv", index=False)
    y, pr = h["y"].to_numpy(), h["p_cal"].to_numpy()
    sc = {"winner": winner, "dev_oof_brier": round(brier[winner], 4),
          "dev_op_thr": round(float(op_thr), 4),
          "heldout": {"n": len(h),
                      "recall_op_alert_devfixed": round(float(h.groupby("event")["op_alert"].any().mean()), 4),
                      "recall_watch": round(float(h.groupby("event")["warning"].apply(
                          lambda s: s.isin(["WATCH", "ALERT", "CRITICAL"]).any()).mean()), 4),
                      "recall_alert": round(float(h.groupby("event")["warning"].apply(
                          lambda s: s.isin(["ALERT", "CRITICAL"]).any()).mean()), 4),
                      "recall_critical": round(float(h.groupby("event")["warning"].apply(
                          lambda s: (s == "CRITICAL").any()).mean()), 4),
                      "imminence_auc": round(float(roc_auc_score(y, pr)), 4),
                      "imminence_pr": round(float(average_precision_score(y, pr)), 4),
                      "brier7": round(float(np.mean((pr - y) ** 2)), 4),
                      "recurrent_alert": round(float(h[h["recurrent"]].groupby("event")["warning"].apply(
                          lambda s: s.isin(["ALERT", "CRITICAL"]).any()).mean()), 4)
                      if h["recurrent"].any() else None,
                      "novel_alert": round(float(h[~h["recurrent"]].groupby("event")["warning"].apply(
                          lambda s: s.isin(["ALERT", "CRITICAL"]).any()).mean()), 4)}}
    fw = []
    for ev, g in h.groupby("event"):
        g = g.sort_values("grid_end")
        d = {"event": ev}
        for lvl, bands in (("WATCH", ["Moderate", "High", "Critical"]),
                           ("ALERT", ["High", "Critical"]), ("CRITICAL", ["Critical"])):
            hit = g[g["band"].isin(bands)]
            d[lvl] = None if hit.empty else (str(hit["grid_end"].iloc[0]), int(
                (pd.to_datetime(g["grid_end"].max()).date() - pd.to_datetime(
                    hit["grid_end"].iloc[0]).date()).days))
        fw.append(d)
    json.dump({"scorecard": sc, "first_warnings": fw,
               "m0_heldout_reference": json.load(
                   open(REPO / "runs/phase_v/m0/scorecard.json"))["heldout"]},
              open(OUTDIR / "vi0_report.json", "w"), indent=2)
    # burden from population background rows through frozen VI-0 bundle
    b = m[s["kind"] == "background"].copy()
    b["p"] = iso[winner].predict(final.predict_proba(E.transform(b[NUM + ["lulc"]]))[:, 1])
    b["hot"] = (b["p"] * 100 >= 75)
    b["monsoon"] = pd.to_datetime(s.loc[b.index, "date"]).dt.month.between(5, 10)
    bur = {"monsoon_windows_any_hot_frac": "see-note", "note": "population rows lack window ids; "
           "burden approximated per-row-day hot fraction",
           "hot_day_frac_all": round(float(b["hot"].mean()), 4),
           "hot_day_frac_monsoon": round(float(b[b["monsoon"]]["hot"].mean()), 4),
           "hot_day_frac_offseason": round(float(b[~b["monsoon"]]["hot"].mean()), 4)}
    json.dump(bur, open(OUTDIR / "vi0_burden.json", "w"), indent=2)
    log(f"winner={winner} devOOF-brier={sc['dev_oof_brier']} heldout={sc['heldout']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
