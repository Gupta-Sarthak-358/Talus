"""Inventory-scale training matrix builder (SIH26001 model-training lane).

Spec: docs/sih26001/MODEL_TRAINING_HANDOFF.md (Phase 1) + target/schema from
docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md. Defaults (no owner answers):
season-window proxy target, tile-bounded study area, Phase 1.

Pipeline (all local-first; network only for WorldCover/Sentinel-2 COGs +
two bulk Overpass queries — stage 0 fails fast if offline):
  0. connectivity probe (WorldCover 1px + Overpass tiny query)
  1. positives: GSI shapefile Sikkim pts + PDF p659-676 Sikkim rows -> dedupe <50m
  2. study-area filter (tile bbox n27_e088: 88-89E/27-28N, Sikkim extent inset)
  3. negatives: seed-42 uniform, >300m from any positive, 1:1
  4. DEM point ops from USGS tile (bilinear elev, Horn slope/aspect, Laplacian curv)
  5. hydro per 0.1-deg block (+margin): priority-flood + D8 + descending
     accumulation (same defs as scripts/extract_usgs.py) -> TWI/SPI,
     drain_density (channel acc>=1km2 within 300m), distance_to_river (EDT)
  6. rain climatology 1991-2020 (IMD): per-cell June-total mean, max-7d-in-JJAS
     mean, max-daily-in-JJAS mean -> rainfall_30d/7d/24d proxy (tagged)
  7. soil quasi-static: CCI June-2024 7-day mean grid (kill-bit masked) (tagged)
  8. optical batched by 0.02-deg cell: Sentinel-2 pinned-scene NDVI (+SCL gate)
     + WorldCover 3x3-mode LULC (tagged quasi-static)
  9. OSM bulk out-center queries (roads filtered like pilot, rivers) -> local
     haversine nearest (geometry->center approx delta, logged, osm-qa-unverified)
 10. assemble 22-col matrix + sidecar (lat/lon/year/source for clustering);
     committed <=20-row stratified sample in fixture column order.

Hard rules enforced here: never reads the n=4 fixture for training (only its
header for column order); asserts both event classes + n_pos>=100; no FILL;
lithology/lineament uniform PROXY kept in sample rows but OMITTED from the
trainer feature list by scripts/train_sih26001.py (delta logged in manifest);
previous_landslide computed excl-self for sample rows, omitted from X (leakage).

Outputs (git-ignored except sample + manifest):
  data/sih26001/processed/feature_matrix.training.csv  (ML matrix, no lat/lon)
  data/sih26001/processed/training_sidecar.csv         (zone_id,lat,lon,year,source)
  data/sih26001/processed/stage caches (*.csv/.npz/.json)
  data/sih26001/evidence/feature_matrix.training.sample.csv (COMMITTED, <=20 rows)
  data/sih26001/manifest.training.json                 (COMMITTED)

Run: py scripts/build_training_matrix.py [--rebuild]  (needs numpy/pandas/
rasterio/xarray/scipy; network for stages 0/8/9)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import heapq
import json
import math
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
import sys as _sys
_sys.path.insert(0, str(REPO / "scripts"))
from extract_sikkim_labels import clean, load as load_shp_all  # noqa: E402  (struct+numpy loader, no side effects)

SEED = 42
TILE = REPO / "data/raw/dem/n27_e088_1arc_v3.tif"
PDF = REPO / "data/raw/landslide_report.pdf"
IMD_DIR = REPO / "data/raw/imd"
SOIL_GLOB = "C3S-SOILMOISTURE-*.nc"
SOIL_DIR = REPO / "data/raw/soil"
PROCDIR = REPO / "data/sih26001/processed"
EVIDDIR = REPO / "data/sih26001/evidence"
FIXDIR = REPO / "data/sih26001/fixtures"
MATRIX_CSV = PROCDIR / "feature_matrix.training.csv"
SIDECAR_CSV = PROCDIR / "training_sidecar.csv"
SAMPLE_CSV = EVIDDIR / "feature_matrix.training.sample.csv"
MANIFEST = REPO / "data/sih26001/manifest.training.json"

# Study area: inside USGS tile (88-89E/27-28N), Sikkim-extent inset (logged).
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.08, 27.999
BUFFER_M = 300.0
DEDUPE_M = 50.0
NEG_RATIO = 1.0  # 1:1
CLIM_YEARS = list(range(1991, 2021))
NODATA = -32767
KILL_BITS = 4 | 8 | 16 | 32
WC_URL = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E087_Map.tif"
WC2LABEL = {10: "FOREST", 20: "FOREST", 30: "AGRI", 40: "AGRI", 50: "BUILT",
            60: "BARREN", 70: "WATER", 80: "WETLAND", 90: "WETLAND", 95: "BARREN"}
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
ROAD_EXCL = {"footway", "path", "steps", "bridleway", "cycleway", "pedestrian"}
MOVEMENTS = {"Slide", "Flow", "Fall", "Subsidence", "Composite"}
FLOAT_RE = re.compile(r"\d{2}\.\d+")
YEAR_RE = re.compile(r"(19|20)\d{2}")

STATS: dict = {"started": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "seed": SEED}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def hav_chunk(lat1, lon1, lat2, lon2):
    """Vectorised haversine metres: (n,) x (m,) -> (n,m). Inputs degrees."""
    R = 6371000.0
    p1 = np.radians(np.asarray(lat1, dtype=float))[:, None]
    p2 = np.radians(np.asarray(lat2, dtype=float))[None, :]
    dp = p2 - p1
    dl = np.radians(np.asarray(lon2, dtype=float))[None, :] - np.radians(np.asarray(lon1, dtype=float))[:, None]
    h = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


# ---------------------------------------------------------------- stage 0
def stage0_probe(need_wc: bool = True, need_osm: bool = True) -> None:
    import rasterio
    if need_wc:
        with rasterio.open(WC_URL) as src:
            assert src.crs.to_epsg() == 4326, src.crs
        log("stage0: WorldCover reachable")
    else:
        log("stage0: WorldCover skipped (optical cached)")
    if not need_osm:
        log("stage0: Overpass skipped (OSM cached)")
        return
    q = '[out:json][timeout:60];(way["highway"](27.30,88.58,27.36,88.63););out center;'
    data = urllib.parse.urlencode({"data": q}).encode()
    for ep in OVERPASS:
        try:
            req = urllib.request.Request(ep, data=data, headers=UA)
            n = len(json.loads(urllib.request.urlopen(req, timeout=90).read()).get("elements", []))
            log(f"stage0: Overpass {ep} OK ({n} ways test bbox)")
            break
        except Exception as exc:  # noqa: BLE001
            log(f"stage0: {ep} failed: {exc}")
    else:
        raise RuntimeError("stage0: all Overpass endpoints unreachable — aborting (no silent fallback)")
    log("stage0: network probe OK (WorldCover + Overpass)")


# ---------------------------------------------------------------- stage 1
def parse_pdf_rows() -> pd.DataFrame:
    import pymupdf
    doc = pymupdf.open(str(PDF))
    assert len(doc) == 904, f"expected 904 pages, got {len(doc)}"
    pages = {p: doc[p - 1].get_text().split("\n") for p in range(659, 677)}
    anchors = []
    for pno, lines in pages.items():
        for i, ln in enumerate(lines):
            if re.fullmatch(r"\d{5}", ln.strip()):
                anchors.append((pno, i, ln.strip()))
    anchors.sort()
    rows = []
    for k, (pno, i, sl) in enumerate(anchors):
        if k + 1 < len(anchors):
            npno, ni, _ = anchors[k + 1]
            if npno == pno:
                buf = pages[pno][i + 1:ni]
            else:
                buf = pages[pno][i + 1:]
                for p in range(pno + 1, npno):
                    buf += pages[p]
                buf += pages[npno][:ni]
        else:
            buf = pages[pno][i + 1:]
        if len(buf) < 7:
            continue
        try:
            # Layouts observed in the Sikkim block (all handled, assertion guards):
            #  A normal:    Slide_No | Sikkim | District | [Name] | Loc... | lat | lon ...
            #  B 2019 file: "State: .../District : ..." + "District/Toposheet:" + year-line,
            #               then Sikkim | District | [Name] | Loc... | lat | lon ...
            #  C glued:     "<slide-no> Sikkim" (state glued onto slide_no, no state line)
            #  D no-name:   Sikkim | District | Loc(+lat-glued) — name line absent
            # Rule: STATE is the first line (from 0) that == "Sikkim", or that ends
            # with " Sikkim" while containing "/" (layout C). Everything between
            # district and the lat line is name+location (name = first part if >1).
            k = None
            slide_no = ""
            for kk in range(0, min(6, len(buf))):
                s = " ".join(buf[kk].split())
                if s == "Sikkim":
                    k = kk
                    slide_no = " ".join(" ".join(buf[:kk]).split())
                    break
                if s.endswith(" Sikkim") and "/" in s:
                    k = kk
                    slide_no = s[: -len(" Sikkim")].strip()
                    break
            if k is None:
                continue
            district = " ".join(buf[k + 1].split())
            parts, j, lat, lon = [], k + 2, "", ""
            while j < len(buf):
                m = FLOAT_RE.search(buf[j])
                if m:
                    before = buf[j][:m.start()].strip(" ,")
                    if before:
                        parts.append(before)
                    lat = m.group(0)
                    rest = buf[j][m.end():]
                    m2 = FLOAT_RE.search(rest)
                    if m2:
                        lon = m2.group(0)
                    else:
                        lon = " ".join(buf[j + 1].split())
                        j += 1
                    j += 1
                    break
                t = buf[j].strip()
                if t:
                    parts.append(t)
                j += 1
                if len(parts) > 6:
                    break
            mat_parts = []
            while j < len(buf) and " ".join(buf[j].split()) not in MOVEMENTS:
                mat_parts.append(buf[j].strip())
                j += 1
                if len(mat_parts) > 5:
                    break
            hist = " ".join(" ".join(buf[j + 1:]).split())
            name = parts[0] if len(parts) > 1 else ""
            loc = " ".join(parts[1:] if len(parts) > 1 else parts)
            la, lo = float(lat), float(lon)
            if not (20 <= la <= 35 and 80 <= lo <= 100):
                continue
            ym = YEAR_RE.search(hist)
            rows.append({"sl_no": sl, "slide_no": slide_no or f"SL-{sl}", "district": district,
                         "slide_name": name, "lat": la, "lon": lo,
                         "year": int(ym.group(0)) if ym else 0, "source": "pdf"})
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(rows)
    expect = set(str(s) for s in range(26052, 26829))  # contiguous Sikkim block (verified)
    got = set(df["sl_no"].astype(str))
    assert got == expect, f"Sl.No. coverage gap: missing={sorted(expect - got)[:10]} extra={sorted(got - expect)[:10]}"
    assert ((df["slide_no"] == "SKM/SS/78A08/2015/256")).any(), "first-SK anchor moved"
    log(f"stage1: PDF rows={len(df)} (anchor SKM/SS/78A08/2015/256 verified)")
    return df


def load_positives() -> pd.DataFrame:
    a = load_shp_all()
    is_sk = np.array([("SIKKIM" in clean(x).upper()) for x in a["STATE"]])
    sk = a[is_sk]
    lon = np.array([float(x) if x.strip() else float("nan") for x in sk["LONGITUDE"]])
    lat = np.array([float(x) if x.strip() else float("nan") for x in sk["LATITUDE"]])
    ok = ~(np.isnan(lon) | np.isnan(lat))
    sk, lon, lat = sk[ok], lon[ok], lat[ok]
    init = np.array([clean(x) for x in sk["INITIATION"]])
    year = np.array([int(v) if v.isdigit() else 0 for v in init])
    shp = pd.DataFrame({"slide_no": [clean(x) for x in sk["SLIDE_NO"]],
                        "district": [clean(x) for x in sk["DISTRICT"]],
                        "lat": lat, "lon": lon, "year": year, "source": "shp"})
    log(f"stage1: shapefile Sikkim rows={len(shp)}")
    pdf = parse_pdf_rows()
    both = pd.concat([shp, pdf[["slide_no", "district", "lat", "lon", "year", "source"]]],
                     ignore_index=True)
    # greedy <50m dedupe, shapefile priority (listed first)
    blat = both["lat"].to_numpy()
    blon = both["lon"].to_numpy()
    kept_idx: list[int] = []
    kept_lat: list[float] = []
    kept_lon: list[float] = []
    for s in range(0, len(both), 200):
        chunk = np.arange(s, min(s + 200, len(both)))
        keep = np.ones(len(chunk), dtype=bool)
        if kept_lat:
            d = hav_chunk(blat[chunk], blon[chunk], np.array(kept_lat), np.array(kept_lon))
            keep &= (d.min(axis=1) > DEDUPE_M)
        klat: list[float] = []
        klon: list[float] = []
        for k, gi in enumerate(chunk):
            if not keep[k]:
                continue
            if klat and hav_chunk(np.array([blat[gi]]), np.array([blon[gi]]),
                                  np.array(klat), np.array(klon)).min() <= DEDUPE_M:
                keep[k] = False
                continue
            klat.append(float(blat[gi]))
            klon.append(float(blon[gi]))
        kept_idx.extend(chunk[keep].tolist())
        kept_lat.extend([float(blat[gi]) for gi in chunk[keep]])
        kept_lon.extend([float(blon[gi]) for gi in chunk[keep]])
    pos = both.iloc[kept_idx].reset_index(drop=True)
    # rescue year: same slide <50m may have dated PDF history while kept shp is year 0 — take max year in cluster
    raw_lat = both["lat"].to_numpy()
    raw_lon = both["lon"].to_numpy()
    raw_year = both["year"].to_numpy()
    kept_lat_arr = pos["lat"].to_numpy()
    kept_lon_arr = pos["lon"].to_numpy()
    # vectorised distances kept x raw (764 x 1470 ~1M, fine)
    D = hav_chunk(kept_lat_arr, kept_lon_arr, raw_lat, raw_lon)
    rescued = 0
    new_years = pos["year"].to_numpy().copy()
    for i in range(len(pos)):
        mask = D[i] <= DEDUPE_M
        if mask.any():
            my = int(raw_year[mask].max())
            if my != new_years[i]:
                if new_years[i] == 0 and my != 0:
                    rescued += 1
                new_years[i] = my
    pos["year"] = new_years
    by_src = Counter(pos["source"])
    log(f"stage1: deduped positives={len(pos)} "
        f"(shp={by_src.get('shp', 0)} pdf={by_src.get('pdf', 0)} merged-away={len(both) - len(pos)})")
    log(f"stage1: year rescue {rescued} clusters 0->dated via <50m PDF counterpart")
    STATS["positives_raw"] = int(len(both))
    STATS["positives_deduped"] = int(len(pos))
    STATS["positives_by_source"] = {k: int(v) for k, v in by_src.items()}
    STATS["year_rescued"] = int(rescued)
    return pos


# ---------------------------------------------------------------- stage 2+3
def filter_and_negatives(pos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    inside = pos[(pos["lon"] >= LON0) & (pos["lon"] <= LON1)
                 & (pos["lat"] >= LAT0) & (pos["lat"] <= LAT1)].reset_index(drop=True)
    log(f"stage2: study area lon[{LON0},{LON1}] lat[{LAT0},{LAT1}]: kept={len(inside)} dropped={len(pos) - len(inside)}")
    STATS["positives_in_study"] = int(len(inside))
    assert len(inside) >= 100, f"only {len(inside)} positives in study area — aborting (need >=100)"
    rng = np.random.default_rng(SEED)
    n_neg = int(round(len(inside) * NEG_RATIO))
    pla, plo = inside["lat"].to_numpy(), inside["lon"].to_numpy()
    acc_lat: list[float] = []
    acc_lon: list[float] = []
    while len(acc_lat) < n_neg:
        n_c = (n_neg - len(acc_lat)) * 8 + 50
        clat = rng.uniform(LAT0, LAT1, n_c)
        clon = rng.uniform(LON0, LON1, n_c)
        for s in range(0, n_c, 500):
            d = hav_chunk(clat[s:s + 500], clon[s:s + 500], pla, plo)
            okm = d.min(axis=1) > BUFFER_M
            acc_lat.extend(clat[s:s + 500][okm].tolist())
            acc_lon.extend(clon[s:s + 500][okm].tolist())
            if len(acc_lat) >= n_neg:
                break
    neg = pd.DataFrame({"slide_no": [f"BG-{i:05d}" for i in range(n_neg)],
                        "district": "background", "lat": acc_lat[:n_neg], "lon": acc_lon[:n_neg],
                        "year": 0, "source": "synthetic-negative"})
    log(f"stage3: negatives={len(neg)} (seed={SEED}, buffer>{BUFFER_M:.0f}m, ratio={NEG_RATIO})")
    STATS["negatives"] = int(len(neg))
    return inside, neg


# ---------------------------------------------------------------- stage 4
def dem_point_features(df: pd.DataFrame):
    import rasterio
    with rasterio.open(TILE) as ds:
        assert ds.crs.to_epsg() == 4326, ds.crs
        res = ds.res[0]
        west, north = ds.bounds.left, ds.bounds.top
        g = ds.read(1).astype(np.float64)
    void = (g == NODATA)
    log(f"stage4: tile voids={int(void.sum())} — neighbour-mean fill")
    gm = np.where(void, np.nan, g)
    for _ in range(500):
        if not bool(np.isnan(gm).any()):
            break
        tot = np.zeros_like(gm)
        cnt = np.zeros_like(gm)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                sh = np.roll(np.roll(gm, dr, axis=0), dc, axis=1)
                ok = ~np.isnan(sh)
                tot += np.where(ok, sh, 0.0)
                cnt += ok.astype(float)
        fillable = np.isnan(gm) & (cnt > 0)
        if not bool(fillable.any()):
            raise RuntimeError("unfillable void cluster")
        gm[fillable] = tot[fillable] / cnt[fillable]
    assert not bool(np.isnan(gm).any()), "void fill did not converge"
    H, W = gm.shape
    lat = df["lat"].to_numpy()
    lon = df["lon"].to_numpy()
    fr = (north - lat) / res
    fc = (lon - west) / res
    r = np.round(fr).astype(int)
    c = np.round(fc).astype(int)
    assert ((r >= 1) & (r < H - 1) & (c >= 1) & (c < W - 1)).all(), "point outside tile interior"
    r0 = np.floor(fr).astype(int)
    c0 = np.floor(fc).astype(int)
    drf = fr - r0
    dcf = fc - c0
    elev = (gm[r0, c0] * (1 - drf) * (1 - dcf) + gm[r0, c0 + 1] * (1 - drf) * dcf
            + gm[r0 + 1, c0] * drf * (1 - dcf) + gm[r0 + 1, c0 + 1] * drf * dcf)
    dxm = 111320.0 * np.cos(np.radians(lat)) * res
    dym = np.full(len(df), 110540.0 * res)
    w = np.stack([gm[r - 1, c - 1], gm[r - 1, c], gm[r - 1, c + 1],
                  gm[r, c - 1], gm[r, c], gm[r, c + 1],
                  gm[r + 1, c - 1], gm[r + 1, c], gm[r + 1, c + 1]], axis=1)
    dzdx = ((w[:, 2] + 2 * w[:, 5] + w[:, 8]) - (w[:, 0] + 2 * w[:, 3] + w[:, 6])) / (8 * dxm)
    dzdy = ((w[:, 6] + 2 * w[:, 7] + w[:, 8]) - (w[:, 0] + 2 * w[:, 1] + w[:, 2])) / (8 * dym)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    aspect = np.where(slope >= 0.5, (np.degrees(np.arctan2(-dzdx, dzdy)) + 360.0) % 360.0, 0.0)
    curv = ((gm[r, c + 1] - 2 * gm[r, c] + gm[r, c - 1]) / dxm ** 2
            + (gm[r + 1, c] - 2 * gm[r, c] + gm[r - 1, c]) / dym ** 2)
    feat = pd.DataFrame({"elevation": np.round(elev, 1), "slope_angle": np.round(slope, 1),
                         "aspect": np.round(aspect, 0), "curvature": np.round(curv, 4)})
    log(f"stage4: elev {feat['elevation'].min():.0f}-{feat['elevation'].max():.0f}m "
        f"slope {feat['slope_angle'].min():.1f}-{feat['slope_angle'].max():.1f}deg")
    return feat, gm, res, west, north


# ---------------------------------------------------------------- stage 5
def hydro_blocks(df: pd.DataFrame, gm: np.ndarray, res: float, west: float, north: float) -> pd.DataFrame:
    from scipy.ndimage import distance_transform_edt
    BS, MG = 0.1, 0.03
    H, W = gm.shape
    n = len(df)
    twi = np.full(n, np.nan)
    spi = np.full(n, np.nan)
    drain = np.full(n, np.nan)
    rivd = np.full(n, np.nan)
    plat = df["lat"].to_numpy()
    plon = df["lon"].to_numpy()
    OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    bedges = list(np.arange(LON0, LON1, BS)) + [LON1]
    vedges = list(np.arange(LAT0, LAT1, BS)) + [LAT1]
    n_blocks = 0
    for i in range(len(bedges) - 1):
        for j in range(len(vedges) - 1):
            lo0, lo1 = bedges[i], bedges[i + 1]
            la0, la1 = vedges[j], vedges[j + 1]
            last_i = (i == len(bedges) - 2)
            last_j = (j == len(vedges) - 2)
            sel = ((plon >= lo0) & (plon < lo1 if not last_i else plon <= lo1)
                   & (plat >= la0) & (plat < la1 if not last_j else plat <= la1))
            idx = np.where(sel)[0]
            if len(idx) == 0:
                continue
            r1 = max(0, int((north - (la1 + MG)) / res))
            r2 = min(H, int((north - (la0 - MG)) / res) + 1)
            c1 = max(0, int(((lo0 - MG) - west) / res))
            c2 = min(W, int(((lo1 + MG) - west) / res) + 1)
            z = gm[r1:r2, c1:c2].copy()
            h, w = z.shape
            dxm = 111320.0 * math.cos(math.radians((la0 + la1) / 2)) * res
            dym = 110540.0 * res
            filled = z.copy()
            visited = np.zeros((h, w), dtype=bool)
            heap: list = []
            for x in range(w):
                for y in (0, h - 1):
                    heapq.heappush(heap, (filled[y, x], y, x))
                    visited[y, x] = True
            for y in range(h):
                for x in (0, w - 1):
                    if not visited[y, x]:
                        heapq.heappush(heap, (filled[y, x], y, x))
                        visited[y, x] = True
            while heap:
                hh, y, x = heapq.heappop(heap)
                for dr, dc in OFFS:
                    ny, nx = y + dr, x + dc
                    if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                        visited[ny, nx] = True
                        filled[ny, nx] = max(z[ny, nx], hh + 1e-3)
                        heapq.heappush(heap, (filled[ny, nx], ny, nx))
            DIST = [math.sqrt(2) * dxm if abs(dr) + abs(dc) == 2 else dxm for dr, dc in OFFS]
            recv = np.zeros((h, w, 2), dtype=np.int32)
            drop = np.zeros((h, w))
            has = np.zeros((h, w), dtype=bool)
            for (dr, dc), dist in zip(OFFS, DIST):
                dz = filled[1:-1, 1:-1] - filled[1 + dr:h - 1 + dr, 1 + dc:w - 1 + dc]
                sk = np.where(dz > 0, dz / dist, -1.0)
                better = sk > drop[1:-1, 1:-1]
                drop[1:-1, 1:-1][better] = sk[better]
                rr, cc = np.meshgrid(np.arange(1, h - 1), np.arange(1, w - 1), indexing="ij")
                recv[1:-1, 1:-1][better] = np.stack([(rr + dr)[better], (cc + dc)[better]], axis=-1)
                has[1:-1, 1:-1][better] = True
            acc = np.ones((h, w))
            order = np.argsort(-filled[1:-1, 1:-1].ravel(), kind="mergesort")
            ys, xs = np.unravel_index(order, (h - 2, w - 2))
            ys, xs = ys + 1, xs + 1
            recv_y = recv[:, :, 0]
            recv_x = recv[:, :, 1]
            for y, x in zip(ys.tolist(), xs.tolist()):
                if has[y, x]:
                    ry, cx = int(recv_y[y, x]), int(recv_x[y, x])
                    if ry != y or cx != x:
                        acc[ry, cx] += acc[y, x]
            ch_cells = int(1e6 / (dxm * dym))  # ~1 km^2 contributing area
            chan = acc >= ch_cells
            edt = distance_transform_edt(~chan, sampling=[dym, dxm])
            lr = np.round((north - plat[idx]) / res).astype(int) - r1
            lc = np.round((plon[idx] - west) / res).astype(int) - c1
            assert ((lr >= 0) & (lr < h) & (lc >= 0) & (lc < w)).all(), "block sampling out of range"
            a = acc[lr, lc] * dxm
            f3 = np.stack([filled[np.clip(lr + dr, 0, h - 1), np.clip(lc + dc, 0, w - 1)]
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1)], axis=1)
            gx = ((f3[:, 2] + 2 * f3[:, 5] + f3[:, 8]) - (f3[:, 0] + 2 * f3[:, 3] + f3[:, 6])) / (8 * dxm)
            gy = ((f3[:, 6] + 2 * f3[:, 7] + f3[:, 8]) - (f3[:, 0] + 2 * f3[:, 1] + f3[:, 2])) / (8 * dym)
            sl = np.degrees(np.arctan(np.hypot(gx, gy)))
            tanb = np.maximum(np.tan(np.radians(sl)), 1e-4)
            twi[idx] = np.log(a / tanb)
            spi[idx] = a * tanb
            pr = int(300 / dym) + 1
            pc = int(300 / dxm) + 1
            yy, xx = np.ogrid[-pr:pr + 1, -pc:pc + 1]
            disc = (yy * dym) ** 2 + (xx * dxm) ** 2 <= 300.0 ** 2
            dh, dw = disc.shape
            for k, (y, x) in enumerate(zip(lr.tolist(), lc.tolist())):
                y0, y1 = max(0, y - pr), min(h, y + pr + 1)
                x0, x1 = max(0, x - pc), min(w, x + pc + 1)
                my0 = y0 - (y - pr)
                mx0 = x0 - (x - pc)
                m = disc[my0:my0 + (y1 - y0), mx0:mx0 + (x1 - x0)]
                nch = int((chan[y0:y1, x0:x1] & m).sum())
                drain[idx[k]] = round(nch * 29.0 / 1000.0 / (math.pi * 0.09), 3)
            rivd[idx] = np.round(edt[lr, lc], 1)
            n_blocks += 1
    assert not bool(np.isnan(twi).any()), "TWI missing for some points"
    log(f"stage5: {n_blocks} hydro blocks; twi {np.nanmin(twi):.2f}-{np.nanmax(twi):.2f}; "
        f"drain {np.nanmin(drain):.2f}-{np.nanmax(drain):.2f}; river-d {np.nanmin(rivd):.0f}-{np.nanmax(rivd):.0f}m")
    STATS["hydro_blocks"] = n_blocks
    STATS["channel_thresh_cells"] = ch_cells
    return pd.DataFrame({"twi": np.round(twi, 2), "spi": np.round(spi, 1),
                         "drain_density": drain, "distance_to_river_dem": rivd})


# ---------------------------------------------------------------- stage 6
def rain_climatology(df: pd.DataFrame) -> pd.DataFrame:
    import xarray as xr
    sum_jun = sum_max7 = sum_max1 = cnt = None
    clat = clon = None
    have = 0
    for yr in CLIM_YEARS:
        fp = IMD_DIR / f"ind{yr}_rfp25.nc"
        if not fp.exists():
            log(f"stage6: [MISSING] {yr}")
            continue
        with xr.open_dataset(fp) as ds:
            # NOTE: IMD LATITUDE/LONGITUDE are ASCENDING (verified 6.5->38.5 / 66.5->100).
            sub = ds["RAINFALL"].sel(LATITUDE=slice(LAT0, LAT1), LONGITUDE=slice(LON0, LON1),
                                     TIME=ds["TIME"].dt.month.isin([6, 7, 8, 9]))
            assert sub.sizes.get("LATITUDE", 0) > 0 and sub.sizes.get("LONGITUDE", 0) > 0, \
                f"{yr}: empty bbox slice (grid order changed?)"
            t = sub["TIME"].to_numpy()
            v = sub.to_numpy().astype(np.float64)  # (time, lat, lon), lat desc
            months = pd.to_datetime(t).month.to_numpy()
            jun = v[months == 6]
            jjas = np.nan_to_num(v, nan=0.0)
            june_tot = np.nan_to_num(jun, nan=0.0).sum(axis=0)
            # trailing-7d max over JJAS per cell (valid convolution on time axis)
            r7 = np.apply_along_axis(lambda m: np.convolve(m, np.ones(7), mode="valid").max()
                                     if len(m) >= 7 else np.nan, 0, jjas)
            dmax = jjas.max(axis=0)
            if sum_jun is None:
                sum_jun = np.zeros_like(june_tot)
                sum_max7 = np.zeros_like(r7)
                sum_max1 = np.zeros_like(dmax)
                cnt = np.zeros_like(june_tot)
                clat = sub["LATITUDE"].to_numpy()
                clon = sub["LONGITUDE"].to_numpy()
            ok = ~(np.isnan(june_tot) | np.isnan(r7) | np.isnan(dmax))
            sum_jun[ok] += june_tot[ok]
            sum_max7[ok] += r7[ok]
            sum_max1[ok] += dmax[ok]
            cnt[ok] += 1
            have += 1
    assert have >= 25, f"only {have}/30 climatology years present"
    m_jun = sum_jun / np.maximum(cnt, 1)
    m_7 = sum_max7 / np.maximum(cnt, 1)
    m_1 = sum_max1 / np.maximum(cnt, 1)
    assert float(cnt.max()) > 0, "climatology grids empty — bbox/grid mismatch"
    alat = clat  # ascending (verified)
    g_jun, g_7, g_1 = m_jun, m_7, m_1
    ri = np.clip(np.searchsorted(alat, df["lat"].to_numpy()), 0, len(alat) - 1)
    ci = np.clip(np.searchsorted(clon, df["lon"].to_numpy()), 0, len(clon) - 1)
    out = pd.DataFrame({"rainfall_30d_mm": np.round(g_jun[ri, ci], 1),
                        "rainfall_7d_mm": np.round(g_7[ri, ci], 1),
                        "rainfall_24h_mm": np.round(g_1[ri, ci], 1)})
    for col in out.columns:
        med = float(out[col].median())
        out[col] = out[col].fillna(med)
    log(f"stage6: {have}/30 years; cell-count min={float(cnt.min()):.0f}; "
        f"jun {out['rainfall_30d_mm'].min():.0f}-{out['rainfall_30d_mm'].max():.0f}mm; "
        f"max7d {out['rainfall_7d_mm'].min():.0f}-{out['rainfall_7d_mm'].max():.0f}mm")
    STATS["clim_years"] = have
    STATS["clim_cell_min_count"] = float(cnt.min())
    return out


# ---------------------------------------------------------------- stage 7
def soil_quasistatic(df: pd.DataFrame) -> pd.DataFrame:
    import xarray as xr
    files = sorted(SOIL_DIR.glob(SOIL_GLOB))
    assert files, f"no CCI files in {SOIL_DIR}"
    tot = cnt = None
    glat = glon = None
    ndays = 0
    for fp in files:
        with xr.open_dataset(fp) as ds:
            day = str(ds["time"].values[0])[:10]
            if not ("2024-06-10" <= day <= "2024-06-16"):
                continue
            # NOTE: CCI lat is DESCENDING (verified 89.875->-89.875); lon ascending.
            sm = ds["sm"].sel(lat=slice(LAT1, LAT0), lon=slice(LON0, LON1))
            fl = ds["flag"].sel(lat=slice(LAT1, LAT0), lon=slice(LON0, LON1))
            assert sm.sizes.get("lat", 0) > 0, f"{day}: empty soil bbox slice"
            s = np.asarray(sm.to_numpy(), dtype=np.float64)
            f = np.asarray(fl.to_numpy(), dtype=np.float64)
            if s.ndim == 3:  # (time=1, lat, lon) -> drop day axis
                s = s[0]
                f = f[0]
            with np.errstate(invalid="ignore"):
                kill = (f == f) & ((f.astype(int) & KILL_BITS) != 0)
            bad = kill | (s != s) | (s < 0) | (s > 1)
            s = np.where(bad, np.nan, s)
            if tot is None:
                tot = np.zeros_like(s)
                cnt = np.zeros_like(s)
                glat = sm["lat"].to_numpy()
                glon = sm["lon"].to_numpy()
            ok = ~np.isnan(s)
            tot[ok] += s[ok]
            cnt[ok] += 1
            ndays += 1
    assert ndays == 7, f"expected 7 CCI days, got {ndays}"
    mean = tot / np.maximum(cnt, 1)
    # glat descending -> flip to ascending for searchsorted
    o = np.argsort(glat)
    glat_a = glat[o]
    mean_a = mean[o, :]
    ri = np.clip(np.searchsorted(glat_a, df["lat"].to_numpy()), 0, len(glat_a) - 1)
    ci = np.clip(np.searchsorted(glon, df["lon"].to_numpy()), 0, len(glon) - 1)
    vals = mean_a[ri, ci]
    med = float(np.nanmedian(vals))
    n_missing = int(np.isnan(vals).sum())
    vals = np.where(np.isnan(vals), med, vals)
    log(f"stage7: CCI {ndays} days; soil {np.nanmin(mean):.3f}-{np.nanmax(mean):.3f}; "
        f"missing pts imputed(median)={n_missing}")
    STATS["soil_missing_imputed"] = n_missing
    return pd.DataFrame({"soil_moisture": np.round(vals, 3)})


# ---------------------------------------------------------------- stage 8
def optical_batched(df: pd.DataFrame) -> pd.DataFrame:
    import rasterio
    s1 = json.loads((REPO / "data/processed/terrain/s1_sentinel2.json").read_text(encoding="utf-8"))
    red_href = s1["cogs"]["red"]
    nir_href = s1["cogs"]["nir"]
    scl_href = s1["cogs"]["scl"]
    log(f"stage8: pinned scene {s1['scene']['product_id']} date={s1['scene']['date']}")
    lat = df["lat"].to_numpy()
    lon = df["lon"].to_numpy()
    cell = 0.02
    keys = list(zip(np.floor((lat - LAT0) / cell).astype(int), np.floor((lon - LON0) / cell).astype(int)))
    groups: dict = {}
    for k, gi in enumerate(keys):
        groups.setdefault(gi, []).append(k)
    log(f"stage8: {len(df)} pts in {len(groups)} occupied 0.02-deg cells")
    ndvi = np.full(len(df), np.nan)
    sclv = np.full(len(df), -1)
    lulc = np.full(len(df), "", dtype=object)
    CLOUD = {3, 7, 8, 9, 10, 11}
    n_out = 0
    n_cloud = 0
    n_wc_unknown = 0
    from rasterio.warp import transform as warp_transform
    # Explicit opens (not `with`): datasets must stay alive across ~828 cell reads;
    # closed explicitly at the end of this stage.
    dR = rasterio.open("/vsicurl/" + red_href)
    dN = rasterio.open("/vsicurl/" + nir_href)
    dS = rasterio.open("/vsicurl/" + scl_href)
    dW = rasterio.open(WC_URL)
    assert dW.crs.to_epsg() == 4326, dW.crs
    def band_window(ds, lo0, lo1, la0, la1):
        """Pixel window for geo bbox in this band's own grid (bands differ: B04/B08 10m, SCL 20m)."""
        xs, ys = warp_transform("EPSG:4326", ds.crs, [lo0, lo1], [la0, la1])
        r0, c0 = ds.index(xs[0], ys[1])
        r1, c1 = ds.index(xs[1], ys[0])
        r0, r1 = max(0, r0), min(ds.height, r1 + 1)
        c0, c1 = max(0, c0), min(ds.width, c1 + 1)
        if r1 <= r0 or c1 <= c0:
            return None
        return ds.read(1, window=((r0, r1), (c0, c1))).astype(np.float64), r0, c0

    for (cy, cx), members in groups.items():
        mlat = lat[members]
        mlon = lon[members]
        # S2 window covering the cell (+~110m margin), read once per band
        la0, la1 = mlat.min() - 0.001, mlat.max() + 0.001
        lo0, lo1 = mlon.min() - 0.001, mlon.max() + 0.001
        R = band_window(dR, lo0, lo1, la0, la1)
        N = band_window(dN, lo0, lo1, la0, la1)
        S = band_window(dS, lo0, lo1, la0, la1)
        # NOTE: rasterio index() does NOT reproject — member lon/lat (degrees)
        # must be warped to each band's CRS first (UTM for S2; dW is 4326-native).
        px_r, py_r = warp_transform("EPSG:4326", dR.crs, mlon.tolist(), mlat.tolist())
        px_s, py_s = warp_transform("EPSG:4326", dS.crs, mlon.tolist(), mlat.tolist())
        for mi, gi in enumerate(members):
            got_ndvi = False
            if R is not None and N is not None and S is not None:
                try:
                    (arr_r, r0, c0) = R
                    (arr_n, _, _) = N
                    (arr_s, rs0, cs0) = S
                    rr, cc = dR.index(px_r[mi], py_r[mi])
                    lr, lc = rr - r0, cc - c0
                    rs, cs = dS.index(px_s[mi], py_s[mi])
                    lrs, lcs = rs - rs0, cs - cs0
                    if (0 <= lr < arr_r.shape[0] and 0 <= lc < arr_r.shape[1]
                            and 0 <= lrs < arr_s.shape[0] and 0 <= lcs < arr_s.shape[1]):
                        rd, nr, sc = arr_r[lr, lc], arr_n[lr, lc], int(arr_s[lrs, lcs])
                        den = nr + rd
                        nd = (nr - rd) / den if den != 0 else 0.0
                        if -1.0 <= nd <= 1.0 and sc not in CLOUD:
                            ndvi[gi] = round(float(nd), 3)
                            sclv[gi] = sc
                            got_ndvi = True
                        else:
                            n_cloud += 1
                    else:
                        n_out += 1
                except Exception:  # noqa: BLE001
                    n_out += 1
            else:
                n_out += 1
            # WorldCover 3x3 mode (own try — independent of S2).
            # NOTE: mlon/mlat are member-subsets: index with mi (position), not gi.
            try:
                wr, wc = dW.index(mlon[mi], mlat[mi])
                if not (1 <= wr < dW.height - 1 and 1 <= wc < dW.width - 1):
                    raise RuntimeError("WC edge")
                win = dW.read(1, window=((wr - 1, wr + 2), (wc - 1, wc + 2))).flatten()
                mode = Counter(int(v) for v in win).most_common(1)[0][0]
                if mode in WC2LABEL:
                    lulc[gi] = WC2LABEL[mode]
                else:
                    n_wc_unknown += 1
            except Exception:  # noqa: BLE001
                pass
    miss_ndvi = int(np.isnan(ndvi).sum())
    if miss_ndvi:
        med = float(np.nanmedian(ndvi))
        ndvi = np.where(np.isnan(ndvi), med, ndvi)
    miss_lulc = int((lulc == "").sum())
    if miss_lulc:
        mode_lab = Counter(lulc[lulc != ""].tolist()).most_common(1)[0][0]
        lulc[lulc == ""] = mode_lab
    log(f"stage8: ndvi range {np.min(ndvi):.3f}-{np.max(ndvi):.3f}; "
        f"imputed ndvi(median)={miss_ndvi} (outside-scene={n_out} cloud/snow={n_cloud}); "
        f"lulc missing->mode={miss_lulc} (unknown-codes={n_wc_unknown}); "
        f"lulc mix={dict(Counter(lulc.tolist()))}")
    STATS["ndvi_missing_imputed"] = miss_ndvi
    STATS["ndvi_outside_scene"] = n_out
    STATS["ndvi_cloud_masked"] = n_cloud
    STATS["lulc_missing_mode"] = miss_lulc
    STATS["lulc_mix"] = {k: int(v) for k, v in Counter(lulc.tolist()).items()}
    dR.close(); dN.close(); dS.close(); dW.close()
    return pd.DataFrame({"ndvi": ndvi, "lulc": lulc})


