"""VI-A negatives: N0 same-site quiet + N1 wet-but-safe (13 dev sites).

Exclusion calendar: every Track-A row with exact_date (58, incl. all 23
championship events). Candidate row (site S, date t) valid iff NO calendar
event within 50 km of S dated in (t, t+14d]. Conservative by design:
over-exclusion only shrinks the pool; under-exclusion would poison labels.
Row pipeline mirrors build_vit.py (timestamp-gated <= d, v09.2
single-version, frozen FoS ensemble, date-gated seismic). N0 = 61-day window
same calendar dates other year; N1 = 31-day window ending wettest clean day
(May-Oct scan). Held-out sites never constructed (dev sites only).
Run: mnemo-venv python scripts/build_vit_neg.py
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
sys.path.insert(0, str(REPO / "scripts"))
import build_vit as BV  # noqa: E402  (pure fns R/fos_median; main not run)

RDIR = REPO / "runs" / "phase_v" / "daily_replay"
OUTDIR = REPO / "data" / "vit"
SPLIT = REPO / "splits" / "championship_split_v1.json"
SOILDIR = REPO / "data/raw/soil/v09.2"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import xarray as xr
    import event_soil_upgrade as ES
    KILL = ES.KILL
    sys.path.insert(0, str(REPO / "backend"))

    POS_ALL = pd.read_csv(OUTDIR / "traj_dev_positives.csv")
    POS_ALL = POS_ALL[POS_ALL["train_exclude"] == 0]
    R7S = float(POS_ALL["r7"].std())
    R30S = float(POS_ALL["r30"].std())
    split = {r["slide_no"]: r for r in json.load(open(SPLIT))["events"]}
    dev_ids = {k for k, v in split.items() if v["side"] == "development"}
    assert len(dev_ids) == 13
    champ = set(split)

    # --- exclusion calendar: all dated Track-A rows ---
    track = pd.read_csv(REPO / "data/sih26001/evidence/trackA_candidates.csv")
    cal = track[track["exact_date"].notna()].copy()
    cal["exact_date"] = pd.to_datetime(cal["exact_date"])
    reg = [{"slide_no": r.slide_no, "date": r.exact_date.strftime("%Y-%m-%d"),
            "lat": float(r.lat), "lon": float(r.lon),
            "in_championship": bool(r.slide_no in champ),
            "mechanism": str(r.event_type)} for r in cal.itertuples()]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    json.dump({"rule": "candidate row (S,t) valid iff no calendar event within "
                       "50km of S dated in (t,t+14d]; over-exclusion is safe",
               "n": len(reg), "events": reg},
              open(OUTDIR / "eligible_event_registry.json", "w"), indent=2)
    clat = cal["lat"].to_numpy()
    clon = cal["lon"].to_numpy()
    cdate = cal["exact_date"].to_numpy()

    def clean(site_la, site_lo, d0: pd.Timestamp, d1: pd.Timestamp) -> bool:
        """No calendar event within 50km dated in (d, d+14d] for any row d in [d0,d1]."""
        p1 = np.radians(site_la)
        dist = 2 * 6371.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(clat - site_la) / 2) ** 2 + np.cos(p1) * np.cos(np.radians(clat))
            * np.sin(np.radians(clon - site_lo) / 2) ** 2))
        near = dist <= 50.0
        if not near.any():
            return True
        lo = (d0 + pd.Timedelta(days=1)).date().isoformat()
        hi = (d1 + pd.Timedelta(days=14)).date().isoformat()
        hit = cal[near & (cal["exact_date"] >= lo) & (cal["exact_date"] <= hi)]
        return len(hit) == 0

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
        return round(float(np.mean(vals)), 4), \
            ("REAL" if all(p == "REAL" for p in provs) else "PROXY-spatial")

    def build_rows(sid, la, lo, terr, base, dates, stratum, win_year):
        rain = rain_series(win_year, la, lo)
        beta = float(np.radians(terr["slope_deg"]))
        june = rain.loc[f"{win_year}-06-01":f"{win_year}-06-30"]
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
        p1 = np.radians([la])
        dall = 2 * 6371.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(qlat - la) / 2) ** 2 + np.cos(p1[0]) * np.cos(np.radians(qlat))
            * np.sin(np.radians(qlon - lo) / 2) ** 2))
        ext = pd.date_range(dates[0] - pd.Timedelta(days=7), dates[-1])
        soilt = {d: soil_trail(d, la, lo) for d in ext}
        fost = {d: BV.fos_median(rain.loc[:d].iloc[-30:].values, beta) for d in ext}
        out = []
        for d in dates:
            gd = d.date()
            w = rain.loc[:d]
            r24 = round(float(w.iloc[-1]), 1)
            r7 = round(float(w.iloc[-7:].sum()), 1)
            r30 = round(float(w.iloc[-30:].sum()), 1)
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
            out.append({"slide_no": sid, "date": str(gd), "stratum": stratum,
                        "window_year": win_year, "y14": 0, "y7": 0, "train_exclude": 0,
                        "r24": r24, "r3": round(float(w.iloc[-3:].sum()), 1), "r7": r7, "r30": r30,
                        "d_r24_1d": round(r24 - float(rain.loc[:d - pd.Timedelta(days=1)].iloc[-1]), 1),
                        "d_r7_3d": round(r7 - float(rain.loc[:d - pd.Timedelta(days=3)].iloc[-7:].sum()), 1),
                        "accel": round((r7 - float(rain.loc[:d - pd.Timedelta(days=7)].iloc[-7:].sum())) / 7.0, 3),
                        "dryspell": dry, "soil": sm, "soil_prov": smprov,
                        "d_soil_3d": None if (sm is None or sm3 is None) else round(sm - sm3, 4),
                        "d_soil_7d": None if (sm is None or sm7 is None) else round(sm - sm7, 4),
                        "fos_med": fos, "fos_prov": "ABSTAIN-flat" if fos is None else "ANALYTICAL-ensemble",
                        "d_fos_7d": None if (fos is None or fos7 is None) else round(fos - fos7, 3),
                        "seis_n50": int(mask.sum()),
                        "seis_dist": round(float(dall[qdate < str(gd)].min())
                                           if (qdate < str(gd)).any() else 999.0, 2),
                        "seis_yrs": 60 if mask.sum() == 0 else int(
                            min(gd.year - int(qyr[mask].max()), 60)),
                        "slope": terr["slope_deg"], "elev": terr["elevation_m"],
                        "aspect": terr["aspect_deg"], "curv": terr["curvature"],
                        "twi": terr["twi"], "spi": terr["spi"], "draind": terr["drain_density"],
                        "ndvi": float(base["ndvi"]), "d_road": float(base["distance_to_road"]),
                        "d_river": float(base["distance_to_river"]), "lulc": str(base["lulc"]),
                        "susceptibility": susc})
        return out

    rows = []
    for f in sorted(RDIR.glob("event_*.json")):
        e = json.load(open(f, encoding="utf-8"))
        sid = e["slide_no"]
        if sid not in dev_ids:
            continue
        la, lo, T = e["lat"], e["lon"], pd.Timestamp(e["event_date"])
        terr = e["snapshots"]["T"]["terrain"]
        ai = int(np.argmin(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat))
            * np.sin(np.radians(mlon - lo) / 2) ** 2))))
        base = mat.iloc[ai]
        md, dy = T.month, T.day
        # N0: same calendar dates, nearest clean other year
        n0 = None
        for yr in sorted(range(2015, 2025), key=lambda y: abs(y - T.year)):
            if yr == T.year:
                continue
            try:
                w0 = pd.Timestamp(yr, md, dy) - pd.Timedelta(days=60)
                w1 = pd.Timestamp(yr, md, dy)
            except ValueError:
                continue  # Feb-29 edge
            if clean(la, lo, w0, w1):
                n0 = (yr, pd.date_range(w0, w1))
                break
        assert n0, f"no clean N0 window for {sid}"
        # N1: clean 31-day May-Oct window (other years) MATCHED to the site's own
        # pre-event rain regime (median r7/r30 of its POS pre rows), standardized by
        # POS-global std. Wettest-window overshoots (inversion risk: rain=>safe).
        pos_pre = POS_ALL[(POS_ALL["slide_no"] == sid) & (POS_ALL["region"] == "pre")]
        ctr = np.array([pos_pre["r7"].median(), pos_pre["r30"].median()])
        best = None
        for yr in range(2015, 2025):
            if yr == T.year:
                continue
            rain = rain_series(yr, la, lo)
            scan = pd.date_range(f"{yr}-05-01", f"{yr}-10-31")
            r7 = rain.loc[scan[0] - pd.Timedelta(days=6):scan[-1]].rolling(7).sum()
            r30 = rain.loc[scan[0] - pd.Timedelta(days=29):scan[-1]].rolling(30).sum()
            for d in scan:
                w0, w1 = d - pd.Timedelta(days=30), d
                if not clean(la, lo, w0, w1):
                    continue
                v = np.array([(float(r7.loc[d]) - ctr[0]) / R7S, (float(r30.loc[d]) - ctr[1]) / R30S])
                dist = float(np.sqrt((v ** 2).sum()))
                if best is None or dist < best[0]:
                    best = (dist, yr, pd.date_range(w0, w1))
        assert best, f"no clean N1 window for {sid}"
        rows += build_rows(sid, la, lo, terr, base, n0[1], "N0", n0[0])
        rows += build_rows(sid, la, lo, terr, base, best[2], "N1", best[1])
        log(f"{sid}: N0 {n0[0]} ({n0[1][0].date()}..{n0[1][-1].date()}), "
            f"N1 {best[1]} matchdist={best[0]:.2f} ({best[2][0].date()}..{best[2][-1].date()})")
    p = pd.DataFrame(rows)
    assert len(p) == 13 * 61 + 13 * 31 and set(p["slide_no"]) == dev_ids
    assert ((p["y14"] == 0) & (p["y7"] == 0)).all()
    p.to_csv(OUTDIR / "traj_dev_negatives.csv", index=False)
    aud = {"n": len(p), "n0": int((p["stratum"] == "N0").sum()),
           "n1": int((p["stratum"] == "N1").sum()),
           "soil_missing": int(p["soil"].isna().sum()),
           "soil_provenance": p["soil_prov"].value_counts().to_dict(),
           "rule": "window-level clean + per-row assert below"}
    # per-row clean check with true site coords
    coords = {}
    for f in sorted(RDIR.glob("event_*.json")):
        e = json.load(open(f, encoding="utf-8"))
        if e["slide_no"] in dev_ids:
            coords[e["slide_no"]] = (e["lat"], e["lon"])
    bad = 0
    for r in p.itertuples():
        la, lo = coords[r.slide_no]
        if not clean(la, lo, pd.Timestamp(r.date), pd.Timestamp(r.date)):
            bad += 1
    aud["per_row_violations"] = bad
    assert bad == 0, "negative censoring violated!"
    json.dump(aud, open(OUTDIR / "traj_dev_negatives_audit.json", "w"), indent=2)
    log(f"wrote {len(p)} negatives; violations={bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
