"""Extract S1 NDVI/LULC from Sentinel-2 L2A (SIH26001, Person-3 Item D).

SOURCE: Sentinel-2 L2A via Element84 open Earth-Search STAC (no account),
least-cloudy 2024 scene over the pilot bbox. Red/NIR read straight from the
AWS COGs with rasterio /vsicurl/ (no raster download): ndvi=(NIR-R)/(NIR+R).
SCL (scene classification) read at S1 as a cloud/snow flag.
LULC is NOT read from the raster (no trained classifier tonight): it comes
from the nearest OSM landuse=* polygon as a documented PROXY with the
mapping below; if no landuse polygon exists within 300 m, lulc stays STUB.

OSM landuse -> codebook map (codebook = existing CSV codes):
  residential|commercial|industrial|retail|institutional -> BUILT
  forest -> FOREST | farmland|meadow|orchard|farmyard -> AGRI
  highway|railway corridor polygons -> ROAD

Outputs (committed, small):
  data/processed/terrain/s1_sentinel2.json  (product id, date, cloud_cover,
  COG hrefs, DNs, ndvi, scl class, lulc mapping + tag)
Row values printed to stdout for the S1 feature-row update
(ndvi REAL from COG; lulc PROXY from OSM, tagged).

Run (needs rasterio — system py311 has it; mnemo venv does not):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_s1_sentinel2.py
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import rasterio
from rasterio.warp import transform as warp_transform

# S1 Tathangchen (upper) — contract SCAFFOLD_CONTRACT_SEPT5.md §1
S1_LAT = 27.3450
S1_LON = 88.6000

STAC = "https://earth-search.aws.element84.com/v1/search"
BBOX = [88.55, 27.28, 88.65, 27.38]
YEAR = "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z"
MAX_CLOUD = 20

OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}

LULC_MAP = {
    "residential": "BUILT", "commercial": "BUILT", "industrial": "BUILT",
    "retail": "BUILT", "institutional": "BUILT",
    "forest": "FOREST",
    "farmland": "AGRI", "meadow": "AGRI", "orchard": "AGRI", "farmyard": "AGRI",
}

OUTPUT = Path("data/processed/terrain/s1_sentinel2.json")


def stac_search() -> dict:
    body = json.dumps({
        "collections": ["sentinel-2-l2a"], "bbox": BBOX, "datetime": YEAR,
        "query": {"eo:cloud_cover": {"lt": MAX_CLOUD}}, "limit": 25,
    }).encode()
    req = urllib.request.Request(STAC, data=body, headers={"Content-Type": "application/json", **UA})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    feats = d.get("features", [])
    if not feats:
        raise RuntimeError("STAC returned no scenes for pilot bbox/year")
    feats.sort(key=lambda f: f["properties"].get("eo:cloud_cover", 99))
    return feats[0]


def cog_read(href: str, lon: float, lat: float) -> tuple[float, tuple]:
    with rasterio.open("/vsicurl/" + href) as ds:
        xs, ys = warp_transform("EPSG:4326", ds.crs, [lon], [lat])
        row, col = ds.index(xs[0], ys[0])
        if not (0 <= row < ds.height and 0 <= col < ds.width):
            raise RuntimeError(f"S1 outside COG bounds ({ds.bounds})")
        val = float(ds.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
        return val, (ds.crs.to_string(), ds.width, ds.height)


def osm_landuse(lat: float, lon: float) -> dict | None:
    q = (f"[out:json][timeout:60];(way[\"landuse\"](around:300,{lat},{lon});"
         f"relation[\"landuse\"](around:300,{lat},{lon}););out tags center;")
    data = urllib.parse.urlencode({"data": q}).encode()
    import math
    best, best_d = None, math.inf
    for ep in OVERPASS:
        try:
            req = urllib.request.Request(ep, data=data, headers=UA)
            els = json.loads(urllib.request.urlopen(req, timeout=90).read()).get("elements", [])
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] {ep} failed: {exc}")
            els = None
    if els is None:
        return None
    kx = 111320.0 * math.cos(math.radians(lat))
    for el in els:
        lu = (el.get("tags") or {}).get("landuse")
        if not lu:
            continue
        c = el.get("center", {})
        if "lat" not in c:
            continue
        d = math.hypot((c["lon"] - lon) * kx, (c["lat"] - lat) * 110540.0)
        if d < best_d:
            best_d, best = d, {"landuse": lu, "dist_m": round(d, 1),
                               "osm_id": el.get("id"), "name": (el.get("tags") or {}).get("name")}
    return best


def main() -> None:
    argparse.ArgumentParser(description="S1 Sentinel-2 NDVI/LULC extraction").parse_args()
    item = stac_search()
    props = item["properties"]
    pid = item.get("id", "")
    date = str(props.get("datetime", ""))[:10]
    cloud = props.get("eo:cloud_cover")
    print(f"[OK] scene {pid} date={date} cloud={cloud}%")
    assets = item.get("assets", {})
    red_href = assets["red"]["href"]
    nir_href = assets["nir"]["href"]
    scl_href = assets["scl"]["href"]
    red, _ = cog_read(red_href, S1_LON, S1_LAT)
    nir, _ = cog_read(nir_href, S1_LON, S1_LAT)
    scl, _ = cog_read(scl_href, S1_LON, S1_LAT)
    scl_i = int(scl)
    print(f"[OK] DN red={red:.0f} nir={nir:.0f} scl={scl_i}")
    if scl_i in (3, 7, 8, 9, 10, 11):
        raise RuntimeError(f"S1 pixel is cloud/shadow/snow (SCL={scl_i}) — pick another scene, not shipping this NDVI")
    ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0.0
    assert -1.0 <= ndvi <= 1.0, f"ndvi {ndvi} out of range"
    lu = osm_landuse(S1_LAT, S1_LON)
    print(f"[OK] nearest OSM landuse: {lu}")
    if lu and lu["landuse"] in LULC_MAP:
        lulc, lulc_how = LULC_MAP[lu["landuse"]], f"OSM landuse={lu['landuse']} {lu['dist_m']}m (PROXY, tagged)"
    else:
        lulc, lulc_how = None, "no mappable landuse polygon in 300m — lulc stays STUB"
    out = {
        "s1": {"lat": S1_LAT, "lon": S1_LON},
        "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scene": {"product_id": pid, "date": date, "cloud_cover_pct": cloud,
                  "tile": props.get("grid:code", props.get("sentinel:utm_zone", ""))},
        "cogs": {"red": red_href, "nir": nir_href, "scl": scl_href},
        "dn": {"red": round(red, 1), "nir": round(nir, 1), "scl": scl_i},
        "row_values": {"ndvi": round(ndvi, 3), "lulc": lulc},
        "lulc_method": lulc_how,
        "lulc_map": LULC_MAP,
        "tag": "ndvi REAL from COG; lulc PROXY from OSM landuse" if lulc else "ndvi REAL from COG; lulc STUB",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print()
    print("=== S1 ROW VALUES ===")
    print(f"ndvi = {out['row_values']['ndvi']}")
    print(f"lulc = {out['row_values']['lulc']}  ({lulc_how})")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main())
