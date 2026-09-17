"""Runout screening + exposure counts (hazard ≠ risk lane).

Method (documented screening approximation, NOT a debris-flow simulator):
  - From each pilot-zone centroid, walk downhill on USGS SRTM 1-arcsec
    (bilinear, 30m steps) following steepest descent; stop at slope <5°,
    1.8km, or tile edge. Path length L and drop H logged per zone.
  - Exposure = OSM building centers within 100m of the path (Overpass,
    per-zone boxes, cached git-ignored) + fixture road-segment meters with
    midpoint within 100m (same corridor shifts as the backend).
  - Angle-of-reach note: a 30° reach from the zone elevation covers
    L_reach = H_zone/tan(30°); paths longer than that are flagged
    over-reach (screening conservatism, logged not hidden).

Outputs: data/sih26001/evidence/runout_exposure.json (COMMITTED, ~12 zones)
  + processed/osm_buildings_cache.json (git-ignored scratch).
Backend serves it at GET /api/runout/exposure; the map draws the paths.

Run (py311, rasterio): Python311/python.exe scripts/runout_exposure.py
"""
from __future__ import annotations

import datetime
import json
import math
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROCDIR = REPO / "data/sih26001/processed"
EVIDDIR = REPO / "data/sih26001/evidence"
FIXDIR = REPO / "data/sih26001/fixtures"
OUT = EVIDDIR / "runout_exposure.json"
CACHE = PROCDIR / "osm_buildings_cache.json"
DEM = REPO / "data/raw/dem/n27_e088_1arc_v3.tif"
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
STEP_M = 30.0
MAX_STEPS = 60
STOP_SLOPE_DEG = 5.0
HALF_WIDTH_M = 100.0
REACH_ANGLE_DEG = 30.0
ROAD_SHIFT = {"gangtok": (0.0, 0.0), "lachung": (0.35, 0.135),
              "darjeeling": (-0.298, -0.337)}
ZONE_LOC = (lambda: {z: loc for loc, pre in
                     (("gangtok", "S"), ("lachung", "N"), ("darjeeling", "D"))
                     for z in (f"{pre}{i}" for i in range(1, 5))})()


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def pt_seg_m(plat, plon, alat, alon, blat, blon):
    mid_lat = (alat + blat) / 2
    kx = 111320.0 * math.cos(math.radians(mid_lat))
    ky = 110540.0
    ax, ay = alon * kx, alat * ky
    bx, by = blon * kx, blat * ky
    px, py = plon * kx, plat * ky
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dist_to_path_m(lat, lon, path):
    if len(path) < 2:
        return float("inf")
    return min(pt_seg_m(lat, lon, *path[i], *path[i + 1]) for i in range(len(path) - 1))


def load_zones():
    zones = {}
    for fp, loc in (("slopes.json", "gangtok"), ("slopes.lachung.json", "lachung"),
                    ("slopes.darjeeling.json", "darjeeling")):
        for z in json.loads((FIXDIR / fp).read_text(encoding="utf-8"))["zones"]:
            zones[z["zone_id"]] = {"lat": float(z["geometry"]["lat"]),
                                   "lon": float(z["geometry"]["lon"]),
                                   "loc": loc, "name": z.get("name", z["zone_id"])}
    return zones


def walk_downhill(sample, lat, lon):
    import numpy as np
    import math as _m
    # seed: centroid DEM cell may be void/flat (valley floor) — try 30m ring
    e0 = sample(lat, lon)
    if not np.isfinite(e0):
        for bearing in range(0, 360, 45):
            br = _m.radians(bearing)
            nlat = lat + 30.0 / 110540.0 * _m.cos(br)
            nlon = lon + 30.0 / (111320.0 * _m.cos(_m.radians(lat))) * _m.sin(br)
            if np.isfinite(sample(nlat, nlon)):
                lat, lon = nlat, nlon
                e0 = sample(lat, lon)
                break
    path = [(lat, lon)]
    for _ in range(MAX_STEPS):
        e0 = sample(lat, lon)
        best, best_e = None, e0
        for bearing in range(0, 360, 45):
            br = math.radians(bearing)
            nlat = lat + (STEP_M * math.cos(br)) / 110540.0
            nlon = lon + (STEP_M * math.sin(br)) / (111320.0 * math.cos(math.radians(lat)))
            e = sample(nlat, nlon)
            if e < best_e:
                best_e, best = e, (nlat, nlon)
        if best is None:
            break
        drop = e0 - best_e
        slope = math.degrees(math.atan2(drop, STEP_M))
        if slope < STOP_SLOPE_DEG:
            path.append(best)
            break
        path.append(best)
        lat, lon = best
    return path


