"""Extract Gangtok-pilot IMD daily rainfall (SIH26001, honest NGEN Person-1).

Reads the committed IMD 0.25° gridded NetCDF archive (data/raw/imd/ind*_rfp25.nc,
same files + grid as the v1 Neyveli extraction) at the grid cell nearest the
S1 slope (Tathangchen, 27.3450N 88.6000E) via xarray nearest-neighbour
selection — identical method to ml/data_generation/extract_neyveli_rainfall.py,
only the target lat/lon differ.

Outputs:
  data/processed/imd/gangtok_rainfall_<start>_<end>.csv  (TIME, rainfall_mm)
plus a peak-monsoon window report printed to stdout for the S1 feature row
(rainfall_24h/7d/30d_mm trailing sums ending on a REAL date).

Run (system python has xarray+netCDF4; mnemo venv does not):
  C:\\Users\\satvi\\AppData\\Local\\Programs\\Python\\Python311\\python.exe scripts/extract_gangtok_rainfall.py --start 2024 --end 2024
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import xarray as xr

IMD_DIR = Path("data/raw/imd")
OUTPUT_DIR = Path("data/processed/imd")

# S1 Tathangchen (upper) — contract SCAFFOLD_CONTRACT_SEPT5.md §1
TARGET_LAT = 27.3450
TARGET_LON = 88.6000


def parse_args():
    p = argparse.ArgumentParser(description="Extract Gangtok IMD daily rainfall")
    p.add_argument("--start", type=int, default=2024)
    p.add_argument("--end", type=int, default=2024)
    return p.parse_args()


def extract_year(file_path: Path) -> pd.DataFrame:
    with xr.open_dataset(file_path) as ds:
        rainfall = ds["RAINFALL"].sel(
            LATITUDE=TARGET_LAT, LONGITUDE=TARGET_LON, method="nearest"
        )
        actual_lat = float(rainfall["LATITUDE"].values)
        actual_lon = float(rainfall["LONGITUDE"].values)
        df = rainfall.to_dataframe(name="rainfall_mm").reset_index()
        df["grid_lat"] = actual_lat
        df["grid_lon"] = actual_lon
        return df[["TIME", "rainfall_mm", "grid_lat", "grid_lon"]]


def main():
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for year in range(args.start, args.end + 1):
        fp = IMD_DIR / f"ind{year}_rfp25.nc"
        if not fp.exists():
            print(f"[MISSING] {year}")
            continue
        print(f"[READING] {year}")
        frames.append(extract_year(fp))
    if not frames:
        raise RuntimeError("No rainfall files found.")
    rain = pd.concat(frames, ignore_index=True).sort_values("TIME")
    rain = rain.rename(columns={"TIME": "timestamp"})
    out = OUTPUT_DIR / f"gangtok_rainfall_{args.start}_{args.end}.csv"
    rain.to_csv(out, index=False)
    print()
    print("=== EXTRACTION COMPLETE ===")
    print(f"Grid cell used: lat={rain['grid_lat'].iloc[0]}, lon={rain['grid_lon'].iloc[0]}")
    print(f"Rows: {len(rain):,}")
    print(f"Start: {rain['timestamp'].min()}")
    print(f"End:   {rain['timestamp'].max()}")
    print(f"Missing rainfall: {rain['rainfall_mm'].isna().sum():,}")

    # Peak-monsoon window: wettest trailing-7d spell of the year (demo event window)
    r = rain.set_index("timestamp")["rainfall_mm"].fillna(0.0)
    roll7 = r.rolling(7, min_periods=7).sum()
    peak = roll7.idxmax()
    day = r.loc[peak]
    w7 = roll7.loc[peak]
    idx = r.index.get_loc(peak)
    w30 = r.iloc[max(0, idx - 29):idx + 1].sum()
    print()
    print("=== PEAK 7-DAY WINDOW (S1 event-window candidate) ===")
    print(f"End date (time_window): {peak.date()}")
    print(f"rainfall_24h_mm = {day:.1f}")
    print(f"rainfall_7d_mm  = {w7:.1f}")
    print(f"rainfall_30d_mm = {w30:.1f}")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
