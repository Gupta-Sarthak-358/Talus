"""Selective ESA CCI COMBINED daily soil moisture downloader (v09.2, CEDA DAP).

Why selective, not `wget --mirror`: the full 1978-2024 archive is ~17k files
(~40 GB); the training lane only needs monsoon windows (May-Oct) for years
with dated slides. This script reads CEDA's JSON directory listing per year
and downloads only YYYY-05-01..YYYY-10-31 dailies into data/raw/soil/v09.2/.

Default scope 2006-2024 (~3.5k files, ~8 GB) covers ~90% of dated positives
(the 2010-2015 Darjeeling/Sikkim bulk). Extend with --start 1978 if disk
allows (adds the 1965-2005 tail; note CCI starts 1978, so 1965-1977 slides
keep quasi-static fallback regardless).

Version caveat (read before mixing): the 7 files already in data/raw/soil/
are v202505 TCDR; these are v09.2. After download, run the overlap check
(same June-2024 window in both versions at the study bbox); if bias is
small we tag rows by version and proceed, else we recompute the current
window-mean in v09.2 for full consistency. See docs/SOIL_DATA_FETCH_GUIDE.md.

Usage:
  python scripts/download_cci_soil.py --probe 2024        # list actual filenames first
  python scripts/download_cci_soil.py                     # 2006-2024, May-Oct
  python scripts/download_cci_soil.py --start 1978 --end 2024 --months 5-10

Stdlib only. Skips files already on disk. Logs to data/raw/soil/v09.2/_fetch_log.jsonl
"""
from __future__ import annotations

import argparse
import datetime
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "data" / "raw" / "soil" / "v09.2"
BASE = "https://dap.ceda.ac.uk/neodc/esacci/soil_moisture/data/daily_files/COMBINED/v09.2"
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def year_listing(year: int) -> list[dict]:
    """File items for a year dir via the CEDA THREDDS catalog (verified 2024:
    367 entries, urlPath -> fileServer download)."""
    import xml.etree.ElementTree as ET
    url = (f"https://dap.ceda.ac.uk/thredds/catalog/neodc/esacci/soil_moisture/"
           f"data/daily_files/COMBINED/v09.2/{year}/catalog.xml")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        root = ET.fromstring(resp.read())
    ns = {"t": "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"}
    items = []
    for e in root.findall(".//t:dataset", ns):
        name, path = e.get("name"), e.get("urlPath")
        if name and path and name.endswith(".nc"):
            items.append({"name": name,
                          "download": f"https://dap.ceda.ac.uk/thredds/fileServer/{path}",
                          "type": "file"})
    if not items:
        raise RuntimeError(f"THREDDS catalog for {year} yielded no .nc entries ({url})")
    return items


def wanted(name: str, months: set[int]) -> bool:
    if not name.endswith(".nc"):
        return False
    for tok in name.split("-"):
        if len(tok) >= 8 and tok[:8].isdigit():
            try:
                d = datetime.date(int(tok[:4]), int(tok[4:6]), int(tok[6:8]))
            except ValueError:
                continue
            return d.month in months
    return False


def download(url: str, dest: Path, retries: int = 3) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True  # skip
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as fh:
                shutil_copy(resp, fh)
            return True
        except Exception as exc:  # noqa: BLE001
            log(f"  retry {attempt}/{retries} {dest.name}: {exc}")
            dest.unlink(missing_ok=True)
            time.sleep(2 * attempt)
    return False


def shutil_copy(resp, fh, chunk: int = 1 << 20) -> None:
    while True:
        b = resp.read(chunk)
        if not b:
            return
        fh.write(b)


def main() -> int:
    ap = argparse.ArgumentParser(description="Selective CCI v09.2 soil moisture fetch")
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2024)
    ap.add_argument("--months", default="5-10",
                    help="month range MM-MM kept per year (default 5-10)")
    ap.add_argument("--probe", type=int, default=None,
                    help="list files for one year and exit (no download)")
    ap.add_argument("--sleep", type=float, default=0.2, help="pause between files (s)")
    ap.add_argument("--workers", type=int, default=8,
                    help="parallel download threads (default 8; single-thread measured ~50KB/s)")
    args = ap.parse_args()
    m0, m1 = (int(x) for x in args.months.split("-"))
    months = set(range(m0, m1 + 1))
    OUTDIR.mkdir(parents=True, exist_ok=True)

    if args.probe is not None:
        items = year_listing(args.probe)
        names = sorted(it.get("name", "?") for it in items)
        log(f"{args.probe}: {len(names)} files, e.g. {names[0]} .. {names[-1]}")
        keep = [n for n in names if wanted(n, months)]
        log(f"months {args.months}: {len(keep)} wanted, e.g. {keep[:3]}")
        return 0

    import threading
    from concurrent.futures import ThreadPoolExecutor
    fetch_log = OUTDIR / "_fetch_log.jsonl"
    lock = threading.Lock()
    totals = {"ok": 0, "fail": 0}

    def one(it: dict) -> None:
        name = it["name"]
        url = it.get("download") or f"{BASE}/{name}?download=1"
        dest = OUTDIR / name
        if dest.exists() and dest.stat().st_size > 0:
            ok = True  # skip (already fetched, incl. previous single-thread pass)
        else:
            ok = download(url, dest)
        with lock:
            totals["ok" if ok else "fail"] += 1
            with fetch_log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"file": name, "ok": ok,
                                     "at": datetime.datetime.now(datetime.timezone.utc).isoformat()}) + "\n")
        time.sleep(args.sleep)

    for year in range(args.start, args.end + 1):
        items = year_listing(year)
        keep = [it for it in items if wanted(it.get("name", ""), months)]
        log(f"{year}: {len(keep)}/{len(items)} files wanted ({args.workers} workers)")
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            list(pool.map(one, keep))
    log(f"done: {totals['ok']} ok, {totals['fail']} failed -> {OUTDIR}")
    return 0 if totals["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
