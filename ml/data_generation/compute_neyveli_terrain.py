from pathlib import Path

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.transform import array_bounds
from rasterio.windows import from_bounds

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TILE = BASE_DIR / "data" / "raw" / "dem" / "Copernicus_DSM_GLO30_N11_E079.tif"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "terrain"

CONTEXT_WEST, CONTEXT_EAST = 79.35, 79.70
CONTEXT_SOUTH, CONTEXT_NORTH = 11.30, 11.70

FOCUS_WEST, FOCUS_EAST = 79.45, 79.58
FOCUS_SOUTH, FOCUS_NORTH = 11.45, 11.53

SLOPE_THRESHOLDS = [1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 45.0]
PERCENTILES = [50, 90, 95, 99, 99.9]
PIT_THRESHOLDS = [0.0, -20.0, -50.0, -75.0]

DEG_LAT_M = 110540.0
METERS_PER_DEGREE_LON = 111320.0


def read_window(src, west, south, east, north):
    win = from_bounds(west, south, east, north, src.transform)
    elev = src.read(1, window=win).astype(np.float32)
    return elev, win


def dst_resolution(transform):
    return abs(transform.a), abs(transform.e)


def compute_slope(elev, res_x_m, res_y_m):
    dz_dx = np.gradient(elev, axis=1)
    dz_dy = np.gradient(elev, axis=0)
    grad = np.sqrt((dz_dx / res_x_m) ** 2 + (dz_dy / res_y_m) ** 2)
    return np.degrees(np.arctan(grad))


def block_relief_3x3(elev):
    mx = elev.copy()
    mn = elev.copy()
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if i == 0 and j == 0:
                continue
            shifted_mx = np.full_like(elev, -np.inf)
            shifted_mn = np.full_like(elev, np.inf)
            shifted_mx[max(0, i): elev.shape[0] + min(0, i), max(0, j): elev.shape[1] + min(0, j)] = (
                elev[max(0, -i): elev.shape[0] - max(0, i), max(0, -j): elev.shape[1] - max(0, j)]
            )
            shifted_mn[max(0, i): elev.shape[0] + min(0, i), max(0, j): elev.shape[1] + min(0, j)] = (
                elev[max(0, -i): elev.shape[0] - max(0, i), max(0, -j): elev.shape[1] - max(0, j)]
            )
            mx = np.maximum(mx, shifted_mx)
            mn = np.minimum(mn, shifted_mn)
    return mx - mn


def summarize(name, values, res_x_m, res_y_m, slope=None, relief=None, out_dct=None):
    flat = values[~np.isnan(values)]
    st = {
        "name": name,
        "n_cells": int(flat.size),
        "min_m": round(float(flat.min()), 3),
        "max_m": round(float(flat.max()), 3),
        "mean_m": round(float(flat.mean()), 3),
        "median_m": round(float(np.median(flat)), 3),
        "std_m": round(float(flat.std()), 3),
        "range_m": round(float(flat.max() - flat.min()), 3),
    }
    for p in PERCENTILES:
        st[f"p{p}"] = round(float(np.percentile(flat, p)), 3)

    if slope is not None:
        sflat = slope[~np.isnan(slope)]
        s = {"min_deg": round(float(sflat.min()), 3), "max_deg": round(float(sflat.max()), 3),
             "mean_deg": round(float(sflat.mean()), 3), "median_deg": round(float(np.median(sflat)), 3),
             "std_deg": round(float(sflat.std()), 3)}
        for p in PERCENTILES:
            s[f"p{p}_deg"] = round(float(np.percentile(sflat, p)), 3)
        s["pct_area_over"] = {}
        for th in SLOPE_THRESHOLDS:
            s["pct_area_over"][f"{th:.0f}deg"] = round(float((sflat > th).mean()) * 100, 4)
        st["slope"] = s

    if relief is not None:
        rflat = relief[~np.isnan(relief)]
        st["local_relief_3x3"] = {
            "mean_m": round(float(rflat.mean()), 3),
            "max_m": round(float(rflat.max()), 3),
            "p95_m": round(float(np.percentile(rflat, 95)), 3),
        }

    if name == "mine_focus":
        pit = {}
        for th in PIT_THRESHOLDS:
            pit[f"below_{th:g}m_pct"] = round(float((flat < th).mean()) * 100, 4)
        pit["area_km2"] = round(flat.size * 30.92 * 30.71 / 1e6, 3)
        pit["pit_area_km2_below_0m"] = round(
            int((flat < 0).sum()) * 30.92 * 30.71 / 1e6, 3
        )
        st["pit"] = pit

    return st


