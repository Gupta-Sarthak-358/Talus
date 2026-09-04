"""Re-derive S1-S4 terrain from the USGS SRTM 1 Arc-Second tile (Person-3 USGS round).

SOURCE: data/raw/dem/n27_e088_1arc_v3.tif (USGS SRTMGL1 v3, EPSG:4326,
3601x3601 int16, nodata -32767 — LOCAL ONLY, git-ignored; tile identity +
committed per-slope JSON + this script = full reproducibility).
This PROMOTES the six DEM derivatives from PROXY (Terrarium mirror) to REAL.

Method (same definitions as the mirror scripts, new source):
  - elevation: bilinear at exact slope coords
  - slope/aspect: Horn (1981) 3x3, anisotropic metres (dx=111320*cos(lat)/3600,
    dy=110540/3600); aspect downslope clockwise-from-north, flat<0.5deg->0
  - curvature: Laplacian central differences
  - TWI/SPI: D8 + priority-flood + descending-order accumulation on a cropped
    catchment window (lat 27.29-27.36, lon 88.57-88.63, ~7.8x5.9 km, >=5 km
    bar kept); TWI=ln(a/tanB), SPI=a*tanB, tanB floor 1e-4 logged
Voids: asserted absent in all slope 3x3 neighbourhoods (fail loudly otherwise).
Sanity vs mirror values is LOGGED, not asserted tight (sources differ
legitimately); absurdity gates only (elev +-150 m, slope +-12 deg, TWI 2-20).

Output (committed): data/processed/terrain/usgs_s234.json (per-slope values
+ tile identity + mirror deltas). Row values printed for the CSV update.

Run (needs rasterio+numpy — system py311):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_usgs.py
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio

TILE = Path("data/raw/dem/n27_e088_1arc_v3.tif")
OUTPUT = Path("data/processed/terrain/usgs_s234.json")
SLOPES = {
    "S1": (27.3450, 88.6000),
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}
# Committed mirror values for the sanity log (not targets)
MIRROR = {
    "S1": {"elevation": 1287, "slope_angle": 22.1, "twi": 4.24, "spi": 9.4},
    "S2": {"elevation": 1643, "slope_angle": 17.9, "twi": 3.96, "spi": 5.5},
    "S3": {"elevation": 1367, "slope_angle": 37.0, "twi": 4.03, "spi": 31.9},
    "S4": {"elevation": 1131, "slope_angle": 23.2, "twi": 5.47, "spi": 43.7},
}
CATCH = {"lat0": 27.29, "lat1": 27.36, "lon0": 88.57, "lon1": 88.63}


def main() -> None:
    argparse.ArgumentParser(description="USGS SRTM re-derivation").parse_args()
    ds = rasterio.open(TILE)
    assert ds.crs.to_epsg() == 4326, ds.crs
    res = ds.res[0]  # 1/3600 deg
    west, south, east, north = ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top
    full = ds.read(1).astype(np.float64)
    print(f"[OK] tile {TILE.name} {ds.width}x{ds.height} res={res} nodata={ds.nodata}")

    def grid_xy(lat, lon):
        return (north - lat) / res, (lon - west) / res  # fractional (row, col)

    def bilinear(g, fr, fc):
        r0, c0 = math.floor(fr), math.floor(fc)
        dr, dc = fr - r0, fc - c0
        return (g[r0, c0] * (1 - dr) * (1 - dc) + g[r0, c0 + 1] * (1 - dr) * dc
                + g[r0 + 1, c0] * dr * (1 - dc) + g[r0 + 1, c0 + 1] * dr * dc)

    out_slopes = {}
    for zid, (la, lo) in SLOPES.items():
        fr, fc = grid_xy(la, lo)
        r, c = int(round(fr)), int(round(fc))
        win = full[r - 1:r + 2, c - 1:c + 2]
        assert not (win == ds.nodata).any(), f"{zid}: void in 3x3 neighbourhood"
        dx_m = 111320.0 * math.cos(math.radians(la)) * res
        dy_m = 110540.0 * res
        dzdx = ((win[0, 2] + 2 * win[1, 2] + win[2, 2]) - (win[0, 0] + 2 * win[1, 0] + win[2, 0])) / (8 * dx_m)
        dzdy = ((win[2, 0] + 2 * win[2, 1] + win[2, 2]) - (win[0, 0] + 2 * win[0, 1] + win[0, 2])) / (8 * dy_m)
        slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        aspect = (math.degrees(math.atan2(-dzdx, dzdy)) + 360.0) % 360.0 if slope >= 0.5 else 0.0
        d2x = (full[r, c + 1] - 2 * full[r, c] + full[r, c - 1]) / dx_m**2
        d2y = (full[r + 1, c] - 2 * full[r, c] + full[r - 1, c]) / dy_m**2
        out_slopes[zid] = {"row": r, "col": c, "dx_m": round(dx_m, 2), "dy_m": round(dy_m, 2),
                           "elevation": round(float(bilinear(full, fr, fc)), 0),
                           "slope_angle": round(slope, 1), "aspect": round(aspect, 0),
                           "curvature": round(float(d2x + d2y), 4)}

    # Catchment window crop (pixel indices from geo bounds)
    r1 = int((north - CATCH["lat1"]) / res)
    r2 = int((north - CATCH["lat0"]) / res)
    c1 = int((CATCH["lon0"] - west) / res)
    c2 = int((CATCH["lon1"] - west) / res)
    z = full[r1:r2, c1:c2].copy()
    # Void fill (standard practice, logged): scattered SRTM voids filled by
    # iterative valid-neighbour mean. Slope 3x3 neighbourhoods were already
    # asserted void-free above, so per-slope derivatives are unaffected.
    void = (z == ds.nodata)
    print(f"[OK] voids in window: {int(void.sum())} ({100*float(void.mean()):.2f}%) — filling by neighbour mean")
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
            raise RuntimeError("unfillable void cluster (no valid neighbour)")
        zm[fillable] = tot[fillable] / cnt[fillable]
    if bool(np.isnan(zm).any()):
        raise RuntimeError("void fill did not converge")
    z = zm
    H, W = z.shape
    print(f"[OK] catchment window {H}x{W} (~{(r2-r1)*res*110.54:.1f}x{(c2-c1)*res*111.32*math.cos(math.radians(27.33)):.1f} km)")
    dxm = 111320.0 * math.cos(math.radians(27.33)) * res

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
    print("[OK] priority-flood complete; max fill = %.2f m" % float((filled - z).max()))

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
    print("[OK] accumulation done; max cells =", int(acc.max()))

    for zid, (la, lo) in SLOPES.items():
        fr, fc = grid_xy(la, lo)
        lr, lc = int(round(fr)) - r1, int(round(fc)) - c1
        edge = min(lr, lc, (r2 - r1) - 1 - lr, (c2 - c1) - 1 - lc)
        assert edge > 30, f"{zid} too close to catchment edge ({edge}px)"
        a = acc[lr, lc] * dxm
        dzdx, dzdy = None, None
        w = filled[lr - 1:lr + 2, lc - 1:lc + 2]
        dzdx = ((w[0, 2] + 2 * w[1, 2] + w[2, 2]) - (w[0, 0] + 2 * w[1, 0] + w[2, 0])) / (8 * dxm)
        dzdy = ((w[2, 0] + 2 * w[2, 1] + w[2, 2]) - (w[0, 0] + 2 * w[0, 1] + w[0, 2])) / (8 * dxm)
        sl = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        tanb = max(math.tan(math.radians(sl)), 1e-4)
        out_slopes[zid]["twi"] = round(math.log(a / tanb), 2)
        out_slopes[zid]["spi"] = round(a * tanb, 1)
        out_slopes[zid]["catchment_cells"] = int(acc[lr, lc])
        out_slopes[zid]["catch_edge_px"] = edge

    print()
    print("=== USGS VALUES vs MIRROR (sanity log, not targets) ===")
    for zid, v in out_slopes.items():
        m = MIRROR[zid]
        print(f"{zid}: elev {v['elevation']:.0f} (mir {m['elevation']}) | "
              f"slope {v['slope_angle']} (mir {m['slope_angle']}) | "
              f"aspect {v['aspect']:.0f} | curv {v['curvature']} | "
              f"twi {v['twi']} (mir {m['twi']}) | spi {v['spi']} (mir {m['spi']})")
        assert abs(v["elevation"] - m["elevation"]) <= 150, zid
        assert abs(v["slope_angle"] - m["slope_angle"]) <= 12, zid
        assert 2.0 <= v["twi"] <= 20.0 and v["spi"] >= 0, zid

    out = {"tile": {"file": TILE.name, "source": "USGS SRTM 1 Arc-Second Global v3 (SRTMGL1.003)",
                    "crs": "EPSG:4326", "local_only_gitignored": True},
           "slopes": out_slopes,
           "method": "bilinear elev; Horn-1981 anisotropic; Laplacian curv; D8 priority-flood TWI=ln(a/tanB) SPI=a*tanB",
           "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Saved: {OUTPUT}  sha256:{hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    sys.exit(main())
