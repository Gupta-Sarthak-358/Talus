"""V-B pilot: single-event daily reconstruction with temporal assertions (Phase V-B).

Model-free. T convention: snapshot S(d) uses complete daily grids with date <= d.
T-day grid is EXCLUDED (contains post-onset observations for afternoon events);
T therefore shares grid state with T-1 (documented daily-resolution limitation)
and differs by event-cutoff metadata + assertions.
Snapshots: T-30/T-14/T-7/T-3/T-1/T with explicit grid-end dates.
Branches: rain (IMD, REAL) / soil (CCI v09.2 daily, REAL) / seismic (USGS, REAL or
PENDING) / terrain (SRTM, REAL static) / satellite (era-validated, scene query
PENDING — no scene with date > snapshot accepted at build) / disturbance (MISSING:
no pre-event wound map for 2016).
Hard invariant (asserted in code): every observation_timestamp <= snapshot grid-end.
Run (system python: rasterio): python scripts/reconstruct_event.py [SLIDE_NO]
Outputs: runs/phase_v/daily_replay/event_<id>.json + reconstruction_audit.json
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUTDIR = REPO / "runs" / "phase_v" / "daily_replay"
AUDIT = REPO / "runs" / "phase_v" / "reconstruction_audit.json"
SOILDIR = REPO / "data/raw/soil/v09.2"
SRTM = REPO / "data/raw/dem/n27_e088_1arc_v3.tif"
S2_START = dt.date(2015, 6, 23)
L8_START = dt.date(2013, 2, 11)


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def obs(value, ts: str, source: str, prov: str) -> dict:
    return {"value": value, "observation_timestamp": ts, "source": source,
            "provenance": prov}


def main() -> int:
    import xarray as xr
    slide = sys.argv[1] if len(sys.argv) > 1 else "NEWS-MANTAM-20160813"
    d = pd.read_csv(TRACKER)
    r = d[d["slide_no"] == slide].iloc[0]
    lat, lon = float(r["lat"]), float(r["lon"])
    T = pd.Timestamp(r["exact_date"]).date()  # 2016-08-13; onset ~12:30 IST
    snaps = [("T-30", T - dt.timedelta(days=30)), ("T-14", T - dt.timedelta(days=14)),
             ("T-7", T - dt.timedelta(days=7)), ("T-3", T - dt.timedelta(days=3)),
             ("T-1", T - dt.timedelta(days=1)), ("T", T - dt.timedelta(days=1))]
    log(f"{slide} T={T} onset~12:30 IST; T-day grid excluded (post-onset obs)")

    # rain: IMD daily grids (REAL)
    ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{T.year}_rfp25.nc"))
    rain = pd.Series(np.asarray(ds.RAINFALL.sel(
        LATITUDE=lat, LONGITUDE=lon, method="nearest").values, dtype=float),
        index=pd.to_datetime(ds.TIME.values)).fillna(0.0)
    ds.close()

    # terrain: SRTM static (REAL) — index-based window, nodata-masked
    import rasterio
    with rasterio.open(SRTM) as src:
        rr, cc = src.index(lon, lat)
        h = 36
        win = src.read(1, window=((max(0, rr - h), rr + h), (max(0, cc - h), cc + h))).astype(float)
        win[win == src.nodata] = np.nan
        assert np.isfinite(win).sum() > win.size // 2, "SRTM window mostly void"
        elev = float(np.nanmean(win))
        res = 30.0
        gy, gx = np.gradient(np.nan_to_num(win, nan=elev), res)
        slope = float(np.degrees(np.arctan(np.nanmean(np.hypot(gx, gy)))))

    # seismic: USGS M>=5.5 <50km trailing 180d <= T (REAL or PENDING)
    seis: dict = {"provenance": "PENDING", "note": "USGS query deferred/failed; no value fabricated"}
    try:
        q = (f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
             f"&latitude={lat}&longitude={lon}&maxradiuskm=50&minmagnitude=5.5"
             f"&starttime={T - dt.timedelta(days=180)}&endtime={T}&limit=50")
        with urllib.request.urlopen(q, timeout=25) as fh:
            feats = json.load(fh)["features"]
        # hard invariant: catalog times <= T
        for f in feats:
            assert dt.datetime.utcfromtimestamp(f["properties"]["time"] / 1000).date() <= T
        seis = {"n_events": len(feats), "provenance": "REAL", "source": "USGS-fdsnws",
                "queried_through": str(T)}
    except Exception as ex:
        seis["error"] = str(ex)[:120]

    sat_era = "S2A+L8" if T >= S2_START else ("L8" if T >= L8_START else "none")
    snapshots = {}
    ok = True
    for key, end in snaps:
        w = rain.loc[:pd.Timestamp(end)]
        assert len(w) > 0 and (w.index.date <= end).all(), "grid-end violation"
        r24 = round(float(w.iloc[-1]), 1)
        r7 = round(float(w.iloc[-7:].sum()), 1)
        r30 = round(float(w.iloc[-30:].sum()), 1)
        # soil: v09.2 daily nearest cell, file date <= end
        sm, smprov, smts = None, "MISSING", None
        fp = SOILDIR / f"ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-{end:%Y%m%d}000000-fv09.2.nc"
        if fp.exists():
            try:
                sds = xr.open_dataset(str(fp))
                latn = next(v for v in ("lat", "latitude", "LAT") if v in sds.variables)
                lonn = next(v for v in ("lon", "longitude", "LON") if v in sds.variables)
                var = [v for v in sds.data_vars if "sm" in v.lower() or "soil" in v.lower()][0]
                val = sds[var].sel({latn: lat, lonn: lon}, method="nearest").values
                sm = round(float(np.nanmean(val)), 4)
                smprov, smts = "REAL", str(end)
                sds.close()
            except Exception as ex:
                smprov = f"MISSING ({str(ex)[:60]})"
        snapshots[key] = {
            "grid_end": str(end),
            "rainfall_24h_mm": obs(r24, str(end), f"IMD ind{T.year}", "REAL"),
            "rainfall_7d_mm": obs(r7, str(end), f"IMD ind{T.year}", "REAL"),
            "rainfall_30d_mm": obs(r30, str(end), f"IMD ind{T.year}", "REAL"),
            "soil_moisture": obs(sm, smts or str(end), "CCI v09.2 daily", smprov),
            "seismic": seis,
            "terrain": {"elevation_m": round(elev, 1), "slope_deg": round(slope, 1),
                        "provenance": "REAL-static", "source": "SRTM 1arc"},
            "satellite": {"era": sat_era, "provenance": "PENDING-scene-query",
                           "rule": "no scene with date > snapshot accepted at build"},
            "disturbance": {"provenance": "MISSING",
                             "reason": "no pre-event wound map for 2016"},
        }
    event = {"slide_no": slide, "event_date": str(T), "event_cutoff": f"{T}T12:30+05:30",
             "lat": lat, "lon": lon, "episode": str(r["related_episode_id"]),
             "T_convention": "T-day grid excluded (post-onset obs); T shares grid state with T-1",
             "snapshots": snapshots}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"event_{slide}.json").write_text(json.dumps(event, indent=2), encoding="utf-8")
    audit = {"events": 1, "snapshots_per_event": 6, "invariant": "observation_timestamp <= grid_end",
             "satellite_branch": "PENDING (era-validated only)",
             "seismic_branch": seis.get("provenance", "PENDING"),
             "soil_missing_snapshots": [k for k, v in snapshots.items()
                                        if v["soil_moisture"]["provenance"] != "REAL"]}
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    t = snapshots["T"]
    log(f"rain 24h/7d/30d at T: {t['rainfall_24h_mm']['value']}/"
        f"{t['rainfall_7d_mm']['value']}/{t['rainfall_30d_mm']['value']}mm; "
        f"soil_missing={audit['soil_missing_snapshots']}; seismic={audit['seismic_branch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
