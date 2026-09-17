"""Check CDSE SLC availability for Mantam pair dates (read-only probe)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "TALUS-research"}


def main() -> int:
    filt = ("Collection/Name eq 'SENTINEL-1' and contains(Name,'SLC') and "
            "OData.CSC.Intersects(area=geography'SRID=4326;POINT(88.5007 27.5397)') and "
            "ContentDate/Start gt 2016-07-29T00:00:00.000Z and "
            "ContentDate/Start lt 2016-08-12T00:00:00Z")
    q = ("https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter="
         + urllib.parse.quote(filt, safe="") + "&$top=20")
    try:
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(q, headers=UA), timeout=120))
    except Exception as ex:
        print("CDSE query ERROR:", str(ex)[:200], flush=True)
        return 0
    print("total:", d.get("@odata.count"), flush=True)
    for p in d.get("value", [])[:10]:
        print(p.get("Name", "?")[:75], p.get("ContentLength", 0) // 1024 // 1024, "MB",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
