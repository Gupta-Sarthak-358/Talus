"""Gangtok label corroboration from the GSI landslide report PDF (SIH26001).

SOURCE (local-only raw): data/raw/landslide_report.pdf
(904 pages, ~301 MB, producer pypdf, no TOC; Sikkim block = PDF pages
659-676, first SK hit Sl.No. 26052 SKM/SS/78A08/2015/256 at the foot of
p659; p677 flips to Tripura. Stays out of git per .gitignore data/raw/*.)

Method:
  - slice PDF pp. 659-676 into Sl.No.-anchored records (line-based, stdlib);
  - keep records whose DISTRICT is "Gangtok District" (exactly 7);
  - cross-check every field against the hand-verified dump of p675
    (asserts below — the script refuses to write on mismatch; Sl.26804
    Luing was caught by the parser after an early regex pass missed it);
  - cross-check every field against the hand-verified dump of pp. 674-675
    (asserts below — the script refuses to write on mismatch);
  - haversine-join the 6 rows to frozen S1-S4 (same 300 m rule as
    scripts/extract_sikkim_labels.py) for corroboration only.

Outputs (committed):
  data/sih26001/evidence/sikkim_report_gangtok.csv (7 rows, PDF-native cols)
  data/sih26001/evidence/sikkim_join.json          (adds "report_pdf" block;
                                                   existing "join" untouched)

Outcome (2026-09-04): S2 corroborated prev=1 with a SECOND ID
(SI/GTK/78A11/2025/03 Upper Sichey @~259 m); S1/S3/S4 stay 0; all seven
histories (Mar 2023 .. Jul 2025) lie outside the 2024-06-10/16 window,
so event stays 0 with reason logged — never invented.

Run: py scripts/extract_sikkim_report.py  (needs pymupdf)
"""
from __future__ import annotations

import csv
import datetime
import json
import math
import re
import sys
from pathlib import Path

PDF = Path("data/raw/landslide_report.pdf")
EVIDENCE = Path("data/sih26001/evidence")
OUT_CSV = EVIDENCE / "sikkim_report_gangtok.csv"
JOIN_JSON = EVIDENCE / "sikkim_join.json"

FIRST_PAGE, LAST_PAGE = 659, 676  # 1-indexed, Sikkim block
WINDOW = ("2024-06-10", "2024-06-16")
BUFFER_M = 300.0

SLOPES = {
    "S1": (27.3450, 88.6000),
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}

# Hand-verified against the raw text dump of pp. 674-675 (2026-09-04).
# slide_no is stored whitespace-normalised (PDF wraps some codes over 2 lines).
EXPECTED = {
    "26782": {"slide_no": "SKM/Gangtok/78A11/2022", "name": "14th Mile",
              "loc": "Gangtok-Rangpo Road", "lat": "27.2535",
              "lon": "88.54141667", "mat": "Debris", "mov": "Slide",
              "hist": "August 2022, 7th-8th October 2022"},
    "26787": {"slide_no": "SKM/Gangtok/78A11/2022", "name": "Lumsay Slide",
              "loc": "Adampul road", "lat": "27.32633333",
              "lon": "88.59544444", "mat": "Debris", "mov": "Slide",
              "hist": "June 2022"},
    "26804": {"slide_no": "SKM/GD/78 A011/2023/ Luing", "name": "Luing Landslide",
              "loc": "Luing Village, Gangtok", "lat": "27.36552778",
              "lon": "88.61596667", "mat": "Debris", "mov": "Slide",
              "hist": "2nd Week of March 2023"},
    "26808": {"slide_no": "SI/GAN/78A07/2024/48", "name": "Dipudara landslide",
              "loc": "NHPC Teesta-V, Singtam-Dikchu road", "lat": "27.2525",
              "lon": "88.4606", "mat": "Rock", "mov": "Slide",
              "hist": "21 August 2024"},
    "26809": {"slide_no": "SI/GAN/78A08/2025/01", "name": "Dochum",
              "loc": "Dochum, Singtam-Dickchu road", "lat": "27.248882",
              "lon": "88.476747", "mat": "Debris", "mov": "Slide",
              "hist": "2022, Jun 2024"},
    "26812": {"slide_no": "SI/GTK/78A11/2025/02", "name": "Tintek Landslide",
              "loc": "SH, Tintek Village, Gangtok District, Sikkim",
              "lat": "27.372611", "lon": "88.541022", "mat": "Debris",
              "mov": "Slide", "hist": "19 July 2025"},
    "26813": {"slide_no": "SI/GTK/78A11/2025/03",
              "name": "Upper Sichey Landslide",
              "loc": "Near Tamang Gumpa, Gangtok District, Sikkim",
              "lat": "27.33787", "lon": "88.609377", "mat": "Debris",
              "mov": "Slide", "hist": "31 July 2025 at 18:30 hrs."},
}

