"""Dynamic (non-rainfall) inputs for the Talus counterfactual replays.

What moves vs what is static — and why:
  DYNAMIC (observed, event-contemporary):
    - rainfall 24h/7d/30d .... daily IMD archive (counterfactual_past_events.py)
    - soil_moisture .......... daily ESA CCI COMBINED TCDR v202505 from
                               data/raw/soil/soildata.zip (full 2024 only ->
                               2024 cases only; 2021/2022 keep matrix value, logged)
    - ndvi ................... pre-event Sentinel-2 L2A scene per site via
                               Element84 STAC (no account) + AWS COG /vsicurl/
                               reads, SCL-gated (SCL 3,7,8,9,10,11 rejected)
  STATIC (correctly so — physics):
    - slope/elevation/aspect/curvature/twi/spi .... landforms don't move in weeks
    - drain_density, distance_to_road/river ..... network state (pre-event map)
    - lulc/lithology/lineament .................. categorical ground truth

Output (git-ignored scratch, consumed by counterfactual_past_events.py):
  data/sih26001/processed/counterfactual_dynamic.json
  {case_id: {"soil": {date: value|None, ...}, "soil_meta": {...},
             "ndvi": value|None, "ndvi_meta": {scene, date, cloud, scl}}}

Run: py scripts/counterfactual_dynamic_inputs.py
     (needs xarray/netCDF4, rasterio; network for STAC+COGs)
"""
from __future__ import annotations

import datetime
import json
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from zipfile import ZipFile

REPO = Path(__file__).resolve().parents[1]
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}
KILL_BITS = 4 | 8 | 16 | 32
CLOUD_OK = {4, 5, 6}  # vegetation, bare, water — accept; reject cloud/shadow/snow
SCL_BAD = {3, 7, 8, 9, 10, 11}

SITES = {
    # case_id: (lat, lon, soil_start, soil_end | None, stac_datetime_range)
    "mangan-jun2024": (27.51, 88.53, "2024-05-14", "2024-06-13",
                       "2024-04-01T00:00:00Z/2024-06-12T23:59:59Z"),
    "dipudara-aug2024": (27.2525, 88.4606, "2024-07-21", "2024-08-20",
                         "2024-06-01T00:00:00Z/2024-08-19T23:59:59Z"),
    "lumsay-jun2022": (27.32633333, 88.59544444, None, None,
                       "2022-04-01T00:00:00Z/2022-06-29T23:59:59Z"),
    "sichey-jun2021": (27.33787, 88.609377, None, None,
                       "2021-04-01T00:00:00Z/2021-06-07T23:59:59Z"),
    "nh10-oct2022": (27.13, 88.51, None, None,
                     "2022-08-01T00:00:00Z/2022-10-08T23:59:59Z"),
}


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def soil_series(lat, lon, d0, d1):
    """Daily CCI soil moisture from soildata.zip (2024 only). Returns (dict, meta)."""
    import xarray as xr
    want = set(pd_dates(d0, d1))
    series, flags, cell = {}, {}, None
    with ZipFile(REPO / "data/raw/soil/soildata.zip") as z:
        names = [n for n in z.namelist() if n.endswith(".nc")]
        with tempfile.TemporaryDirectory(prefix="talus_soil_") as tmp:
            for n in names:
                m = re.search(r"(\d{4})(\d{2})(\d{2})\d{6}", n)
                if not m:
                    continue
                stamp = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                if stamp not in want:
                    continue
                fp = Path(tmp) / n
                fp.write_bytes(z.read(n))
                ds = xr.open_dataset(fp)
                s = ds["sm"].sel(lat=lat, lon=lon, method="nearest")
                fl = ds["flag"].sel(lat=lat, lon=lon, method="nearest")
                cell = [round(float(s["lat"].values.item()), 3),
                        round(float(s["lon"].values.item()), 3)]
                fraw = fl.values.item()
                flag = int(fraw) if fraw == fraw else -1
                v = float(s.values.item())
                series[stamp] = None if (v != v or (flag >= 0 and (flag & KILL_BITS))) else round(v, 4)
                flags[stamp] = flag
                ds.close()
    meta = {"source": "ESA CCI SM COMBINED TCDR v202505, data/raw/soil/soildata.zip (LOCAL ONLY)",
            "cell": cell, "kill_bits": "4|8|16|32 masked",
            "valid_days": f"{sum(v is not None for v in series.values())}/{len(series)}"}
    return series, meta


