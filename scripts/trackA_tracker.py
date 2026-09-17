"""Track A candidate tracker: 57 month-year PDF rows + mining status fields (SIH26001).

Outputs: data/sih26001/evidence/trackA_candidates.csv (committed, human-edited).
Run: mnemo-venv python scripts/trackA_tracker.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data/sih26001/evidence/trackA_candidates.csv"

MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december"
          "|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
FULL_DATE = re.compile(r"\b([0-3]?\d)[\-/]([0-1]?\d|%s)[\-/](19|20)\d{2}\b" % MONTHS, re.I)
MONTH_YEAR = re.compile(r"\b(%s)[,\s]+(19|20)\d{2}\b" % MONTHS, re.I)


def main() -> int:
    import build_training_matrix as B
    import pymupdf
    pos = B.load_positives()
    doc = pymupdf.open(str(REPO / "data/raw/landslide_report.pdf"))
    pages = {p: doc[p - 1].get_text().split("\n") for p in range(659, 677)}
    anchors = []
    for pno, lines in pages.items():
        for i, ln in enumerate(lines):
            if re.fullmatch(r"\d{5}", ln.strip()):
                anchors.append((pno, i, ln.strip()))
    anchors.sort()
    hist_by_sl = {}
    for k, (pno, i, sl) in enumerate(anchors):
        if k + 1 < len(anchors):
            npno, ni, _ = anchors[k + 1]
            buf = pages[pno][i + 1:ni] if npno == pno else pages[pno][i + 1:] + \
                [ln for p in range(pno + 1, npno) for ln in pages[p]] + pages[npno][:ni]
        else:
            buf = pages[pno][i + 1:]
        hist_by_sl[sl] = " ".join(" ".join(buf).split())

    rows = []
    for _, r in pos[pos["source"] == "pdf"].iterrows():
        hit = [hh for hh in hist_by_sl.values() if r["slide_no"] in hh]
        h = hit[0] if hit else ""
        my = MONTH_YEAR.search(h)
        if FULL_DATE.search(h) or not my:
            continue
        rows.append({"slide_no": r["slide_no"], "district": r["district"],
                     "lat": round(float(r["lat"]), 4), "lon": round(float(r["lon"]), 4),
                     "year": int(r["year"]), "month_hint": my.group(0),
                     "exact_date": "", "time": "", "source": "", "source_url": "",
                     "date_precision": "month-year", "location_precision": "",
                     "fatalities": "", "road_association": "", "status": "to-mine"})
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"[{time.strftime('%H:%M:%S')}] tracker rows: {len(rows)} -> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
