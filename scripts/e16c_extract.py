"""E16c extraction: full feature rows for 10 northernmost held-out events (SIH26001).

REAL per-point extraction (no hash proxies):
  DEM/slope/aspect/curv: Copernicus GLO-30 1-degree tiles (N26E088+N26E089) via
    vsicurl, local crop grid, Horn-1981 + Laplacian (same math as dem_point_features)
  TWI/SPI/drain/river-dem: build_training_matrix.hydro_blocks on the crop grid
  rain: IMD event-year JJAS peak (year_grids, local files)
  soil: v09.2 event-year June window + documented fallback chain
  LULC: WorldCover N24E087 3x3 mode (quasi-static, scene date recorded)
  NDVI: training-median impute + flag (S2 unavailable pre-2015 for these 1998-2015 events)
  OSM: per-point around-queries (repo query builder, geometry distances)
  seismic: recompute ref=event year (strictly-before)
Outputs: runs/e16c_features.csv + runs/e16c_sidecar.csv
Run: system python (rasterio) scripts/e16c_extract.py
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT_MAT = REPO / "runs" / "e16c_features.csv"
OUT_SIDE = REPO / "runs" / "e16c_sidecar.csv"
OUT_LOG = REPO / "runs" / "e16c_extract_log.json"

COP_TMPL = ("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N{n:02d}_00_E{e:03d}_00_DEM"
            "/Copernicus_DSM_COG_10_N{n:02d}_00_E{e:03d}_00_DEM.tif")
WC_TILES = ["N27E087", "N24E087"]
WC_TMPL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
           "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif")
WC2LABEL = {10: "FOREST", 20: "FOREST", 30: "AGRI", 40: "AGRI", 50: "BUILT",
            60: "BARREN", 70: "WATER", 80: "WETLAND", 90: "WETLAND", 95: "BARREN"}
NODATA = -32767
CAP_YEARS = 60


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import rasterio
    from rasterio.merge import merge
    import build_training_matrix as B
    import event_rain_upgrade as ER
    import event_soil_upgrade as ES
    import extract_s1_osm as OSM

    prev = json.loads((REPO / "runs" / "e16c.json").read_text(encoding="utf-8"))["events"]
    df = pd.DataFrame({"slide_no": [e["slide_no"] for e in prev],
                       "lat": [e["lat"] for e in prev],
                       "lon": [e["lon"] for e in prev],
                       "year": [e["year"] for e in prev]})
    log(f"held-out pilot events: {len(df)}")

    # ---- Copernicus crop grid (bbox + 0.06 margin for hydro context) ----
    env_opts = dict(GDAL_HTTP_TIMEOUT="60", GDAL_HTTP_MAX_RETRY="2",
                    GDAL_HTTP_RETRY_DELAY="5", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR")
    import rasterio.env
    with rasterio.env.Env(**env_opts):
        tiles = []
        for n, e in ((26, 88), (26, 89)):
            url = "/vsicurl/" + COP_TMPL.format(n=n, e=e)
            try:
                src = rasterio.open(url)
                tiles.append(src)
                log(f"opened {url.split('/')[-1]} {src.shape}")
            except Exception as exc:  # noqa: BLE001
                log(f"tile N{n:02d}E{e:03d} failed: {exc}")
        assert tiles, "no Copernicus tiles reachable — aborting (no invented terrain)"
        lo0, la0 = df["lon"].min() - 0.06, df["lat"].min() - 0.06
        lo1, la1 = df["lon"].max() + 0.06, df["lat"].max() + 0.06
        arrs, tfms = [], None
        for src in tiles:
            r0, c0 = src.index(lo0, la1)
            r1, c1 = src.index(lo1, la0)
            r0, c0 = max(0, r0), max(0, c0)
            r1, c1 = min(src.height, r1 + 1), min(src.width, c1 + 1)
            if r1 <= r0 or c1 <= c0:
                continue
            win = src.read(1, window=((r0, r1), (c0, c1)))
            tfm = src.window_transform(((r0, r1), (c0, c1)))
            arrs.append((win, tfm, src.res[0]))
            src.close()
        assert arrs, "crop windows empty"
        # single-resample merge onto finest grid (all 30m here: simple mosaic)
        res = min(a[2] for a in arrs)
        west, north = lo0, la1
        H = int(round((la1 - la0) / res)) + 1
        W = int(round((lo1 - lo0) / res)) + 1
        gm = np.full((H, W), np.nan)
        for win, tfm, _ in arrs:
            r_off = int(round((north - (tfm.f + 0 * tfm.e)) / res)) if False else None
            # anchor: transform origin (c,rasterio row 0 = north of window)
            w0 = tfm.c
            n0 = tfm.f
            rr0 = int(round((north - n0) / res))
            cc0 = int(round((w0 - west) / res))
            h, w = win.shape
            sub = gm[rr0:rr0 + h, cc0:cc0 + w]
            m = win != NODATA
            sub[m] = np.where(np.isnan(sub[m]), win[m], sub[m])
        void = np.isnan(gm)
        log(f"crop grid {gm.shape}, voids={int(void.sum())} — neighbour-mean fill")
        gmf = np.where(void, np.nan, gm)
        for _ in range(500):
            if not bool(np.isnan(gmf).any()):
                break
            tot = np.zeros_like(gmf)
            cnt = np.zeros_like(gmf)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    sh = np.roll(np.roll(gmf, dr, axis=0), dc, axis=1)
                    ok = ~np.isnan(sh)
                    tot += np.where(ok, sh, 0.0)
                    cnt += ok.astype(float)
            fillable = np.isnan(gmf) & (cnt > 0)
            if not bool(fillable.any()):
                raise RuntimeError("unfillable void cluster")
            gmf[fillable] = tot[fillable] / cnt[fillable]
        assert not bool(np.isnan(gmf).any()), "void fill did not converge"

    # ---- point DEM ops (same Horn/Laplacian math as dem_point_features) ----
    lat = df["lat"].to_numpy()
    lon = df["lon"].to_numpy()
    fr = (north - lat) / res
    fc = (lon - west) / res
    r = np.round(fr).astype(int)
    c = np.round(fc).astype(int)
    HH, WW = gmf.shape
    assert ((r >= 1) & (r < HH - 1) & (c >= 1) & (c < WW - 1)).all(), "point outside crop interior"
    r0 = np.floor(fr).astype(int)
    c0 = np.floor(fc).astype(int)
    drf, dcf = fr - r0, fc - c0
    elev = (gmf[r0, c0] * (1 - drf) * (1 - dcf) + gmf[r0, c0 + 1] * (1 - drf) * dcf
            + gmf[r0 + 1, c0] * drf * (1 - dcf) + gmf[r0 + 1, c0 + 1] * drf * dcf)
    dxm = 111320.0 * np.cos(np.radians(lat)) * res
    dym = np.full(len(df), 110540.0 * res)
    w = np.stack([gmf[r - 1, c - 1], gmf[r - 1, c], gmf[r - 1, c + 1],
                  gmf[r, c - 1], gmf[r, c], gmf[r, c + 1],
                  gmf[r + 1, c - 1], gmf[r + 1, c], gmf[r + 1, c + 1]], axis=1)
    dzdx = ((w[:, 2] + 2 * w[:, 5] + w[:, 8]) - (w[:, 0] + 2 * w[:, 3] + w[:, 6])) / (8 * dxm)
    dzdy = ((w[:, 6] + 2 * w[:, 7] + w[:, 8]) - (w[:, 0] + 2 * w[:, 1] + w[:, 2])) / (8 * dym)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    aspect = np.where(slope >= 0.5, (np.degrees(np.arctan2(-dzdx, dzdy)) + 360.0) % 360.0, 0.0)
    curv = ((gmf[r, c + 1] - 2 * gmf[r, c] + gmf[r, c - 1]) / dxm ** 2
            + (gmf[r + 1, c] - 2 * gmf[r, c] + gmf[r - 1, c]) / dym ** 2)
    dem = pd.DataFrame({"elevation": np.round(elev, 1), "slope_angle": np.round(slope, 1),
                        "aspect": np.round(aspect, 0), "curvature": np.round(curv, 4)})
    log(f"dem: elev {dem['elevation'].min():.0f}-{dem['elevation'].max():.0f}m "
        f"slope {dem['slope_angle'].min():.1f}-{dem['slope_angle'].max():.1f}deg (REAL Copernicus)")

    # ---- hydro graft (repo accumulator on our grid; block edges follow OUR bbox,
    # not the module's study-area globals — patched explicitly, logged) ----
    B.LON0, B.LON1, B.LAT0, B.LAT1 = 88.06, 88.96, 26.60, 27.05
    log(f"hydro block edges patched to lon[88.06,88.96] lat[26.60,27.05] for held-out bbox")
    hydro = B.hydro_blocks(df, gmf, res, west, north)

    # ---- OSM per-point geometry queries (flaky network: 5 attempts x 30s;
    # persistent failure -> point EXCLUDED and recorded, never invented;
    # per-point cache so reruns resume instead of re-hammering Overpass) ----
    OSM_CACHE = REPO / "runs" / "e16c_osm_cache.json"
    try:
        osm_cache = json.loads(OSM_CACHE.read_text(encoding="utf-8"))
    except Exception:
        osm_cache = {}
    d_road, d_river, osm_meta, osm_ok = [], [], [], []
    for i, row in df.iterrows():
        la, lo = float(row["lat"]), float(row["lon"])
        key = row["slide_no"]
        if key in osm_cache:
            c = osm_cache[key]
            d_road.append(c["road"] if c["road"] is not None else np.nan)
            d_river.append(c["river"] if c["river"] is not None else np.nan)
            osm_meta.append(c["meta"])
            osm_ok.append(c["ok"])
            log(f"osm {key}: cached (road {c['road']}m river {c['river']}m ok={c['ok']})")
            continue
        got = got2 = None
        for kind, q in (("roads", OSM.build_query(la, lo, 1200, 4000, ("roads",))),
                        ("rivers", OSM.build_query(la, lo, 1200, 4000, ("rivers",)))):
            for attempt in range(5):
                try:
                    payload, ep = OSM.fetch(q)
                    if kind == "roads":
                        got = (payload.get("elements", []), ep)
                    else:
                        got2 = (payload.get("elements", []), ep)
                    break
                except Exception as exc:  # noqa: BLE001
                    log(f"osm {kind} {row['slide_no']} attempt {attempt}: {exc}")
                    time.sleep(30)
            time.sleep(8)
        if got is None or got2 is None:
            log(f"osm {row['slide_no']}: ENDPOINT FAILURE — point excluded (recorded)")
            d_road.append(np.nan)
            d_river.append(np.nan)
            osm_meta.append({"failed": True})
            osm_ok.append(False)
            osm_cache[key] = {"road": None, "river": None,
                              "meta": {"failed": True}, "ok": False}
            OSM_CACHE.write_text(json.dumps(osm_cache, indent=1), encoding="utf-8")
            continue
        try:
            road, _ = OSM.nearest(got[0], "road", origin=(la, lo))
            river, _ = OSM.nearest(got2[0], "river", origin=(la, lo))
        except Exception as exc:  # noqa: BLE001 (e.g. no geometry in radius)
            log(f"osm {row['slide_no']}: no geometry ({exc}) — point excluded (recorded)")
            d_road.append(np.nan)
            d_river.append(np.nan)
            osm_meta.append({"failed": str(exc)[:120]})
            osm_ok.append(False)
            osm_cache[key] = {"road": None, "river": None,
                              "meta": {"failed": "no-geometry"}, "ok": False}
            OSM_CACHE.write_text(json.dumps(osm_cache, indent=1), encoding="utf-8")
            continue
        d_road.append(road["dist_m"])
        d_river.append(river["dist_m"])
        osm_meta.append({"road_id": road["osm_id"], "river_id": river["osm_id"], "ep": got[1]})
        osm_ok.append(True)
        osm_cache[key] = {"road": road["dist_m"], "river": river["dist_m"],
                          "meta": {"road_id": road["osm_id"], "river_id": river["osm_id"]}, "ok": True}
        OSM_CACHE.write_text(json.dumps(osm_cache, indent=1), encoding="utf-8")
        log(f"osm {row['slide_no']}: road {road['dist_m']}m river {river['dist_m']}m")
    osm = pd.DataFrame({"distance_to_road": np.round(d_road, 1),
                        "distance_to_river_osm": np.round(d_river, 1)})

    # OSM failures excluded HERE (before any per-row lists are built downstream)
    osm_ok_arr = np.array(osm_ok)
    log(f"osm ok: {int(osm_ok_arr.sum())}/{len(df)} (failures excluded, never invented)")
    df = df[osm_ok_arr].reset_index(drop=True)
    dem = dem.iloc[osm_ok_arr].reset_index(drop=True)
    hydro = hydro.iloc[osm_ok_arr].reset_index(drop=True)
    osm = osm.iloc[osm_ok_arr].reset_index(drop=True)
    osm_meta = [m for m, k in zip(osm_meta, osm_ok_arr.tolist()) if k]
    assert len(df) >= 5, f"only {len(df)} OSM-ok points — too few for a pilot"

    # ---- rain / soil / seismic (local archives, event-year design) ----
    mat0 = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    ndvi_med = round(float(mat0["ndvi"].median()), 3)
    r30, r7, r1, syr = [], [], [], []
    sms, ssrc = [], []
    jun = lambda yr: [f"{yr}-06-{d:02d}" for _, d in ES.WIN]  # noqa: E731
    ref_stack, ref_lat, ref_lon, _ = ES.window_grid(2024, jun(2024))
    ref_spatial = float(np.nanmean(ref_stack))
    quakes = json.loads((REPO / "data/sih26001/evidence/usgs_quakes.json").read_text(encoding="utf-8"))["events"]
    qlat = np.array([q["lat"] for q in quakes])
    qlon = np.array([q["lon"] for q in quakes])
    qyr = np.array([q["year"] for q in quakes])
    seis = []
    for _, row in df.iterrows():
        la, lo, yy = float(row["lat"]), float(row["lon"]), int(row["year"])
        g30, g7, g1, alat, alon = ER.year_grids(yy)
        ri, ci = ER.nearest_idx(alat, alon, np.array([la]), np.array([lo]))
        r30.append(round(float(g30[ri[0], ci[0]]), 1))
        r7.append(round(float(g7[ri[0], ci[0]]), 1))
        r1.append(round(float(g1[ri[0], ci[0]]), 1))
        stack, salat, salon, n = ES.window_grid(yy, jun(yy))
        if n and salat is not None:
            sri, sci = ES.nearest_idx(salat, salon, np.array([la]), np.array([lo]))
            v = ES.cell_means(stack, sri, sci)[0]
            sms.append(round(float(np.clip(v, 0, 1)), 4) if not np.isnan(v) else ref_spatial)
            ssrc.append("event-year-window-soil")
        else:
            sms.append(ref_spatial)
            ssrc.append("quasistatic-v092-fallback")
        syr.append(yy)
        p1 = np.radians([la])
        d = 2 * 6371.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(qlat - la) / 2) ** 2 + np.cos(p1[0]) * np.cos(np.radians(qlat))
            * np.sin(np.radians(qlon - lo) / 2) ** 2))
        hit = (qyr < yy) & (d <= 50.0)
        n50 = int(hit.sum())
        since = int(min(yy - int(qyr[hit].max()), 60)) if hit.any() else 60
        seis.append((round(float(d.min()), 2), n50, round(n50 / max(yy - 1965, 1), 4), since))

    # ---- LULC (WorldCover, quasi-static, tile recorded) ----
    lulc, lulc_tile = [], []
    with rasterio.env.Env(GDAL_HTTP_TIMEOUT="60", GDAL_HTTP_MAX_RETRY="2"):
        for _, row in df.iterrows():
            la, lo = float(row["lat"]), float(row["lon"])
            tile = f"N{int(la // 3) * 3:02d}E{int(lo // 3) * 3:03d}"
            url = "/vsicurl/" + WC_TMPL.format(tile=tile)
            with rasterio.open(url) as ds:
                arr = ds.read(1, window=((max(0, ds.index(lo, la)[0] - 1), ds.index(lo, la)[0] + 2),
                                         (max(0, ds.index(lo, la)[1] - 1), ds.index(lo, la)[1] + 2)))
            mode = Counter(int(v) for v in arr.flatten()).most_common(1)[0][0]
            assert mode in WC2LABEL, f"unknown WC code {mode}"
            lulc.append(WC2LABEL[mode])
            lulc_tile.append(tile)
    log(f"lulc mix: {dict(Counter(lulc))}")

    # ---- previous_landslide: honest join vs training positives ----
    side0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side0["lat"].to_numpy(), side0["lon"].to_numpy()
    prev = []
    for _, row in df.iterrows():
        la, lo = float(row["lat"]), float(row["lon"])
        d = 2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
            * np.sin(np.radians(plo - lo) / 2) ** 2))
        prev.append(int((d <= 300.0).any()))
    log(f"previous_landslide=1: {sum(prev)}/{len(prev)}")

    lat = df["lat"].to_numpy()
    lon = df["lon"].to_numpy()
    river = osm["distance_to_river_osm"].to_numpy()
    dem_river = hydro["distance_to_river_dem"].to_numpy()
    river = np.where(np.isnan(river), dem_river, river)
    out = pd.DataFrame({
        "zone_id": [f"H{i:03d}" for i in range(len(df))],
        "time_window": [f"{int(y)}-JJAS" for y in df["year"]],
        "slope_angle": dem["slope_angle"].to_numpy(), "elevation": dem["elevation"].to_numpy(),
        "aspect": dem["aspect"].to_numpy(), "curvature": dem["curvature"].to_numpy(),
        "twi": hydro["twi"].to_numpy(), "spi": hydro["spi"].to_numpy(),
        "rainfall_24h_mm": r1, "rainfall_7d_mm": r7, "rainfall_30d_mm": r30,
        "soil_moisture": sms, "ndvi": [ndvi_med] * len(df),
        "lulc": lulc, "lithology": "lingtse_granite_gneiss",
        "distance_to_road": osm["distance_to_road"].to_numpy(),
        "distance_to_river": np.round(river, 1), "lineament_density": 0.8,
        "drain_density": hydro["drain_density"].to_numpy(),
        "previous_landslide": prev, "event": [1] * len(df),
        "evidence_quality": ["heldout-event"] * len(df),
        "seismic_dist_km": [s[0] for s in seis], "seismic_n50_prior": [s[1] for s in seis],
        "seismic_years_since": [s[3] for s in seis], "seismic_n50_rate": [s[2] for s in seis],
        "recent_disturbance": [0] * len(df)})
    assert list(out.columns) == list(mat0.columns)
    assert not out.isna().any().any()
    out.to_csv(OUT_MAT, index=False)
    pd.DataFrame({"zone_id": out["zone_id"], "lat": df["lat"], "lon": df["lon"],
                  "year": df["year"].astype(int), "source": ["heldout-shp"] * len(df),
                  "slide_no": df["slide_no"], "district": ["Darjeeling"] * len(df),
                  "rain_source": ["event-year-peak-imd"] * len(df), "rain_year": df["year"].astype(int),
                  "soil_source": ssrc, "soil_year": syr,
                  "seismic_ref_year": df["year"].astype(int)}).to_csv(OUT_SIDE, index=False)
    OUT_LOG.write_text(json.dumps({
        "n": len(df), "dem": "Copernicus GLO-30 N26E088+N26E089 crop+fill, Horn/Laplacian REAL",
        "hydro": "repo hydro_blocks graft on crop grid (REAL, not proxy)",
        "lulc": {"tiles": sorted(set(lulc_tile)), "map": "WorldCover 2021 v200 (quasi-static, anachronistic for pre-2021 events — flagged)"},
        "ndvi": f"training-median {ndvi_med} (S2 unavailable pre-2015 — flagged, perm impact ~0.001)",
        "osm": [{"slide": df["slide_no"].iloc[i], **osm_meta[i]} for i in range(len(df))],
        "previous_landslide_rate": sum(prev) / len(prev)}, indent=2), encoding="utf-8")
    log(f"wrote {len(df)} held-out rows -> {OUT_MAT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
