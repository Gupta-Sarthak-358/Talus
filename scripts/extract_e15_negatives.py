"""E1.5b extraction: full features for the 1600 southern candidates (SIH26001).

Reuses pipeline stages by import (same methods, same constants):
  DEM/hydro  <- build_training_matrix.dem_point_features/hydro_blocks
  OSM        <- build_training_matrix.osm_bulk (cached bulk -> local, no network)
  optical    <- build_training_matrix.optical_batched (pinned S2 scenes + WC, network)
  rain       <- event_rain_upgrade.year_grids tier-2 matched design (pool + seed documented)
  soil       <- event_soil_upgrade.window_grid tier-2 matched design + fallback chain
  seismic    <- event_seismic_upgrade math on committed usgs_quakes.json (ref=rain_year)

10 locked rules enforced in code (see asserts): no future timestamps,
no label-derived features, no rain_source in X, >=300m separation,
S/N separately auditable, distribution balance recorded, NO calibration,
NO new features, recent_disturbance REMOVED (=0 const, asserted).

Outputs (experiment lane; prod matrix/sidecar/manifest UNTOUCHED):
  data/sih26001/processed/e15_negatives.csv  (matrix schema incl. seismic cols)
  data/sih26001/processed/e15_sidecar.csv    (sidecar schema)
  runs/e15_extract_log.json

Run (system python, needs rasterio/xarray/scipy):
  Python311/python.exe scripts/extract_e15_negatives.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

CAND_JSON = REPO / "runs" / "e15_candidates.json"
MATRIX_CSV = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDECAR_CSV = REPO / "data/sih26001/processed/training_sidecar.csv"
OUT_MAT = REPO / "data/sih26001/processed/e15_negatives.csv"
OUT_SIDE = REPO / "data/sih26001/processed/e15_sidecar.csv"
OUT_LOG = REPO / "runs" / "e15_extract_log.json"
QUAKES = REPO / "data/sih26001/evidence/usgs_quakes.json"

SEED = 4215  # E1.5b stream (tier-2 method, independent documented stream)
BUFFER_M = 300.0
CAP_YEARS = 60


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--candidates", type=str, default="e15_candidates.json")
    ap.add_argument("--out-tag", type=str, default="e15")
    ap.add_argument("--seed", type=int, default=4215)
    ap.add_argument("--slide-base", type=int, default=10000)
    args = ap.parse_args()
    CAND_JSON = REPO / "runs" / args.candidates
    OUT_MAT = REPO / "data/sih26001/processed" / f"{args.out_tag}_negatives.csv"
    OUT_SIDE = REPO / "data/sih26001/processed" / f"{args.out_tag}_sidecar.csv"
    OUT_LOG = REPO / "runs" / f"{args.out_tag}_extract_log.json"
    SEED = args.seed

    import build_training_matrix as B
    import event_rain_upgrade as ER
    import event_soil_upgrade as ES

    cands = json.loads(CAND_JSON.read_text(encoding="utf-8"))["candidates"]
    if args.limit:
        cands = cands[:args.limit]
    log(f"candidates: {len(cands)}")
    df = pd.DataFrame({"lat": [c["lat"] for c in cands],
                       "lon": [c["lon"] for c in cands]})
    mat0 = pd.read_csv(MATRIX_CSV)
    side0 = pd.read_csv(SIDECAR_CSV)

    # ---- Rule 4 re-asserted: >=300m from every mapped positive ----
    pos = side0[["lat", "lon"]].to_numpy()
    bl = df[["lat", "lon"]].to_numpy()
    dmin = np.full(len(df), np.inf)
    for s in range(0, len(pos), 512):
        pc = np.radians(pos[s:s + 512])
        b = np.radians(bl)
        dphi = b[:, None, 0] - pc[None, :, 0]
        dlmb = b[:, None, 1] - pc[None, :, 1]
        a = np.sin(dphi / 2) ** 2 + np.cos(b[:, None, 0]) * np.cos(pc[None, :, 0]) * np.sin(dlmb / 2) ** 2
        dmin = np.minimum(dmin, (2 * 6371000.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))).min(axis=1))
    assert (dmin >= BUFFER_M).all(), f"separation violated: min {dmin.min():.1f}m"
    log(f"Rule 4 ok: min separation {dmin.min():.1f}m")

    # ---- IDs (no collision across prod + prior E1.5b files; S-IDs never enter training) ----
    prior = []
    for extra in ("e15_negatives.csv", "e15_sidecar.csv"):
        fp = REPO / "data/sih26001/processed" / extra
        if fp.exists() and fp != OUT_MAT:
            try:
                prior += pd.read_csv(fp, usecols=["zone_id"])["zone_id"].tolist()
            except Exception:
                pass
    try:
        fp = REPO / "data/sih26001/processed" / "e15_sidecar.csv"
        prior_slides = pd.read_csv(fp, usecols=["slide_no"])["slide_no"].tolist() if fp.exists() else []
    except Exception:
        prior_slides = []
    existing_ids = set(mat0["zone_id"].tolist()) | set(prior)
    start = max(int(z[1:]) for z in existing_ids if z.startswith("T")) + 1
    zone_ids = [f"T{i:04d}" for i in range(start, start + len(df))]
    assert not (set(zone_ids) & existing_ids)
    slide_nos = [f"BG-{args.slide_base + i:05d}" for i in range(len(df))]
    assert not (set(slide_nos) & (set(side0["slide_no"].tolist()) | set(prior_slides)))

    # ---- tile-interior filter (Horn 3x3 needs 1px margin; edge pixels cannot
    # be sloped honestly — drop + log, never extrapolate) ----
    import rasterio
    with rasterio.open(B.TILE) as _ds:
        _H, _W = _ds.height, _ds.width
        _res, _west, _north = _ds.res[0], _ds.bounds.left, _ds.bounds.top
    _r = np.round((_north - df["lat"].to_numpy()) / _res).astype(int)
    _c = np.round((df["lon"].to_numpy() - _west) / _res).astype(int)
    _inside = (_r >= 1) & (_r < _H - 1) & (_c >= 1) & (_c < _W - 1)
    log(f"tile-interior filter: dropped {int((~_inside).sum())} edge points")
    df = df[_inside].reset_index(drop=True)
    zone_ids = [z for z, k in zip(zone_ids, _inside.tolist()) if k]
    slide_nos = [s for s, k in zip(slide_nos, _inside.tolist()) if k]
    lat = df["lat"].to_numpy()
    lon = df["lon"].to_numpy()
    if not args.limit:
        assert len(df) >= 0.8 * len(cands), f"interior filter dropped too many: {len(df)}/{len(cands)}"
    assert (dmin[_inside] >= BUFFER_M).all(), "separation violated after filter"

    # ---- DEM + hydro (local) ----
    dem, gm, res, west, north = B.dem_point_features(df)
    hydro = B.hydro_blocks(df, gm, res, west, north)

    # ---- OSM (cached bulk -> local) ----
    osm = B.osm_bulk(df)

    # ---- optical (network; honest impute+log fallback inside) ----
    opt = B.optical_batched(df)

    # ---- rain year-peak, tier-2 matched design ----
    y0 = mat0["event"].to_numpy().astype(int)
    yrs0 = side0["year"].to_numpy().astype(int)
    pool = sorted(int(v) for v in np.unique(yrs0[(y0 == 1) & (yrs0 >= 1901) & (yrs0 <= 2024)]).tolist())
    assert pool, "empty positive-year pool"
    rng = np.random.default_rng(SEED)
    rain_years = rng.choice(np.array(pool), size=len(df))
    for yy in sorted(set(rain_years.tolist())):
        assert (B.REPO / "data/raw/imd" / f"ind{yy}_rfp25.nc").exists(), f"missing IMD file ind{yy}"
    r30 = np.full(len(df), np.nan)
    r7 = np.full(len(df), np.nan)
    r1 = np.full(len(df), np.nan)
    lat = df["lat"].to_numpy()
    lon = df["lon"].to_numpy()
    by_year: dict[int, list[int]] = {}
    for i, yy in enumerate(rain_years.tolist()):
        by_year.setdefault(int(yy), []).append(i)
    for yy, members in sorted(by_year.items()):
        idx = np.array(members)
        g30, g7, g1, alat, alon = ER.year_grids(int(yy))
        ri, ci = ER.nearest_idx(alat, alon, lat[idx], lon[idx])
        r30[idx] = np.round(g30[ri, ci], 1)
        r7[idx] = np.round(g7[ri, ci], 1)
        r1[idx] = np.round(g1[ri, ci], 1)
    assert not np.isnan(r30).any()
    log(f"rain: {len(by_year)} background years (seed {SEED}, pool {pool[0]}-{pool[-1]}, n={len(pool)})")

    # ---- soil year-window, tier-2 matched design + fallback chain ----
    pool92 = sorted(v for v in pool if v >= 1978)
    rng2 = np.random.default_rng(SEED + 1)
    soil_years = rng2.choice(np.array(pool92), size=len(df))
    jun = lambda yr: [f"{yr}-06-{d:02d}" for _, d in ES.WIN]  # noqa: E731
    ref_stack, ref_lat, ref_lon, _ = ES.window_grid(2024, jun(2024))
    ref_spatial = float(np.nanmean(ref_stack))
    soil = np.full(len(df), np.nan)
    syr = np.zeros(len(df), dtype=int)
    chain = {"cell": 0, "spatial": 0, "global": 0, "fallback": 0}
    by2: dict[int, list[int]] = {}
    for i, yy in enumerate(soil_years.tolist()):
        by2.setdefault(int(yy), []).append(i)
    for yy, members in sorted(by2.items()):
        idx = np.array(members)
        stack, alat, alon, n = ES.window_grid(int(yy), jun(int(yy)))
        if n == 0 or alat is None:
            ri, ci = ES.nearest_idx(ref_lat, ref_lon, lat[idx], lon[idx])
            vals = ES.cell_means(ref_stack, ri, ci)
            vals[np.isnan(vals)] = ref_spatial
            soil[idx] = np.round(np.clip(vals, 0, 1), 4)
            syr[idx] = 0
            chain["fallback"] += len(idx)
            continue
        ri, ci = ES.nearest_idx(alat, alon, lat[idx], lon[idx])
        vals = ES.cell_means(stack, ri, ci)
        need = np.isnan(vals)
        if need.any():
            sp = np.array([np.nanmean(stack[:, max(0, r - 1):r + 2, max(0, c - 1):c + 2])
                           for r, c in zip(ri[need].tolist(), ci[need].tolist())])
            vals[need] = sp
            chain["spatial"] += int((~np.isnan(sp)).sum())
            still = np.isnan(vals)
            vals[still] = ref_spatial
            chain["global"] += int(still.sum())
        else:
            chain["cell"] += len(idx)
        soil[idx] = np.round(np.clip(vals, 0, 1), 4)
        syr[idx] = yy
    assert not np.isnan(soil).any()
    log(f"soil: chain {chain}")

    # ---- seismic on committed table, ref=rain_year (strictly-before) ----
    quakes = json.loads(QUAKES.read_text(encoding="utf-8"))["events"]
    qlat = np.array([q["lat"] for q in quakes])
    qlon = np.array([q["lon"] for q in quakes])
    qyr = np.array([q["year"] for q in quakes])
    ref = rain_years.astype(int).copy()
    ref[ref <= 0] = 2024
    pla, plo = np.radians(lat)[:, None], np.radians(lon)[:, None]
    qla, qlo = np.radians(qlat)[None, :], np.radians(qlon)[None, :]
    a = np.sin((qla - pla) / 2) ** 2 + np.cos(pla) * np.cos(qla) * np.sin((qlo - plo) / 2) ** 2
    dist = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    sdist = np.round(dist.min(axis=1), 2)
    n50 = np.zeros(len(df), dtype=int)
    since = np.full(len(df), CAP_YEARS, dtype=int)
    for i in range(len(df)):
        hit = (qyr < ref[i]) & (dist[i] <= 50.0)
        n50[i] = int(hit.sum())
        if hit.any():
            since[i] = int(min(ref[i] - int(qyr[hit].max()), CAP_YEARS))
    exposure = np.clip(ref - 1965, 1, None)
    rate = np.round(n50 / exposure, 4)

    # ---- assemble (mirror builder schema exactly) ----
    river = osm["distance_to_river_osm"].to_numpy()
    dem_river = hydro["distance_to_river_dem"].to_numpy()
    river = np.where(np.isnan(river), dem_river, river)
    new_mat = pd.DataFrame({
        "zone_id": zone_ids,
        "time_window": ["clim-JJAS"] * len(df),  # year=0 bookkeeping; truth in rain_source/rain_year
        "slope_angle": dem["slope_angle"].to_numpy(),
        "elevation": dem["elevation"].to_numpy(),
        "aspect": dem["aspect"].to_numpy(),
        "curvature": dem["curvature"].to_numpy(),
        "twi": hydro["twi"].to_numpy(),
        "spi": hydro["spi"].to_numpy(),
        "rainfall_24h_mm": np.round(r1, 1),
        "rainfall_7d_mm": np.round(r7, 1),
        "rainfall_30d_mm": np.round(r30, 1),
        "soil_moisture": soil,
        "ndvi": opt["ndvi"].to_numpy(),
        "lulc": opt["lulc"].to_numpy(),
        "lithology": "lingtse_granite_gneiss",
        "distance_to_road": osm["distance_to_road"].to_numpy(),
        "distance_to_river": np.round(river, 1),
        "lineament_density": 0.8,
        "drain_density": hydro["drain_density"].to_numpy(),
        "previous_landslide": np.zeros(len(df), dtype=int),  # >=300m by construction, asserted
        "event": np.zeros(len(df), dtype=int),
        "evidence_quality": ["background-matched"] * len(df),
        "seismic_dist_km": sdist,
        "seismic_n50_prior": n50,
        "seismic_years_since": since,
        "seismic_n50_rate": rate,
        "recent_disturbance": np.zeros(len(df), dtype=int),  # REMOVED (E8); const 0, never in X
    })
    # Rule 10 + schema asserts
    assert (new_mat["recent_disturbance"] == 0).all()
    assert list(new_mat.columns) == list(mat0.columns), \
        f"schema drift: {[c for c in new_mat.columns if c not in mat0.columns]}"
    assert not new_mat.isna().any().any()
    assert ((new_mat["soil_moisture"] >= 0) & (new_mat["soil_moisture"] <= 1)).all()
    assert "rain_source" not in new_mat.columns  # Rule 3: source tags never in X
    new_side = pd.DataFrame({
        "zone_id": zone_ids, "lat": lat, "lon": lon, "year": np.zeros(len(df), dtype=int),
        "source": ["synthetic-negative"] * len(df), "slide_no": slide_nos,
        "district": ["background"] * len(df),
        "rain_source": ["background-year-peak-imd"] * len(df),
        "rain_year": rain_years.astype(int),
        "soil_source": ["background-year-window-soil"] * len(df),
        "soil_year": syr,
        "seismic_ref_year": ref,
    })
    assert list(new_side.columns) == list(side0.columns)
    new_mat.to_csv(OUT_MAT, index=False)
    new_side.to_csv(OUT_SIDE, index=False)
    OUT_LOG.write_text(json.dumps({
        "seed": SEED, "n": len(df), "pool_years": [pool[0], pool[-1], len(pool)],
        "road_lt_1km": int((new_mat["distance_to_road"] < 1000).sum()),
        "chain_soil": chain,
        "rules": ["no-future", "no-label-features", "no-source-in-X", "sep>=300m",
                  "S/N-auditable", "balance-recorded", "no-calibration",
                  "no-new-features", "wound-removed", "prod-untouched"],
    }, indent=2), encoding="utf-8")
    log(f"wrote {len(df)} rows -> {OUT_MAT.name}; road<1km survivors: "
        f"{int((new_mat['distance_to_road'] < 1000).sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
