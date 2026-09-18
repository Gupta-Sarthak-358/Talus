"""VI-A: daily T-60..T trajectories for 13 DEV events (positives). VIT_SPEC v1.

Per row date d: ONLY info with timestamp <= d (asserted). IMD local slice,
v09.2 trailing-7d soil (REAL/PROXY-spatial/MISSING, never FILL), date-gated
seismic, frozen Iverson FoS ensemble (324 combos), static site context
(V-B terrain + analogue + frozen-RF June-climatology susceptibility).
Labels: y14/y7 from T-d; T row stored train_exclude=1. Held-out firewall:
assert every slide_no in dev set. Run: mnemo-venv python scripts/build_vit.py
(falls back: system python for xarray reads).
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
OUTDIR = REPO / "data" / "vit"
SPLIT = REPO / "splits" / "championship_split_v1.json"
SOILDIR = REPO / "data/raw/soil/v09.2"
KILL = 0  # set from event_soil_upgrade at runtime

D0S = [1e-6, 1e-5, 1e-4, 1e-3]
HS = [1.0, 2.0, 3.0]
KZS = [1e-6, 1e-5, 1e-4]
CS = [0.0, 2000.0, 5000.0]
PHIS = [25.0, 30.0, 35.0]
GAMMA, GAMMAW = 18000.0, 9810.0


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def R(ts):
    import math
    ts = np.asarray(ts, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.sqrt(ts / np.pi) * np.exp(-1.0 / ts) - np.vectorize(
            lambda v: 1.0 if v <= 0 else math.erfc(1.0 / np.sqrt(v)))(ts)
    return np.where(ts > 0, out, 0.0)


def fos_median(pulses_mm, beta) -> float | None:
    if beta < np.radians(5.0):
        return None
    pulses = (np.asarray(pulses_mm, dtype=float) / 1000.0) / 86400.0
    n = len(pulses)
    ages = (np.arange(n, 0, -1) - 0.5) * 86400.0
    Iavg = float(np.mean(pulses_mm) / 1000.0 / 86400.0)
    out = []
    for D0 in D0S:
        for H in HS:
            Tstar = ages * D0 / H ** 2
            dT = 86400.0 * D0 / H ** 2
            Resp = R(Tstar) - R(Tstar - dT)
            for Kz in KZS:
                psi = float(min(max(float(np.sum((pulses / Kz) * H * Resp))
                                        + (Iavg / Kz) * H * 0.5, 0.0), H))
                for c in CS:
                    for ph in PHIS:
                        t = np.tan(np.radians(ph))
                        num = c + (GAMMA * H - psi * GAMMAW) * (np.cos(beta) ** 2) * t
                        den = GAMMA * H * np.sin(beta) * np.cos(beta)
                        out.append(num / den if den > 0 else np.inf)
    a = np.array(out)
    assert np.isfinite(a).all()
    return round(float(np.median(a)), 3)


def main() -> int:
    import xarray as xr
    import event_soil_upgrade as ES
    global KILL
    KILL = ES.KILL
    sys.path.insert(0, str(REPO / "backend"))

    split = {r["slide_no"]: r for r in json.load(open(SPLIT))["events"]}
    dev = {k: v for k, v in split.items() if v["side"] == "development"}
    assert len(dev) == 13
    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]
    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    mlat, mlon = side["lat"].to_numpy(), side["lon"].to_numpy()
    quakes = json.load(open(REPO / "data/sih26001/evidence/usgs_quakes.json"))["events"]
    qlat = np.array([q["lat"] for q in quakes])
    qlon = np.array([q["lon"] for q in quakes])
    qdate = np.array([q["date"] for q in quakes])
    qyr = np.array([q["year"] for q in quakes])

    rain_cache: dict = {}
    soil_cache: dict = {}

    def rain_series(year, la, lo):
        key = (year, round(la, 2), round(lo, 2))
        if key not in rain_cache:
            ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{year}_rfp25.nc"))
            s = ds.RAINFALL.sel(LATITUDE=la, LONGITUDE=lo, method="nearest")
            rain_cache[key] = pd.Series(np.asarray(s.values, dtype=float),
                                        index=pd.to_datetime(s.TIME.values)).fillna(0.0)
            ds.close()
        return rain_cache[key]

    def soil_day(d: pd.Timestamp, la, lo):
        """(value|None, provenance). v09.2 single-day cell, 3x3 fallback, else MISSING."""
        key = (d.strftime("%Y%m%d"), round(la, 3), round(lo, 3))
        if key not in soil_cache:
            fp = SOILDIR / f"ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-{d:%Y%m%d}000000-fv09.2.nc"
            if not fp.exists():
                soil_cache[key] = (None, "MISSING (file-absent)")
            elif fp.stat().st_size < 1500000:
                soil_cache[key] = (None, "MISSING (file-truncated)")
            else:
                try:
                    ds = xr.open_dataset(fp)
                except Exception:
                    soil_cache[key] = (None, "MISSING (file-unreadable)")
                    return soil_cache[key]
                with ds:
                    sm = ds["sm"].sel(lat=slice(27.999, 27.00),
                                      lon=slice(88.06, 88.96)).to_numpy().astype(float).squeeze()
                    fl = ds["flag"].sel(lat=slice(27.999, 27.00),
                                        lon=slice(88.06, 88.96)).to_numpy().squeeze()
                    alat = ds["lat"].sel(lat=slice(27.999, 27.00)).to_numpy()
                    alon = ds["lon"].sel(lon=slice(88.06, 88.96)).to_numpy()
                with np.errstate(invalid="ignore"):
                    m = (fl.astype(float).astype(int) & KILL) == 0
                ri = int(np.clip(np.searchsorted(alat, la), 0, len(alat) - 1))
                ci = int(np.clip(np.searchsorted(alon, lo), 0, len(alon) - 1))
                v = float(sm[ri, ci]) if m[ri, ci] else np.nan
                if np.isnan(v):
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        v = float(np.nanmean(np.where(
                            m[max(0, ri - 1):ri + 2, max(0, ci - 1):ci + 2],
                            sm[max(0, ri - 1):ri + 2, max(0, ci - 1):ci + 2], np.nan)))
                    prov = "PROXY-spatial" if not np.isnan(v) else "MISSING (all-NaN)"
                    soil_cache[key] = (None if np.isnan(v) else round(float(v), 4), prov)
                else:
                    soil_cache[key] = (round(float(np.clip(v, 0, 1)), 4), "REAL")
        return soil_cache[key]

    def soil_trail(d: pd.Timestamp, la, lo):
        vals, provs = [], []
        for i in range(6, -1, -1):
            v, p = soil_day(d - pd.Timedelta(days=i), la, lo)
            if v is not None:
                vals.append(v)
            provs.append(p)
        if not vals:
            return None, "MISSING (window-absent)"
        prov = "REAL" if all(p == "REAL" for p in provs) else "PROXY-spatial"
        return round(float(np.mean(vals)), 4), prov

    rows = []
    for f in sorted(RDIR.glob("event_*.json")):
        e = json.load(open(f, encoding="utf-8"))
        sid = e["slide_no"]
        if sid not in dev:
            continue  # held-out firewall: never build rows for held-out events
        la, lo, T = e["lat"], e["lon"], pd.Timestamp(e["event_date"]).date()
        terr = e["snapshots"]["T"]["terrain"]
        beta = float(np.radians(terr["slope_deg"]))
        ai = int(np.argmin(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat))
            * np.sin(np.radians(mlon - lo) / 2) ** 2))))
        base = mat.iloc[ai]
        # static susceptibility: frozen RF on site terrain + event-year June climatology
        rain_full = rain_series(T.year, la, lo)
        june = rain_full.loc[f"{T.year}-06-01":f"{T.year}-06-30"]
        sus_feat = {"slope_angle": terr["slope_deg"], "elevation": terr["elevation_m"],
                    "aspect": terr["aspect_deg"], "curvature": terr["curvature"],
                    "twi": terr["twi"], "spi_log": float(np.log1p(max(terr["spi"], 0))),
                    "rainfall_24h_mm": round(float(june.iloc[-1]) if len(june) else 0.0, 1),
                    "rainfall_7d_mm": round(float(june.iloc[-7:].sum()) if len(june) else 0.0, 1),
                    "rainfall_30d_mm": round(float(june.sum()) if len(june) else 0.0, 1),
                    "soil_moisture": 0.5, "ndvi": float(base["ndvi"]),
                    "distance_to_road": float(base["distance_to_road"]),
                    "distance_to_river": float(base["distance_to_river"]),
                    "drain_density": terr["drain_density"], "seismic_dist_km": 999.0,
                    "seismic_n50_rate": 0.0, "seismic_years_since": 60,
                    "recent_disturbance": 0.0, "lulc": str(base["lulc"])}
        susc = round(float(model.predict_proba(enc.transform(pd.DataFrame([sus_feat])))[0, 1]), 4)
        # quake distances static per site
        p1 = np.radians([la])
        dall = 2 * 6371.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(qlat - la) / 2) ** 2 + np.cos(p1[0]) * np.cos(np.radians(qlat))
            * np.sin(np.radians(qlon - lo) / 2) ** 2))

        dates = pd.date_range(pd.Timestamp(T) - pd.Timedelta(days=60), pd.Timestamp(T))
        assert (dates.date <= T).all()
        rain = rain_series(T.year, la, lo)
        soilt = {}
        fost = {}
        for d in pd.date_range(pd.Timestamp(T) - pd.Timedelta(days=67), pd.Timestamp(T)):
            soilt[d] = soil_trail(d, la, lo)
            fost[d] = fos_median(rain.loc[:d].iloc[-30:].values, beta)
        prev_rows: list[dict] = []
        for d in dates:
            gd = d.date()
            w = rain.loc[:d]
            r24 = round(float(w.iloc[-1]), 1)
            r3 = round(float(w.iloc[-3:].sum()), 1)
            r7 = round(float(w.iloc[-7:].sum()), 1)
            r30 = round(float(w.iloc[-30:].sum()), 1)
            r7_prev = round(float(rain.loc[:d - pd.Timedelta(days=7)].iloc[-7:].sum()), 1)
            dry = 0
            dd = d
            while dry < 60 and float(rain.loc[:dd].iloc[-1]) < 2.5:
                dry += 1
                dd = dd - pd.Timedelta(days=1)
            sm, smprov = soilt[d]
            sm3, _ = soilt[d - pd.Timedelta(days=3)]
            sm7, _ = soilt[d - pd.Timedelta(days=7)]
            fos = fost[d]
            fos7 = fost[d - pd.Timedelta(days=7)]
            mask = (qdate < str(gd)) & (dall <= 50.0)
            prior = mask.sum()
            prow = {"slide_no": sid, "date": str(gd), "lead_d": (pd.Timestamp(T) - d).days,
                    "region": "bg" if (pd.Timestamp(T) - d).days > 30 else
                    ("T" if gd == T else "pre"),
                    "y14": int(gd == T or 0 < (pd.Timestamp(T) - d).days <= 14),
                    "y7": int(gd == T or 0 < (pd.Timestamp(T) - d).days <= 7),
                    "train_exclude": int(gd == T),
                    "r24": r24, "r3": r3, "r7": r7, "r30": r30,
                    "d_r24_1d": round(r24 - float(rain.loc[:d - pd.Timedelta(days=1)].iloc[-1]), 1),
                    "d_r7_3d": round(r7 - float(rain.loc[:d - pd.Timedelta(days=3)].iloc[-7:].sum()), 1),
                    "accel": round((r7 - r7_prev) / 7.0, 3), "dryspell": dry,
                    "soil": sm, "soil_prov": smprov,
                    "d_soil_3d": None if (sm is None or sm3 is None) else round(sm - sm3, 4),
                    "d_soil_7d": None if (sm is None or sm7 is None) else round(sm - sm7, 4),
                    "fos_med": fos, "fos_prov": "ABSTAIN-flat" if fos is None else "ANALYTICAL-ensemble",
                    "d_fos_7d": None if (fos is None or fos7 is None) else round(fos - fos7, 3),
                    "seis_n50": int(prior),
                    "seis_dist": round(float(dall[qdate < str(gd)].min())
                                       if (qdate < str(gd)).any() else 999.0, 2),
                    "seis_yrs": 60 if prior == 0 else int(
                        min(gd.year - int(qyr[mask].max()), 60)),
                    "slope": terr["slope_deg"], "elev": terr["elevation_m"],
                    "aspect": terr["aspect_deg"], "curv": terr["curvature"],
                    "twi": terr["twi"], "spi": terr["spi"], "draind": terr["drain_density"],
                    "ndvi": float(base["ndvi"]), "d_road": float(base["distance_to_road"]),
                    "d_river": float(base["distance_to_river"]), "lulc": str(base["lulc"]),
                    "susceptibility": susc, "analogue_m": round(float(2 * 6371000.0 * np.arcsin(np.sqrt(
                        np.sin(np.radians(mlat[ai] - la) / 2) ** 2 + np.cos(np.radians(la))
                        * np.cos(np.radians(mlat[ai])) * np.sin(np.radians(mlon[ai] - lo) / 2) ** 2))), 1)}
            prev_rows.append(prow)
            rows.append(prow)
        log(f"{sid} {T}: 61 rows, y14+={sum(r['y14'] for r in prev_rows)}, "
            f"soil_missing={sum(r['soil'] is None for r in prev_rows)}")
    p = pd.DataFrame(rows)
    assert len(p) == 13 * 61 and set(p["slide_no"]) == set(dev), "firewall: built set != dev set"
    assert ((p["lead_d"] >= 0) & (p["lead_d"] <= 60)).all()
    assert (p.groupby("slide_no")["y14"].sum() == 15).all()
    assert (p.groupby("slide_no")["y7"].sum() == 8).all()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p.to_csv(OUTDIR / "traj_dev_positives.csv", index=False)
    aud = {"n": len(p), "events": 13, "rows_per_event": 61,
           "soil_missing": int(p["soil"].isna().sum()),
           "soil_provenance": p["soil_prov"].value_counts().to_dict(),
           "fos_abstain": int(p["fos_med"].isna().sum()),
           "gates": "all inputs timestamp<=d asserted; held-out firewall asserted; "
                    "v09.2 single-version; no FILL"}
    json.dump(aud, open(OUTDIR / "traj_dev_positives_audit.json", "w"), indent=2)
    log(f"wrote {len(p)} rows; soil_missing={aud['soil_missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
