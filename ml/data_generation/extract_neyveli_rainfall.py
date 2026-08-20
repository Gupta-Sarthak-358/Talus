from pathlib import Path

import argparse

import pandas as pd
import xarray as xr

IMD_DIR = Path("data/raw/imd")
OUTPUT_DIR = Path("data/processed/imd")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_LAT = 11.50
TARGET_LON = 79.50

START_YEAR = 2000
END_YEAR = 2024


def parse_args():
    parser = argparse.ArgumentParser(description="Extract Neyveli IMD daily rainfall")
    parser.add_argument("--start", type=int, default=START_YEAR)
    parser.add_argument("--end", type=int, default=END_YEAR)
    return parser.parse_args()


def extract_year(file_path):
    with xr.open_dataset(file_path) as ds:
        rainfall = ds["RAINFALL"].sel(
            LATITUDE=TARGET_LAT,
            LONGITUDE=TARGET_LON,
        )

        df = rainfall.to_dataframe(name="rainfall_mm").reset_index()

        return df[["TIME", "rainfall_mm"]]


def main():
    args = parse_args()

    frames = []

    for year in range(args.start, args.end + 1):

        file_path = IMD_DIR / f"ind{year}_rfp25.nc"

        if not file_path.exists():
            print(f"[MISSING] {year}")
            continue

        print(f"[READING] {year}")

        df = extract_year(file_path)
        frames.append(df)

    if not frames:
        raise RuntimeError("No rainfall files found.")

    rainfall = pd.concat(frames, ignore_index=True)

    rainfall = rainfall.sort_values("TIME")

    rainfall = rainfall.rename(
        columns={
            "TIME": "timestamp"
        }
    )

    output_path = OUTPUT_DIR / f"neyveli_rainfall_{args.start}_{args.end}.csv"

    rainfall.to_csv(output_path, index=False)

    print()
    print("=== EXTRACTION COMPLETE ===")
    print(f"Rows: {len(rainfall):,}")
    print(f"Start: {rainfall['timestamp'].min()}")
    print(f"End:   {rainfall['timestamp'].max()}")
    print(f"Missing rainfall: {rainfall['rainfall_mm'].isna().sum():,}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()