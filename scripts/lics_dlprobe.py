"""Probe CEDA TIFF vs PNG access right now (temporary diagnostic)."""
from __future__ import annotations

import urllib.request

UA = {"User-Agent": "TALUS-research-feasibility"}
P = ("48/048D_06252_131313/interferograms/20160730_20160811/20160730_20160811")


def main() -> int:
    for suffix, rng in ((".geo.cc.png", None), (".geo.cc.tif", None),
                        (".geo.cc.tif", "bytes=0-1023"), (".geo.unw.tif", None)):
        u = f"https://data.ceda.ac.uk/neodc/comet/data/licsar_products/{P}{suffix}"
        try:
            h = dict(UA)
            if rng:
                h["Range"] = rng
            r = urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=90)
            print(r.status, suffix, "range=" + str(rng), len(r.read()), flush=True)
        except Exception as ex:
            print("ERROR", suffix, "range=" + str(rng), str(ex)[:120], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
