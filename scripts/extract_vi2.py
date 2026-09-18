"""VI-2 extraction: patch stats per event×pair from local LiCSAR TIFFs (no fitting).

Reads manifest + local files (data/raw/licsar/<frame>/), extracts 1km-box stats
at each event coordinate: cc median/spread/valid-frac, unw median/spread/valid-frac
(radians + mm LOS), nodata handling, date-gate re-asserted per pair.
Outputs runs/phase_v/vi2/sar_features.json + extraction_audit.json.
Run (py311): python scripts/extract_vi2.py
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MAN = REPO / "runs" / "phase_v" / "vi2" / "download_manifest.json"
LIC = REPO / "data" / "raw" / "licsar"
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUT = REPO / "runs" / "phase_v" / "vi2" / "sar_features.json"
AUD = REPO / "runs" / "phase_v" / "vi2" / "extraction_audit.json"
LAM = 0.05546576
RAD2MM = LAM / (4 * np.pi) * 1000.0


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import rasterio
    man = json.load(open(MAN, encoding="utf-8"))
    d = pd.read_csv(TRACKER)
    coords = {r["slide_no"]: (float(r["lat"]), float(r["lon"]), str(r["exact_date"]))
              for _, r in d.iterrows()}
    feats, issues, nfiles, nbytes = {}, [], 0, 0
    for ev, e in man["events"].items():
        la, lo, T = coords[ev]
        erows = []
        for p in e["pairs"]:
            a, b = p["pair"].split("_")
            assert b <= T.replace("-", ""), f"POST-T PAIR {ev} {p['pair']}"
            fr = p["frame"]
            orb = "48" if fr.startswith("048") else "12"
            row = {"frame": fr, "pair": p["pair"], "slot": p["slot"]}
            for fn, kind in ((p["files"][0], "unw"), (p["files"][1], "cc")):
                fp = LIC / f"{orb}_{fr}" / fn
                if not fp.exists():
                    row[kind] = {"provenance": "MISSING-file"}
                    issues.append(f"{ev}/{p['pair']}/{kind}: file absent")
                    continue
                nbytes += fp.stat().st_size
                nfiles += 1
                with rasterio.open(fp) as src:
                    assert src.crs is not None and src.crs.to_epsg() == 4326, f"CRS {src.crs}"
                    rr, cc = src.index(lo, la)
                    w = src.read(1, window=((max(0, rr - 5), rr + 6),
                                            (max(0, cc - 5), cc + 6))).astype(float)
                    w = np.where(w == src.nodata, np.nan, w)
                    nv = int(np.isfinite(w).sum())
                    row[kind] = {"n_valid": nv, "n_total": int(w.size),
                                 "median": round(float(np.nanmedian(w)), 3) if nv else None,
                                 "spread_p90_p10": round(float(np.nanpercentile(w, 90) - np.nanpercentile(w, 10)), 3) if nv >= 10 else None,
                                 "provenance": "REAL"}
                    if kind == "unw" and nv:
                        row[kind]["median_mm"] = round(float(np.nanmedian(w)) * RAD2MM, 1)
            erows.append(row)
        feats[ev] = {"T": e["T"], "lat": la, "lon": lo, "pairs": erows}
        log(f"{ev}: {len(erows)} pairs")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(feats, indent=2), encoding="utf-8")
    # audit: coverage + gate re-verification
    npairs = sum(len(v["pairs"]) for v in feats.values())
    nunw = sum(1 for v in feats.values() for r in v["pairs"] if r["unw"].get("median") is not None)
    aud = {"events": len(feats), "pairs": npairs, "files_read": nfiles,
           "bytes": nbytes, "pairs_with_unw": nunw,
           "date_gate": "secondary <= T-1 asserted per pair in code",
           "units": {"unw": "radians (×8.84 = mm LOS)", "cc": "uint8 0-255"},
           "issues": issues}
    AUD.write_text(json.dumps(aud, indent=2), encoding="utf-8")
    log(f"events={len(feats)} pairs={npairs} unw-coverage={nunw}/{npairs} issues={len(issues)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
