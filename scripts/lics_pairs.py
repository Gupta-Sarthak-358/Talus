"""LiCSAR pair availability around championship windows (VI-2 feasibility, read-only).

Lists interferograms/ for covering frames, extracts pair dates, and reports for
each championship event: n pairs fully before T, earliest/latest, and whether a
T-60..T-1 deformation trajectory (>=3 pre-T epochs) is constructible.
No downloads of pair data, no fitting. Outputs into vi2_feasibility.json.
Run (py311): python scripts/lics_pairs.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FEAS = REPO / "runs" / "phase_v" / "vi2_feasibility.json"
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
UA = {"User-Agent": "TALUS-research-feasibility"}
ROOT = "https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products"
FRAMES = [("12", "012A_06241_131313"), ("48", "048D_06252_131313"),
          ("114", "114A_06191_131313"), ("114", "114A_06391_131313")]


def log(m: str) -> None:
    print(f"[{__import__('time').strftime('%H:%M:%S')}] {m}", flush=True)


def get(u: str) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=120).read().decode()


def main() -> int:
    feas = json.load(open(FEAS, encoding="utf-8"))
    d = pd.read_csv(TRACKER)
    e = d[d["eligible_for_championship"].astype(str) == "True"]
    frame_pairs: dict = {}
    for orb, fr in FRAMES:
        try:
            h = get(f"{ROOT}/{orb}/{fr}/interferograms/")
            dates = sorted({m for m in re.findall(r"(\d{8})_\d{8}", h)})
            # pair list YYYYMMDD_YYYYMMDD from file names like 20160808_20160820/...
            pairs = sorted(set(re.findall(r"(\d{8}_\d{8})", h)))
            frame_pairs[fr] = {"n_pair_names": len(pairs), "first": pairs[0] if pairs else None,
                               "last": pairs[-1] if pairs else None,
                               "n_acq_dates": len(dates)}
            log(f"{fr}: {len(pairs)} pairs {frame_pairs[fr]['first']}..{frame_pairs[fr]['last']}")
        except Exception as ex:
            frame_pairs[fr] = {"error": str(ex)[:100]}
            log(f"{fr}: ERROR {str(ex)[:100]}")
    feas["frames"] = frame_pairs
    # per-event: pairs with primary >= T-90d and secondary <= T-1d (all frames pooled)
    pair_lists: dict = {}
    for orb, fr in FRAMES:
        try:
            h = get(f"{ROOT}/{orb}/{fr}/interferograms/")
            pair_lists[fr] = sorted(set(re.findall(r"(\d{8})_(\d{8})", h)))
        except Exception:
            pair_lists[fr] = []
    ev_cov = {}
    for _, r in e.iterrows():
        T = pd.Timestamp(r["exact_date"]).date()
        lo = (T - dt.timedelta(days=90)).strftime("%Y%m%d")
        hi = (T - dt.timedelta(days=1)).strftime("%Y%m%d")
        n, frames = 0, set()
        for fr, pl in pair_lists.items():
            k = sum(1 for a, b in pl if lo <= a and b <= hi)
            if k:
                n += k
                frames.add(fr)
        epochs = n > 0
        ev_cov[r["slide_no"]] = {"T": str(T), "preT_pairs_90d": n,
                                 "frames": sorted(frames),
                                 "trajectory_ok": bool(n >= 3)}
    feas["per_event"] = ev_cov
    feas["summary"] = {
        "events_with_ge3_preT_pairs": sum(1 for v in ev_cov.values() if v["trajectory_ok"]),
        "events_total": len(ev_cov)}
    FEAS.write_text(json.dumps(feas, indent=2), encoding="utf-8")
    log(f"events with >=3 pre-T pairs: {feas['summary']['events_with_ge3_preT_pairs']}/{len(ev_cov)}")
    for k, v in ev_cov.items():
        if not v["trajectory_ok"]:
            log(f"  thin: {k} T={v['T']} pairs={v['preT_pairs_90d']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
