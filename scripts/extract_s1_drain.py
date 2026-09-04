"""S1-window drain density from OSM waterways + committed DEM window (Person-3 C-a).

Method: re-query Overpass for waterway=river|stream geometry within 400 m of
S1, clip every segment to the committed 64x64 DEM window
(data/processed/terrain/s1_dem_window.csv, ~271 m side), sum in-window stream
length, divide by window area. Result is labelled PROXY-window: a 271-m
window cannot see catchment-scale drainage, and OSM misses unmapped streams.
If no waterway crosses the window, density is honestly 0.0 for the window
(still a measured value, not an invention).

Output: data/processed/terrain/s1_drain_window.json (query, clip bounds,
in-window length, density, row value).

Run: <venv-python> scripts/extract_s1_drain.py  (stdlib only)
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

S1_LAT = 27.3450
S1_LON = 88.6000
RADIUS_M = 400
DEM_CSV = Path("data/processed/terrain/s1_dem_window.csv")
OUTPUT = Path("data/processed/terrain/s1_drain_window.json")
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}


def fetch(query: str) -> list:
    data = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=data, headers=UA)
            return json.loads(urllib.request.urlopen(req, timeout=120).read()).get("elements", [])
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] {ep} failed: {exc}")
            last = exc
    raise RuntimeError(f"All Overpass endpoints failed (last: {last})")


def main() -> None:
    argparse.ArgumentParser(description="S1-window drain density").parse_args()
    # Window bounds from the committed DEM extract
    lats, lons = [], []
    with DEM_CSV.open(newline="", encoding="utf-8") as f:
        for row in f:
            if row.startswith("#") or row.startswith("i,"):
                continue
            _, _, la, lo, _ = row.strip().split(",")
            lats.append(float(la))
            lons.append(float(lo))
    lat0, lat1 = min(lats), max(lats)
    lon0, lon1 = min(lons), max(lons)
    kx = 111320.0 * math.cos(math.radians(S1_LAT))
    ky = 110540.0
    w_m = (lon1 - lon0) * kx
    h_m = (lat1 - lat0) * ky
    area_km2 = (w_m / 1000.0) * (h_m / 1000.0)
    print(f"[OK] window lat {lat0:.6f}-{lat1:.6f} lon {lon0:.6f}-{lon1:.6f} ~{w_m:.0f}x{h_m:.0f} m area={area_km2:.4f} km2")

    q = (f"[out:json][timeout:90];way[\"waterway\"~\"^(river|stream)$\"]"
         f"(around:{RADIUS_M},{S1_LAT},{S1_LON});out geom;")
    elements = fetch(q)
    print(f"[OK] waterway elements: {len(elements)}")

    def xy(la, lo):
        return ((lo - lon0) * kx, (la - lat0) * ky)

    total = 0.0
    used = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry", [])
        pts = [xy(p["lat"], p["lon"]) for p in geom]
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            # Liang-Barsky clip to [0,w]x[0,h]
            dx, dy = bx - ax, by - ay
            t0, t1 = 0.0, 1.0
            ok = True
            for p_, q_ in ((-dx, ax), (dx, w_m - ax), (-dy, ay), (dy, h_m - ay)):
                if abs(p_) < 1e-12:
                    if q_ < 0:
                        ok = False
                        break
                else:
                    r = q_ / p_
                    if p_ < 0:
                        t0 = max(t0, r)
                    else:
                        t1 = min(t1, r)
            if ok and t0 < t1:
                total += math.hypot(dx * (t1 - t0), dy * (t1 - t0))
                used.append(el.get("id"))
    density = total / 1000.0 / area_km2 if area_km2 > 0 else 0.0
    print(f"[OK] in-window stream length={total:.1f} m from {len(set(used))} ways -> drain_density={density:.3f} km/km2")
    out = {
        "s1": {"lat": S1_LAT, "lon": S1_LON},
        "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {"file": str(DEM_CSV), "side_m": [round(w_m, 1), round(h_m, 1)], "area_km2": round(area_km2, 4)},
        "in_window_stream_m": round(total, 1),
        "ways_used": sorted(set(used)),
        "row_values": {"drain_density": round(density, 3)},
        "tag": "PROXY-window: 271-m window cannot see catchment drainage; OSM misses unmapped streams",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"drain_density = {out['row_values']['drain_density']}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main())
