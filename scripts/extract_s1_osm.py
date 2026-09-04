"""Extract S1 OSM nearest road/river distances (SIH26001, honest NGEN Person-2).

Queries the OpenStreetMap Overpass API (no account needed) for highway and
waterway geometry around the S1 slope (Tathangchen, 27.3450N 88.6000E) and
computes nearest distances in metres with a local equirectangular projection.

Road filter: highway=* EXCEPT footway|path|steps|bridleway|cycleway|pedestrian
(footpaths would understate road-cut disturbance distance; filter is logged
in the output JSON so anyone can re-run with a different filter).
Rivers: waterway=river|stream.

Output:
  data/processed/terrain/s1_osm_nearest.json  (query, endpoint, timestamp,
  counts, nearest road/river with OSM ids, row values, qa tag)

Row values are printed to stdout for the S1 feature-row update
(distance_to_road / distance_to_river, metres, rounded).

Run:
  <venv-python> scripts/extract_s1_osm.py
Requires: Python standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# S1 Tathangchen (upper) — contract SCAFFOLD_CONTRACT_SEPT5.md §1
S1_LAT = 27.3450
S1_LON = 88.6000

ROAD_RADIUS_M = 1200
RIVER_RADIUS_M = 4000
ROAD_SKIP = {"footway", "path", "steps", "bridleway", "cycleway", "pedestrian"}

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]

UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use, contact via repo)"}

OUTPUT = Path("data/processed/terrain/s1_osm_nearest.json")


def build_query(lat: float = S1_LAT, lon: float = S1_LON,
                road_radius: int = ROAD_RADIUS_M, river_radius: int = RIVER_RADIUS_M,
                kinds: tuple[str, ...] = ("roads", "rivers")) -> str:
    parts = []
    if "roads" in kinds:
        parts.append(f'  way["highway"](around:{road_radius},{lat},{lon});')
    if "rivers" in kinds:
        parts.append(f'  way["waterway"~"^(river|stream)$"](around:{river_radius},{lat},{lon});')
    return "[out:json][timeout:90];\n(\n" + "\n".join(parts) + "\n);\nout geom;\n"


def fetch(query: str) -> tuple[dict, str]:
    data = urllib.parse.urlencode({"data": query}).encode()
    last_err: Exception | None = None
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8")), ep
        except Exception as exc:  # noqa: BLE001 — try next mirror
            print(f"[WARN] {ep} failed: {exc}")
            last_err = exc
    raise RuntimeError(f"All Overpass endpoints failed (last: {last_err})")


def to_xy(lat: float, lon: float, origin: tuple[float, float] | None = None) -> tuple[float, float]:
    olat, olon = origin if origin is not None else (S1_LAT, S1_LON)
    kx = 111320.0 * math.cos(math.radians(olat))
    ky = 110540.0
    return ((lon - olon) * kx, (lat - olat) * ky)


def seg_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def nearest(elements: list[dict], kind: str, origin: tuple[float, float] | None = None) -> tuple[dict, int]:
    best: dict | None = None
    best_d = math.inf
    examined = 0
    for el in elements:
        if el.get("type") != "way":
            continue
        tags = el.get("tags", {})
        if kind == "road":
            hw = tags.get("highway", "")
            if not hw or hw in ROAD_SKIP:
                continue
        else:
            if tags.get("waterway") not in ("river", "stream"):
                continue
        geom = el.get("geometry", [])
        if len(geom) < 1:
            continue
        examined += 1
        pts = [to_xy(p["lat"], p["lon"], origin) for p in geom]
        if len(pts) == 1:
            d = math.hypot(pts[0][0], pts[0][1])
        else:
            d = min(seg_dist(0.0, 0.0, ax, ay, bx, by) for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]))
        if d < best_d:
            best_d = d
            best = {
                "osm_id": el.get("id"),
                "name": tags.get("name"),
                "highway": tags.get("highway") if kind == "road" else None,
                "waterway": tags.get("waterway") if kind == "river" else None,
                "dist_m": round(d, 1),
            }
    if best is None:
        raise RuntimeError(f"No {kind} geometry found — widen radius and re-run")
    return best, examined


def main() -> None:
    ap = argparse.ArgumentParser(description="OSM nearest road/river extraction (default: S1)")
    ap.add_argument("--zone", default="S1")
    ap.add_argument("--lat", type=float, default=S1_LAT)
    ap.add_argument("--lon", type=float, default=S1_LON)
    ap.add_argument("--out", default=str(OUTPUT))
    ap.add_argument("--road-radius", type=int, default=ROAD_RADIUS_M)
    ap.add_argument("--river-radius", type=int, default=RIVER_RADIUS_M)
    args = ap.parse_args()
    origin = (args.lat, args.lon)
    # Split queries: one heavy combined query 504s on loaded servers;
    # two lighter queries (roads, then rivers) stay under the timeout.
    queries = {
        "roads": build_query(args.lat, args.lon, args.road_radius, args.river_radius, ("roads",)),
        "rivers": build_query(args.lat, args.lon, args.road_radius, args.river_radius, ("rivers",)),
    }
    elements: list = []
    endpoint = ""
    for kind, query in queries.items():
        payload, endpoint = fetch(query)
        got = payload.get("elements", [])
        print(f"[OK] {kind}: endpoint {endpoint} elements {len(got)}")
        elements += got
    print(f"[OK] total elements: {len(elements)}")
    road, n_road = nearest(elements, "road", origin)
    river, n_river = nearest(elements, "river", origin)
    print(f"[OK] ways examined: roads={n_road} rivers={n_river}")
    print(f"[OK] nearest road: {road}")
    print(f"[OK] nearest river: {river}")
    out = {
        "slope": {"zone_id": args.zone, "lat": args.lat, "lon": args.lon},
        "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endpoint": endpoint,
        "overpass_query": queries,
        "radius_m": {"roads": args.road_radius, "rivers": args.river_radius},
        "road_filter": "highway=* except " + "|".join(sorted(ROAD_SKIP)),
        "ways_examined": {"roads": n_road, "rivers": n_river},
        "nearest_road": road,
        "nearest_river": river,
        "row_values": {
            "distance_to_road": int(round(road["dist_m"])),
            "distance_to_river": int(round(river["dist_m"])),
        },
        "qa": "osm-qa-unverified",
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print()
    print("=== S1 ROW VALUES ===")
    print(f"distance_to_road  = {out['row_values']['distance_to_road']}")
    print(f"distance_to_river = {out['row_values']['distance_to_river']}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    sys.exit(main())
