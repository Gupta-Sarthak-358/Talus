"""VI-2 pilot: Mantam LiCSAR unw/coherence window reads (read-only, no fitting).

Reads geo.unw.tif + geo.cc.tif windows via HTTPS range requests for 3 pre-T pairs
in frame 048D_06252_131313. Validates CRS, units, nodata, date gating.
Run (py311): python scripts/lics_pilot.py
"""
from __future__ import annotations

import time
import urllib.request

UA = {"User-Agent": "TALUS-research-feasibility"}
ROOT = "https://dap.ceda.ac.uk/neodc/comet/data/licsar_products"
FR = "48/048D_06252_131313"
LAT, LON = 27.5397, 88.5007
PAIRS = ["20160730_20160811", "20160718_20160730", "20160718_20160811"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import os
    os.environ["GDAL_HTTP_USERAGENT"] = "TALUS-research"
    import rasterio
    import numpy as np
    for pr in PAIRS:
        a, b = pr.split("_")
        assert b <= "20160812", f"post-T pair {pr}"
        for fn in (f"{pr}.geo.unw.tif", f"{pr}.geo.cc.tif"):
            url = f"/vsicurl/{ROOT}/{FR}/interferograms/{pr}/{fn}"
            try:
                with rasterio.open(url) as src:
                    if src.crs is None or src.crs.to_epsg() != 4326:
                        log(f"{pr}/{fn}: CRS={src.crs} (unexpected)")
                        continue
                    rr, cc = src.index(LON, LAT)
                    w = src.read(1, window=((max(0, rr - 5), rr + 6),
                                            (max(0, cc - 5), cc + 6))).astype(float)
                    w = np.where(w == src.nodata, np.nan, w)
                    log(f"{pr}/{fn}: n={np.isfinite(w).sum()}/{w.size} "
                        f"med={np.nanmedian(w):.3f} mean={np.nanmean(w):.3f}")
            except Exception as ex:
                log(f"{pr}/{fn}: READ-FAIL {str(ex)[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
