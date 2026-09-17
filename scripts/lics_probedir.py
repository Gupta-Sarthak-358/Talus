"""List one LiCSAR frame pair dir (VI-2 pilot probe, read-only)."""
from __future__ import annotations

import sys
import urllib.request

UA = {"User-Agent": "TALUS-research-feasibility"}


def get(u: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=120).read().decode()


def main() -> int:
    print(get(sys.argv[1]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
