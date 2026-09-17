"""E1.5b sampler: southern hard-negative candidates with Gate-A assertions.

Target: ~1600 candidates in south bbox (expect ~500+ to survive the <1km road
filter at extraction time), satisfying NOW: in-bbox, >=300m from every mapped
positive, elev 800-2500m, approx slope 5-60 deg (DEM screening only).
Road/LULC filtering happens at extraction (needs OSM/WorldCover).

DEM: data/raw/dem/n27_e088_1arc_v3.tif via rasterio (system python3.11).
Outputs: runs/e15[_c]_candidates.json/csv (--region south|north; north=E1.5c top-up).
Run: system python scripts/sample_e15_negatives.py [--region north]
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
SIDECAR = REPO / "data/sih26001/processed/training_sidecar.csv"
DEM = REPO / "data/raw/dem/n27_e088_1arc_v3.tif"

MIN_SEP_M = 300.0
SLOPE_MIN, SLOPE_MAX = 5.0, 60.0

REGIONS = {
    "south": {"seed": 42, "n": 1600,
              "bbox": {"lat_min": 27.00, "lat_max": 27.20, "lon_min": 88.06, "lon_max": 88.90},
              "elev": (800.0, 2500.0), "pos_med_note": "positives DARJ med 1094",
              "out_json": "e15_candidates.json", "out_csv": "e15_candidates.csv"},
    "north": {"seed": 4216, "n": 800,
              "bbox": {"lat_min": 27.15, "lat_max": 27.75, "lon_min": 88.06, "lon_max": 88.90},
              "elev": (800.0, 2500.0), "pos_med_note": "positives SK med 1424",
              "out_json": "e15c_candidates.json", "out_csv": "e15c_candidates.csv"},
}


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", choices=["south", "north"], default="south")
    args = ap.parse_args()
    cfg = REGIONS[args.region]
    SEED, N_TARGET, BBOX = cfg["seed"], cfg["n"], cfg["bbox"]
    ELEV_MIN, ELEV_MAX = cfg["elev"]
    OUT_JSON = REPO / "runs" / cfg["out_json"]
    OUT_CSV = REPO / "runs" / cfg["out_csv"]
    import pandas as pd
    import rasterio
    side = pd.read_csv(SIDECAR)
    pos = side[["lat", "lon"]].to_numpy()
    rng = np.random.default_rng(SEED)

    src = rasterio.open(DEM)
    band = src.read(1)
    nodata = src.nodata
    res = src.res[0]  # ~0.000277 deg

    def elev_at(lat, lon) -> float:
        r, c = src.index(lon, lat)
        if 0 <= r < band.shape[0] and 0 <= c < band.shape[1]:
            v = float(band[r, c])
            if v != nodata and -100 < v < 8000:
                return v
        return float("nan")

    def slope_at(lat, lon) -> float:
        d = res * 1.0
        zc = elev_at(lat, lon)
        zx1, zx0 = elev_at(lat, lon + d), elev_at(lat, lon - d)
        zy1, zy0 = elev_at(lat + d, lon), elev_at(lat - d, lon)
        if any(np.isnan(v) for v in (zc, zx1, zx0, zy1, zy0)):
            return float("nan")
        m_per_deg_lat = 111320.0
        m_per_deg_lon = 111320.0 * np.cos(np.radians(lat))
        dzdx = (zx1 - zx0) / (2 * d * m_per_deg_lon)
        dzdy = (zy1 - zy0) / (2 * d * m_per_deg_lat)
        return float(np.degrees(np.arctan(np.hypot(dzdx, dzdy))))

    cands: list[dict] = []
    tries = 0
    # vectorized separation check in batches
    R = 6371000.0

    def min_sep(batch: np.ndarray) -> np.ndarray:
        b = np.radians(batch)
        p = np.radians(pos)
        # batch x pos haversine (chunked over pos to bound memory)
        out = np.full(len(batch), np.inf)
        for s in range(0, len(p), 512):
            pc = p[s:s + 512]
            dphi = b[:, None, 0] - pc[None, :, 0]
            dlmb = b[:, None, 1] - pc[None, :, 1]
            a = np.sin(dphi / 2) ** 2 + np.cos(b[:, None, 0]) * np.cos(pc[None, :, 0]) * np.sin(dlmb / 2) ** 2
            out = np.minimum(out, (2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))).min(axis=1))
        return out

    while len(cands) < N_TARGET and tries < 200000:
        n = min(4000, (N_TARGET - len(cands)) * 4)
        tries += n
        blat = rng.uniform(BBOX["lat_min"], BBOX["lat_max"], n)
        blon = rng.uniform(BBOX["lon_min"], BBOX["lon_max"], n)
        sep = min_sep(np.column_stack([blat, blon]))
        keep = sep >= MIN_SEP_M
        for la, lo, sp in zip(blat[keep], blon[keep], sep[keep]):
            e = elev_at(float(la), float(lo))
            if not (ELEV_MIN <= e <= ELEV_MAX):
                continue
            sl = slope_at(float(la), float(lo))
            if not (SLOPE_MIN <= sl <= SLOPE_MAX):
                continue
            cands.append({"lat": round(float(la), 6), "lon": round(float(lo), 6),
                          "elev_dem": round(e, 1), "slope_dem": round(sl, 1),
                          "min_sep_m": round(float(sp), 1)})
            if len(cands) >= N_TARGET:
                break
    assert len(cands) >= N_TARGET, f"only {len(cands)} candidates in {tries} tries — widen bbox"
    # Gate-A assertions
    assert all(c["min_sep_m"] >= MIN_SEP_M for c in cands), "separation violated"
    assert all(BBOX["lat_min"] <= c["lat"] <= BBOX["lat_max"] for c in cands)
    assert all(BBOX["lon_min"] <= c["lon"] <= BBOX["lon_max"] for c in cands)
    assert all(ELEV_MIN <= c["elev_dem"] <= ELEV_MAX for c in cands)
    OUT_JSON.write_text(json.dumps({"seed": SEED, "n": len(cands), "bbox": BBOX,
                                    "verified_now": ["region", "separation>=300m", "elev", "slope"],
                                    "pending_extraction": ["road_dist<1km filter", "lulc", "rain", "soil",
                                                           "twi/spi/drain", "seismic", "labels=0"],
                                    "candidates": cands}, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lat", "lon", "elev_dem", "slope_dem", "min_sep_m"])
        w.writeheader()
        w.writerows(cands)
    el = np.array([c["elev_dem"] for c in cands])
    log(f"[{args.region}] wrote {len(cands)} candidates in {tries} tries; "
        f"elev med {np.median(el):.0f} ({cfg['pos_med_note']}); "
        f"sep med {np.median([c['min_sep_m'] for c in cands]):.0f}m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
