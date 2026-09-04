"""Extract pilot LULC from ESA WorldCover 2021 v200 (SIH26001, Person-3 follow-up).

No account needed: tile streams straight from the AWS Open Data bucket
(s3://esa-worldcover/v200/2021/map, --no-sign-request equivalent) via
rasterio /vsicurl/ range reads — kilobytes transferred, not the ~89 MB tile.
Tile N27E087 covers 27-30N/87-90E (bounds verified in-repo); all 4 pilot
slopes fall inside it.

Per slope: 3x3 window mode class (robust to single-pixel noise) + centre
pixel + agreement count. WorldCover v200 legend mapped to the repo's
05_FEATURE_SCHEMA labels (mapping logged in the evidence JSON + provenance):
  10 tree cover -> FOREST | 20 shrubland -> FOREST | 30 grassland -> AGRI |
  40 cropland -> AGRI | 50 built-up -> BUILT | 60 bare/sparse -> BARREN |
  70 water -> WATER | 80 wetland -> WETLAND | 90 mangroves -> WETLAND |
  95 moss/lichen -> BARREN
(BARREN/WATER/WETLAND extend the label set with WC codes; validator only
requires text. No invented classes — unknown codes fail loudly.)

Outputs (committed, small):
  data/processed/terrain/s234_lulc.json
Row values printed for the feature-matrix update.

Run (needs rasterio; system py311 has it, mnemo venv does not):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_s234_lulc.py
Requires: rasterio (GDAL /vsicurl/).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

URL = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E087_Map.tif"
TILE = "N27E087 (27-30N/87-90E, EPSG:4326, 36000x36000, bounds verified 2026-09-04)"
SLOPES = {"S1": (27.3450, 88.6000), "S2": (27.3380, 88.6120),
          "S3": (27.3250, 88.6065), "S4": (27.3150, 88.5950)}
WC2LABEL = {10: "FOREST", 20: "FOREST", 30: "AGRI", 40: "AGRI",
            50: "BUILT", 60: "BARREN", 70: "WATER", 80: "WETLAND",
            90: "WETLAND", 95: "BARREN"}
OUTPUT = Path("data/processed/terrain/s234_lulc.json")


def main() -> int:
    import rasterio

    out = {"tile": TILE, "url": URL.replace("/vsicurl/", "https://"),
           "mapping": {str(k): v for k, v in WC2LABEL.items()}, "slopes": {}}
    with rasterio.open(URL) as src:
        assert src.crs.to_epsg() == 4326, src.crs
        for zid, (la, lo) in SLOPES.items():
            r, c = src.index(lo, la)
            win = src.read(1, window=((r - 1, r + 2), (c - 1, c + 2)))
            vals = [int(v) for v in win.flatten()]
            mode, n = Counter(vals).most_common(1)[0]
            centre = vals[4]
            if mode not in WC2LABEL or centre not in WC2LABEL:
                print(f"UNKNOWN WorldCover code at {zid}: mode={mode} centre={centre} — aborting, no invented labels")
                return 1
            out["slopes"][zid] = {
                "lat": la, "lon": lo, "row": r, "col": c,
                "window_3x3": vals, "mode": mode, "centre": centre,
                "agree": n, "label": WC2LABEL[mode],
                "centre_agrees": centre == mode,
            }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print("=== LULC ROW VALUES (WorldCover 2021 v200, 3x3 mode) ===")
    for zid, s in out["slopes"].items():
        print(f"{zid}: {s['label']} (WC-{s['mode']}, centre_agrees={s['centre_agrees']}, agree {s['agree']}/9)")
    print(f"Saved: {OUTPUT}  sha256:{sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
