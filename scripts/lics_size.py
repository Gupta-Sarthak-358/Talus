"""HEAD sizes for LiCSAR pair files (helper)."""
from __future__ import annotations

import urllib.request

UA = {"User-Agent": "TALUS-research-feasibility"}
BASE = ("https://data.ceda.ac.uk/neodc/comet/data/licsar_products"
        "/48/048D_06252_131313/interferograms")


def main() -> int:
    for pr in ("20160730_20160811", "20160718_20160730", "20160718_20160811"):
        for fn in (f"{pr}.geo.unw.tif", f"{pr}.geo.cc.tif"):
            u = f"{BASE}/{pr}/{fn}"
            try:
                r = urllib.request.urlopen(
                    urllib.request.Request(u, headers=UA, method="HEAD"), timeout=60)
                print(fn, r.headers.get("Content-Length"), r.headers.get("Accept-Ranges"),
                      flush=True)
            except Exception as ex:
                print(fn, "ERROR", str(ex)[:100], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
