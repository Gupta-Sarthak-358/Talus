from pathlib import Path

import xarray as xr

IMD_DIR = Path("data/raw/imd")

files = sorted(IMD_DIR.glob("*.nc"))

if not files:
    raise FileNotFoundError("No .nc files found in data/raw/imd/")

print(f"Found {len(files)} NetCDF files")
print(f"Inspecting: {files[-1]}")

ds = xr.open_dataset(files[-1])

print("\n=== DATASET ===")
print(ds)

print("\n=== DIMENSIONS ===")
print(ds.dims)

print("\n=== VARIABLES ===")
for name, var in ds.variables.items():
    print(
        f"{name}: "
        f"dims={var.dims}, "
        f"shape={var.shape}, "
        f"dtype={var.dtype}"
    )

print("\n=== COORDINATES ===")
for name, coord in ds.coords.items():
    print(name, coord.values)

ds.close()