# ---------------------------------------------------------------- stage 9
def osm_bulk(df: pd.DataFrame) -> pd.DataFrame:
    cache = PROCDIR / "osm_bulk_centers.json"
    if cache.exists():
        bulk = json.loads(cache.read_text(encoding="utf-8"))
        log("stage9: using cached OSM bulk extract")
    else:
        bulk = {}
        queries = {
            "roads": f'[out:json][timeout:180];(way["highway"]({LAT0},{LON0},{LAT1},{LON1}););out center;',
            "rivers": f'[out:json][timeout:180];(way["waterway"~"^(river|stream)$"]({LAT0},{LON0},{LAT1},{LON1}););out center;',
        }
        for key, q in queries.items():
            data = urllib.parse.urlencode({"data": q}).encode()
            els = None
            for ep in OVERPASS:
                try:
                    req = urllib.request.Request(ep, data=data, headers=UA)
                    els = json.loads(urllib.request.urlopen(req, timeout=240).read()).get("elements", [])
                    log(f"stage9: {key} via {ep}: {len(els)} ways")
                    break
                except Exception as exc:  # noqa: BLE001
                    log(f"stage9: {ep} {key} failed: {exc}")
            if els is None:
                raise RuntimeError(f"stage9: all Overpass endpoints failed for {key} — aborting")
            bulk[key] = [{"id": e.get("id"), "lat": (e.get("center") or {}).get("lat"),
                          "lon": (e.get("center") or {}).get("lon"),
                          "highway": (e.get("tags") or {}).get("highway"),
                          "waterway": (e.get("tags") or {}).get("waterway")}
                         for e in els if (e.get("center") or {}).get("lat") is not None]
        cache.write_text(json.dumps(bulk), encoding="utf-8")
        log(f"stage9: cached bulk extract -> {cache}")
    roads = [w for w in bulk["roads"] if (w["highway"] or "") not in ROAD_EXCL]
    rivers = bulk["rivers"]
    log(f"stage9: usable roads={len(roads)} (filter excl {sorted(ROAD_EXCL)}), rivers={len(rivers)} "
        f"[CENTER-APPROX delta vs pilot geometry, logged]")
    plat = df["lat"].to_numpy()
    plon = df["lon"].to_numpy()
    droad = np.full(len(df), np.nan)
    driv = np.full(len(df), np.nan)
    rla = np.array([w["lat"] for w in roads])
    rlo = np.array([w["lon"] for w in roads])
    vla = np.array([w["lat"] for w in rivers])
    vlo = np.array([w["lon"] for w in rivers])
    for s in range(0, len(df), 500):
        droad[s:s + 500] = hav_chunk(plat[s:s + 500], plon[s:s + 500], rla, rlo).min(axis=1)
        if len(vla):
            driv[s:s + 500] = hav_chunk(plat[s:s + 500], plon[s:s + 500], vla, vlo).min(axis=1)
    if len(vla) == 0:
        log("stage9: WARNING no river ways — distance_to_river falls back to DEM channel (stage5)")
        driv = None
    STATS["osm_roads"] = len(roads)
    STATS["osm_rivers"] = len(rivers)
    return pd.DataFrame({"distance_to_road": np.round(droad, 1),
                         "distance_to_river_osm": np.round(driv, 1) if driv is not None else np.nan})