def plot_map(values, title, path, cmap, vmin=None, vmax=None, fmt=None):
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(values, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    if fmt:
        cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))
    ax.set_title(title)
    ax.set_xlabel("pixels (~30 m)")
    ax.set_ylabel("pixels (~30 m)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(DEFAULT_TILE) as src:
        tile = {"crs": str(src.crs), "width": src.width, "height": src.height,
                "bounds": list(src.bounds)}
        res_deg_x, res_deg_y = dst_resolution(src.transform)
        res_x_m = res_deg_x * METERS_PER_DEGREE_LON
        res_y_m = res_deg_y * DEG_LAT_M

        tiles = {
            "context": (CONTEXT_WEST, CONTEXT_SOUTH, CONTEXT_EAST, CONTEXT_NORTH),
            "mine_focus": (FOCUS_WEST, FOCUS_SOUTH, FOCUS_EAST, FOCUS_NORTH),
        }

        results = {"tile": tile, "resolution_m": {"x": round(res_x_m, 2), "y": round(res_y_m, 2)},
                   "tiles_loaded": {}}

        for name, (w, s, e, n) in tiles.items():
            elev, win = read_window(src, w, s, e, n)
            slope = compute_slope(elev, res_x_m, res_y_m)
            relief = block_relief_3x3(elev)
            st = summarize(name, elev, res_x_m, res_y_m, slope=slope, relief=relief)
            results["tiles_loaded"][name] = st

            out_elev = OUTPUT_DIR / f"elevation_{name}.tif"
            out_slope = OUTPUT_DIR / f"slope_{name}.tif"
            transform = rasterio.transform.from_bounds(w, s, e, n, elev.shape[1], elev.shape[0])
            with rasterio.open(out_elev, "w", driver="GTiff", height=elev.shape[0],
                               width=elev.shape[1], count=1, dtype=str(elev.dtype),
                               crs=src.crs, transform=transform) as dst:
                dst.write(elev, 1)
            with rasterio.open(out_slope, "w", driver="GTiff", height=slope.shape[0],
                               width=slope.shape[1], count=1, dtype=str(slope.dtype),
                               crs=src.crs, transform=transform) as dst:
                dst.write(slope, 1)
            st["files"] = {"elevation": str(out_elev.relative_to(BASE_DIR)),
                           "slope": str(out_slope.relative_to(BASE_DIR))}

            plot_map(elev, f"Elevation (m) — {name}", OUTPUT_DIR / f"elevation_{name}.png",
                     "terrain", fmt=lambda v, pos: f"{v:,.0f}m")
            vmax_slope = max(st["slope"]["p99_deg"], 5.0)
            plot_map(slope, f"Slope (deg) — {name}", OUTPUT_DIR / f"slope_{name}.png",
                     "YlOrRd", vmin=0, vmax=vmax_slope, fmt=lambda v, pos: f"{v:.1f}°")

            if name == "mine_focus":
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.hist(elev[~np.isnan(elev)], bins=60, color="#4c72b0")
                ax.axvline(0, color="#c44e52", ls="--", label="sea level")
                ax.set_xlabel("Elevation (m)")
                ax.set_ylabel("Cells (30 m)")
                ax.set_title("Mine focus elevation histogram — note pit (negative) mode")
                ax.legend()
                fig.tight_layout()
                fig.savefig(OUTPUT_DIR / "elevation_histogram_mine_focus.png", dpi=150)
                plt.close(fig)

        OUTPUT_DIR.joinpath("terrain_summary.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )

    print(json.dumps(results, indent=2))
    print()
    print("Saved under:", OUTPUT_DIR)


if __name__ == "__main__":
    main()