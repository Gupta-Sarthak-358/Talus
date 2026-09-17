"""Browser-mimicking LiCSAR fetch (diagnostic)."""
from __future__ import annotations

import http.cookiejar
import sys
import urllib.request

JAR = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.5", "Connection": "keep-alive",
     "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "document",
     "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none"}


def main() -> int:
    url = sys.argv[1]
    try:
        r = OP.open(urllib.request.Request(url, headers=H), timeout=120)
        b = r.read(200000)
        print("STATUS", r.status, "BYTES-READ", len(b), "COOKIES", len(JAR), flush=True)
    except Exception as ex:
        print("FAIL:", str(ex)[:200], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