# ---------------------------------------------------------------- stage 10
def assemble(pos, neg, dem, hydro, rain, soil, opt, osm) -> None:
    df = pd.concat([pos, neg], ignore_index=True)
    n = len(df)
    y = np.array([1] * len(pos) + [0] * len(neg))
    assert set(np.unique(y)) == {0, 1}, "single-class matrix — aborting (never train)"
    # previous_landslide excl-self: nearest OTHER kept positive within 300m
    pla = pos["lat"].to_numpy()
    plo = pos["lon"].to_numpy()
    prev = np.zeros(n, dtype=int)
    if len(pos) > 1:
        d = hav_chunk(pla, plo, pla, plo)
        np.fill_diagonal(d, np.inf)
        prev[:len(pos)] = (d.min(axis=1) <= BUFFER_M).astype(int)
    # (negatives are >300m from every positive by construction -> 0)
    eq = np.array(["approximate"] * len(pos) + ["background"] * len(neg))
    tw = [f"{int(yr)}-JJAS" if int(yr) != 0 else "clim-JJAS" for yr in df["year"].to_numpy()]
    river = osm["distance_to_river_osm"].to_numpy()
    dem_river = hydro["distance_to_river_dem"].to_numpy()
    use_dem_fallback = int(np.isnan(river).sum())
    river = np.where(np.isnan(river), dem_river, river)
    mat = pd.DataFrame({
        "zone_id": [f"T{i:04d}" for i in range(n)],
        "time_window": tw,
        "slope_angle": dem["slope_angle"].to_numpy(),
        "elevation": dem["elevation"].to_numpy(),
        "aspect": dem["aspect"].to_numpy(),
        "curvature": dem["curvature"].to_numpy(),
        "twi": hydro["twi"].to_numpy(),
        "spi": hydro["spi"].to_numpy(),
        "rainfall_24h_mm": rain["rainfall_24h_mm"].to_numpy(),
        "rainfall_7d_mm": rain["rainfall_7d_mm"].to_numpy(),
        "rainfall_30d_mm": rain["rainfall_30d_mm"].to_numpy(),
        "soil_moisture": soil["soil_moisture"].to_numpy(),
        "ndvi": opt["ndvi"].to_numpy(),
        "lulc": opt["lulc"].to_numpy(),
        "lithology": "lingtse_granite_gneiss",
        "distance_to_road": osm["distance_to_road"].to_numpy(),
        "distance_to_river": np.round(river, 1),
        "lineament_density": 0.8,
        "drain_density": hydro["drain_density"].to_numpy(),
        "previous_landslide": prev,
        "event": y,
        "evidence_quality": eq,
    })
    assert not mat.isna().any().any(), f"nulls remain:\n{mat.isna().sum()}"
    assert ((mat["soil_moisture"] >= 0) & (mat["soil_moisture"] <= 1)).all()
    assert ((mat["ndvi"] >= -1) & (mat["ndvi"] <= 1)).all()
    assert set(mat["event"].unique()) == {0, 1}
    PROCDIR.mkdir(parents=True, exist_ok=True)
    mat.to_csv(MATRIX_CSV, index=False)
    side = pd.DataFrame({"zone_id": mat["zone_id"], "lat": df["lat"].to_numpy(),
                         "lon": df["lon"].to_numpy(), "year": df["year"].to_numpy().astype(int),
                         "source": df["source"], "slide_no": df["slide_no"],
                         "district": df["district"]})
    side.to_csv(SIDECAR_CSV, index=False)
    # committed stratified sample (10 pos + 10 neg) in fixture column order
    header = pd.read_csv(FIXDIR / "feature_matrix.sample.csv", nrows=0).columns.tolist()
    assert len(header) == 22, header
    rng = np.random.default_rng(SEED)
    pi = rng.choice(np.where(y == 1)[0], size=min(10, int((y == 1).sum())), replace=False)
    ni = rng.choice(np.where(y == 0)[0], size=min(10, int((y == 0).sum())), replace=False)
    samp = mat.iloc[sorted(np.concatenate([pi, ni]).tolist())][header]
    for col in ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
                "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
                "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
                "lineament_density", "drain_density", "previous_landslide", "event"]:
        pd.to_numeric(samp[col])
    assert not samp.isna().any().any()
    assert "FILL" not in samp.to_csv()
    samp.to_csv(SAMPLE_CSV, index=False)
    log(f"stage10: matrix {mat.shape} -> {MATRIX_CSV} sha256:{sha256(MATRIX_CSV)[:16]}…; "
        f"sidecar -> {SIDECAR_CSV}; sample {samp.shape} -> {SAMPLE_CSV}")
    log(f"stage10: river OSM-missing fallback to DEM (pts)={use_dem_fallback}; "
        f"prev=1 rate pos={prev[:len(pos)].mean():.3f}")
    STATS["matrix_shape"] = [int(n), 22]
    STATS["prev_rate_pos"] = round(float(prev[:len(pos)].mean()), 4)
    STATS["river_dem_fallback_pts"] = use_dem_fallback
    STATS["matrix_sha256"] = sha256(MATRIX_CSV)
    STATS["sidecar_sha256"] = sha256(SIDECAR_CSV)
    STATS["sample_sha256"] = sha256(SAMPLE_CSV)