def fetch_buildings(lat, lon):
    key = f"{lat:.4f},{lon:.4f}"
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    if key in cache:
        return cache[key]
    d = 0.008
    q = (f'[out:json][timeout:120];(node["building"]({lat-d},{lon-d},{lat+d},{lon+d});'
         f'way["building"]({lat-d},{lon-d},{lat+d},{lon+d}););out center 400;')
    last = None
    for api in APIS:
        try:
            req = urllib.request.Request(api, data=q.encode(), headers=UA)
            els = json.loads(urllib.request.urlopen(req, timeout=150).read()).get("elements", [])
            pts = []
            for e in els:
                if e["type"] == "node":
                    pts.append([e["lat"], e["lon"]])
                elif "center" in e:
                    pts.append([e["center"]["lat"], e["center"]["lon"]])
            cache[key] = pts
            CACHE.write_text(json.dumps(cache), encoding="utf-8")
            time.sleep(2)
            return pts
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:100]
    log(f"  buildings fetch failed ({last}) -> 0 with note")
    return []


def main() -> int:
    import numpy as np
    import rasterio

    zones = load_zones()
    assert len(zones) == 12, len(zones)
    ds = rasterio.open(DEM)
    band = ds.read(1).astype(float)
    band[band < -1000] = np.nan
    gt = ds.transform
    lat0 = gt[5] + 0.5 * gt[4] if False else None

    def sample(lat, lon):
        r = int((ds.bounds.top - lat) / abs(gt[4]))
        c = int((lon - ds.bounds.left) / gt[0])
        r = min(max(r, 0), ds.height - 1)
        c = min(max(c, 0), ds.width - 1)
        return float(band[r, c])

    roads = json.loads((FIXDIR / "roads.json").read_text(encoding="utf-8"))["segments"]
    out_zones = {}
    for zid, z in zones.items():
        path = walk_downhill(sample, z["lat"], z["lon"])
        length = sum(haversine_m(*path[i], *path[i + 1]) for i in range(len(path) - 1))
        drop = sample(*path[0]) - sample(*path[-1])
        reach = drop / math.tan(math.radians(REACH_ANGLE_DEG)) if drop > 0 else 0.0
        pts = fetch_buildings(z["lat"], z["lon"])
        bld = sum(1 for (blat, blon) in pts if dist_to_path_m(blat, blon, path) <= HALF_WIDTH_M)
        dlat, dlon = ROAD_SHIFT[z["loc"]]
        near_road = float("inf")
        near_seg = None
        road_m = {}
        for s in roads:
            coords = [[la + dlat, lo + dlon] for la, lo in s["coordinates"]]
            for i in range(len(coords) - 1):
                mlat = (coords[i][0] + coords[i + 1][0]) / 2
                mlon = (coords[i][1] + coords[i + 1][1]) / 2
                dmid = dist_to_path_m(mlat, mlon, path)
                if dmid < near_road:
                    near_road, near_seg = dmid, s["id"]
                if dmid <= HALF_WIDTH_M:
                    road_m[s["id"]] = round(road_m.get(s["id"], 0)
                                            + haversine_m(*coords[i], *coords[i + 1]))
        avg_slope = (math.degrees(math.atan2(drop, length))
                     if length > 0 and np.isfinite(drop) else None)
        out_zones[zid] = {"name": z["name"], "path": [[round(a, 5), round(b, 5)] for a, b in path],
                          "length_m": round(length), "drop_m": (round(drop, 1) if np.isfinite(drop) else None),
                          "avg_slope_deg": round(avg_slope, 1) if avg_slope is not None else None,
                          "nearest_road_seg": near_seg,
                          "nearest_road_m": round(near_road) if near_road != float("inf") else None,
                          "buildings_n": bld, "buildings_seen": len(pts),
                          "road_m": road_m}
        log(f"{zid}: path {len(path)}pts {length:.0f}m drop {drop:.0f}m | "
            f"buildings {bld}/{len(pts)} | road {sum(road_m.values()):.0f}m")

    OUT.write_text(json.dumps({
        "method": "screening approximation (NOT a debris-flow simulator): steepest-descent walk "
                  "on SRTM 1-arcsec, 30m steps, stop <5deg/1.8km (void centroid seeds from 30m ring); "
                  "exposure = OSM building centers within 100m of path (fetch capped at 400/zone, "
                  "dense towns undercounted — stated) + fixture road-segment meters within 100m + "
                  "nearest-segment distance (schematic geometry runs 200m+ off-slope, stated).",
        "computed": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "zones": out_zones}, indent=1), encoding="utf-8")
    log(f"bundle -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
