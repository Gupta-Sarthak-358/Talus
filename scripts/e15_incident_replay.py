"""E15: historical incident replay through the frozen pipeline (SIH26001).

Frozen: prod RF weights + E13-protocol regional isotonic (refit deterministically,
seed 42) + policy cutoffs derived once on calib (WATCH recall>=0.95, ALERT R80,
CRITICAL precision>=0.80 else 0.80 fallback, recorded).
Tier-1: 5 dated cases, daily T-30..T, full trajectories + cards (inputs <=T only).
Tier-2: 746 dated positives, event-year point, IN-SAMPLE labeled, recall only.
Tier-B: 60 background windows x 31 monsoon days, burden metrics.
No training of new models, no threshold tuning on test. Outputs: runs/e15_incidents.json.
Run: mnemo-venv python scripts/e15_incident_replay.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "runs" / "e15_incidents.json"

SEED = 42
LAT_SPLIT = 27.15
GRID = np.round(np.arange(0.05, 0.96, 0.05), 2)


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


def main() -> int:
    t0 = time.time()
    import joblib
    from sklearn.isotonic import IsotonicRegression
    import counterfactual_past_events as CPE

    # ---- frozen pool (E13 construction) ----
    m0 = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    s0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    exm, exs = [], []
    for tag in ("e15", "e15c"):
        mm = pd.read_csv(REPO / "data/sih26001/processed" / f"{tag}_negatives.csv")
        ss = pd.read_csv(REPO / "data/sih26001/processed" / f"{tag}_sidecar.csv")
        keep = (mm["distance_to_road"] < 1000).to_numpy()
        exm.append(mm[keep])
        exs.append(ss[keep])
    mat = pd.concat([m0] + exm, ignore_index=True)
    side = pd.concat([s0] + exs, ignore_index=True)
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    coords = side[["lat", "lon"]].to_numpy()
    lat = side["lat"].to_numpy()
    district = side["district"].to_numpy()
    south = ((side["district"] == "Darjeeling").to_numpy()
             | ((district == "background") & (lat < LAT_SPLIT)))

    # ---- prod weights (frozen) + deterministic regional refit ----
    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]
    prod_iso = joblib.load(REPO / "ml/models/sih26001_iso_v1.joblib")["isotonic"]

    def band_of(score: float) -> str:
        if score < 50:
            return "Very Low"
        if score < 65:
            return "Low"
        if score < 75:
            return "Moderate"
        if score < 85:
            return "High"
        return "Critical"

    BAND_STATE = {"Very Low": "NORMAL", "Low": "NORMAL", "Moderate": "WATCH",
                  "High": "ALERT", "Critical": "CRITICAL"}
    try:
        feat_names = [n.split("__")[-1] for n in enc.get_feature_names_out()]
    except Exception:
        feat_names = None

    def score_raw(df: pd.DataFrame) -> np.ndarray:
        # encoder schema: training-time feature order; recent_disturbance=0 const (E8)
        full = df.copy()
        if "recent_disturbance" not in full.columns:
            full["recent_disturbance"] = 0.0
        return model.predict_proba(enc.transform(full))[:, 1]

    # Regional calibrators fit on FULL corrected pool per region (mirrors prod iso
    # construction on full data; maximises calibration support vs E13's thin slices).
    # Caveat: Tier-2 rows are in this fit (in-sample, labeled); Tier-1 cases are new
    # daily rows (analogues in-pool, flagged leakage).
    s_idx = np.where(south)[0]
    n_idx = np.where(~south)[0]
    p_s = score_raw(X.iloc[s_idx])
    p_n = score_raw(X.iloc[n_idx])
    iso_s = IsotonicRegression(out_of_bounds="clip").fit(p_s, y[s_idx])
    iso_n = IsotonicRegression(out_of_bounds="clip").fit(p_n, y[n_idx])
    log(f"regional iso on full pool (S n={len(s_idx)}, N n={len(n_idx)})")

    # ---- policy cutoffs derived once on the same pool ----
    def cutoffs(p_cal, yc):
        w = next((float(t) for t in GRID[::-1] if (p_cal >= t)[yc == 1].mean() >= 0.95), 0.05)
        a = next((float(t) for t in GRID[::-1] if (p_cal >= t)[yc == 1].mean() >= 0.80), 0.05)
        prec = [(float(t), (yc[p_cal >= t] == 1).mean() if (p_cal >= t).any() else 0.0) for t in GRID[::-1]]
        c = next((t for t, pr in prec if pr >= 0.80), None)
        return {"WATCH": w, "ALERT": a,
                "CRITICAL": round(c, 2) if c is not None else 0.80,
                "crit_fallback": c is None}
    pol = {"SOUTH": cutoffs(iso_s.predict(p_s), y[s_idx]),
           "NORTH": cutoffs(iso_n.predict(p_n), y[n_idx])}
    log(f"policy cutoffs: {pol}")

    def state_of(p: float, region: str) -> str:
        c = pol[region]
        if p >= c["CRITICAL"]:
            return "CRITICAL"
        if p >= c["ALERT"]:
            return "ALERT"
        if p >= c["WATCH"]:
            return "WATCH"
        return "NORMAL"

    res: dict = {"policy": pol, "tier1": [], "tier2": {}, "tierB": {},
                 "calibrators": {
                     "south": {"x": [round(float(v), 4) for v in iso_s.X_thresholds_],
                               "y": [round(float(v), 4) for v in iso_s.f_(iso_s.X_thresholds_)]},
                     "north": {"x": [round(float(v), 4) for v in iso_n.X_thresholds_],
                               "y": [round(float(v), 4) for v in iso_n.f_(iso_n.X_thresholds_)]}}}

    # ---- Tier-1: daily trajectories (reuse audited per-day feature logic) ----
    dyn_fp = REPO / "data/sih26001/processed/counterfactual_dynamic.json"
    dyn = json.loads(dyn_fp.read_text())["cases"] if dyn_fp.exists() else {}
    rain_cache: dict = {}

    def imd_window(year, lat0, lon0, d0, d1):
        import xarray as xr
        key = (year, round(lat0, 2), round(lon0, 2))
        if key not in rain_cache:
            ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{year}_rfp25.nc"))
            s = ds.RAINFALL.sel(LATITUDE=lat0, LONGITUDE=lon0, method="nearest")
            vals = pd.Series(np.asarray(s.sel(TIME=slice(d0, d1)).values, dtype=float),
                             index=pd.to_datetime(s.sel(TIME=slice(d0, d1)).TIME.values))
            rain_cache[key] = (vals, (round(float(s.LATITUDE), 2), round(float(s.LONGITUDE), 2)))
            ds.close()
        return rain_cache[key]

    for c in CPE.CASES:
        lat0, lon0 = c["site"]
        D = pd.Timestamp(c["event_date"])
        region = "SOUTH" if lat0 < LAT_SPLIT else "NORTH"
        iso = iso_s if region == "SOUTH" else iso_n
        j, dist_m = CPE.nearest_row(lat0, lon0, mat, side)
        base = mat.iloc[j]
        rain, _ = imd_window(D.year, lat0, lon0,
                             (D - pd.Timedelta(days=45)).strftime("%Y-%m-%d"),
                             D.strftime("%Y-%m-%d"))
        rain = rain.fillna(0.0)
        dcase = dyn.get(c["id"], {})
        dsoil, dndvi = (dcase.get("soil") or {}), dcase.get("ndvi")
        traj = []
        for day in pd.date_range(D - pd.Timedelta(days=30), D, freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            assert ds_ <= c["event_date"], "future leak"
            w = rain.loc[:ds_]
            feat = {k: base[k] for k in CPE.NUMERIC if k != "spi_log"}
            feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
            feat.update({
                "rainfall_24h_mm": round(float(w.iloc[-1]), 1),
                "rainfall_7d_mm": round(float(w.iloc[-7:].sum()), 1),
                "rainfall_30d_mm": round(float(w.iloc[-30:].sum()), 1),
                "soil_moisture": dsoil.get(ds_, base["soil_moisture"]) if dsoil.get(ds_) is not None else base["soil_moisture"],
                "ndvi": dndvi if dndvi is not None else base["ndvi"],
                "lulc": base["lulc"], "recent_disturbance": 0.0})
            pr = float(model.predict_proba(enc.transform(pd.DataFrame([feat])))[0, 1])
            pc = float(iso.predict([pr])[0])
            p_prod = float(prod_iso.predict([pr])[0])
            score_prod = round(p_prod * 100, 1)
            band = band_of(score_prod)
            traj.append({"date": ds_, "p_raw": round(pr, 4), "p_cal": round(pc, 4),
                         "score_prod": score_prod, "band": band,
                         "state": BAND_STATE[band]})
        states = [t["state"] for t in traj]
        dates = [t["date"] for t in traj]
        first = {}
        for st in ("WATCH", "ALERT", "CRITICAL"):
            hit = next((d for d, s in zip(dates, states) if s == st or
                        (st == "WATCH" and s in ("WATCH", "ALERT", "CRITICAL")) or
                        (st == "ALERT" and s in ("ALERT", "CRITICAL"))), None)
            first[st] = hit
        peak = max(traj, key=lambda t: t["p_cal"])
        res["tier1"].append({
            "id": c["id"], "event_date": c["event_date"], "region": region,
            "analogue_row": base["zone_id"], "analogue_dist_m": dist_m,
            "fuzzy": bool(c.get("event_date_fuzzy")),
            "first": first,
            "lead": {k: ((D - pd.Timestamp(v)).days if v else None) for k, v in first.items()},
            "peak_p_cal": peak["p_cal"], "peak_date": peak["date"],
            "hot_days": int(sum(1 for s in states if s in ("ALERT", "CRITICAL"))),
            "trajectory": traj,
            "card": {"title": c["title"], "site": c["site_name"],
                     "states": " ".join(f"{t['date'][5:]}:{t['state'][0]}" for t in traj[::5])}})
        log(f"T1 {c['id']}: W {first['WATCH']} A {first['ALERT']} C {first['Critical'] if False else first['CRITICAL']}")

    # ---- Tier-2: all dated positives, event-year point, IN-SAMPLE ----
    dpos = np.where((y == 1) & (side["year"].to_numpy() > 0))[0]
    p_all = score_raw(X.iloc[dpos])
    regs = np.where(lat[dpos] < LAT_SPLIT, "SOUTH", "NORTH")
    pc_all = np.where(regs == "SOUTH", iso_s.predict(p_all), iso_n.predict(p_all))
    st_all = np.array([state_of(p, r) for p, r in zip(pc_all, regs)])
    order = ["WATCH", "ALERT", "CRITICAL"]
    res["tier2"] = {"n": int(len(dpos)), "in_sample": True,
                    "recall_at_state": {
                        s: round(float(np.isin(st_all, order[order.index(s):]).mean()), 4)
                        for s in order},
                    "by_region": {}}
    for r in ("SOUTH", "NORTH"):
        m = regs == r
        road_m = m & (mat["distance_to_road"].to_numpy()[dpos] < 200)
        res["tier2"]["by_region"][r] = {
            "n": int(m.sum()),
            "recall_at_state": {
                s: round(float(np.isin(st_all[m], order[order.index(s):]).mean()), 4)
                for s in order},
            "road_recall_alert": round(float(np.isin(st_all[road_m], ["ALERT", "CRITICAL"]).mean()), 4)
            if road_m.any() else None}
    log(f"T2 recall: {res['tier2']['recall_at_state']} by_region South/North ALERT="
        f"{res['tier2']['by_region']['SOUTH']['recall_at_state']['ALERT']}/"
        f"{res['tier2']['by_region']['NORTH']['recall_at_state']['ALERT']}")

    # ---- Tier-B: 60 background windows x 31 monsoon days ----
    rng = np.random.default_rng(SEED)
    bg = np.where(y == 0)[0]
    s_bg = bg[lat[bg] < LAT_SPLIT]
    n_bg = bg[lat[bg] >= LAT_SPLIT]
    pick = np.concatenate([rng.choice(s_bg, 30, replace=False), rng.choice(n_bg, 30, replace=False)])
    pool_years = sorted(int(v) for v in np.unique(side.loc[(y == 1) & (side["year"] > 0), "year"].tolist())
                        if 1901 <= int(v) <= 2024 and (REPO / f"data/raw/imd/ind{int(v)}_rfp25.nc").exists())
    burden = []
    for i in pick:
        la, lo = float(side["lat"].iloc[i]), float(side["lon"].iloc[i])
        yr = int(rng.choice(pool_years))
        d0 = pd.Timestamp(f"{yr}-07-01")
        rain, _ = imd_window(yr, la, lo, (d0 - pd.Timedelta(days=45)).strftime("%Y-%m-%d"),
                             (d0 + pd.Timedelta(days=30)).strftime("%Y-%m-%d"))
        rain = rain.fillna(0.0)
        base = mat.iloc[i]
        region = "SOUTH" if la < LAT_SPLIT else "NORTH"
        iso = iso_s if region == "SOUTH" else iso_n
        hot = 0
        top = None
        for day in pd.date_range(d0, d0 + pd.Timedelta(days=30), freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            w = rain.loc[:ds_]
            feat = {k: base[k] for k in CPE.NUMERIC if k != "spi_log"}
            feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
            feat.update({"rainfall_24h_mm": round(float(w.iloc[-1]), 1),
                         "rainfall_7d_mm": round(float(w.iloc[-7:].sum()), 1),
                         "rainfall_30d_mm": round(float(w.iloc[-30:].sum()), 1),
                         "lulc": base["lulc"], "recent_disturbance": 0.0})
            pr = float(model.predict_proba(enc.transform(pd.DataFrame([feat])))[0, 1])
            pc = float(iso.predict([pr])[0])
            p_prod = float(prod_iso.predict([pr])[0])
            st = BAND_STATE[band_of(round(p_prod * 100, 1))]
            if st in ("ALERT", "CRITICAL"):
                hot += 1
                top = st if top != "CRITICAL" else top
        burden.append({"zone": base["zone_id"], "region": region, "year": yr,
                       "hot_days": hot, "top": top or "calm"})
    hot_w = sum(1 for b in burden if b["hot_days"] > 0)
    res["tierB"] = {"windows": len(burden),
                    "frac_windows_any_alert": round(hot_w / len(burden), 3),
                    "mean_hot_days": round(float(np.mean([b["hot_days"] for b in burden])), 1),
                    "by_region": {r: {"frac": round(float(np.mean([b["hot_days"] > 0 for b in burden if b["region"] == r])), 3)}
                                  for r in ("SOUTH", "NORTH")}}
    log(f"Tier-B burden: {hot_w}/{len(burden)} windows any-alert, mean hot-days {res['tierB']['mean_hot_days']}")

    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
