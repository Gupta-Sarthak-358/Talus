"""Fresh-disturbance (wound) candidates: roadside vegetation loss, Sentinel-2.

Method (time-varying evidence layer, honestly bounded):
  - Per corridor (gangtok/lachung/darjeeling): least-cloudy S2 L2A scenes for
    PRE (Oct-Nov 2023) and POST (Oct-Nov 2024) via Element84 STAC (no account).
    Matched post-monsoon phenology: a dry-vs-flush pair would drown clearings
    in seasonal green-up (verified: May->Nov median NDVI rises, max drop 0.22).
  - Sample points: fixture road geometry densified every ~100m + perpendicular
    offsets at 60/120m. NDVI=(B08-B04)/(B08+B04) read from AWS COGs via
    rasterio /vsicurl/ (no raster download), SCL-gated (accept 2,4,5,6 both
    dates; cloud/shadow/snow rejected).
  - Candidate: vegetated before (NDVI>=0.4), cleared after (drop>=0.3 AND
    post<0.45), within 150m of a road. Each candidate carries both scenes.
  - Honest limits: 10-20m pixels miss narrow cuts; monsoon clouds gap many
    points (null rates logged); candidates are REVIEW QUEUE, not confirmed cuts.

Outputs: data/sih26001/evidence/wound_map.json (COMMITTED).
Backend serves it at GET /api/wounds; the map draws amber scar markers.

Run (py311, rasterio): Python311/python.exe scripts/wound_map.py
"""
from __future__ import annotations

import datetime
import json
import math
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXDIR = REPO / "data/sih26001/fixtures"
EVIDDIR = REPO / "data/sih26001/evidence"
OUT = EVIDDIR / "wound_map.json"
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}
ROAD_SHIFT = {"gangtok": (0.0, 0.0), "lachung": (0.35, 0.135),
              "darjeeling": (-0.298, -0.337)}
PRE_WIN = "2023-10-01T00:00:00Z/2023-11-30T23:59:59Z"
POST_WIN = "2024-10-01T00:00:00Z/2024-11-30T23:59:59Z"
SCL_OK = {2, 4, 5, 6}
NDVI_WAS_VEG = 0.4
NDVI_DROP = 0.3
MAX_ROAD_M = 150.0
STEP_M = 100.0
OFFSETS_M = (60.0, 120.0)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def corridor_bbox(loc):
    segs = json.loads((FIXDIR / "roads.json").read_text(encoding="utf-8"))["segments"]
    dlat, dlon = ROAD_SHIFT[loc]
    lats, lons = [], []
    for s in segs:
        for la, lo in s["coordinates"]:
            lats.append(la + dlat)
            lons.append(lo + dlon)
    m = 0.03
    return [min(lons) - m, min(lats) - m, max(lons) + m, max(lats) + m]


def road_points(loc):
    segs = json.loads((FIXDIR / "roads.json").read_text(encoding="utf-8"))["segments"]
    dlat, dlon = ROAD_SHIFT[loc]
    pts = []  # (lat, lon, dist_to_road_m=0)
    for s in segs:
        coords = [[la + dlat, lo + dlon] for la, lo in s["coordinates"]]
        for i in range(len(coords) - 1):
            a, b = coords[i], coords[i + 1]
            seglen = haversine_m(*a, *b)
            n = max(1, int(seglen / STEP_M))
            for k in range(n + 1):
                t = k / n
                lat = a[0] + (b[0] - a[0]) * t
                lon = a[1] + (b[1] - a[1]) * t
                pts.append((lat, lon, s["id"]))
                if k < n:
                    ang = math.atan2((b[1] - a[1]) * 111320.0 * math.cos(math.radians(lat)),
                                     (b[0] - a[0]) * 110540.0)
                    for off in OFFSETS_M:
                        for side in (-1, 1):
                            plat = lat + side * off * math.cos(ang + math.pi / 2) / 110540.0
                            plon = lon + side * off * math.sin(ang + math.pi / 2) / (111320.0 * math.cos(math.radians(lat)))
                            pts.append((plat, plon, s["id"]))
    return pts


def pick_scene(bbox, window):
    body = json.dumps({"collections": ["sentinel-2-l2a"], "bbox": bbox,
                       "datetime": window, "query": {"eo:cloud_cover": {"lt": 30}},
                       "limit": 10}).encode()
    req = urllib.request.Request(STAC, data=body,
                                 headers={"Content-Type": "application/json", **UA})
    feats = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("features", [])
    if not feats:
        return None
    feats.sort(key=lambda f: f["properties"].get("eo:cloud_cover", 99))
    f = feats[0]
    assets = f.get("assets", {})
    return {"id": f["id"], "date": f["properties"]["datetime"][:10],
            "cloud": f["properties"].get("eo:cloud_cover"),
            "red": assets["red"]["href"], "nir": assets["nir08"]["href"],
            "scl": assets["scl"]["href"]}


