"""Debug CEDA GDAL access (temporary)."""
from __future__ import annotations

import sys

import rasterio
from rasterio.env import Env

URL = ("NIL")
if len(sys.argv) > 1:
    URL = sys.argv[1]


def main() -> int:
    with Env(CPL_DEBUG="ON"):
        try:
            src = rasterio.open(URL)
            print("OPENED", src.shape, src.crs, flush=True)
        except Exception as ex:
            print("FAIL:", str(ex)[:200], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
