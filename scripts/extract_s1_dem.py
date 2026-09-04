"""Extract S1 DEM derivatives from open elevation tiles (SIH26001, Person-2).

SOURCE HONESTY (read before citing): elevation comes from AWS Terrain Tiles
(Terrarium encoding, https://s3.amazonaws.com/elevation-tiles-prod), an open
mirror whose land data is SRTM-derived ~30 m resampled to Web-Mercator PNGs.
This is NOT the USGS EarthExplorer / NASA Earthdata SRTM tile N27E088 named
in 03_DATA_PLAN / NGEN_PROVENANCE_S1 §5. Values are therefore labelled PROXY
(a documented substitute), never USGS-grade REAL. Replace with the USGS tile
when it lands; the committed window CSV + this script make re-derivation exact.

Method: fetch z15 3x3 Terrarium tiles around S1 (Tathangchen, 27.3450N
88.6000E), decode elev = R*256 + G + B/256 - 32768, mosaic, then at S1:
  - elevation: bilinear interpolation (metres, rounded)
  - slope: Horn (1981) 3x3, degrees (1 dp)
  - aspect: Horn, degrees clockwise from north, flat(<0.5 deg)->0 (0 dp)
  - curvature: Laplacian central differences, 1/m (4 dp)
Pixel size from Web-Mercator at S1 latitude (~4.2 m at z15).

Outputs (committed, small):
  data/processed/terrain/s1_dem_window.csv  (64x64 elev grid around S1 +
  '#' meta lines with tile ids, decode formula, pixel size, checksums basis)
Row values printed to stdout for the S1 feature-row update.

TWI/SPI are NOT computed here: they need catchment-scale flow accumulation
and a 64-px window would be edge-corrupted. They stay STUB (documented).

Run:
  <venv-python> scripts/extract_s1_dem.py
Requires: Python standard library + numpy.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

import numpy as np

# S1 Tathangchen (upper) — contract SCAFFOLD_CONTRACT_SEPT5.md §1
S1_LAT = 27.3450
S1_LON = 88.6000
Z = 15
HALF = 64 // 2  # committed window: 64x64 px around S1 (~270 m)
TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}

OUTPUT = Path("data/processed/terrain/s1_dem_window.csv")


def deg2tile(lat: float, lon: float, z: int) -> tuple[int, int]:
    n = 2**z
    xt = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    yt = int((1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n)
    return xt, yt


def fetch_png(z: int, x: int, y: int) -> bytes:
    url = TILE_URL.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        blob = resp.read()
    print(f"[OK] {url} ({len(blob)} bytes)")
    return blob


def decode_png_rgb(blob: bytes) -> np.ndarray:
    assert blob[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, w = 8, None
    h, depth, ctype, raw = 0, 0, 0, b""
    while pos < len(blob):
        (ln,) = struct.unpack(">I", blob[pos:pos + 4])
        typ = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, comp, filt, inter = struct.unpack(">IIBBBBB", data)
            assert depth == 8 and ctype == 2, f"need 8-bit RGB, got depth={depth} type={ctype}"
            assert inter == 0, "interlaced PNG not supported"
        elif typ == b"IDAT":
            raw += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    px = zlib.decompress(raw)
    ch, stride = 3, w * 3
    img = np.empty((h, w, ch), dtype=np.uint8)
    prev = bytearray(stride)
    p = 0
    for r in range(h):
        f = px[p]
        p += 1
        line = bytearray(px[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif f != 0:
            raise ValueError(f"unknown PNG filter {f}")
        img[r] = np.frombuffer(line, dtype=np.uint8).reshape(w, ch)
        prev = line
    return img


def terrarium_elev(img: np.ndarray) -> np.ndarray:
    r = img[:, :, 0].astype(np.float64)
    g = img[:, :, 1].astype(np.float64)
    b = img[:, :, 2].astype(np.float64)
    return r * 256.0 + g + b / 256.0 - 32768.0


def px_size_m(lat: float, z: int) -> float:
    return 156543.03392 * math.cos(math.radians(lat)) / 2**z


def tile_latlon(x: int, y: int, z: int, px: float, py: float) -> tuple[float, float]:
    n = 2**z
    lon = (x + px / 256.0) / n * 360.0 - 180.0
    lat_r = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + py / 256.0) / n)))
    return math.degrees(lat_r), lon


def main() -> None:
    argparse.ArgumentParser(description="S1 Terrarium DEM extraction").parse_args()
    xt0, yt0 = deg2tile(S1_LAT, S1_LON, Z)
    print(f"[OK] S1 tile z{Z} x={xt0} y={yt0}")
    mosaic = np.empty((256 * 3, 256 * 3), dtype=np.float64)
    tiles = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            img = decode_png_rgb(fetch_png(Z, xt0 + dx, yt0 + dy))
            mosaic[(dy + 1) * 256:(dy + 2) * 256, (dx + 1) * 256:(dx + 2) * 256] = terrarium_elev(img)
            tiles.append(f"z{Z}/{xt0 + dx}/{yt0 + dy}")
    dx_m = px_size_m(S1_LAT, Z)
    print(f"[OK] mosaic {mosaic.shape}, pixel ~{dx_m:.2f} m")

    # S1 fractional position inside the centre tile -> mosaic pixel
    n = 2**Z
    gx = (S1_LON + 180.0) / 360.0 * n
    lat_r = math.radians(S1_LAT)
    gy = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n
    mx = (gx - (xt0 - 1)) * 256.0
    my = (gy - (yt0 - 1)) * 256.0
    ix, iy = int(round(mx)), int(round(my))
    assert 64 < ix < mosaic.shape[1] - 64 and 64 < iy < mosaic.shape[0] - 64, "S1 too close to mosaic edge"

    # Bilinear elevation at exact S1
    x0, y0 = math.floor(mx), math.floor(my)
    fx, fy = mx - x0, my - y0
    elev = (
        mosaic[y0, x0] * (1 - fx) * (1 - fy) + mosaic[y0, x0 + 1] * fx * (1 - fy)
        + mosaic[y0 + 1, x0] * (1 - fx) * fy + mosaic[y0 + 1, x0 + 1] * fx * fy
    )

    # Horn (1981) slope/aspect on 3x3 at nearest pixel. Aspect is the
    # DOWNSLOPE direction clockwise from north: atan2(-dzdx, dzdy).
    # (atan2(dzdx, -dzdy) gives the UPHILL direction, 180 deg off — fixed
    # 2026-09-04 after independent re-derivation from the committed window.)
    z = mosaic[iy - 1:iy + 2, ix - 1:ix + 2]
    dzdx = ((z[0, 2] + 2 * z[1, 2] + z[2, 2]) - (z[0, 0] + 2 * z[1, 0] + z[2, 0])) / (8 * dx_m)
    dzdy = ((z[2, 0] + 2 * z[2, 1] + z[2, 2]) - (z[0, 0] + 2 * z[0, 1] + z[0, 2])) / (8 * dx_m)
    slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
    if slope < 0.5:
        aspect = 0.0
    else:
        aspect = (math.degrees(math.atan2(-dzdx, dzdy)) + 360.0) % 360.0

    # Laplacian curvature (central differences), 1/m
    d2x = (mosaic[iy, ix + 1] - 2 * mosaic[iy, ix] + mosaic[iy, ix - 1]) / dx_m**2
    d2y = (mosaic[iy + 1, ix] - 2 * mosaic[iy, ix] + mosaic[iy - 1, ix]) / dx_m**2
    curv = d2x + d2y

    # Sanity (Gangtok hillside): fail loudly, never silently ship junk
    assert 1000.0 <= elev <= 2500.0, f"elevation {elev:.1f} outside Gangtok plausibility"
    assert 0.0 <= slope <= 80.0, f"slope {slope:.1f} implausible"

    # Committed 64x64 window around S1 (audit + re-derivation)
    win = mosaic[iy - HALF:iy + HALF, ix - HALF:ix + HALF]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        f.write("# S1 DEM window: AWS Terrain Tiles Terrarium z15 (SRTM-derived mirror, NOT USGS tile)\n")
        f.write(f"# tiles: {','.join(tiles)}\n")
        f.write("# decode: elev = R*256 + G + B/256 - 32768 | pixel_m=%.3f | s1_mosaic_px=%d,%d\n" % (dx_m, ix, iy))
        f.write("i,j,lat,lon,elev_m\n")
        for r in range(win.shape[0]):
            for c in range(win.shape[1]):
                ay = (yt0 - 1) + (iy - HALF + r) / 256.0
                ax = (xt0 - 1) + (ix - HALF + c) / 256.0
                n2 = 2**Z
                lon = ax / n2 * 360.0 - 180.0
                lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * ay / n2))))
                f.write(f"{c},{r},{lat:.6f},{lon:.6f},{win[r, c]:.2f}\n")
    sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print()
    print("=== S1 ROW VALUES (PROXY — Terrarium mirror, see header) ===")
    print(f"slope_angle = {slope:.1f}")
    print(f"elevation   = {elev:.0f}")
    print(f"aspect      = {aspect:.0f}")
    print(f"curvature   = {curv:.4f}")
    print(f"Saved: {OUTPUT}  sha256:{sha}")


if __name__ == "__main__":
    sys.exit(main())