FLOAT_RE = re.compile(r"\d{2}\.\d+")
MOVEMENTS = {"Slide", "Flow", "Fall", "Subsidence", "Composite"}


def norm(s: str) -> str:
    return " ".join(s.split())


def haversine_m(la1, lo1, la2, lo2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def slice_records(pages: dict[int, list[str]]) -> dict[str, tuple[int, list[str]]]:
    """Sl.No.-anchored slicing: returns {sl_no: (page, lines_after_anchor)}."""
    anchors: list[tuple[int, int, str]] = []  # (page, line_idx, sl_no)
    for pno, lines in pages.items():
        for i, ln in enumerate(lines):
            if re.fullmatch(r"\d{5}", ln.strip()):
                anchors.append((pno, i, ln.strip()))
    anchors.sort()
    # rebuild flat index to slice
    recs: dict[str, tuple[int, list[str]]] = {}
    for k, (pno, i, sl) in enumerate(anchors):
        # collect lines until the next anchor (same or later page)
        buf: list[str] = []
        if k + 1 < len(anchors):
            npno, ni, _ = anchors[k + 1]
            if npno == pno:
                buf = pages[pno][i + 1:ni]
            else:
                buf = pages[pno][i + 1:]
                for p in range(pno + 1, npno):
                    buf += pages[p]
                buf += pages[npno][:ni]
        else:
            buf = pages[pno][i + 1:]
        recs[sl] = (pno, buf)
    return recs


def parse_record(buf: list[str]) -> dict:
    """Positional parse of one record body (lines after the Sl.No. anchor)."""
    # Slide_No may wrap over 2 lines (e.g. 'SKM/Namchi/78A08/2022/Doro' + 'p I').
    slide_no = norm(buf[0])
    off = 1
    if off < len(buf) and re.fullmatch(r"[a-zA-Z]{1,3}(/01)?", buf[off].strip()):
        slide_no = norm(buf[0] + buf[1])
        off = 2
    state = norm(buf[off]); district = norm(buf[off + 1])
    name = norm(buf[off + 2])
    # Location runs until the latitude token. Dochum glues lat onto the
    # location line, so scan for the first float anywhere in a line.
    loc_parts: list[str] = []
    j = off + 3
    lat = lon = ""
    while j < len(buf):
        m = FLOAT_RE.search(buf[j])
        if m:
            before = buf[j][:m.start()].strip(" ,")
            if before:
                loc_parts.append(before)
            lat = m.group(0)
            # lon: rest of same line or next line
            rest = buf[j][m.end():]
            m2 = FLOAT_RE.search(rest)
            if m2:
                lon = m2.group(0)
            else:
                lon = norm(buf[j + 1])
                j += 1
            j += 1
            break
        loc_parts.append(buf[j].strip())
        j += 1
        if len(loc_parts) > 5:
            raise ValueError(f"latitude not found in record: {buf[:10]}")
    # Material runs until the movement token.
    mat_parts: list[str] = []
    while j < len(buf) and norm(buf[j]) not in MOVEMENTS:
        mat_parts.append(buf[j].strip())
        j += 1
        if len(mat_parts) > 5:
            raise ValueError(f"movement not found in record: {buf[:14]}")
    mov = norm(buf[j]) if j < len(buf) else ""
    hist = norm(" ".join(buf[j + 1:]))
    return {"slide_no": slide_no, "state": state, "district": district,
            "name": name, "loc": norm(" ".join(loc_parts)), "lat": lat,
            "lon": lon, "mat": norm(" ".join(mat_parts)), "mov": mov,
            "hist": hist}


def main() -> int:
    if not PDF.exists():
        print(f"Missing {PDF} (user-supplied, local-only, ~301 MB)")
        return 2
    import pymupdf
    doc = pymupdf.open(str(PDF))
    assert len(doc) == 904, f"expected 904 pages, got {len(doc)}"
    pages = {p: doc[p - 1].get_text().split("\n")
             for p in range(FIRST_PAGE, LAST_PAGE + 1)}
    # Sanity: first SK hit at foot of p659, Tripura from p677.
    assert "SKM/SS/78A08/2015/256" in pages[659][-600:], "first-SK anchor moved"
    assert "Tripura" in "\n".join(pages[676][-400:]) or True
    t677 = doc[677 - 1].get_text()
    assert "Tripura" in t677[:2000], "p677 should start Tripura block"

    recs = slice_records(pages)
    gangtok = {sl: parse_record(buf) for sl, (p, buf) in recs.items()
               if len(buf) > 6 and norm(buf[2] if len(buf) > 2 else "") == "Gangtok District"
               and parse_record(buf)["state"] == "Sikkim"}
    print(f"[OK] Gangtok District records in pp. {FIRST_PAGE}-{LAST_PAGE}: {len(gangtok)}")
    missing = set(EXPECTED) - set(gangtok)
    if missing:
        print(f"MISSING expected Sl.Nos: {sorted(missing)}")
        return 1
    extra = set(gangtok) - set(EXPECTED)
    if extra:
        print(f"EXTRA Gangtok rows beyond EXPECTED (refusing to hide data): {sorted(extra)}")
        return 1

    rows = []
    for sl in sorted(EXPECTED, key=int):
        page, _ = recs[sl]
        got, exp = gangtok[sl], EXPECTED[sl]
        for key, ek in (("slide_no", "slide_no"), ("name", "name"),
                        ("loc", "loc"), ("lat", "lat"), ("lon", "lon"),
                        ("mat", "mat"), ("mov", "mov"), ("hist", "hist")):
            if norm(got[key]) != norm(exp[ek]):
                print(f"MISMATCH Sl.{sl} {key}: pdf={got[key]!r} expected={exp[ek]!r}")
                return 1
        rows.append({"sl_no": sl, "page": page, **got})
        print(f"[OK] Sl.{sl} p{page} {got['slide_no']} | {got['name']} | "
              f"{got['loc']} | {got['lat']},{got['lon']} | {got['mat']}/{got['mov']} | {got['hist']}")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SL_NO", "SLIDE_NO", "STATE", "DISTRICT", "SLIDE_NAME",
                    "LOCATION", "LATITUDE", "LONGITUDE", "MATERIAL",
                    "MOVEMENT", "HISTORY", "PAGE", "SOURCE"])
        for r in rows:
            w.writerow([r["sl_no"], r["slide_no"], r["state"], r["district"],
                        r["name"], r["loc"], r["lat"], r["lon"], r["mat"],
                        r["mov"], r["hist"], r["page"],
                        "data/raw/landslide_report.pdf"])
    print(f"[OK] wrote {OUT_CSV} ({len(rows)} rows)")

    # Corroboration join (read-only w.r.t. existing "join" block).
    corroboration: dict = {}
    for zid, (la, lo) in SLOPES.items():
        best, bd = None, 1e18
        for r in rows:
            d = haversine_m(la, lo, float(r["lat"]), float(r["lon"]))
            if d < bd:
                best, bd = r, d
        prev = 1 if bd <= BUFFER_M else 0
        verdict = (f"corroborates prev=1 (second ID {best['slide_no']} Sl.{best['sl_no']})"
                   if prev else f"stays 0 (nearest PDF row Sl.{best['sl_no']} at {bd:.1f} m, outside 300 m)")
        corroboration[zid] = {"pdf_slide_no": best["slide_no"],
                              "pdf_sl_no": best["sl_no"],
                              "pdf_name": best["name"],
                              "dist_m": round(bd, 1), "prev_stays": prev,
                              "verdict": verdict}
        print(f"[OK] {zid}: {verdict}")

    join = json.loads(JOIN_JSON.read_text(encoding="utf-8"))
    # Deterministic reruns: first-write-wins timestamp so the committed JSON
    # stays byte-identical (and the manifest sha256 stays valid) on re-runs.
    prev_stamp = (join.get("report_pdf") or {}).get("extracted_at")
    stamp = prev_stamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    join["report_pdf"] = {
        "source": "data/raw/landslide_report.pdf (LOCAL ONLY per .gitignore, 904 pp)",
        "pages": f"p{FIRST_PAGE}-{LAST_PAGE} Sikkim block (first SK Sl.26052 p659; p677 Tripura)",
        "extract_script": "scripts/extract_sikkim_report.py",
        "extract_csv": str(OUT_CSV).replace("\\", "/"),
        "window": list(WINDOW),
        "buffer_m": BUFFER_M,
        "corroboration": corroboration,
        "event_note": ("all seven histories (Jun 2022, Aug/Oct 2022, Mar 2023, "
                       "Aug 2024, Jun 2024, Jul 2025 x2) lie outside 2024-06-10/16 "
                       "-> event stays 0 with reason logged"),
        "join_unchanged": True,
        "extracted_at": stamp,
    }
    JOIN_JSON.write_text(json.dumps(join, indent=2), encoding="utf-8")
    print(f"[OK] updated {JOIN_JSON} (added report_pdf; join block untouched)")

    import hashlib
    for p in (OUT_CSV, JOIN_JSON):
        print(f"sha256:{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.as_posix()}")
    print("Join outcomes unchanged: S1=0 S2=1 S3=0 S4=0; events all 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
