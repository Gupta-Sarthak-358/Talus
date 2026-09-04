"""Extract pilot soil moisture from the CDS CCI download (SIH26001, soil round).

Reads the user-supplied ESA CCI Soil Moisture NetCDF (local-only raw) and
pulls the daily volumetric series at the grid cell nearest each slope
(S1-S4), same nearest-cell honesty as the IMD extraction. Handles both
unit conventions found in CCI files: m3/m3 (0-1, used as-is) and percent
saturation (divided by 100 — conversion LOGGED in the output JSON, never
silent).

Outputs (local until the .gitignore exception + manifest entry land):
  data/processed/soil/gangtok_soil_cci.csv  (timestamp, S1..S4 volumetric)
plus a per-slope window readout printed to stdout for the CSV row update
(soil_moisture = window-mean over --start/--end, 0-1).

Provenance label on success: REAL (satellite-observed CCI, not ERA5
reanalysis — stronger pedigree; 0.25-degree coarse-cell caveat same as IMD).

Run (needs xarray+netCDF4 — system py311 has them; mnemo venv does not):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_soil_cds.py --file data/raw/soil/<your-file>.nc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import xarray as xr

RAW_DIR = Path("data/raw/soil")
OUTPUT_DIR = Path("data/processed/soil")

SLOPES = {
    "S1": (27.3450, 88.6000),
    "S2": (27.3380, 88.6120),
    "S3": (27.3250, 88.6065),
    "S4": (27.3150, 88.5950),
}


def parse_args():
    p = argparse.ArgumentParser(description="Extract Gangtok CCI soil moisture")
    p.add_argument("--file", default=None, help="input NetCDF (default: first data/raw/soil/*.nc)")
    p.add_argument("--start", default="2024-06-10")
    p.add_argument("--end", default="2024-06-16")
    return p.parse_args()


def find_soil_var(ds: xr.Dataset) -> tuple[str, float, str]:
    """Return (var_name, scale_to_unit_interval, units_note)."""
    prefs = ["sm", "surface_soil_moisture", "soil_moisture", "swvl1"]
    for name in prefs:
        if name in ds:
            break
    else:
        cands = [v for v in ds.data_vars if "soil" in v.lower() or v.lower().startswith("sm")]
        if not cands:
            raise RuntimeError(f"No soil variable found among {list(ds.data_vars)}")
        name = cands[0]
    units = str(ds[name].attrs.get("units", "")).lower()
    if "percent" in units or "%" in units:
        return name, 1.0 / 100.0, f"{units} -> /100 to 0-1 (LOGGED conversion)"
    return name, 1.0, f"{units or 'unitless'} used as-is (0-1)"


def find_coords(ds: xr.Dataset) -> tuple[str, str, str]:
    lat = next((c for c in ("lat", "latitude", "LATITUDE") if c in ds.coords), None)
    lon = next((c for c in ("lon", "longitude", "LONGITUDE") if c in ds.coords), None)
    time = next((c for c in ("time", "TIME") if c in ds.coords), None)
    if not (lat and lon and time):
        raise RuntimeError(f"Unrecognised coords: {list(ds.coords)}")
    return lat, lon, time


def main():
    args = parse_args()
    fp = Path(args.file) if args.file else next(iter(sorted(RAW_DIR.glob("*.nc"))), None)
    if fp is None or not fp.exists():
        raise RuntimeError(f"No NetCDF found (looked for {fp}); paste the CDS file into data/raw/soil/ first")
    print(f"[READING] {fp} ({fp.stat().st_size / 1e6:.1f} MB)")
    ds = xr.open_dataset(fp)
    var, scale, note = find_soil_var(ds)
    latn, lonn, timen = find_coords(ds)
    print(f"[OK] var={var} ({note}); coords {latn}/{lonn}/{timen}")
    sub = ds[var].sel({timen: slice(args.start, args.end)})
    print(f"[OK] window {args.start}..{args.end}: {sub[timen].size} steps")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    series = {}
    for zid, (la, lo) in SLOPES.items():
        s = sub.sel({latn: la, lonn: lo}, method="nearest")
        alat, alon = float(s[latn].values), float(s[lonn].values)
        vals = (s.values.astype(float) * scale).tolist()
        series[zid] = {"grid": [alat, alon], "values": vals}
        import datetime
        times = [str(t)[:10] for t in sub[timen].values.tolist()]
        good = [v for v in vals if v == v]  # drop NaN
        mean = sum(good) / len(good) if good else float("nan")
        print(f"[OK] {zid}: grid=({alat},{alon}) n={len(vals)} missing={len(vals)-len(good)} window-mean={mean:.3f}")
    out_csv = OUTPUT_DIR / "gangtok_soil_cci.csv"
    with out_csv.open("w", encoding="utf-8") as f:
        f.write("timestamp," + ",".join(SLOPES) + "\n")
        for i, t in enumerate(times):
            f.write(str(t) + "," + ",".join(
                ("" if series[z]["values"][i] != series[z]["values"][i] else f"{series[z]['values'][i]:.4f}")
                for z in SLOPES) + "\n")
    meta = {"source_file": str(fp), "variable": var, "units_note": note,
            "window": [args.start, args.end],
            "row_values": {z: round(sum(v for v in series[z]["values"] if v == v) /
                                    max(1, sum(1 for v in series[z]["values"] if v == v)), 3)
                           for z in SLOPES}}
    (OUTPUT_DIR / "gangtok_soil_cci.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print()
    print("=== ROW VALUES (soil_moisture, window mean) ===")
    for z, v in meta["row_values"].items():
        print(f"{z}: soil_moisture = {v}")
    print(f"Saved: {out_csv} (+ .meta.json)")


if __name__ == "__main__":
    main()
