"""Build VI-0 temporal training population (Phase VI). NO MODEL FITTING.

Positives: DEV championship snapshots with event-in-7d (T-7/T-3/T-1/T).
Negatives: same-site T-30/T-14 (N2/N5) + monsoon background daily rows in DEV
years (N3, seed 42) + off-season background daily rows (N0/N4, seed 43 windows).
Features: M0-18 + rain_3d + soil_change_7d + rain_accel_7d + lulc (new encoder later).
Leakage assertions: timestamps <= row date; no event within 7d after background
rows <2km; held-out 10 absent; soil v09.2 only.
Outputs data/sih26001/processed/vi0_training.csv + vi0_sidecar.csv.
Run: mnemo-venv python scripts/build_vi0.py
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
SPLIT = REPO / "splits" / "championship_split_v1.json"
MAT = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDE = REPO / "data/sih26001/processed/training_sidecar.csv"
OUTM = REPO / "data/sih26001/processed/vi0_training.csv"
OUTS = REPO / "data/sih26001/processed/vi0_sidecar.csv"
LAT_SPLIT = 27.15
BASE_COLS = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
             "ndvi", "distance_to_road", "distance_to_river", "drain_density",
             "recent_disturbance", "lulc"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import xarray as xr
    man = json.load(open(SPLIT, encoding="utf-8"))
    dev = {r["slide_no"] for r in man["events"] if r["side"] == "development"}
    ho = {r["slide_no"] for r in man["events"] if r["side"] == "held-out"}
    mat = pd.read_csv(MAT)
    side = pd.read_csv(SIDE)
    y0 = mat["event"].to_numpy().astype(int)
    mlat, mlon = side["lat"].to_numpy(), side["lon"].to_numpy()
    quakes = json.load(open(REPO / "data/sih26001/evidence/usgs_quakes.json"))["events"]
    RAIN, SOIL, SOIL_DS = {}, {}, {}

    def soil_ds(date):
        key = str(date)
        if key not in SOIL_DS:
            import xarray as _xr
            fp = REPO / ("data/raw/soil/v09.2/ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-"
                         f"{pd.Timestamp(date):%Y%m%d}000000-fv09.2.nc")
            SOIL_DS[key] = _xr.open_dataset(str(fp)) if fp.exists() else None
        return SOIL_DS[key]

    def rain_series(year, la, lo):
        key = (year, round(la, 2), round(lo, 2))
        if key not in RAIN:
            ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{year}_rfp25.nc"))
            s = ds.RAINFALL.sel(LATITUDE=la, LONGITUDE=lo, method="nearest")
            RAIN[key] = pd.Series(np.asarray(s.values, dtype=float),
                                  index=pd.to_datetime(s.TIME.values)).fillna(0.0)
            ds.close()
        return RAIN[key]

    def soil_on(date, la, lo):
        import warnings
        key = (str(date), round(la, 2), round(lo, 2))
        if key not in SOIL:
            v, prov = (None, "MISSING (file-absent)")
            sds = soil_ds(date)
            if sds is not None:
                try:
                    da = sds["sm"] if "sm" in sds.data_vars else sds[
                        [x for x in sds.data_vars if "sm" in x.lower()][0]]
                    c = float(da.sel(lat=la, lon=lo, method="nearest").values.flat[0])
                    v, prov = (round(c, 4), "REAL") if np.isfinite(c) else (None, None)
                    if v is None:
                        laa = np.asarray(sds["lat"].values).ravel()
                        loo = np.asarray(sds["lon"].values).ravel()
                        ii, jj = int(np.argmin(np.abs(laa - la))), int(np.argmin(np.abs(loo - lo)))
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            m = float(np.nanmean(da.isel(lat=slice(max(0, ii - 1), ii + 2),
                                                         lon=slice(max(0, jj - 1), jj + 2)).values))
                        if np.isfinite(m):
                            v, prov = round(m, 4), "PROXY-spatial"
                        else:
                            try:
                                fl = int(float(sds["flag"].sel(lat=la, lon=lo,
                                                               method="nearest").values.flat[0]))
                            except Exception:
                                fl = -1
                            v, prov = None, f"MISSING (all-NaN, flag={fl})"
                except Exception as ex:
                    prov = f"MISSING ({str(ex)[:50]})"
            SOIL[key] = (v, prov)
        return SOIL[key]

    def nearest_row(la, lo):
        i = int(np.argmin(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat))
            * np.sin(np.radians(mlon - lo) / 2) ** 2))))
        dd = float(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat[i] - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat[i]))
            * np.sin(np.radians(mlon[i] - lo) / 2) ** 2)))
        return mat.iloc[i], dd

    def seis(la, lo, dstr):
        d = pd.Timestamp(dstr).date()
        ds_, pr = [], 0
        for q in quakes:
            if q["date"] >= dstr:
                continue
            dd = 2 * 6371.0 * np.arcsin(np.sqrt(
                np.sin(np.radians(q["lat"] - la) / 2) ** 2 + np.cos(np.radians(la))
                * np.cos(np.radians(q["lat"])) * np.sin(np.radians(q["lon"] - lo) / 2) ** 2))
            ds_.append(dd)
            if dd <= 50.0:
                pr += 1
        yrs = [q["year"] for q in quakes if q["date"] < dstr and
               2 * 6371.0 * np.arcsin(np.sqrt(np.sin(np.radians(q["lat"] - la) / 2) ** 2
               + np.cos(np.radians(la)) * np.cos(np.radians(q["lat"]))
               * np.sin(np.radians(q["lon"] - lo) / 2) ** 2)) <= 50.0]
        return (round(float(min(ds_)), 2) if ds_ else 999.0,
                round(pr / max(pd.Timestamp(dstr).year - 1965, 1), 4),
                min(pd.Timestamp(dstr).year - max(yrs), 60) if yrs else 60)

    rows, Scar = [], []
    ev_coords = {}
    # --- DEV event snapshots (positives + N2/N5) ---
    for f in sorted(glob.glob(str(RDIR / "event_*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        assert not (e["slide_no"] in ho and e["slide_no"] in dev), "split overlap!"
        if e["slide_no"] not in dev:
            continue  # held-out sealed — never in VI-0 population
        la, lo, evd = e["lat"], e["lon"], pd.Timestamp(e["event_date"]).date()
        ev_coords[e["slide_no"]] = (la, lo, evd)
        base, ad = nearest_row(la, lo)
        for key, s in e["snapshots"].items():
            gd = str(s["grid_end"])
            w = rain_series(int(gd[:4]), la, lo).loc[:gd]
            assert (w.index.date <= pd.Timestamp(gd).date()).all()
            sm, smp = soil_on(gd, la, lo)
            sm7, _ = soil_on(str(pd.Timestamp(gd).date() - pd.Timedelta(days=7)), la, lo)
            if sm is None:
                smp = "BASE-FALLBACK" if "file-absent" in smp else f"BASE-{smp}"
            r7 = float(w.iloc[-7:].sum())
            r7l = float(w.iloc[-14:-7].sum())
            dd, rt, ys = seis(la, lo, gd)
            rows.append({"slope_angle": s["terrain"]["slope_deg"], "elevation": s["terrain"]["elevation_m"],
                         "aspect": s["terrain"]["aspect_deg"], "curvature": s["terrain"]["curvature"],
                         "twi": s["terrain"]["twi"], "spi_log": float(np.log1p(max(s["terrain"]["spi"], 0))),
                         "rainfall_24h_mm": s["rainfall_24h_mm"]["value"],
                         "rainfall_3d_mm": s["rainfall_3d_mm"]["value"],
                         "rainfall_7d_mm": s["rainfall_7d_mm"]["value"],
                         "rainfall_30d_mm": s["rainfall_30d_mm"]["value"],
                         "soil_moisture": sm if sm is not None else float(base["soil_moisture"]),
                         "soil_prov": smp,
                         "soil_change_7d": round((sm if sm is not None else 0) - (sm7 if sm7 is not None else 0), 4),
                         "rain_accel_7d": round(r7 - r7l, 1),
                         "ndvi": float(base["ndvi"]), "distance_to_road": float(base["distance_to_road"]),
                         "distance_to_river": float(base["distance_to_river"]),
                         "drain_density": s["terrain"]["drain_density"],
                         "seismic_dist_km": dd, "seismic_n50_rate": rt, "seismic_years_since": ys,
                         "recent_disturbance": 0.0, "lulc": str(base["lulc"]),
                         "y7d": int(key in ("T-7", "T-3", "T-1", "T"))})
            Scar.append({"slide_no": e["slide_no"], "kind": "dev-event", "date": gd,
                         "analogue_m": round(ad, 1)})

    # --- background daily rows (N3 monsoon seed42 + N0 off-season seed43 windows) ---
    rng = np.random.default_rng(42)
    bg = np.where(y0 == 0)[0]
    pick = np.concatenate([rng.choice(bg[mlat[bg] < LAT_SPLIT], 30, replace=False),
                           rng.choice(bg[mlat[bg] >= LAT_SPLIT], 30, replace=False)])
    dev_years = sorted({int(pd.Timestamp(json.load(open(f, encoding="utf-8"))["event_date"]).year)
                        for f in glob.glob(str(RDIR / "event_*.json"))
                        if json.load(open(f, encoding="utf-8"))["slide_no"] in dev})
    wins = [(float(side["lat"].iloc[i]), float(side["lon"].iloc[i]),
             pd.Timestamp(f"{int(rng.choice(dev_years))}-07-01"), mat.iloc[i]) for i in pick]
    off = json.load(open(REPO / "runs" / "burden_offseason.json"))["windows"]
    zid2i = {z: n for n, z in enumerate(mat["zone_id"])} if "zone_id" in mat else {}
    for w in off:
        z = w.get("zone")
        i = zid2i.get(z)
        if i is None:
            continue
        ym = pd.Timestamp(w["window"] + "-01")
        wins.append((float(side["lat"].iloc[i]), float(side["lon"].iloc[i]), ym, mat.iloc[i]))
    for wi, (la, lo, d0, base) in enumerate(wins):
        if wi % 20 == 0:
            log(f"background window {wi}/{len(wins)}")
        for day in pd.date_range(d0, d0 + pd.Timedelta(days=30), freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            for sev, (ela, elo, ed) in ev_coords.items():
                dist = 2 * 6371000.0 * np.arcsin(np.sqrt(
                    np.sin(np.radians(ela - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(ela))
                    * np.sin(np.radians(elo - lo) / 2) ** 2))
                assert not (dist < 2000 and 0 <= (ed - day.date()).days <= 7), f"bg too close to {sev}"
            w = rain_series(int(ds_[:4]), la, lo).loc[:ds_]
            sm, smp = soil_on(ds_, la, lo)
            sm7, _ = soil_on(str(day.date() - pd.Timedelta(days=7)), la, lo)
            r7 = float(w.iloc[-7:].sum())
            r7l = float(w.iloc[-14:-7].sum())
            dd, rt, ys = seis(la, lo, ds_)
            rows.append({"slope_angle": float(base["slope_angle"]), "elevation": float(base["elevation"]),
                         "aspect": float(base["aspect"]), "curvature": float(base["curvature"]),
                         "twi": float(base["twi"]), "spi_log": float(np.log1p(max(float(base["spi"]), 0))),
                         "rainfall_24h_mm": round(float(w.iloc[-1]), 1),
                         "rainfall_3d_mm": round(float(w.iloc[-3:].sum()), 1),
                         "rainfall_7d_mm": round(r7, 1),
                         "rainfall_30d_mm": round(float(w.iloc[-30:].sum()), 1),
                         "soil_moisture": sm if sm is not None else float(base["soil_moisture"]),
                         "soil_prov": smp if sm is not None else "BASE-" + smp.replace("BASE-", ""),
                         "soil_change_7d": round((sm if sm is not None else 0) - (sm7 if sm7 is not None else 0), 4),
                         "rain_accel_7d": round(r7 - r7l, 1),
                         "ndvi": float(base["ndvi"]), "distance_to_road": float(base["distance_to_road"]),
                         "distance_to_river": float(base["distance_to_river"]),
                         "drain_density": float(base["drain_density"]),
                         "seismic_dist_km": dd, "seismic_n50_rate": rt, "seismic_years_since": ys,
                         "recent_disturbance": 0.0, "lulc": str(base["lulc"]), "y7d": 0})
            Scar.append({"slide_no": f"BG@{la:.2f},{lo:.2f}", "kind": "background", "date": ds_,
                         "analogue_m": 0.0})
    for sds in SOIL_DS.values():
        try:
            if sds is not None:
                sds.close()
        except Exception:
            pass
    m = pd.DataFrame(rows)
    assert len(m) > 3000 and set(m["y7d"]) == {0, 1}
    m.to_csv(OUTM, index=False)
    pd.DataFrame(Scar).to_csv(OUTS, index=False)
    log(f"rows={len(m)} pos={int(m['y7d'].sum())} "
        f"soil_REAL={(m['soil_prov'] == 'REAL').sum()} PROXY={(m['soil_prov'] == 'PROXY-spatial').sum()} "
        f"fallback={(m['soil_prov'] == 'BASE-FALLBACK').sum()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
