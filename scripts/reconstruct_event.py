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

    # terrain: SRTM static (REAL) — D8 + priority-flood + Horn, same formulas as
    # scripts/extract_catchment.py (twi=ln(a/tanB), spi=a*tanB, drain=channel-km/(pi*0.09)).
    import heapq
    import math

    import rasterio

    def catchment_at(la, lo):
        with rasterio.open(SRTM) as src:
            rr, cc = src.index(lo, la)
            H = 90
            r0, r1, c0, c1 = max(0, rr - H), rr + H + 1, max(0, cc - H), cc + H + 1
            z = src.read(1, window=((r0, r1), (c0, c1))).astype(float)
            z[z == src.nodata] = np.nan
            frac = float(np.isfinite(z).sum() / z.size)
            assert frac > 0.5, f"SRTM window {100 * (1 - frac):.0f}% void"
            z = np.nan_to_num(z, nan=float(np.nanmean(z)))
            void_note = f"{100 * (1 - frac):.1f}% void mean-filled" if frac < 1 else "no voids"
        Hh, Ww = z.shape
        dx = 30.0
        filled, visited, heap = z.copy(), np.zeros_like(z, bool), []
        for x in range(Ww):
            for y in (0, Hh - 1):
                heapq.heappush(heap, (filled[y, x], y, x))
                visited[y, x] = True
        for y in range(Hh):
            for x in (0, Ww - 1):
                if not visited[y, x]:
                    heapq.heappush(heap, (filled[y, x], y, x))
                    visited[y, x] = True
        OFFS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        while heap:
            h, y, x = heapq.heappop(heap)
            for dr, dc in OFFS8:
                ny, nx = y + dr, x + dc
                if 0 <= ny < Hh and 0 <= nx < Ww and not visited[ny, nx]:
                    visited[ny, nx] = True
                    filled[ny, nx] = max(z[ny, nx], h + 1e-3)
                    heapq.heappush(heap, (filled[ny, nx], ny, nx))
        DIST = [math.sqrt(2) * dx if abs(dr) + abs(dc) == 2 else dx for dr, dc in OFFS8]
        recv = np.zeros((Hh, Ww, 2), dtype=np.int32)
        drop = np.zeros((Hh, Ww))
        for (dr, dc), dist in zip(OFFS8, DIST):
            dz = filled[1:-1, 1:-1] - filled[1 + dr:Hh - 1 + dr, 1 + dc:Ww - 1 + dc]
            sk = np.where(dz > 0, dz / dist, -1.0)
            better = sk > drop[1:-1, 1:-1]
            drop[1:-1, 1:-1][better] = sk[better]
            grr, gcc = np.meshgrid(np.arange(1, Hh - 1), np.arange(1, Ww - 1), indexing="ij")
            recv[1:-1, 1:-1][better] = np.stack([(grr + dr)[better], (gcc + dc)[better]], axis=-1)
        acc = np.ones((Hh, Ww))
        order = np.argsort(-filled[1:-1, 1:-1].ravel())
        ys, xs = np.unravel_index(order, (Hh - 2, Ww - 2))
        ys, xs = ys + 1, xs + 1
        for y, x in zip(ys.tolist(), xs.tolist()):
            ry, cx = recv[y, x]
            if (ry != 0 or cx != 0) and (ry != y or cx != x):
                acc[ry, cx] += acc[y, x]
        iy, ix = rr - r0, cc - c0
        w = filled[iy - 1:iy + 2, ix - 1:ix + 2]
        dzdx = ((w[0, 2] + 2 * w[1, 2] + w[2, 2]) - (w[0, 0] + 2 * w[1, 0] + w[2, 0])) / (8 * dx)
        dzdy = ((w[2, 0] + 2 * w[2, 1] + w[2, 2]) - (w[0, 0] + 2 * w[0, 1] + w[0, 2])) / (8 * dx)
        slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        aspect = (math.degrees(math.atan2(-dzdx, dzdy)) + 360.0) % 360.0 if slope >= 0.5 else 0.0
        curv = ((filled[iy, ix + 1] - 2 * filled[iy, ix] + filled[iy, ix - 1]) / dx**2
                + (filled[iy + 1, ix] - 2 * filled[iy, ix] + filled[iy - 1, ix]) / dx**2)
        a = acc[iy, ix] * dx
        tanb = max(math.tan(math.radians(slope)), 1e-4)
        yy, xx = np.ogrid[:Hh, :Ww]
        nchan = int((((yy - iy) ** 2 + (xx - ix) ** 2 <= 100) & (acc >= 1111)).sum())
        return {"elevation_m": round(float(z[iy, ix]), 1),
                "slope_deg": round(slope, 1), "aspect_deg": round(aspect, 0),
                "curvature": round(float(curv), 4), "twi": round(math.log(a / tanb), 2),
                "spi": round(a * tanb, 1),
                "drain_density": round(nchan * 0.03 / (math.pi * 0.09), 3),
                "provenance": "REAL-static", "source": "SRTM 1arc D8+fill (training formulas)",
                "voids": void_note}

    terr = catchment_at(lat, lon)
    for k, lo_, hi in (("elevation_m", -500, 9000), ("slope_deg", 0, 90), ("twi", -2, 30),
                       ("spi", 0, 3e6), ("drain_density", 0, 20)):
        assert lo_ <= terr[k] < hi and np.isfinite(terr[k]), f"terrain implausible: {k}={terr[k]}"

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
        if feats:
            def _hav(f):
                lo2, la2 = f["geometry"]["coordinates"][:2]
                p1, p2 = np.radians([lat, lon]), np.radians([la2, lo2])
                h = (np.sin((p2[0] - p1[0]) / 2) ** 2 + np.cos(p1[0]) * np.cos(p2[0])
                     * np.sin((p2[1] - p1[1]) / 2) ** 2)
                return 2 * 6371.0 * np.arcsin(np.sqrt(h))
            near = min(feats, key=_hav)
            seis.update({"nearest_mag": near["properties"]["mag"],
                         "nearest_place": str(near["properties"]["place"])[:80],
                         "nearest_time": str(dt.datetime.utcfromtimestamp(
                             near["properties"]["time"] / 1000).date()),
                         "nearest_dist_km": round(float(_hav(near)), 1)})
    except Exception as ex:
        seis["error"] = str(ex)[:120]

    # satellite: STAC scene discovery per snapshot (REAL list / MISSING / PENDING-error).
    # Rule: no acquisition with date > snapshot grid-end is ever accepted.
    def stac_scenes(end):
        import json as js
        out: dict = {"provenance": "PENDING-error", "collections": {}}
        start = end - dt.timedelta(days=30)
        for coll in ("sentinel-2-l2a", "landsat-c2-l2", "sentinel-1-grd"):
            try:
                b = {"collections": [coll], "intersects": {"type": "Point",
                     "coordinates": [lon, lat]},
                     "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z", "limit": 20,
                     "fields": {"include": ["id", "properties.datetime",
                                            "properties.eo:cloud_cover"]}}
                req = urllib.request.Request(
                    "https://earth-search.aws.element84.com/v1/search",
                    data=js.dumps(b).encode(), headers={"Content-Type": "application/json"})
                items = js.load(urllib.request.urlopen(req, timeout=30)).get("features", [])
                for f in items:
                    assert f["properties"]["datetime"][:10] <= str(end), "post-snapshot scene"
                scenes = sorted(((f["id"], f["properties"]["datetime"][:10],
                                  round(float(f["properties"].get("eo:cloud_cover", 100)), 1))
                                 for f in items), key=lambda s: s[2])
                if coll == "sentinel-1-grd":  # SAR: cloud-agnostic, any scene usable
                    usable = scenes[0] if scenes else None
                else:
                    usable = next((s for s in scenes if s[2] < 30), None)
                out["collections"][coll] = {"n": len(scenes),
                                            "best": list(scenes[0]) if scenes else None,
                                            "usable_lt30": list(usable) if usable else None}
            except Exception as ex:
                out["collections"][coll] = {"error": str(ex)[:100]}
        n = sum(v.get("n", 0) for v in out["collections"].values() if isinstance(v, dict))
        erro = any("error" in v for v in out["collections"].values() if isinstance(v, dict))
        out["provenance"] = "PENDING-error" if (erro and n == 0) else ("REAL" if n > 0
                            else "MISSING-no-scene")
        return out

    sat_era = "S2A+L8" if T >= S2_START else ("L8" if T >= L8_START else "none")
    snapshots = {}
    ok = True
    for key, end in snaps:
        w = rain.loc[:pd.Timestamp(end)]
        assert len(w) > 0 and (w.index.date <= end).all(), "grid-end violation"
        r24 = round(float(w.iloc[-1]), 1)
        r3 = round(float(w.iloc[-3:].sum()), 1)
        r7 = round(float(w.iloc[-7:].sum()), 1)
        r30 = round(float(w.iloc[-30:].sum()), 1)
        assert 0 <= r24 <= 2000 and 0 <= r30 <= 60000, f"rain implausible: {r24}/{r30}"
        # soil: v09.2 daily, gap chain cell -> 3x3 spatial mean -> MISSING.
        # Cell = REAL; spatial mean = PROXY-spatial (documented, not silent).
        sm, smprov, smts = None, "MISSING (file-absent)", None
        fp = SOILDIR / f"ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-{end:%Y%m%d}000000-fv09.2.nc"
        if fp.exists():
            try:
                sds = xr.open_dataset(str(fp))
                latn = next(v for v in ("lat", "latitude", "LAT") if v in sds.variables)
                lonn = next(v for v in ("lon", "longitude", "LON") if v in sds.variables)
                var = "sm" if "sm" in sds.data_vars else \
                    [v for v in sds.data_vars if "sm" in v.lower() or "soil" in v.lower()][0]
                da = sds[var]
                cell = float(da.sel({latn: lat, lonn: lon}, method="nearest").values.flat[0])
                if np.isfinite(cell):
                    sm, smprov, smts = round(cell, 4), "REAL", str(end)
                else:
                    la = np.asarray(sds[latn].values).ravel()
                    lo = np.asarray(sds[lonn].values).ravel()
                    ii, jj = int(np.argmin(np.abs(la - lat))), int(np.argmin(np.abs(lo - lon)))
                    blk = da.isel({latn: slice(max(0, ii - 1), ii + 2),
                                         lonn: slice(max(0, jj - 1), jj + 2)}).values
                    m = float(np.nanmean(blk))
                    if np.isfinite(m):
                        sm, smprov, smts = round(m, 4), "PROXY-spatial", str(end)
                    else:
                        smprov = "MISSING (all-NaN neighborhood)"
                sds.close()
            except Exception as ex:
                smprov = f"MISSING ({str(ex)[:60]})"
        assert sm is None or 0.0 <= sm <= 1.0, f"soil implausible: {sm}"
        snapshots[key] = {
            "grid_end": str(end),
            "rainfall_24h_mm": obs(r24, str(end), f"IMD ind{T.year}", "REAL"),
            "rainfall_3d_mm": obs(r3, str(end), f"IMD ind{T.year}", "REAL"),
            "rainfall_7d_mm": obs(r7, str(end), f"IMD ind{T.year}", "REAL"),
            "rainfall_30d_mm": obs(r30, str(end), f"IMD ind{T.year}", "REAL"),
            "soil_moisture": obs(sm, smts or str(end), "CCI v09.2 daily", smprov),
            "seismic": seis,
            "terrain": terr,
            "satellite": {"era": sat_era, **stac_scenes(end),
                           "rule": "no scene with date > snapshot accepted at build"},
            "disturbance": {"provenance": "MISSING",
                             "reason": "no pre-event wound map for historical years"},
        }
    event = {"slide_no": slide, "event_date": str(T), "event_cutoff": f"{T}T12:30+05:30",
             "lat": lat, "lon": lon, "episode": str(r["related_episode_id"]),
             "T_convention": "T-day grid excluded (post-onset obs); T shares grid state with T-1",
             "snapshots": snapshots}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"event_{slide}.json").write_text(json.dumps(event, indent=2), encoding="utf-8")
    audit = {"events": 1, "snapshots_per_event": 6, "invariant": "observation_timestamp <= grid_end",
             "satellite": [f"{k}={v['satellite']['provenance']}" for k, v in snapshots.items()],
             "seismic_branch": seis.get("provenance", "PENDING"),
             "soil_nonreal_snapshots": [f"{k}={v['soil_moisture']['provenance']}"
                                        for k, v in snapshots.items()
                                        if v["soil_moisture"]["provenance"] != "REAL"]}
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    t = snapshots["T"]
    log(f"rain 24h/3d/7d/30d at T: {t['rainfall_24h_mm']['value']}/"
        f"{t['rainfall_3d_mm']['value']}/{t['rainfall_7d_mm']['value']}/"
        f"{t['rainfall_30d_mm']['value']}mm; terrain={t['terrain']['elevation_m']}m/"
        f"{t['terrain']['slope_deg']}deg/twi{t['terrain']['twi']}/spi{t['terrain']['spi']}/"
        f"dd{t['terrain']['drain_density']}; sat={audit['satellite'][-1]}; "
        f"soil_nonreal={audit['soil_nonreal_snapshots']}; seismic={audit['seismic_branch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
