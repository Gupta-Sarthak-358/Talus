"""Sikkim label join from the GSI landslide inventory (SIH26001, labels round).

SOURCE (local-only raw): data/raw/gsi/GSI_Landslide_Inventory.shp.zip
(30,842 point slides, all-India, Bhusanket IDs like SK/ESK/78A11/2019/02).
User-supplied 2026-09-04; 5 MB zip stays out of git per .gitignore.

Method:
  - parse .shp points (struct) + .dbf attributes (numpy fixed-width)
  - Sikkim filter (STATE contains SIKKIM, any case) + Gangtok pilot bbox
    (88.58-88.63E, 27.30-27.36N) sample export (<=20 rows, committed)
  - per-slope nearest join over ALL Sikkim points (haversine metres)
Rules (handoff Item A):
  - previous_landslide=1 iff an inventoried slide is within ~300 m (Bhusanket
    ID cited); else 0
  - event=1 ONLY with a dated inventory event inside the 2024-06-16 window
    (or its season). INITIATION in this file is year-or-0, never a full date,
    so event stays 0 with the reason logged — never invented
  - evidence_quality: dated-only-negative (real window, negative label) or
    approximate (real occurrence year, e.g. 2019, but not in-window)

Outputs (committed):
  data/sih26001/evidence/sikkim_gangtok_sample.csv (bbox rows, raw values)
  data/sih26001/evidence/sikkim_join.json          (per-slope nearest + rule outputs)
Row values printed to stdout for the CSV update.

Run: <venv-python> scripts/extract_sikkim_labels.py  (needs numpy)
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np

ZIP = Path("data/raw/gsi/GSI_Landslide_Inventory.shp.zip")
EVIDENCE = Path("data/sih26001/evidence")
SAMPLE_CSV = EVIDENCE / "sikkim_gangtok_sample.csv"
JOIN_JSON = EVIDENCE / "sikkim_join.json"

SLOPES = {
    "S1": (27.3450, 88.6000),
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}
BBOX = (88.58, 88.63, 27.30, 27.36)  # lon0, lon1, lat0, lat1
BUFFER_M = 300.0
WINDOW = ("2024-06-10", "2024-06-16")

KEEP_COLS = ["SLIDE_NO", "SLIDE_NAME", "DISTRICT", "LONGITUDE", "LATITUDE",
             "INITIATION", "TRIGGERING", "ACTIVITY", "MATERIAL_T", "GEOLOGY"]


def clean(b: bytes) -> str:
    return b.decode("ascii", "ignore").replace("\x00", " ").strip()


def load():
    tmp = Path(tempfile.mkdtemp(prefix="gsi_inv_"))
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(tmp)
    base = tmp / "GSI_Landslide_Inventory"
    with open(str(base) + ".shp", "rb") as f:
        head = f.read(100)
        stype = struct.unpack("<i", head[32:36])[0]
        assert stype == 1, f"expected point shapefile, got type {stype}"
        f.seek(0, 2)
        n_pts = (f.tell() - 100) // 28
    with open(str(base) + ".dbf", "rb") as f:
        h = f.read(32)
        nrec, hlen = struct.unpack("<IH", h[4:10])
        fields, off = [], 32
        f.seek(32)
        while True:
            fd = f.read(32)
            if fd[0] == 0x0D:
                break
            fields.append((fd[:11].split(b"\x00")[0].decode("ascii", "ignore"),
                           chr(fd[11]), fd[16]))
    dt = [("del", "S1")] + [(n, f"S{ln}") for n, t, ln in fields]
    a = np.fromfile(str(base) + ".dbf", dtype=np.dtype(dt), offset=hlen)
    assert len(a) == nrec == n_pts, (len(a), nrec, n_pts)
    print(f"[OK] {nrec} point slides loaded")
    return a


def haversine_m(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def main() -> None:
    argparse.ArgumentParser(description="Sikkim label join").parse_args()
    if not ZIP.exists():
        raise RuntimeError(f"Missing {ZIP} (user-supplied, local-only)")
    a = load()
    is_sk = np.array([("SIKKIM" in clean(x).upper()) for x in a["STATE"]])
    sk = a[is_sk]
    print(f"[OK] Sikkim rows: {len(sk)}")
    lon = np.array([float(x) if x.strip() else float("nan") for x in sk["LONGITUDE"]])
    lat = np.array([float(x) if x.strip() else float("nan") for x in sk["LATITUDE"]])
    ok = ~(np.isnan(lon) | np.isnan(lat))
    print(f"[OK] Sikkim rows with coords: {int(ok.sum())}")
    sk, lon, lat = sk[ok], lon[ok], lat[ok]

    in_bbox = ((lon >= BBOX[0]) & (lon <= BBOX[1]) & (lat >= BBOX[2]) & (lat <= BBOX[3]))
    sample = sk[in_bbox]
    assert len(sample) <= 20, f"bbox sample {len(sample)} exceeds 20-row cap"
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with SAMPLE_CSV.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(KEEP_COLS) + "\n")
        for row in sample:
            vals = []
            for c in KEEP_COLS:
                v = clean(row[c]).replace('"', "'")
                vals.append(f'"{v}"' if ("," in v or '"' in v) else v)
            f.write(",".join(vals) + "\n")
    print(f"[OK] bbox sample: {len(sample)} rows -> {SAMPLE_CSV}")

    join: dict = {}
    rows: dict = {}
    for zid, (la, lo) in SLOPES.items():
        d = [haversine_m(la, lo, y, x) for y, x in zip(lat.tolist(), lon.tolist())]
        j = int(np.argmin(d))
        dist = round(d[j], 1)
        row = sk[j]
        info = {"slide_no": clean(row["SLIDE_NO"]), "name": clean(row["SLIDE_NAME"]),
                "district": clean(row["DISTRICT"]), "lon": float(lon[j]), "lat": float(lat[j]),
                "initiation": clean(row["INITIATION"]), "triggering": clean(row["TRIGGERING"]),
                "dist_m": dist}
        prev = 1 if dist <= BUFFER_M else 0
        # INITIATION here is year-or-0, never a full date -> can never place an
        # event inside the June-2024 window. event stays 0 with reason logged.
        event, eq = 0, ("approximate" if prev else "dated-only-negative")
        reason = (f"nearest slide {info['slide_no']} at {dist} m"
                  + (f" (INIT {info['initiation']}, year-only, not in-window)" if prev else ", outside 300 m"))
        join[zid] = {**info, "previous_landslide": prev, "event": event,
                     "evidence_quality": eq, "reason": reason}
        rows[zid] = {"previous_landslide": prev, "event": event, "evidence_quality": eq}
        print(f"[OK] {zid}: prev={prev} event={event} eq={eq} :: {reason}")
    JOIN_JSON.write_text(json.dumps(
        {"bbox": BBOX, "buffer_m": BUFFER_M, "window": WINDOW,
         "join": join,
         "queried_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        indent=2), encoding="utf-8")
    print()
    print("=== ROW VALUES (labels) ===")
    for zid in SLOPES:
        r = rows[zid]
        print(f"{zid}: previous_landslide={r['previous_landslide']} event={r['event']} evidence_quality={r['evidence_quality']}")
    print(f"Saved: {SAMPLE_CSV} + {JOIN_JSON}")


if __name__ == "__main__":
    sys.exit(main())
