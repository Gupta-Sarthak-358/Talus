"""Extend S1 OSM extraction to S2-S4 (SIH26001, Person-3 Item F).

Drives scripts/extract_s1_osm.py per slope (same filters, same radii, same
distance method — the S1 script is the single source of truth) and merges
the per-slope outputs. Per-slope reads only, never copy-paste S1.

Output:
  data/processed/terrain/s234_osm_nearest.json  (per-slope nearest road/river
  + OSM ids + counts + row values, qa tag osm-qa-unverified)

Row values printed to stdout for the S2-S4 feature-row updates.

Run:
  <venv-python> scripts/extract_s234_osm.py
Requires: Python standard library only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S1_SCRIPT = HERE / "extract_s1_osm.py"
OUTPUT = Path("data/processed/terrain/s234_osm_nearest.json")

# Contract SCAFFOLD_CONTRACT_SEPT5.md §1 + slopes.json geometry
SLOPES = {
    "S2": {"lat": 27.3380, "lon": 88.6120},
    "S3": {"lat": 27.3250, "lon": 88.6065},
    "S4": {"lat": 27.3150, "lon": 88.5950},
}


def main() -> None:
    merged: dict = {"slopes": {}, "row_values": {}, "qa": "osm-qa-unverified"}
    for zid, pt in SLOPES.items():
        tmp = HERE / f".tmp_osm_{zid}.json"
        print(f"--- {zid} ({pt['lat']},{pt['lon']}) ---")
        subprocess.run(
            [sys.executable, str(S1_SCRIPT), "--zone", zid,
             "--lat", str(pt["lat"]), "--lon", str(pt["lon"]),
             "--out", str(tmp)],
            check=True,
        )
        block = json.loads(tmp.read_text(encoding="utf-8"))
        tmp.unlink()
        merged["slopes"][zid] = block
        merged["row_values"][zid] = block["row_values"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print()
    print("=== S2-S4 ROW VALUES ===")
    for zid, rv in merged["row_values"].items():
        print(f"{zid}: distance_to_road={rv['distance_to_road']} distance_to_river={rv['distance_to_river']}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main())