def read_points(scene, points):
    import numpy as np
    import rasterio
    from rasterio.warp import transform as warp_transform
    out = {}
    with rasterio.Env():
        ds_r = rasterio.open("/vsicurl/" + scene["red"])
        ds_n = rasterio.open("/vsicurl/" + scene["nir"])
        ds_s = rasterio.open("/vsicurl/" + scene["scl"])
        lons = [p[1] for p in points]
        lats = [p[0] for p in points]
        for ds, key in ((ds_r, "r"), (ds_n, "n"), (ds_s, "s")):
            xs, ys = warp_transform("EPSG:4326", ds.crs, lons, lats)
            vals = list(ds.sample(list(zip(xs, ys)), indexes=1))
            for i, v in enumerate(vals):
                out.setdefault(i, {})[key] = float(v[0])
        ds_r.close()
        ds_n.close()
        ds_s.close()
    res = []
    for i in range(len(points)):
        d = out.get(i, {})
        if any(k not in d for k in ("r", "n", "s")):
            res.append(None)
            continue
        if int(d["s"]) not in SCL_OK or (d["n"] + d["r"]) == 0:
            res.append(None)
            continue
        res.append((d["n"] - d["r"]) / (d["n"] + d["r"]))
    return res


def main() -> int:
    corridors = {}
    for loc in ("gangtok", "lachung", "darjeeling"):
        try:
            bbox = corridor_bbox(loc)
            pre = pick_scene(bbox, PRE_WIN)
            post = pick_scene(bbox, POST_WIN)
            if not pre or not post:
                log(f"{loc}: no scene pair (pre={bool(pre)} post={bool(post)}) -> skipped honest")
                corridors[loc] = {"status": "no-scene-pair", "candidates": []}
                continue
            pts = road_points(loc)
            log(f"{loc}: {len(pts)} sample pts | pre {pre['id'][:28]} {pre['date']} cl{pre['cloud']} | "
                f"post {post['id'][:28]} {post['date']} cl{post['cloud']}")
            v_pre = read_points(pre, pts)
            v_post = read_points(post, pts)
            n_null = sum(1 for a, b in zip(v_pre, v_post) if a is None or b is None)
            cands = []
            for (lat, lon, seg), a, b in zip(pts, v_pre, v_post):
                if a is None or b is None:
                    continue
                if a >= NDVI_WAS_VEG and (a - b) >= NDVI_DROP and b < 0.45:
                    cands.append({"lat": round(lat, 5), "lon": round(lon, 5),
                                  "seg": seg, "ndvi_pre": round(a, 3),
                                  "ndvi_post": round(b, 3), "drop": round(a - b, 3)})
            # dedupe to ~75m cells (keep max drop)
            dedup: dict[tuple, dict] = {}
            for c in cands:
                key = (round(c["lat"], 3), round(c["lon"], 3))
                if key not in dedup or dedup[key]["drop"] < c["drop"]:
                    dedup[key] = c
            corridors[loc] = {"status": "ok", "pre": {k: pre[k] for k in ("id", "date", "cloud")},
                              "post": {k: post[k] for k in ("id", "date", "cloud")},
                              "sampled": len(pts), "cloud_gap": n_null,
                              "candidates": sorted(dedup.values(), key=lambda c: -c["drop"])}
            log(f"{loc}: {len(dedup)} wound candidates ({n_null} cloud-gapped)")
        except Exception as exc:  # noqa: BLE001
            log(f"{loc}: FAILED ({str(exc)[:120]}) -> recorded, not hidden")
            corridors[loc] = {"status": f"error: {str(exc)[:120]}", "candidates": []}

    OUT.write_text(json.dumps({
        "method": "roadside NDVI loss between pre/post-monsoon 2024 S2 L2A scenes "
                  "(SCL-gated both dates; was-vegetated>=0.4, drop>=0.3, <=150m of road). "
                  "Candidates are a REVIEW QUEUE (fresh cuts, slides, seasonal clearing, "
                  "or missed cloud) — not confirmed cuts. 10-20m pixels miss narrow cuts.",
        "computed": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "corridors": corridors}, indent=1), encoding="utf-8")
    total = sum(len(c.get("candidates", [])) for c in corridors.values())
    log(f"bundle -> {OUT} ({total} candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
