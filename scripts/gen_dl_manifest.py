"""VI-2 Selenium download manifest: exact pair files per event (read-only listings).

Per championship event × frames (048D desc + 012A asc primary): recent/mid/baseline
pairs, secondary <= T-1 (hard gate), span <= 48 d preferred. Files: unw+cc TIFFs
via GWS pair pages (browser-proven route). Outputs runs/phase_v/vi2/download_manifest.json.
Run (py311): python scripts/gen_dl_manifest.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUTDIR = REPO / "runs" / "phase_v" / "vi2"
UA = {"User-Agent": "TALUS-research"}
GWS = "https://gws-access.jasmin.ac.uk/public/nceo_geohazards"
FRAMES = [("48", "048D_06252_131313"), ("12", "012A_06241_131313")]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def get(u: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=180).read().decode()


def main() -> int:
    d = pd.read_csv(TRACKER)
    e = d[d["eligible_for_championship"].astype(str) == "True"]
    pair_lists = {}
    for orb, fr in FRAMES:
        h = get(f"{GWS}/LiCSAR_products/{orb}/{fr}/interferograms/")
        pairs = sorted(set(re.findall(r"(\d{8})_(\d{8})", h)))
        pair_lists[fr] = pairs
        log(f"{fr}: {len(pairs)} pairs")
    man = {"frames": [f for _, f in FRAMES],
           "rule": "secondary <= T-1d; span<=48d preferred; slots recent/mid/baseline",
           "events": {}}
    for _, r in e.iterrows():
        T = pd.Timestamp(r["exact_date"]).date()
        ev = {"T": str(T), "pairs": []}
        for orb, fr in FRAMES:
            cands = [(a, b) for a, b in pair_lists[fr]
                     if b <= (T - dt.timedelta(days=1)).strftime("%Y%m%d")]
            def pick(lo, hi):
                c = [(a, b) for a, b in cands
                     if lo <= b <= hi and (pd.Timestamp(b) - pd.Timestamp(a)).days <= 48]
                c += [(a, b) for a, b in cands if lo <= b <= hi]
                return c[-1] if c else None
            slots = {"recent": ((T - dt.timedelta(days=20)).strftime("%Y%m%d"),
                                (T - dt.timedelta(days=1)).strftime("%Y%m%d")),
                     "mid": ((T - dt.timedelta(days=45)).strftime("%Y%m%d"),
                             (T - dt.timedelta(days=15)).strftime("%Y%m%d")),
                     "baseline": ((T - dt.timedelta(days=75)).strftime("%Y%m%d"),
                                  (T - dt.timedelta(days=30)).strftime("%Y%m%d"))}
            for slot, (lo, hi) in slots.items():
                hit = pick(lo, hi)
                if hit:
                    a, b = hit
                    ev["pairs"].append({
                        "frame": fr, "slot": slot, "pair": f"{a}_{b}",
                        "page": f"{GWS}/LiCSAR_products/{orb}/{fr}/interferograms/{a}_{b}",
                        "files": [f"{a}_{b}.geo.unw.tif", f"{a}_{b}.geo.cc.tif"]})
        man["events"][r["slide_no"]] = ev
        log(f"{r['slide_no']}: {len(ev['pairs'])} pairs")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "download_manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
