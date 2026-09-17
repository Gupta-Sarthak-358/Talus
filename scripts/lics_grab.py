"""Grab one LiCSAR pair's unw+cc TIFFs via dap enclosure URLs (persist immediately)."""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

UA = {"User-Agent": "TALUS-research"}
REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    orb, frame, pair = sys.argv[1], sys.argv[2], sys.argv[3]
    out = REPO / "data" / "raw" / "licsar" / f"{orb}_{frame}"
    out.mkdir(parents=True, exist_ok=True)
    for kind in ("geo.cc.tif", "geo.unw.tif"):
        url = (f"https://dap.ceda.ac.uk/neodc/comet/data/licsar_products/{orb}/{frame}"
               f"/interferograms/{pair}/{pair}.{kind}")
        dest = out / f"{pair}.{kind}"
        try:
            b = urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=900).read()
            dest.write_bytes(b)
            print(f"SAVED {dest.name} {len(b)} sha={hashlib.sha256(b).hexdigest()[:16]}",
                  flush=True)
        except Exception as ex:
            print(f"FAIL {pair}.{kind}: {str(ex)[:100]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
