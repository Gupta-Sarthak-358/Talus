from pathlib import Path

import argparse

import numpy as np
import pandas as pd
import xarray as xr

BASE_DIR = Path(__file__).resolve().parents[2]
IMD_DIR = BASE_DIR / "data" / "raw" / "imd"

TARGET_LAT = 11.50
TARGET_LON = 79.50
LAT_IDX = 20
LON_IDX = 52

EVENTS = {
    2015: ["2015-11-10"],
    2008: ["2008-11-28"],
}

WINDOWS = [1, 3, 7]


def excerpt(values, index, radius=10):
    lo = max(0, index - radius)
    hi = min(len(values), index + radius + 1)
    return list(enumerate(range(lo, hi))), values[lo:hi]


def main():
    rows = []
    for year, dates in EVENTS.items():
        file_path = IMD_DIR / f"ind{year}_rfp25.nc"
        if not file_path.exists():
            print(f"[MISSING] {file_path.name}")
            continue
        with xr.open_dataset(file_path) as ds:
            series = ds["RAINFALL"].values[:, LAT_IDX, LON_IDX]
            time = np.asarray(ds["TIME"].values, dtype="datetime64[ns]")

        for date_str in dates:
            target = np.datetime64(date_str)
            idx = int(np.flatnonzero(time == target)[0])
            print(f"\n=== {date_str}  (year file: {file_path.name}) ===")
            for w in WINDOWS:
                lo = idx - w + 1
                window = series[lo: idx + 1] if lo >= 0 else series[: idx + 1]
                total = float(np.nansum(window))
                local = pd.Timestamp(target)
                print(f"  {w}-day accumulation ending {local.date()}: {total:.2f} mm"
                      f"  ({len(window)} days"
                      + (", FULL window" if lo >= 0 else ", TRUNCATED at series start") + ")")

            print(f"  daily values around event (window ±6 days):")
            start = max(0, idx - 6)
            end = min(len(series), idx + 7)
            for t, v in zip(time[start:end], series[start:end]):
                mark = " <== EVENT" if pd.Timestamp(t).date().isoformat() == date_str else ""
                print(f"    {pd.Timestamp(t).date()}  {float(v):8.2f} mm{mark}")

            rows.append(
                {
                    "event": date_str,
                    "year_file": file_path.name,
                    "1d_mm": round(float(series[idx]), 2),
                    "3d_mm": round(
                        float(np.nansum(series[max(0, idx - 2): idx + 1])), 2
                    ),
                    "7d_mm": round(
                        float(np.nansum(series[max(0, idx - 6): idx + 1])), 2
                    ),
                }
            )

    print("\n=== VERIFICATION SUMMARY ===")
    for r in rows:
        print(
            f"{r['event']}: 1d={r['1d_mm']:.2f}  3d={r['3d_mm']:.2f}  7d={r['7d_mm']:.2f}  (from {r['year_file']})"
        )


if __name__ == "__main__":
    main()