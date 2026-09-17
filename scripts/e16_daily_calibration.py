"""E16: daily-regime calibration + cleaned Tier-1 redo (SIH26001).

Daily population: exact-date event days (label 1, fuzzy excluded from fit) +
Tier-B background days (label 0, identical seed/construction as E15 replay).
Fit isotonic AND Platt (pre-registered stable candidate at tiny-n); compare by
leave-one-event-out. Tier-1 redo: soil backfill via v09.2 dailies where files
exist + seismic ref=event-year recompute. Tier-B burden redo. No architecture gate.
Outputs: runs/e16.json. Run: mnemo-venv python scripts/e16_daily_calibration.py
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
OUT = REPO / "runs" / "e16.json"

SEED = 42
LAT_SPLIT = 27.15
CAP_YEARS = 60

EXACT = [  # exact-date positives only (fuzzy lumsay/sichey excluded from fit)
    {"id": "mangan-jun2024", "lat": 27.51, "lon": 88.53, "date": "2024-06-13"},
    {"id": "dipudara-0820", "lat": 27.2525, "lon": 88.4606, "date": "2024-08-20"},
    {"id": "dipudara-0821", "lat": 27.2525, "lon": 88.4606, "date": "2024-08-21"},
    {"id": "nh10-oct2022", "lat": 27.13, "lon": 88.51, "date": "2022-10-09"},
]
TIER1_CLEAN = [  # Tier-1 redo set (incl. fuzzy, flagged)
    {"id": "mangan-jun2024", "lat": 27.51, "lon": 88.53, "date": "2024-06-13", "fuzzy": False},
    {"id": "dipudara-aug2024", "lat": 27.2525, "lon": 88.4606, "date": "2024-08-20", "fuzzy": False},
    {"id": "lumsay-jun2022", "lat": 27.32633333, "lon": 88.59544444, "date": "2022-06-30", "fuzzy": True},
    {"id": "sichey-jun2021", "lat": 27.33787, "lon": 88.609377, "date": "2021-06-08", "fuzzy": True},
    {"id": "nh10-oct2022", "lat": 27.13, "lon": 88.51, "date": "2022-10-09", "fuzzy": False},
]


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


RAIN_CACHE: dict = {}


def imd_window(year, lat0, lon0, d0, d1):
    import xarray as xr
    key = (year, round(lat0, 2), round(lon0, 2), d0, d1)
    if key not in RAIN_CACHE:
        ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{year}_rfp25.nc"))
        s = ds.RAINFALL.sel(LATITUDE=lat0, LONGITUDE=lon0, method="nearest")
        vals = pd.Series(np.asarray(s.sel(TIME=slice(d0, d1)).values, dtype=float),
                         index=pd.to_datetime(s.sel(TIME=slice(d0, d1)).TIME.values))
        RAIN_CACHE[key] = vals.fillna(0.0)
        ds.close()
    return RAIN_CACHE[key]


def soil_trailing(lat0, lon0, day: str):
    """v09.2 trailing-7d mean ending `day` (kill-bit masked); None if files missing."""
    import event_soil_upgrade as ES
    import xarray as xr
    end = pd.Timestamp(day)
    dates = [(end - pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    files = ES.day_files(end.year, dates)
    if not files:
        return None
    stack, alat, alon = [], None, None
    for fp in files:
        with xr.open_dataset(fp) as ds:
            sm = ds["sm"].sel(lat=slice(27.999, 27.00), lon=slice(88.06, 88.96)).to_numpy().astype(float).squeeze()
            fl = ds["flag"].sel(lat=slice(27.999, 27.00), lon=slice(88.06, 88.96)).to_numpy().squeeze()
            with np.errstate(invalid="ignore"):
                m = (fl.astype(float).astype(int) & ES.KILL) == 0
            stack.append(np.where(m, sm, np.nan))
            if alat is None:
                alat = ds["lat"].sel(lat=slice(27.999, 27.00)).to_numpy()
                alon = ds["lon"].sel(lon=slice(88.06, 88.96)).to_numpy()
    ri = int(np.clip(np.searchsorted(alat, lat0), 0, len(alat) - 1))
    ci = int(np.clip(np.searchsorted(alon, lon0), 0, len(alon) - 1))
    v = float(np.nanmean(np.array(stack)[:, ri, ci]))
    if np.isnan(v):
        v = float(np.nanmean(np.array(stack)[:, max(0, ri - 1):ri + 2, max(0, ci - 1):ci + 2]))
    return None if np.isnan(v) else round(float(np.clip(v, 0, 1)), 4)


def seismic_for(lat0, lon0, ref_year: int):
    quakes = json.loads((REPO / "data/sih26001/evidence/usgs_quakes.json").read_text(encoding="utf-8"))["events"]
    qlat = np.array([q["lat"] for q in quakes])
    qlon = np.array([q["lon"] for q in quakes])
    qyr = np.array([q["year"] for q in quakes])
    p1 = np.radians([lat0])
    d = 2 * 6371.0 * np.arcsin(np.sqrt(
        np.sin(np.radians(qlat - lat0) / 2) ** 2 + np.cos(p1[0]) * np.cos(np.radians(qlat))
        * np.sin(np.radians(qlon - lon0) / 2) ** 2))
    dist = round(float(d.min()), 2)
    hit = (qyr < ref_year) & (d <= 50.0)
    n50 = int(hit.sum())
    since = int(min(ref_year - int(qyr[hit].max()), CAP_YEARS)) if hit.any() else CAP_YEARS
    rate = round(n50 / max(ref_year - 1965, 1), 4)
    return dist, n50, rate, since


def main() -> int:
    t0 = time.time()
    import joblib
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    import counterfactual_past_events as CPE
    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]
    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    y_all = mat["event"].to_numpy().astype(int)
    dyn = json.loads((REPO / "data/sih26001/processed/counterfactual_dynamic.json").read_text())["cases"]

    def score_feat(feat: dict) -> float:
        f2 = dict(feat)
        f2.setdefault("recent_disturbance", 0.0)
        return float(model.predict_proba(enc.transform(pd.DataFrame([f2])))[0, 1])

    def daily_row(base, lat0, lon0, day: str, ref_year: int, soil_override=True):
        w = imd_window(int(day[:4]), lat0, lon0,
                       (pd.Timestamp(day) - pd.Timedelta(days=45)).strftime("%Y-%m-%d"), day)
        sw = w.loc[:day]
        feat = {k: base[k] for k in CPE.NUMERIC if k != "spi_log"}
        feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
        sm = soil_trailing(lat0, lon0, day) if soil_override else None
        feat.update({"rainfall_24h_mm": round(float(sw.iloc[-1]), 1),
                     "rainfall_7d_mm": round(float(sw.iloc[-7:].sum()), 1),
                     "rainfall_30d_mm": round(float(sw.iloc[-30:].sum()), 1),
                     "soil_moisture": sm if sm is not None else base["soil_moisture"],
                     "lulc": base["lulc"], "recent_disturbance": 0.0})
        dist, n50, rate, since = seismic_for(lat0, lon0, ref_year)
        feat.update({"seismic_dist_km": dist, "seismic_n50_rate": rate, "seismic_years_since": since})
        return feat, {"soil_backfilled": sm is not None}

    res: dict = {"exact_positives": len(EXACT)}

    # ---- daily calibration population ----
    pos_rows, pos_meta = [], []
    for e in EXACT:
        j, _ = CPE.nearest_row(e["lat"], e["lon"], mat, side)
        base = mat.iloc[j]
        feat, _ = daily_row(base, e["lat"], e["lon"], e["date"], int(e["date"][:4]))
        pos_rows.append((score_feat(feat), e["id"]))
    # background: identical Tier-B construction (seed 42, 30 S + 30 N, matched years)
    rng = np.random.default_rng(SEED)
    bg_idx = np.where(y_all == 0)[0]
    lat_all = side["lat"].to_numpy()
    s_bg = bg_idx[lat_all[bg_idx] < LAT_SPLIT]
    n_bg = bg_idx[lat_all[bg_idx] >= LAT_SPLIT]
    pick = np.concatenate([rng.choice(s_bg, 30, replace=False), rng.choice(n_bg, 30, replace=False)])
    pool_years = sorted(int(v) for v in np.unique(side.loc[(y_all == 1) & (side["year"] > 0), "year"].tolist())
                        if 1901 <= int(v) <= 2024 and (REPO / f"data/raw/imd/ind{int(v)}_rfp25.nc").exists())
    neg_rows = []
    for i in pick:
        la, lo = float(side["lat"].iloc[i]), float(side["lon"].iloc[i])
        yr = int(rng.choice(pool_years))
        d0 = pd.Timestamp(f"{yr}-07-01")
        base = mat.iloc[i]
        for day in pd.date_range(d0, d0 + pd.Timedelta(days=30), freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            w = imd_window(yr, la, lo, (d0 - pd.Timedelta(days=45)).strftime("%Y-%m-%d"), ds_)
            sw = w.loc[:ds_]
            feat = {k: base[k] for k in CPE.NUMERIC if k != "spi_log"}
            feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
            feat.update({"rainfall_24h_mm": round(float(sw.iloc[-1]), 1),
                         "rainfall_7d_mm": round(float(sw.iloc[-7:].sum()), 1),
                         "rainfall_30d_mm": round(float(sw.iloc[-30:].sum()), 1),
                         "lulc": base["lulc"], "recent_disturbance": 0.0})
            neg_rows.append(score_feat(feat))
    yp = np.ones(len(pos_rows), dtype=int)
    yn = np.zeros(len(neg_rows), dtype=int)
    pp = np.array([p for p, _ in pos_rows])
    pn = np.array(neg_rows)
    log(f"daily cal population: {len(pp)} exact positives, {len(pn)} background days")
    res["n_pos_exact"] = int(len(pp))
    res["n_neg_days"] = int(len(pn))

    # ---- leave-one-event-out: iso vs Platt vs raw ----
    from collections import defaultdict
    ev_ids = sorted(set(e for _, e in pos_rows))
    loo = {"iso": [], "platt": [], "raw": []}
    for ev in ev_ids:
        tr_mask = np.array([e != ev for _, e in pos_rows])
        p_tr = np.concatenate([pp[tr_mask], pn])
        y_tr = np.concatenate([yp[tr_mask], yn])
        p_te = np.concatenate([pp[~tr_mask], pn])
        y_te = np.concatenate([yp[~tr_mask], yn])
        iso = IsotonicRegression(out_of_bounds="clip").fit(p_tr, y_tr)
        pl = LogisticRegression(C=1.0, max_iter=5000).fit(p_tr.reshape(-1, 1), y_tr)
        for k, f in (("iso", iso.predict), ("platt", lambda v: pl.predict_proba(v.reshape(-1, 1))[:, 1])):
            loo[k].append((brier(y_te, f(p_te)), ece(y_te, f(p_te))))
        loo["raw"].append((brier(y_te, p_te), ece(y_te, p_te)))
    res["loo"] = {k: {"brier_mean": round(float(np.mean([b for b, _ in v])), 4),
                      "ece_mean": round(float(np.mean([e for _, e in v])), 4)} for k, v in loo.items()}
    log(f"LOO-event: {res['loo']}")

    # ---- final daily calibrators on all daily data ----
    p_all = np.concatenate([pp, pn])
    y_cal = np.concatenate([yp, yn])
    iso_f = IsotonicRegression(out_of_bounds="clip").fit(p_all, y_cal)
    platt_f = LogisticRegression(C=1.0, max_iter=5000).fit(p_all.reshape(-1, 1), y_cal)
    res["calibrators"] = {
        "iso": {"x": [round(float(v), 4) for v in iso_f.X_thresholds_],
                "y": [round(float(v), 4) for v in iso_f.f_(iso_f.X_thresholds_)]},
        "platt_coef": [round(float(v), 4) for v in platt_f.coef_.ravel().tolist()],
        "platt_intercept": round(float(platt_f.intercept_[0]), 4)}

    # ---- Tier-1 redo, cleaned (soil backfill + seismic ref=event year) ----
    res["tier1"] = []
    for c in TIER1_CLEAN:
        j, dist_m = CPE.nearest_row(c["lat"], c["lon"], mat, side)
        base = mat.iloc[j]
        D = pd.Timestamp(c["date"])
        traj = []
        for day in pd.date_range(D - pd.Timedelta(days=30), D, freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            feat, _ = daily_row(base, c["lat"], c["lon"], ds_, int(c["date"][:4]))
            pr = score_feat(feat)
            traj.append({"date": ds_, "p_raw": round(pr, 4),
                         "p_iso": round(float(iso_f.predict([pr])[0]), 4),
                         "p_platt": round(float(platt_f.predict_proba([[pr]])[0, 1]), 4)})
        peak = max(traj, key=lambda t: t["p_iso"])
        res["tier1"].append({"id": c["id"], "date": c["date"], "fuzzy": c["fuzzy"],
                             "analogue_dist_m": dist_m,
                             "peak_iso": peak["p_iso"], "peak_date": peak["date"],
                             "event_day_iso": traj[-1]["p_iso"],
                             "trajectory": traj})
        log(f"T1 {c['id']}: peak_iso {peak['p_iso']} on {peak['date']} (event {traj[-1]['p_iso']})")

    # ---- Tier-B burden redo under daily iso ----
    hot_iso = hot_platt = 0
    hot_days_iso = []
    for i in pick:
        la, lo = float(side["lat"].iloc[i]), float(side["lon"].iloc[i])
        yr = int(rng.choice(pool_years))  # NOTE: fresh draws continue the stream (documented)
        d0 = pd.Timestamp(f"{yr}-07-01")
        base = mat.iloc[i]
        hd = 0
        for day in pd.date_range(d0, d0 + pd.Timedelta(days=30), freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            w = imd_window(yr, la, lo, (d0 - pd.Timedelta(days=45)).strftime("%Y-%m-%d"), ds_)
            sw = w.loc[:ds_]
            feat = {k: base[k] for k in CPE.NUMERIC if k != "spi_log"}
            feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
            feat.update({"rainfall_24h_mm": round(float(sw.iloc[-1]), 1),
                         "rainfall_7d_mm": round(float(sw.iloc[-7:].sum()), 1),
                         "rainfall_30d_mm": round(float(sw.iloc[-30:].sum()), 1),
                         "lulc": base["lulc"], "recent_disturbance": 0.0})
            pr = score_feat(feat)
            if float(iso_f.predict([pr])[0]) >= 0.5:
                hd += 1
        hot_days_iso.append(hd)
        if hd > 0:
            hot_iso += 1
    res["tierB_redo"] = {"windows": len(pick), "frac_any_hot_iso05": round(hot_iso / len(pick), 3),
                         "mean_hot_days": round(float(np.mean(hot_days_iso)), 1)}
    log(f"Tier-B redo: {hot_iso}/{len(pick)} windows any-hot(iso>=0.5), mean {res['tierB_redo']['mean_hot_days']}")

    res["minutes"] = round((time.time() - t0) / 60, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} in {res['minutes']} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