def pd_dates(d0, d1):
    import pandas as pd
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(d0, d1)]


def ndvi_for_site(lat, lon, dt_range):
    """Least-cloudy pre-event S2 L2A scene; SCL-gated point NDVI. Returns (value|None, meta)."""
    import rasterio
    from rasterio.warp import transform as warp_transform
    pad = 0.05
    body = json.dumps({
        "collections": ["sentinel-2-l2a"],
        "bbox": [lon - pad, lat - pad, lon + pad, lat + pad],
        "datetime": dt_range,
        "query": {"eo:cloud_cover": {"lt": 40}}, "limit": 10,
    }).encode()
    req = urllib.request.Request(STAC, data=body, headers={"Content-Type": "application/json", **UA})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    feats = sorted(d.get("features", []), key=lambda f: f["properties"].get("eo:cloud_cover", 99))
    if not feats:
        return None, {"status": "no-scene", "range": dt_range}
    for f in feats:
        p = f["properties"]
        pid = f.get("id", "")
        try:
            a = f.get("assets", {})
            red = float(_cog(a["red"]["href"], lon, lat))
            nir = float(_cog(a["nir"]["href"], lon, lat))
            scl = int(_cog(a["scl"]["href"], lon, lat))
            if scl in SCL_BAD or (nir + red) == 0:
                continue
            ndvi = (nir - red) / (nir + red)
            if not (-1.0 <= ndvi <= 1.0):
                continue
            return round(ndvi, 3), {"status": "ok", "scene": pid,
                                    "date": str(p.get("datetime", ""))[:10],
                                    "cloud_pct": p.get("eo:cloud_cover"), "scl": scl}
        except Exception as e:  # noqa: BLE001 - try next scene, log at end
            last_err = str(e)[:120]
            continue
    return None, {"status": "all-scenes-rejected", "range": dt_range, "last_error": last_err}


def _cog(href, lon, lat):
    import rasterio
    from rasterio.warp import transform as warp_transform
    with rasterio.open("/vsicurl/" + href) as ds:
        xs, ys = warp_transform("EPSG:4326", ds.crs, [lon], [lat])
        row, col = ds.index(xs[0], ys[0])
        if not (0 <= row < ds.height and 0 <= col < ds.width):
            raise RuntimeError("point outside COG bounds")
        return float(ds.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])


def main():
    out = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "cases": {}}
    fp = REPO / "data/sih26001/processed/counterfactual_dynamic.json"
    prev = {}
    if fp.exists():
        try:
            prev = json.loads(fp.read_text()).get("cases", {})
            log("reusing previously fetched NDVI (slow STAC/COG reads not repeated)")
        except Exception:
            prev = {}
    for cid, (lat, lon, s0, s1, dtr) in SITES.items():
        log(f"{cid} @ ({lat}, {lon})")
        if s0:
            series, meta = soil_series(lat, lon, s0, s1)
            log(f"  soil: {meta['valid_days']} valid, cell={meta['cell']}")
        else:
            series, meta = {}, {"status": "no-2024-zip-coverage (2021/2022) — matrix quasi-static value kept, logged"}
            log("  soil: no zip coverage (2021/2022) — keeping matrix value")
        if cid in prev and prev[cid].get("ndvi_meta", {}).get("status") == "ok":
            ndvi, nmeta = prev[cid]["ndvi"], prev[cid]["ndvi_meta"]
            log(f"  ndvi: {ndvi} (cached) {nmeta}")
        else:
            try:
                ndvi, nmeta = ndvi_for_site(lat, lon, dtr)
            except Exception as e:  # noqa: BLE001
                ndvi, nmeta = None, {"status": f"stac-failed: {str(e)[:120]}"}
            log(f"  ndvi: {ndvi} {nmeta}")
        out["cases"][cid] = {"soil": series, "soil_meta": meta, "ndvi": ndvi, "ndvi_meta": nmeta}
    fp.write_text(json.dumps(out, indent=2))
    log(f"wrote {fp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
