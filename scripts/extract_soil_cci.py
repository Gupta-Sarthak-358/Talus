"""Extract pilot soil moisture from CDS CCI daily files (SIH26001, soil round).

SOURCE (local-only raw): data/raw/soil/C3S-SOILMOISTURE-L3S-SSMV-COMBINED-DAILY-*.nc
(ESA CCI COMBINED TCDR v202505, global 0.25-degree, one file per day).
`sm` units are m3/m3 valid 0-1 (used as-is, no conversion). Flag mask:
bits snow/frozen(1), dense-veg(2), no-convergence(4), exceeds-boundary(8),
weight-low(16), unreliable(32), barren(64) — days with reliability-killer
bits (4|8|16|32) are masked as missing and counted; other flags are kept
but logged. Nearest-cell honesty applies (0.25-degree, same as IMD).

Outputs (committed extract + meta; raw stays git-ignored):
  data/processed/soil/gangtok_soil_cci.csv       (timestamp,S1..S4 volumetric)
  data/processed/soil/gangtok_soil_cci.meta.json (source/method/flags/row values)
plus a per-slope window-mean readout for the CSV row update
(soil_moisture = mean of valid days in window).

Provenance label: REAL (satellite-observed CCI, stronger than ERA5 reanalysis).

Run (needs xarray+netCDF4 — system py311):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_soil_cci.py
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import math
import sys
from pathlib import Path

import xarray as xr

RAW_DIR = Path("data/raw/soil")
OUTPUT_DIR = Path("data/processed/soil")
KILL_BITS = 4 | 8 | 16 | 32  # no-convergence, exceeds-boundary, weight-low, unreliable

SLOPES = {
    "S1": (27.3450, 88.6000),
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Gangtok CCI soil moisture extraction")
    ap.add_argument("--start", default="2024-06-10")
    ap.add_argument("--end", default="2024-06-16")
    args = ap.parse_args()
    files = sorted(RAW_DIR.glob("C3S-SOILMOISTURE-*.nc"))
    if not files:
        raise RuntimeError(f"No CCI files in {RAW_DIR}")
    print(f"[OK] {len(files)} daily files")
    series: dict[str, list] = {z: [] for z in SLOPES}
    stamps: list[str] = []
    cells: dict = {}
    flag_seen: dict[str, set] = {z: set() for z in SLOPES}
    for fp in files:
        ds = xr.open_dataset(fp)
        day = str(ds["time"].values[0])[:10]
        if not (args.start <= day <= args.end):
            ds.close()
            continue
        stamps.append(day)
        for zid, (la, lo) in SLOPES.items():
            s = ds["sm"].sel(lat=la, lon=lo, method="nearest")
            fl = ds["flag"].sel(lat=la, lon=lo, method="nearest")
            alat, alon = float(s["lat"].values.item()), float(s["lon"].values.item())
            cells[zid] = [alat, alon]
            flag_raw = fl.values.item()
            flag = int(flag_raw) if flag_raw == flag_raw else -1
            flag_seen[zid].add(flag)
            v = float(s.values.item())
            if v != v or (flag >= 0 and (flag & KILL_BITS)):
                series[zid].append(float("nan"))
            else:
                series[zid].append(round(v, 4))
        ds.close()
    if not stamps:
        raise RuntimeError(f"No files in window {args.start}..{args.end}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / "gangtok_soil_cci.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        f.write("timestamp," + ",".join(SLOPES) + "\n")
        for i, t in enumerate(stamps):
            f.write(t + "," + ",".join(
                ("" if series[z][i] != series[z][i] else f"{series[z][i]:.4f}") for z in SLOPES) + "\n")
    row_values = {}
    for zid in SLOPES:
        good = [v for v in series[zid] if v == v]
        mean = round(sum(good) / len(good), 3) if good else float("nan")
        row_values[zid] = {"window_mean": mean, "valid_days": f"{len(good)}/{len(series[zid])}",
                           "cell": cells[zid], "flags_seen": sorted(flag_seen[zid])}
        print(f"[OK] {zid}: cell={cells[zid]} valid={len(good)}/{len(series[zid])} "
              f"flags={sorted(flag_seen[zid])} window-mean={mean}")
    meta = {"source": "ESA CCI SM COMBINED TCDR v202505 (CDS, user download 2026-09-04)",
            "doi": "10.24381/cds.d7782f18", "units": "m3/m3 used as-is (0-1)",
            "grid": "0.25-degree nearest-cell (same representativeness caveat as IMD)",
            "kill_bits": "4|8|16|32 masked as missing; other flags kept but logged",
            "window": [args.start, args.end], "row_values": row_values}
    (OUTPUT_DIR / "gangtok_soil_cci.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print()
    print("=== ROW VALUES (soil_moisture, window mean of valid days) ===")
    for zid in SLOPES:
        print(f"{zid}: soil_moisture = {row_values[zid]['window_mean']}  ({row_values[zid]['valid_days']} valid)")
    print(f"Saved: {out_csv} (+ .meta.json)")


if __name__ == "__main__":
    sys.exit(main())
