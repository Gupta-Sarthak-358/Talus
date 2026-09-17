"""Print raw hrefs of a LiCSAR listing (helper)."""
from __future__ import annotations

import re
import sys
import urllib.request

UA = {"User-Agent": "TALUS-research-feasibility"}


def main() -> int:
    h = urllib.request.urlopen(
        urllib.request.Request(sys.argv[1], headers=UA), timeout=120).read().decode()
    hrefs = re.findall(r'''href=["']([^"']+)["']''', h)
    print(len(hrefs))
    for x in hrefs[:40]:
        print(x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