def write_manifest() -> None:
    STATS["finished"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    man = {
        "lane": "model-training Phase 1 (inventory-scale susceptibility prototype)",
        "spec": "docs/sih26001/MODEL_TRAINING_HANDOFF.md",
        "defaults": "season-window proxy target; tile-bounded study area (no n28 fetch); Phase 1",
        "study_area": {"lon": [LON0, LON1], "lat": [LAT0, LAT1], "crs": "EPSG:4326",
                       "note": "inside USGS tile n27_e088 (88-89E/27-28N); Sikkim-extent inset"},
        "seeds": [SEED],
        "dedupe_m": DEDUPE_M,
        "negative_buffer_m": BUFFER_M,
        "negative_ratio": NEG_RATIO,
        "target": "event: 1=inventoried slide in season-window proxy (tagged approximate), 0=background negative",
        "features": {
            "dem6": "USGS SRTMGL1 v3 tile n27_e088 (LOCAL ONLY): bilinear elev, Horn-1981 anisotropic slope/aspect (per-point dx), Laplacian curvature",
            "twi_spi": "D8 + priority-flood + descending accumulation per 0.1-deg block (+0.03 margin); TWI=ln(a/tanB) SPI=a*tanB tanB-floor 1e-4; channel>=~1km2",
            "drain_density": "channel-cell length within 300m / pi*0.09 km2 (same accumulation grids)",
            "distance_to_river": "Overpass bulk out-center nearest (fallback: DEM channel EDT); osm-qa-unverified",
            "distance_to_road": "Overpass bulk out-center nearest, pilot highway filter; CENTER-APPROX delta vs pilot geometry (logged)",
            "rain": "IMD 0.25deg 1991-2020 climatology at nearest cell: June-total mean->30d, max-7d-in-JJAS mean->7d, max-daily-in-JJAS mean->24h (PROXY season-window, tagged)",
            "soil": "CCI COMBINED TCDR v202505 June-10-16-2024 window-mean grid, kill-bits masked (QUASI-STATIC proxy, tagged)",
            "ndvi": "Sentinel-2 pinned scene S2B_45RXL_20241129 (+SCL gate; median-imputed if outside/cloud, rate logged) (QUASI-STATIC, tagged)",
            "lulc": "ESA WorldCover 2021 v200 3x3-mode + repo mapping (REAL)",
            "lithology": "UNIFORM lingtse_granite_gneiss (PROXY-published-map, pilot value) — OMITTED from trainer X, delta logged",
            "lineament": "UNIFORM 0.8 km/km2 (PROXY-published-map, pilot value) — OMITTED from trainer X, delta logged",
            "previous_landslide": "nearest-OTHER-slide<=300m (sample rows only) — OMITTED from trainer X (leakage), delta logged",
        },
        "stats": STATS,
        "sources": {
            "shapefile": "data/raw/gsi/GSI_Landslide_Inventory.shp.zip (LOCAL ONLY)",
            "pdf": "data/raw/landslide_report.pdf p659-676 (LOCAL ONLY)",
            "dem": "data/raw/dem/n27_e088_1arc_v3.tif (LOCAL ONLY)",
            "imd": "data/raw/imd/ind1991-2020_rfp25.nc (LOCAL ONLY)",
            "soil": "data/raw/soil/C3S-SOILMOISTURE-*-DAILY-202406*.nc (LOCAL ONLY)",
            "ndvi_scene": "S2B_45RXL_20241129_0_L2A via Element84/AWS COGs (remote, pinned hrefs)",
            "lulc": "ESA WorldCover 2021 v200 N27E087 via AWS Open Data (remote)",
            "osm": "Overpass bulk out-center, study bbox (remote, cached git-ignored)",
        },
        "honesty": "INITIATION year-or-0 + PDF month/year histories cannot support per-event 24h windows — all rain/soil/ndvi time-varying inputs are climatology/quasi-static proxies, tagged; year used only for temporal-split bookkeeping + evidence tags; never invented dates.",
    }
    MANIFEST.write_text(json.dumps(man, indent=2), encoding="utf-8")
    log(f"manifest -> {MANIFEST}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build inventory-scale training matrix")
    ap.add_argument("--rebuild", action="store_true", help="ignore stage caches")
    args = ap.parse_args()
    PROCDIR.mkdir(parents=True, exist_ok=True)

    def cache(name: str):
        p = PROCDIR / f"cache_{name}.csv"
        if p.exists() and not args.rebuild:
            log(f"cache hit: {name}")
            return pd.read_csv(p)
        return None

    def save(name: str, df: pd.DataFrame):
        df.to_csv(PROCDIR / f"cache_{name}.csv", index=False)

    # Cache-aware probe: only require network for stages that must actually run.
    need_opt = args.rebuild or not (PROCDIR / "cache_optical.csv").exists()
    need_osm = args.rebuild or not (PROCDIR / "cache_osm.csv").exists()
    stage0_probe(need_wc=need_opt, need_osm=need_osm)
    pos = cache("positives")
    if pos is None:
        pos = load_positives()
        save("positives", pos)
    else:
        STATS["positives_deduped"] = int(len(pos))
    filt = cache("study")
    if filt is None:
        inside, neg = filter_and_negatives(pos)
        filt = pd.concat([inside.assign(_cls=1), neg.assign(_cls=0)], ignore_index=True)
        save("study", filt)
    else:
        STATS["positives_in_study"] = int((filt["_cls"] == 1).sum())
        STATS["negatives"] = int((filt["_cls"] == 0).sum())
    df = filt.drop(columns=["_cls"])
    y_cls = filt["_cls"].to_numpy()
    pos_df = df[y_cls == 1].reset_index(drop=True)
    neg_df = df[y_cls == 0].reset_index(drop=True)

    dem = cache("dem")
    if dem is None:
        dem, gm, res, west, north = dem_point_features(df)
        save("dem", dem)
        np.savez_compressed(PROCDIR / "cache_dem_grid.npz", gm=gm, res=np.array(res),
                            west=np.array(west), north=np.array(north))
    else:
        z = np.load(PROCDIR / "cache_dem_grid.npz")
        gm, res, west, north = z["gm"], float(z["res"]), float(z["west"]), float(z["north"])
    hydro = cache("hydro")
    if hydro is None:
        hydro = hydro_blocks(df, gm, res, west, north)
        save("hydro", hydro)
    rain = cache("rain")
    if rain is None:
        rain = rain_climatology(df)
        save("rain", rain)
    soil = cache("soil")
    if soil is None:
        soil = soil_quasistatic(df)
        save("soil", soil)
    opt = cache("optical")
    if opt is None:
        opt = optical_batched(df)
        save("optical", opt)
    osm = cache("osm")
    if osm is None:
        osm = osm_bulk(df)
        save("osm", osm)
    assemble(pos_df, neg_df, dem, hydro, rain, soil, opt, osm)
    write_manifest()
    log("BUILD OK: never touched fixtures/feature_matrix.sample.csv (header read only)")
    return 0


if __name__ == "__main__":
    sys_exit = main()
    raise SystemExit(sys_exit)
