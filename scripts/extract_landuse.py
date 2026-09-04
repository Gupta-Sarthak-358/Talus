"""Nearest OSM landuse polygon per slope (SIH26001, Person-3 landuse round).

Queries landuse=* ways+relations around each slope and records the nearest
polygon (or containing polygon, dist 0) for the lulc codebook mapping.
Acceptance bar: nearest polygon within 300 m, else lulc stays STUB for that
slope (a distant polygon is weak evidence — documented, not used).

OSM landuse -> codebook map (codebook = existing CSV codes):
  residential|commercial|industrial|retail|institutional -> BUILT
  forest -> FOREST | farmland|meadow|orchard|farmyard -> AGRI

Output: data/processed/terrain/s234_landuse.json (per-slope nearest + map +
row values or STUB reason). Row values printed to stdout.

Run: <venv-python> scripts/extract_landuse.py  (stdlib only)
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

SLOPES = {
    "S1": {"lat": 27.3450, "lon": 88.6000},
    "S2": {"lat": 27.3380, "lon": 88.6120},
    "S3": {"lat": 27.3250, "lon": 88.6065},
    "S4": {"lat": 27.3150, "lon": 88.5950},
}
RADIUS_M = 1000
ACCEPT_M = 300.0

LULC_MAP = {
    "residential": "BUILT", "commercial": "BUILT", "industrial": "BUILT",
    "retail": "BUILT", "institutional": "BUILT",
    "forest": "FOREST",
    "farmland": "AGRI", "meadow": "AGRI", "orchard": "AGRI", "farmyard": "AGRI",
}

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}
OUTPUT = Path("data/processed/terrain/s234_landuse.json")


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
    argparse.ArgumentParser(description="Per-slope OSM landuse extraction").parse_args()
    merged: dict = {"slopes": {}, "row_values": {}}
    for zid, pt in SLOPES.items():
        lat, lon = pt["lat"], pt["lon"]
        q = (f"[out:json][timeout:90];(way[\"landuse\"](around:{RADIUS_M},{lat},{lon});"
             f"relation[\"landuse\"](around:{RADIUS_M},{lat},{lon}););out tags center;")
        try:
            elements = fetch(q)
        except RuntimeError as exc:
            print(f"[{zid}] FETCH FAIL: {exc}")
            merged["slopes"][zid] = {"error": str(exc), "lulc": None}
            merged["row_values"][zid] = {"lulc": None}
            continue
        kx = 111320.0 * math.cos(math.radians(lat))
        best, best_d = None, math.inf
        for el in elements:
            lu = (el.get("tags") or {}).get("landuse")
            c = el.get("center", {})
            if not lu or "lat" not in c:
                continue
            d = math.hypot((c["lon"] - lon) * kx, (c["lat"] - lat) * 110540.0)
            if d < best_d:
                best_d, best = d, {"landuse": lu, "dist_m": round(d, 1),
                                   "osm_id": el.get("id"),
                                   "name": (el.get("tags") or {}).get("name")}
        print(f"[{zid}] nearest landuse: {best} (examined {len(elements)})")
        if best and best_d <= ACCEPT_M and best["landuse"] in LULC_MAP:
            code = LULC_MAP[best["landuse"]]
            merged["slopes"][zid] = {"nearest": best, "lulc": code, "how": "PROXY: OSM landuse map, tagged"}
            merged["row_values"][zid] = {"lulc": code}
        else:
            reason = ("none in 300m" if not best or best_d > ACCEPT_M
                      else f"unmappable class {best['landuse']}")
            merged["slopes"][zid] = {"nearest": best, "lulc": None, "how": f"STUB ({reason})"}
            merged["row_values"][zid] = {"lulc": None}
    merged["map"] = LULC_MAP
    merged["queried_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("=== ROW VALUES ===")
    for zid, rv in merged["row_values"].items():
        print(f"{zid}: lulc={rv['lulc']}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main())
