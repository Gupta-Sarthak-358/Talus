"""Probe LiCSAR GWS for frames covering Sikkim (VI-2 feasibility, read-only)."""
from __future__ import annotations

import re
import urllib.request

UA = {"User-Agent": "TALUS-research-feasibility"}
ROOT = "https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products"


def get(u: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=90).read().decode()


def main() -> int:
    import sys
    if len(sys.argv) > 1:
        h = get(f"{ROOT}/{sys.argv[1]}/")
        print(h, flush=True)
        return 0
    for orb in ("12", "48", "85"):
        try:
            h = get(f"{ROOT}/{orb}/")
            frames = [f for f in re.findall(r'href="([^"]+/)">', h) if not f.startswith("?")]
            print(orb, len(frames), frames[:15], flush=True)
        except Exception as ex:
            print(orb, "ERROR", str(ex)[:100], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
