"""Find LiCSAR frames covering the championship box (VI-2 feasibility, read-only).

Fetches *-poly.txt corner polygons for frames on candidate tracks and tests the
study box (88.06-88.96E, 27.00-28.00N). Outputs runs/phase_v/vi2_feasibility.json.
Run (py311): python scripts/lics_frames.py
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "runs" / "phase_v" / "vi2_feasibility.json"
UA = {"User-Agent": "TALUS-research-feasibility"}
ROOT = "https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products"
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 28.00
CORNERS = [(LON0, LAT0), (LON1, LAT0), (LON1, LAT1), (LON0, LAT1), (88.5, 27.5)]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def get(u: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=90).read().decode()


def in_poly(px, py, poly) -> bool:
    inside, n = False, len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def main() -> int:
    hits: dict = {}
    for orb in ("12", "48", "85", "114", "121"):
        try:
            h = get(f"{ROOT}/{orb}/")
        except Exception as ex:
            log(f"{orb}: list failed {str(ex)[:60]}")
            continue
        frames = sorted({f.strip("/") for f in re.findall(r'href="((?:\d+[AD]_)[^"]+/)"', h)})
        log(f"{orb}: {len(frames)} frames")
        for fr in frames:
            try:
                txt = get(f"{ROOT}/{orb}/{fr}/metadata/{fr.rstrip('/')}-poly.txt")
                nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", txt)]
                poly = list(zip(nums[0::2], nums[1::2]))
                if len(poly) >= 3 and any(in_poly(x, y, poly) for x, y in CORNERS):
                    hits.setdefault(orb, []).append(fr.rstrip("/"))
            except Exception:
                continue
    res = {"box": [LON0, LON1, LAT0, LAT1], "covering_frames": hits,
           "note": "frame-level coverage only; per-epoch pair availability is the next check"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log("covering frames: " + json.dumps(hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
