"""S2-S4 NDVI from the pinned Sentinel-2 scene (SIH26001, Person-3 NDVI round).

Reads red/NIR at S2-S4 from the SAME scene as S1 (hrefs pinned from the
committed data/processed/terrain/s1_sentinel2.json — no re-query drift) with
rasterio /vsicurl/. Per-slope reads only.

Output: data/processed/terrain/s234_ndvi.json (per-slope DNs + ndvi).
Row values printed to stdout.

Run (needs rasterio — system py311):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_s234_ndvi.py
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_s1_sentinel2 import cog_read  # noqa: E402

SLOPES = {
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}
S1_JSON = Path("data/processed/terrain/s1_sentinel2.json")
OUTPUT = Path("data/processed/terrain/s234_ndvi.json")


def main() -> None:
    argparse.ArgumentParser(description="S2-S4 NDVI from pinned scene").parse_args()
    base = json.loads(S1_JSON.read_text(encoding="utf-8"))
    red_href = base["cogs"]["red"]
    nir_href = base["cogs"]["nir"]
    scl_href = base["cogs"]["scl"]
    print(f"[OK] pinned scene {base['scene']['product_id']} date={base['scene']['date']}")
    merged: dict = {"scene": base["scene"], "slopes": {}, "row_values": {},
                    "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    for zid, (la, lo) in SLOPES.items():
        red, _ = cog_read(red_href, lo, la)
        nir, _ = cog_read(nir_href, lo, la)
        scl, _ = cog_read(scl_href, lo, la)
        ndvi = (nir - red) / (nir + red) if (nir + red) != 0 else 0.0
        assert -1.0 <= ndvi <= 1.0, (zid, ndvi)
        flag = "SCL non-vegetation (context, value still reported)" if int(scl) != 4 else "SCL vegetation"
        print(f"[OK] {zid}: red={red:.0f} nir={nir:.0f} scl={int(scl)} ndvi={ndvi:.3f} ({flag})")
        merged["slopes"][zid] = {"dn": {"red": round(red, 1), "nir": round(nir, 1), "scl": int(scl)},
                                 "ndvi": round(ndvi, 3), "note": flag}
        merged["row_values"][zid] = {"ndvi": round(ndvi, 3)}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print("=== ROW VALUES ===")
    for zid, rv in merged["row_values"].items():
        print(f"{zid}: ndvi={rv['ndvi']}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main())
