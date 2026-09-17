"""Parse saved LiCSAR dir listing (helper)."""
from __future__ import annotations

import re
import sys

pat = sys.argv[2] if len(sys.argv) > 2 else r"(\d{8}_\d{8})"
t = open(sys.argv[1], encoding="utf-8").read()
ds = sorted(set(re.findall(pat, t)))
print(len(ds))
for d in ds:
    print(d)
