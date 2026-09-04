"""Lachung-corridor NGEN extraction (SIH26001, closes the Lachung data gap).

Mirrors the Gangtok S1-S4 pipeline with identical methods, new coordinates.
Zone coords are read from data/sih26001/fixtures/slopes.lachung.json
(single source - never hardcode D points here).

Pedigree per feature (same bars as Gangtok):
  IMD rain ..... LOCAL NetCDF data/raw/imd/ind2024_rfp25.nc, nearest 0.25-deg
                 cell, wettest trailing-7d spell of 2024 -> 24h/7d/30d (REAL)
  USGS DEM-6 ... LOCAL tile data/raw/dem/n27_e088_1arc_v3.tif (Lachung
                 27.0-27.1N/88.2-88.3E is inside 88-89E/27-28N): bilinear
                 elev, Horn-1981 anisotropic slope/aspect, Laplacian
                 curvature + D8 priority-flood TWI/SPI + channel drain
                 density on a Lachung catchment window (REAL)
  CCI soil ..... LOCAL data/raw/soil/C3S-*.nc June 10-16 2024, same flag-mask
                 method as extract_soil_cci.py, per-D-cell mean (REAL)
  WorldCover ... SAME tile N27E087 (27-30N/87-90E covers Lachung),
                 rasterio /vsicurl/ 3x3 mode (REAL, network)
  Sentinel-2 ... Element84 STAC least-cloudy 2024 scene over Lachung bbox
                 + COG red/NIR/SCL reads (REAL, network)
  OSM .......... Overpass via extract_s1_osm.py driver, same filters/radii
                 (osm-qa-unverified, network)
  lithology .... chungthang_subgroup_gneiss PROXY-published-map (CGWB 2025:
                 Chungthang Subgroup = North-Sikkim country rock; nearest
                 verified map is Gangtok town, limit stated)
  lineament .... 0.8 km/km2 PROXY-regional (same Himalayan-50K literature
                 basis; Lachung sits INSIDE verified Bhuvan SK_LN50K_0506
                 bbox but no per-slope clip; Bhuvan clip = upgrade path)
  labels ....... LOCAL GSI shapefile SIKKIM rows, 300 m rule, event=0
                 (INITIATION year-only, same rule as Gangtok)

Outputs (committed, small):
  data/processed/terrain/lachung_ngen.json
  data/sih26001/evidence/lachung_bbox_sample.csv (<=20 SK rows)
  data/sih26001/evidence/lachung_join.json
Row values printed for the CSV freeze (review before freezing).

Run (system py311 has xarray+netCDF4+rasterio+numpy):
  python scripts/extract_lachung_ngen.py --only local
  python scripts/extract_lachung_ngen.py --only network
  python scripts/extract_lachung_ngen.py   (all)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import heapq
import json
import math
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402

FIX = ROOT / "data" / "sih26001" / "fixtures"
EVID = ROOT / "data" / "sih26001" / "evidence"
PROC = ROOT / "data" / "processed" / "terrain"
OUT_JSON = PROC / "lachung_ngen.json"

SLOPES_FIX = json.loads((FIX / "slopes.lachung.json").read_text(encoding="utf-8"))
ZONES: dict[str, tuple[float, float]] = {
    z["zone_id"]: (z["geometry"]["lat"], z["geometry"]["lon"])
    for z in SLOPES_FIX["zones"]
}

IMD_DIR = ROOT / "data" / "raw" / "imd"
SOIL_DIR = ROOT / "data" / "raw" / "soil"
USGS_TILE = ROOT / "data" / "raw" / "dem" / "n27_e088_1arc_v3.tif"
GSI_ZIP = ROOT / "data" / "raw" / "gsi" / "GSI_Landslide_Inventory.shp.zip"
S1_OSM = HERE / "extract_s1_osm.py"

WC_URL = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E087_Map.tif"
WC2LABEL = {10: "FOREST", 20: "FOREST", 30: "AGRI", 40: "AGRI",
            50: "BUILT", 60: "BARREN", 70: "WATER", 80: "WETLAND",
            90: "WETLAND", 95: "BARREN"}
STAC = "https://earth-search.aws.element84.com/v1/search"
LACH_BBOX = [88.68, 27.64, 88.80, 27.72]
LACH_CATCH = {"lat0": 27.64, "lat1": 27.72, "lon0": 88.68, "lon1": 88.80}
LABEL_BBOX = (88.65, 88.80, 27.60, 27.72)
BUFFER_M = 300.0
KILL_BITS = 4 | 8 | 16 | 32
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}


def haversine_m(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    h = (math.sin(math.radians(la2 - la1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def phase_imd() -> dict:
    import xarray as xr
    fp = IMD_DIR / "ind2024_rfp25.nc"
    assert fp.exists(), f"missing {fp}"
    cla = sum(la for la, _ in ZONES.values()) / len(ZONES)
    clo = sum(lo for _, lo in ZONES.values()) / len(ZONES)
    with xr.open_dataset(fp) as ds:
        rain = ds["RAINFALL"].sel(LATITUDE=cla, LONGITUDE=clo, method="nearest")
        alat = float(rain["LATITUDE"].values)
        alon = float(rain["LONGITUDE"].values)
        df = rain.to_dataframe(name="rainfall_mm").reset_index()
    df = df.rename(columns={"TIME": "timestamp"}).sort_values("timestamp")
    r = df.set_index("timestamp")["rainfall_mm"].fillna(0.0)
    roll7 = r.rolling(7, min_periods=7).sum()
    peak = roll7.idxmax()
    day = float(r.loc[peak])
    w7 = float(roll7.loc[peak])
    idx = r.index.get_loc(peak)
    w30 = float(r.iloc[max(0, idx - 29):idx + 1].sum())
    print(f"[OK] IMD cell lat={alat} lon={alon} rows={len(df)}")
    print(f"[OK] Lachung peak window end={peak.date()} 24h={day:.1f} 7d={w7:.1f} 30d={w30:.1f}")
    return {"cell": [alat, alon], "window_end": str(peak.date()),
            "rainfall_24h_mm": round(day, 1), "rainfall_7d_mm": round(w7, 1),
            "rainfall_30d_mm": round(w30, 1),
            "tag": "REAL (IMD 0.25-deg nearest cell, same-cell all D, stated)"}


def usgs_accumulation():
    import rasterio
    ds = rasterio.open(USGS_TILE)
    assert ds.crs.to_epsg() == 4326, ds.crs
    res = ds.res[0]
    west, south, east, north = ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top
    full = ds.read(1).astype(np.float64)

    def grid_xy(lat, lon):
        return (north - lat) / res, (lon - west) / res

    r1 = int((north - LACH_CATCH["lat1"]) / res)
    r2 = int((north - LACH_CATCH["lat0"]) / res)
    c1 = int((LACH_CATCH["lon0"] - west) / res)
    c2 = int((LACH_CATCH["lon1"] - west) / res)
    z = full[r1:r2, c1:c2].copy()
    void = (z == ds.nodata)
    print(f"[OK] Lachung window voids: {int(void.sum())} - filling by neighbour mean")
    zm = np.where(void, np.nan, z)
    for _ in range(1000):
        if not bool(np.isnan(zm).any()):
            break
        tot = np.zeros_like(zm)
        cnt = np.zeros_like(zm)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                shifted = np.roll(np.roll(zm, dr, axis=0), dc, axis=1)
                ok = ~np.isnan(shifted)
                tot += np.where(ok, shifted, 0.0)
                cnt += ok.astype(float)
        fillable = np.isnan(zm) & (cnt > 0)
        if not bool(fillable.any()):
            raise RuntimeError("unfillable void cluster")
        zm[fillable] = tot[fillable] / cnt[fillable]
    z = zm
    # Void-filled (but unflooded) full grid for per-slope derivatives: high
    # Himalaya has real SRTM voids (28k in the Lachung window vs 0 at
    # Darjeeling), so raw `full` cannot be indexed directly at N points.
    full_f = full.copy()
    full_f[r1:r2, c1:c2] = z
    H, W = z.shape
    dxm = 111320.0 * math.cos(math.radians(27.68)) * res
    filled = z.copy()
    visited = np.zeros((H, W), dtype=bool)
    heap = []
    for x in range(W):
        for y in (0, H - 1):
            heapq.heappush(heap, (filled[y, x], y, x))
            visited[y, x] = True
    for y in range(H):
        for x in (0, W - 1):
            if not visited[y, x]:
                heapq.heappush(heap, (filled[y, x], y, x))
                visited[y, x] = True
    OFFS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    while heap:
        h, y, x = heapq.heappop(heap)
        for dr, dc in OFFS8:
            ny, nx = y + dr, x + dc
            if 0 <= ny < H and 0 <= nx < W and not visited[ny, nx]:
                visited[ny, nx] = True
                filled[ny, nx] = max(z[ny, nx], h + 1e-3)
                heapq.heappush(heap, (filled[ny, nx], ny, nx))
    OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    DIST = [math.sqrt(2) * dxm if abs(dr) + abs(dc) == 2 else dxm for dr, dc in OFFS]
    recv = np.zeros((H, W, 2), dtype=np.int32)
    drop = np.zeros((H, W))
    has = np.zeros((H, W), dtype=bool)
    for (dr, dc), dist in zip(OFFS, DIST):
        dz = filled[1:-1, 1:-1] - filled[1 + dr:H - 1 + dr, 1 + dc:W - 1 + dc]
        sk = np.where(dz > 0, dz / dist, -1.0)
        better = sk > drop[1:-1, 1:-1]
        drop[1:-1, 1:-1][better] = sk[better]
        rr, cc = np.meshgrid(np.arange(1, H - 1), np.arange(1, W - 1), indexing="ij")
        recv[1:-1, 1:-1][better] = np.stack([(rr + dr)[better], (cc + dc)[better]], axis=-1)
        has[1:-1, 1:-1][better] = True
    acc = np.ones((H, W))
    order = np.argsort(-filled[1:-1, 1:-1].ravel())
    ys, xs = np.unravel_index(order, (H - 2, W - 2))
    ys, xs = ys + 1, xs + 1
    for y, x in zip(ys.tolist(), xs.tolist()):
        if has[y, x]:
            ry, cx = recv[y, x].tolist()
            if ry != y or cx != x:
                acc[ry, cx] += acc[y, x]
    print(f"[OK] Lachung accumulation done; max cells = {int(acc.max())}")
    return ds, full_f, res, west, north, grid_xy, acc, r1, c1, dxm


def phase_usgs() -> dict:
    ds, full, res, west, north, grid_xy, acc, r1, c1, dxm = usgs_accumulation()
    out = {}
    for zid, (la, lo) in ZONES.items():
        fr, fc = grid_xy(la, lo)
        r, c = int(round(fr)), int(round(fc))
        win = full[r - 1:r + 2, c - 1:c + 2]
        assert not (win == ds.nodata).any(), f"{zid}: void in 3x3"
        dx_m = 111320.0 * math.cos(math.radians(la)) * res
        dy_m = 110540.0 * res

        def bil(g, fr_, fc_):
            r0, c0 = math.floor(fr_), math.floor(fc_)
            dr_, dc_ = fr_ - r0, fc_ - c0
            return (g[r0, c0] * (1 - dr_) * (1 - dc_) + g[r0, c0 + 1] * (1 - dr_) * dc_
                    + g[r0 + 1, c0] * dr_ * (1 - dc_) + g[r0 + 1, c0 + 1] * dr_ * dc_)

        elev = round(float(bil(full, fr, fc)), 0)
        dzdx = ((win[0, 2] + 2 * win[1, 2] + win[2, 2]) - (win[0, 0] + 2 * win[1, 0] + win[2, 0])) / (8 * dx_m)
        dzdy = ((win[2, 0] + 2 * win[2, 1] + win[2, 2]) - (win[0, 0] + 2 * win[0, 1] + win[0, 2])) / (8 * dx_m)
        slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        aspect = (math.degrees(math.atan2(-dzdx, dzdy)) + 360.0) % 360.0 if slope >= 0.5 else 0.0
        d2x = (full[r, c + 1] - 2 * full[r, c] + full[r, c - 1]) / dx_m ** 2
        d2y = (full[r + 1, c] - 2 * full[r, c] + full[r - 1, c]) / dx_m ** 2
        curv = d2x + d2y
        assert 1800.0 <= elev <= 3200.0, f"{zid} elev {elev} outside Lachung plausibility"
        assert 0.0 <= slope <= 80.0, f"{zid} slope {slope} implausible"
        lr, lc = r - r1, c - c1
        a = acc[lr, lc] * dxm
        w = full[r - 1:r + 2, c - 1:c + 2]
        gx = ((w[0, 2] + 2 * w[1, 2] + w[2, 2]) - (w[0, 0] + 2 * w[1, 0] + w[2, 0])) / (8 * dxm)
        gy = ((w[2, 0] + 2 * w[2, 1] + w[2, 2]) - (w[0, 0] + 2 * w[0, 1] + w[0, 2])) / (8 * dxm)
        sl = math.degrees(math.atan(math.hypot(gx, gy)))
        tanb = max(math.tan(math.radians(sl)), 1e-4)
        twi = round(math.log(a / tanb), 2)
        spi = round(a * tanb, 1)
        assert 2.0 <= twi <= 20.0 and spi >= 0, (zid, twi, spi)
        # drain density: channel cells (>=1 km2 contributing) within 300 m
        ch_thr = 1e6 / dxm ** 2
        dmin = 300.0 / ((dxm + 110540.0 * res) / 2)
        rl0, rl1 = max(0, lr - int(dmin) - 1), min(acc.shape[0], lr + int(dmin) + 2)
        cl0, cl1 = max(0, lc - int(dmin) - 1), min(acc.shape[1], lc + int(dmin) + 2)
        n_ch = int(((acc[rl0:rl1, cl0:cl1] >= ch_thr)).sum())
        dd = round((n_ch * dxm / 1000.0) / (math.pi * 0.09), 2)
        out[zid] = {"elevation": elev, "slope_angle": round(slope, 1),
                    "aspect": round(aspect, 0), "curvature": round(float(curv), 4),
                    "twi": twi, "spi": spi, "drain_density": dd,
                    "catchment_cells": int(acc[lr, lc])}
        print(f"[OK] {zid}: elev={elev:.0f} slope={slope:.1f} asp={aspect:.0f} "
              f"curv={curv:.4f} twi={twi} spi={spi} dd={dd}")
    ds.close()
    return out


def phase_soil(window=("2024-06-10", "2024-06-16")) -> dict:
    import xarray as xr
    files = sorted(SOIL_DIR.glob("C3S-SOILMOISTURE-*.nc"))
    assert files, f"No CCI files in {SOIL_DIR}"
    out = {}
    for zid, (la, lo) in ZONES.items():
        vals, flags = [], set()
        for fp in files:
            ds = xr.open_dataset(fp)
            day = str(ds["time"].values[0])[:10]
            if not (window[0] <= day <= window[1]):
                ds.close()
                continue
            s = ds["sm"].sel(lat=la, lon=lo, method="nearest")
            fl = ds["flag"].sel(lat=la, lon=lo, method="nearest")
            alat, alon = float(s["lat"].values.item()), float(s["lon"].values.item())
            fraw = fl.values.item()
            flag = int(fraw) if fraw == fraw else -1
            flags.add(flag)
            v = float(s.values.item())
            vals.append(float("nan") if (v != v or (flag >= 0 and (flag & KILL_BITS))) else round(v, 4))
            ds.close()
        good = [v for v in vals if v == v]
        mean = round(sum(good) / len(good), 3) if good else float("nan")
        out[zid] = {"soil_moisture": mean, "valid_days": f"{len(good)}/{len(vals)}",
                    "cell": [alat, alon], "flags_seen": sorted(flags)}
        print(f"[OK] {zid}: soil={mean} valid={len(good)}/{len(vals)} cell={[alat, alon]}")
    return out


def gsi_load():
    import numpy as np
    tmp = Path(tempfile.mkdtemp(prefix="gsi_lach_"))
    with zipfile.ZipFile(GSI_ZIP) as z:
        z.extractall(tmp)
    base = tmp / "GSI_Landslide_Inventory"
    with open(str(base) + ".dbf", "rb") as f:
        h = f.read(32)
        nrec, hlen = struct.unpack("<IH", h[4:10])
        fields = []
        f.seek(32)
        while True:
            fd = f.read(32)
            if fd[0] == 0x0D:
                break
            fields.append((fd[:11].split(b"\x00")[0].decode("ascii", "ignore"),
                           chr(fd[11]), fd[16]))
    dt = [("del", "S1")] + [(n, f"S{ln}") for n, t, ln in fields]
    return np.fromfile(str(base) + ".dbf", dtype=np.dtype(dt), offset=hlen)


def clean(b: bytes) -> str:
    return b.decode("ascii", "ignore").replace("\x00", " ").strip()


def phase_labels() -> dict:
    import numpy as np
    assert GSI_ZIP.exists(), f"missing {GSI_ZIP}"
    a = gsi_load()
    wb = np.array([("SIKKIM" in clean(x).upper()) for x in a["STATE"]])
    sub = a[wb]
    print(f"[OK] SK rows: {len(sub)}")
    lon = np.array([float(x) if x.strip() else float("nan") for x in sub["LONGITUDE"]])
    lat = np.array([float(x) if x.strip() else float("nan") for x in sub["LATITUDE"]])
    ok = ~(np.isnan(lon) | np.isnan(lat))
    sub, lon, lat = sub[ok], lon[ok], lat[ok]
    print(f"[OK] SK rows with coords: {len(sub)}")
    lon0, lon1, lat0, lat1 = LABEL_BBOX
    in_bbox = ((lon >= lon0) & (lon <= lon1) & (lat >= lat0) & (lat <= lat1))
    sample = sub[in_bbox]
    assert len(sample) <= 20 * 9, f"bbox sample {len(sample)} too large to trim honestly"
    sample = sample[:180]
    EVID.mkdir(parents=True, exist_ok=True)
    cols = ["SLIDE_NO", "SLIDE_NAME", "DISTRICT", "LONGITUDE", "LATITUDE",
            "INITIATION", "TRIGGERING", "ACTIVITY", "MATERIAL_T", "GEOLOGY"]
    with (EVID / "lachung_bbox_sample.csv").open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(cols) + "\n")
        for row in sample:
            vals = []
            for c in cols:
                v = clean(row[c]).replace('"', "'")
                vals.append(f'"{v}"' if ("," in v or '"' in v) else v)
            f.write(",".join(vals) + "\n")
    print(f"[OK] Lachung-bbox sample: {len(sample)} rows")
    join, rows = {}, {}
    for zid, (la, lo) in ZONES.items():
        d = [haversine_m(la, lo, y, x) for y, x in zip(lat.tolist(), lon.tolist())]
        j = int(np.argmin(d))
        dist = round(d[j], 1)
        row = sub[j]
        info = {"slide_no": clean(row["SLIDE_NO"]), "name": clean(row["SLIDE_NAME"]),
                "district": clean(row["DISTRICT"]), "lon": float(lon[j]), "lat": float(lat[j]),
                "initiation": clean(row["INITIATION"]), "triggering": clean(row["TRIGGERING"]),
                "dist_m": dist}
        prev = 1 if dist <= BUFFER_M else 0
        event, eq = 0, ("approximate" if prev else "dated-only-negative")
        reason = (f"nearest slide {info['slide_no']} at {dist} m"
                  + (f" (INIT {info['initiation']}, year-only, not in-window)" if prev else ", outside 300 m"))
        join[zid] = {**info, "previous_landslide": prev, "event": event,
                     "evidence_quality": eq, "reason": reason}
        rows[zid] = {"previous_landslide": prev, "event": event, "evidence_quality": eq}
        print(f"[OK] {zid}: prev={prev} event={event} eq={eq} :: {reason}")
    (EVID / "lachung_join.json").write_text(json.dumps(
        {"bbox": LABEL_BBOX, "buffer_m": BUFFER_M, "join": join,
         "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        indent=2), encoding="utf-8")
    return rows


def phase_static() -> dict:
    # Lithology + lineament: honest PROXY with stated limits (same pattern as
    # Gangtok extract_lithology/extract_lineament, Lachung-specific basis).
    return {
        "lithology": {
            zid: "chungthang_subgroup_gneiss" for zid in ZONES
        },
        "lithology_basis": ("CGWB_Gangtok_2025 describes Chungthang Subgroup (biotite gneiss, quartzite, "
                            "impure marble, graphitic schist) as the North-Sikkim country rock; nearest verified "
                            "map extent is Gangtok town (DRAP Fig 9-25). PROXY-published-map, not a Bhukosh vector clip."),
        "lineament_density": {zid: 0.8 for zid in ZONES},
        "lineament_basis": ("Same Himalayan-50K literature basis as Gangtok (0.3-1.4, conservative 0.8); "
                            "Lachung lies INSIDE the verified Bhuvan layer SK_LN50K_0506 bbox "
                            "(88.035/27.073-88.892/28.061) but no per-slope vector clip was taken. "
                            "PROXY-regional; Bhuvan clip is the upgrade path."),
    }


def phase_osm(retries: int = 4, backoff_s: int = 30) -> dict:
    import time
    out = {}
    for zid, (la, lo) in ZONES.items():
        tmp = HERE / f".tmp_osm_lach_{zid}.json"
        print(f"--- {zid} ({la},{lo}) ---")
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                subprocess.run(
                    [sys.executable, str(S1_OSM), "--zone", zid,
                     "--lat", str(la), "--lon", str(lo), "--out", str(tmp)],
                    check=True,
                )
                last_err = None
                break
            except subprocess.CalledProcessError as exc:
                last_err = exc
                print(f"[WARN] {zid} attempt {attempt}/{retries} failed; "
                      f"backing off {backoff_s}s (Overpass rate-limit/DNS)")
                time.sleep(backoff_s)
        if last_err is not None:
            raise RuntimeError(f"{zid}: OSM extract failed after {retries} attempts - "
                               f"re-run --only network later (no fabrication)")
        block = json.loads(tmp.read_text(encoding="utf-8"))
        tmp.unlink()
        out[zid] = {"distance_to_road": block["row_values"]["distance_to_road"],
                    "distance_to_river": block["row_values"]["distance_to_river"],
                    "nearest_road": block["nearest_road"],
                    "nearest_river": block["nearest_river"],
                    "endpoint": block["endpoint"]}
        print(f"[OK] {zid}: road={out[zid]['distance_to_road']} river={out[zid]['distance_to_river']}")
    return out


def phase_worldcover() -> dict:
    import rasterio
    from collections import Counter
    out = {}
    with rasterio.open(WC_URL) as src:
        assert src.crs.to_epsg() == 4326, src.crs
        for zid, (la, lo) in ZONES.items():
            r, c = src.index(lo, la)
            win = src.read(1, window=((r - 1, r + 2), (c - 1, c + 2)))
            vals = [int(v) for v in win.flatten()]
            mode, n = Counter(vals).most_common(1)[0]
            centre = vals[4]
            if mode not in WC2LABEL or centre not in WC2LABEL:
                raise RuntimeError(f"UNKNOWN WorldCover code at {zid}: mode={mode} centre={centre}")
            out[zid] = {"lulc": WC2LABEL[mode], "wc_mode": mode, "wc_centre": centre,
                        "agree": n, "centre_agrees": centre == mode}
            print(f"[OK] {zid}: {out[zid]['lulc']} (WC-{mode}, agree {n}/9)")
    return out


def phase_sentinel() -> dict:
    from extract_s1_sentinel2 import cog_read
    body = json.dumps({
        "collections": ["sentinel-2-l2a"], "bbox": LACH_BBOX,
        "datetime": "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 20}}, "limit": 25,
    }).encode()
    req = urllib.request.Request(STAC, data=body,
                                 headers={"Content-Type": "application/json", **UA})
    feats = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("features", [])
    if not feats:
        raise RuntimeError("STAC returned no scenes for Lachung bbox/year")
    feats.sort(key=lambda f: f["properties"].get("eo:cloud_cover", 99))
    # The least-cloudy scene's granule may not cover all N points (one granule
    # missed D3/D4 at Darjeeling). Pick the first candidate whose red COG
    # contains every N zone - single-scene consistency preserved.
    import rasterio
    from rasterio.warp import transform as warp_transform
    item, red_href = None, None
    for cand in feats:
        href = (cand.get("assets", {}).get("red") or {}).get("href")
        if not href:
            continue
        try:
            with rasterio.open("/vsicurl/" + href) as ds:
                ok_all = True
                for la, lo in ZONES.values():
                    xs, ys = warp_transform("EPSG:4326", ds.crs, [lo], [la])
                    row, col = ds.index(xs[0], ys[0])
                    if not (0 <= row < ds.height and 0 <= col < ds.width):
                        ok_all = False
                        break
        except Exception as exc:  # noqa: BLE001 - try next candidate
            print(f"[WARN] coverage probe failed for {cand.get('id')}: {exc}")
            continue
        if ok_all:
            item, red_href = cand, href
            break
    if item is None:
        raise RuntimeError("no 2024 scene covers all N1-N4 in one granule - not shipping split-scene NDVI")
    props = item["properties"]
    pid, date, cloud = item.get("id", ""), str(props.get("datetime", ""))[:10], props.get("eo:cloud_cover")
    print(f"[OK] scene {pid} date={date} cloud={cloud}% (covers all N)")
    assets = item.get("assets", {})
    out = {"scene": {"product_id": pid, "date": date, "cloud_cover_pct": cloud,
                     "tile": props.get("grid:code", props.get("sentinel:utm_zone", ""))}}
    for zid, (la, lo) in ZONES.items():
        red, _ = cog_read(assets["red"]["href"], lo, la)
        nir, _ = cog_read(assets["nir"]["href"], lo, la)
        scl, _ = cog_read(assets["scl"]["href"], lo, la)
        scl_i = int(scl)
        if scl_i in (3, 7, 8, 9, 10, 11):
            raise RuntimeError(f"{zid} pixel is cloud/shadow/snow (SCL={scl_i}) - not shipping this NDVI")
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0.0
        assert -1.0 <= ndvi <= 1.0, (zid, ndvi)
        out[zid] = {"ndvi": round(ndvi, 3), "dn_red": round(red, 1),
                    "dn_nir": round(nir, 1), "scl": scl_i}
        print(f"[OK] {zid}: ndvi={ndvi:.3f} scl={scl_i}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Lachung NGEN extraction")
    ap.add_argument("--only", choices=["local", "network", "all"], default="all")
    args = ap.parse_args()
    merged: dict = {"zones": list(ZONES),
                    "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ")}
    if args.only in ("local", "all"):
        merged["imd"] = phase_imd()
        merged["usgs"] = phase_usgs()
        merged["soil"] = phase_soil()
        merged["labels"] = phase_labels()
        merged["static"] = phase_static()
    if args.only in ("network", "all"):
        merged["osm"] = phase_osm()
        merged["worldcover"] = phase_worldcover()
        merged["sentinel"] = phase_sentinel()
    PROC.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    sha = hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()
    print()
    print("=== LACHUNG ROW VALUES (review before CSV freeze) ===")
    imd = merged.get("imd", {})
    print(f"time_window = {imd.get('window_end', '?')}")
    for zid in ZONES:
        g = (merged.get("usgs", {}).get(zid, {}), merged.get("soil", {}).get(zid, {}),
             merged.get("worldcover", {}).get(zid, {}), merged.get("sentinel", {}).get(zid, {}),
             merged.get("osm", {}).get(zid, {}), merged.get("labels", {}).get(zid, {}))
        us, so, wc, se, os_, lb = g
        print(f"{zid}: slope={us.get('slope_angle')} elev={us.get('elevation')} asp={us.get('aspect')} "
              f"curv={us.get('curvature')} twi={us.get('twi')} spi={us.get('spi')} dd={us.get('drain_density')} "
              f"rain={imd.get('rainfall_24h_mm')}/{imd.get('rainfall_7d_mm')}/{imd.get('rainfall_30d_mm')} "
              f"soil={so.get('soil_moisture')} ndvi={se.get('ndvi')} lulc={wc.get('lulc')} "
              f"lith=chungthang_subgroup_gneiss road={os_.get('distance_to_road')} river={os_.get('distance_to_river')} "
              f"lin=0.8 prev={lb.get('previous_landslide')} event={lb.get('event')} eq={lb.get('evidence_quality')}")
    print(f"Saved: {OUT_JSON}  sha256:{sha}")


if __name__ == "__main__":
    sys.exit(main())
