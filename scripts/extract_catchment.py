"""Catchment-scale DEM derivatives for S1-S4 (SIH26001, Person-3 catchment round).

WHY: TWI/SPI need catchment flow routing; the committed 64-px window is
edge-corrupted for this (documented). This script fetches a z14 3x3 Terrarium
mosaic (~6.5 km side, meets the >=5 km context bar in PERSON3_HANDOFF.md §4),
runs D8 flow routing with pit filling, and derives per-slope:
  - TWI = ln(a / tanB), a = specific catchment area (m2/m), B = Horn slope
  - SPI = a * tanB
  - plus S2-S4 slope/elevation/aspect/curvature (S1 keeps its committed z15
    values; z14 agreement is logged as a consistency check, not a replacement)
SOURCE HONESTY: AWS Terrain Tiles Terrarium (SRTM-derived mirror, open, no
account) — NOT the USGS N27E088 tile. All values PROXY with stated limits:
mirror resampling smooths micro-relief; D8 on 8.5-m pixels approximates true
flow; border cells (outer 64 px) have truncated catchments (slopes are
interior, min edge distance logged); flats capped at tanB>=1e-4 (logged).

Outputs (committed):
  data/processed/terrain/terrarium_z14/z14_{x}_{y}.png  (9 source tiles)
  data/processed/terrain/catchment_s234.json            (per-slope values +
  method + edge distances + consistency checks)

Run: <venv-python> scripts/extract_catchment.py  (needs numpy only)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_s1_dem import (  # noqa: E402  (single source of truth for tiles/decode)
    Z as _Z15,
    decode_png_rgb,
    deg2tile,
    fetch_png,
    px_size_m,
    terrarium_elev,
)

Z = 14
SLOPES = {
    "S1": (27.3450, 88.6000),
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}
# Mosaic centred on the S1-S4 centroid (not S1) so all four slopes clear the
# 64-px edge margin: span is ~3.3 km N-S inside a ~6.5 km mosaic.
CENTER = (27.3308, 88.6034)
PNG_DIR = Path("data/processed/terrain/terrarium_z14")
OUTPUT = Path("data/processed/terrain/catchment_s234.json")


def mosaic_latlon(xt0, yt0, mx, my):
    n = 2**Z
    gx = (xt0 - 1) + mx / 256.0
    gy = (yt0 - 1) + my / 256.0
    lon = gx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * gy / n))))
    return lat, lon


def main() -> None:
    argparse.ArgumentParser(description="Catchment D8/TWI/SPI extraction").parse_args()
    xt0, yt0 = deg2tile(*CENTER, Z)
    print(f"[OK] centre tile z{Z} x={xt0} y={yt0}")
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    mosaic = np.empty((768, 768), dtype=np.float64)
    tiles = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            x, y = xt0 + dx, yt0 + dy
            p = PNG_DIR / f"z{Z}_{x}_{y}.png"
            if not p.exists():
                # fetch_png hardcodes z15 URL pattern via TILE_URL format — pass z explicitly
                import extract_s1_dem as dem
                url = dem.TILE_URL.format(z=Z, x=x, y=y)
                req = urllib.request.Request(url, headers=dem.UA)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    p.write_bytes(resp.read())
                print(f"[OK] fetched {url}")
            else:
                print(f"[OK] cached {p.name}")
            mosaic[(dy + 1) * 256:(dy + 2) * 256, (dx + 1) * 256:(dx + 2) * 256] = terrarium_elev(
                decode_png_rgb(p.read_bytes()))
            tiles.append(f"z{Z}/{x}/{y}")
    dx_m = px_size_m(sum(s[0] for s in SLOPES.values()) / 4.0, Z)
    print(f"[OK] mosaic {mosaic.shape}, pixel ~{dx_m:.2f} m (~{768 * dx_m / 1000:.1f} km side)")

    # Pit filling: priority-flood (Barnes): spill-consistent, single pass.
    # Border cells are fixed outlets; interior fills to its pour point.
    import heapq
    H, W = mosaic.shape
    filled = mosaic.copy()
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
                filled[ny, nx] = max(mosaic[ny, nx], h + 1e-3)
                heapq.heappush(heap, (filled[ny, nx], ny, nx))
    assert visited.all(), "flood did not reach all cells"
    z = filled
    H, W = z.shape
    print("[OK] priority-flood complete; max fill = %.2f m" % float((filled - mosaic).max()))

    # D8 steepest descent (row, col offsets + distances)
    OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    DIST = [math.sqrt(2) * dx_m if abs(dr) + abs(dc) == 2 else dx_m for dr, dc in OFFS]
    recv_r = np.zeros((H, W), dtype=np.int32)
    recv_c = np.zeros((H, W), dtype=np.int32)
    drop = np.zeros((H, W))
    for k, ((dr, dc), dist) in enumerate(zip(OFFS, DIST)):
        dz = z[1:-1, 1:-1] - z[1 + dr:H - 1 + dr, 1 + dc:W - 1 + dc]
        slope_k = np.where(dz > 0, dz / dist, -1.0)
        better = slope_k > drop[1:-1, 1:-1]
        drop[1:-1, 1:-1][better] = slope_k[better]
        rr, cc = np.meshgrid(np.arange(1, H - 1), np.arange(1, W - 1), indexing="ij")
        recv_r[1:-1, 1:-1][better] = (rr + dr)[better]
        recv_c[1:-1, 1:-1][better] = (cc + dc)[better]

    # Accumulation in descending-elevation order (interior; edges drain out)
    acc = np.ones((H, W), dtype=np.float64)
    order = np.argsort(-z[1:-1, 1:-1].ravel())
    ys, xs = np.unravel_index(order, (H - 2, W - 2))
    ys = ys + 1
    xs = xs + 1
    rr_all = recv_r[ys, xs]
    cc_all = recv_c[ys, xs]
    has_recv = (rr_all != 0) | (cc_all != 0)
    # cells with no lower neighbour keep their water (residual flats post-fill)
    for y, x, ry, cx, ok in zip(ys.tolist(), xs.tolist(), rr_all.tolist(), cc_all.tolist(), has_recv.tolist()):
        if ok and (ry != y or cx != x):
            acc[ry, cx] += acc[y, x]
    print("[OK] accumulation done; max contributing cells =", int(acc.max()))

    # Horn slope on the FILLED grid (for TWI/SPI + per-slope derivatives)
    def horn(gy, gx):
        w = z[gy - 1:gy + 2, gx - 1:gx + 2]
        dzdx = ((w[0, 2] + 2 * w[1, 2] + w[2, 2]) - (w[0, 0] + 2 * w[1, 0] + w[2, 0])) / (8 * dx_m)
        dzdy = ((w[2, 0] + 2 * w[2, 1] + w[2, 2]) - (w[0, 0] + 2 * w[0, 1] + w[0, 2])) / (8 * dx_m)
        return dzdx, dzdy

    n = 2**Z
    out_slopes = {}
    for zid, (la, lo) in SLOPES.items():
        lr = math.radians(la)
        gx = (lo + 180.0) / 360.0 * n
        gy = (1.0 - math.log(math.tan(lr) + 1.0 / math.cos(lr)) / math.pi) / 2.0 * n
        mx = (gx - (xt0 - 1)) * 256.0
        my = (gy - (yt0 - 1)) * 256.0
        ix, iy = int(round(mx)), int(round(my))
        edge = min(ix, iy, 767 - ix, 767 - iy)
        assert edge > 64, f"{zid} too close to mosaic edge ({edge}px)"
        x0, y0 = math.floor(mx), math.floor(my)
        fx, fy = mx - x0, my - y0
        elev = (mosaic[y0, x0] * (1 - fx) * (1 - fy) + mosaic[y0, x0 + 1] * fx * (1 - fy)
                + mosaic[y0 + 1, x0] * (1 - fx) * fy + mosaic[y0 + 1, x0 + 1] * fx * fy)
        dzdx, dzdy = horn(iy, ix)
        slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        aspect = (math.degrees(math.atan2(-dzdx, dzdy)) + 360.0) % 360.0 if slope >= 0.5 else 0.0
        d2x = (mosaic[iy, ix + 1] - 2 * mosaic[iy, ix] + mosaic[iy, ix - 1]) / dx_m**2
        d2y = (mosaic[iy + 1, ix] - 2 * mosaic[iy, ix] + mosaic[iy - 1, ix]) / dx_m**2
        a = acc[iy, ix] * dx_m  # specific catchment area (m2/m)
        tanb = max(math.tan(math.radians(slope)), 1e-4)
        twi = math.log(a / tanb)
        spi = a * tanb
        out_slopes[zid] = {
            "mosaic_px": [ix, iy], "edge_px": edge,
            "elevation": round(float(elev), 0),
            "slope_angle": round(slope, 1),
            "aspect": round(aspect, 0),
            "curvature": round(float(d2x + d2y), 4),
            "catchment_cells": int(acc[iy, ix]),
            "twi": round(twi, 2),
            "spi": round(spi, 1),
        }
        print(f"[OK] {zid}: elev={elev:.0f} slope={slope:.1f} twi={twi:.2f} spi={spi:.1f} cells={int(acc[iy,ix])} edge={edge}px")

    # Sanity vs committed z15 S1 values (consistency check, not replacement)
    s1 = out_slopes["S1"]
    assert abs(s1["elevation"] - 1287) <= 40, s1
    assert abs(s1["slope_angle"] - 22.1) <= 5.0, s1
    assert 2.0 <= s1["twi"] <= 20.0, s1
    assert s1["spi"] >= 0, s1

    out = {
        "mosaic": {"z": Z, "tiles": tiles, "pixel_m": round(dx_m, 2),
                   "side_km": round(768 * dx_m / 1000, 2),
                   "method": "D8 steepest descent + iterative pit fill + descending-order accumulation"},
        "slopes": out_slopes,
        "formulas": {"twi": "ln(a/tanB), a=acc*dx (specific catchment area)",
                     "spi": "a*tanB", "slope/aspect": "Horn-1981", "curvature": "Laplacian central differences"},
        "limits": ["Terrarium mirror (NOT USGS tile) — PROXY",
                   "tanB floor 1e-4 on flats (logged)", "outer-64px borders truncated (slopes interior)"],
        "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"Saved: {OUTPUT}  sha256:{sha}")


if __name__ == "__main__":
    sys.exit(main())
