"""Track A: date-precision audit of the inventory (SIH26001).

Classifies every positive's date knowledge: exact (news-anchored list + any
day-precision found in sources) / month-year (PDF histories) / year-only
(INITIATION year) / undated. Defines the calibration-candidate inclusion filter
and quantifies the gap to ~30-50 exact-date events.
Outputs: runs/trackA_date_audit.json. Run: mnemo-venv python scripts/trackA_date_audit.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "runs" / "trackA_date_audit.json"

MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december"
          "|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
FULL_DATE = re.compile(r"\b([0-3]?\d)[\-/]([0-1]?\d|%s)[\-/](19|20)\d{2}\b" % MONTHS, re.I)
MONTH_YEAR = re.compile(r"\b(%s)[,\s]+(19|20)\d{2}\b" % MONTHS, re.I)


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import build_training_matrix as B
    pos = B.load_positives()
    log(f"positives: {len(pos)}")

    # PDF histories: re-extract hist text blocks for month classification
    import pymupdf
    doc = pymupdf.open(str(REPO / "data/raw/landslide_report.pdf"))
    pages = {p: doc[p - 1].get_text().split("\n") for p in range(659, 677)}
    hist_by_sl = {}
    anchors = []
    for pno, lines in pages.items():
        for i, ln in enumerate(lines):
            if re.fullmatch(r"\d{5}", ln.strip()):
                anchors.append((pno, i, ln.strip()))
    anchors.sort()
    for k, (pno, i, sl) in enumerate(anchors):
        if k + 1 < len(anchors):
            npno, ni, _ = anchors[k + 1]
            buf = pages[pno][i + 1:ni] if npno == pno else pages[pno][i + 1:] + \
                [ln for p in range(pno + 1, npno) for ln in pages[p]] + pages[npno][:ni]
        else:
            buf = pages[pno][i + 1:]
        hist_by_sl[sl] = " ".join(" ".join(buf).split())

    def pdf_precision(row) -> str:
        if row["source"] != "pdf":
            return "n/a"
        # match by slide_no suffix
        return "unknown"

    # classify PDF rows via their sl_no if present else slide_no
    prec = []
    for _, r in pos.iterrows():
        if r["source"] != "pdf":
            prec.append("year-or-undated(shapefile)")
            continue
        # find hist by slide_no fragment
        key = next((k for k, h in hist_by_sl.items() if r["slide_no"].split("/")[-1] in h or r["slide_no"] in h), None)
        h = hist_by_sl.get(key, "") if key else ""
        if not h:
            # fallback: search all hists for slide_no
            hit = [hh for hh in hist_by_sl.values() if r["slide_no"] in hh]
            h = hit[0] if hit else ""
        if FULL_DATE.search(h):
            prec.append("month+exact-mention(pdf-hist)")
        elif MONTH_YEAR.search(h):
            prec.append("month-year(pdf-hist)")
        elif r["year"] > 0:
            prec.append("year-only(pdf-year)")
        else:
            prec.append("undated")
    pos = pos.copy()
    pos["date_precision"] = prec
    res: dict = {"precision_counts": {str(k): int(v) for k, v in pos["date_precision"].value_counts().items()}}
    # exact news-anchored seed list
    import event_rain_upgrade as ER
    res["exact_news_anchored"] = [{"label": l, "date": d} for l, _, _, d in ER.EXACT_DATES]
    # inclusion filter application
    cal = pos[pos["date_precision"].isin(["month+exact-mention(pdf-hist)"])]
    res["calibration_candidates_month_plus"] = int(len(cal))
    res["gap_to_30"] = max(0, 30 - res["calibration_candidates_month_plus"] - len(res["exact_news_anchored"]))
    # schema for future candidates
    res["candidate_schema"] = ["event_id", "date", "time", "lat", "lon", "district/state",
                               "source", "source_url/reference", "date_precision",
                               "location_precision", "fatalities", "road_association"]
    res["inclusion_filter"] = ("exact/usable event date + inside supported geography + "
                               "feature coverage + pre-event daily inputs available; "
                               "fuzzy dates stay replay-only, never calibration labels")
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT}")
    print(json.dumps({k: v for k, v in res.items() if k != "candidate_schema"}, indent=1)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
