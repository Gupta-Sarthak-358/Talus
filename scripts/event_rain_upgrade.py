"""Event-anchored rain upgrade for the SIH26001 training matrix (rain-fix lane).

Problem (ablation proof): rainfall_24h/7d/30d are 1991-2020 climatology means,
so the model learned rain is noise (no_rain +0.0042). Fix: replace climatology
with year- and date-anchored IMD daily values where dates exist.

Tiers (per-row tag in sidecar.rain_source, never invented dates):
  event-imd-daily       exact event date known (news/PDF-anchored, <=4 cases):
                        trailing 30d/7d/1d windows ending on the event date.
  event-year-peak-imd   year known (GSI INITIATION / PDF year, 746 positives):
                        THAT year's June total -> 30d, max trailing-7d in JJAS
                        -> 7d, max daily in JJAS -> 24h (same math as the
                        climatology builder, single-year, no averaging).
  background-year-peak  negatives: random year from the positive-year pool
                        (seed 42), same year-peak extraction, so both classes
                        see "how wet was this place in year Y" (matched design,
                        no construction leakage).
  climatology-1991-2020 fallback for year 0 / year 2025+ / missing file.

Schema: unchanged 22 columns, same order. Matrix + sidecar are git-ignored;
the stratified 20-row sample + manifest shas are regenerated (same rng
method as the builder, so sample row selection is stable).

Outputs: processed/feature_matrix.training.csv + training_sidecar.csv
(+rain_source, +rain_year), evidence/feature_matrix.training.sample.csv,
manifest.training.json shas/stats/provenance. Backup of pre-upgrade files
goes to runs/rain_upgrade_backup/ (git-ignored).

Run (mnemo venv): C:\\Users\\satvi\\Desktop\\mnemo\\.venv\\Scripts\\python.exe scripts/event_rain_upgrade.py
Then: train_sih26001.py, ablate_features.py, physics_fos_check.py
"""
from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IMD_DIR = REPO / "data/raw/imd"
PROCDIR = REPO / "data/sih26001/processed"
EVIDDIR = REPO / "data/sih26001/evidence"
FIXDIR = REPO / "data/sih26001/fixtures"
MATRIX_CSV = PROCDIR / "feature_matrix.training.csv"
SIDECAR_CSV = PROCDIR / "training_sidecar.csv"
SAMPLE_CSV = EVIDDIR / "feature_matrix.training.sample.csv"
MANIFEST = REPO / "data/sih26001/manifest.training.json"
BACKUP = REPO / "runs" / "rain_upgrade_backup"
SEED = 42
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999
IMD_MIN_YEAR, IMD_MAX_YEAR = 1901, 2024

# Exact-date overlay: (label, lat, lon, yyyy-mm-dd). News/PDF-anchored only.
EXACT_DATES = [
    ("mangan-jun2024", 27.51, 88.53, "2024-06-13"),
    ("dipudara-aug2024", 27.2525, 88.4606, "2024-08-20"),
    ("dipudara-rock-aug2024", 27.2525, 88.4606, "2024-08-21"),
    ("nh10-oct2022", 27.13, 88.51, "2022-10-09"),
]
EXACT_MATCH_M = 500.0


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    from math import radians
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    _ = radians(0)
    return 2 * r * np.arcsin(np.sqrt(a))


def year_grids(year: int):
    """Per-cell (june_total, max_trailing_7d_JJAS, max_daily_JJAS, lat, lon)."""
    import xarray as xr
    fp = IMD_DIR / f"ind{year}_rfp25.nc"
    with xr.open_dataset(fp) as ds:
        sub = ds["RAINFALL"].sel(LATITUDE=slice(LAT0, LAT1), LONGITUDE=slice(LON0, LON1),
                                 TIME=ds["TIME"].dt.month.isin([6, 7, 8, 9]))
        t = pd.to_datetime(sub["TIME"].to_numpy())
        v = np.nan_to_num(sub.to_numpy().astype(np.float64), nan=0.0)
        months = t.month.to_numpy()
        june_tot = v[months == 6].sum(axis=0)
        r7 = np.apply_along_axis(lambda m: np.convolve(m, np.ones(7), mode="valid").max()
                                 if len(m) >= 7 else np.nan, 0, v)
        dmax = v.max(axis=0)
        return june_tot, r7, dmax, sub["LATITUDE"].to_numpy(), sub["LONGITUDE"].to_numpy()


def date_windows(year: int, end: str):
    """Per-cell (trailing30d, trailing7d, day) ending on `end` (inclusive)."""
    import xarray as xr
    fp = IMD_DIR / f"ind{year}_rfp25.nc"
    end_d = pd.Timestamp(end)
    start_d = end_d - pd.Timedelta(days=29)
    with xr.open_dataset(fp) as ds:
        sub = ds["RAINFALL"].sel(LATITUDE=slice(LAT0, LAT1), LONGITUDE=slice(LON0, LON1),
                                 TIME=slice(str(start_d.date()), str(end_d.date())))
        t = pd.to_datetime(sub["TIME"].to_numpy())
        v = np.nan_to_num(sub.to_numpy().astype(np.float64), nan=0.0)
        assert len(t) >= 7, f"{year} {end}: only {len(t)} days in file window"
        w30 = v.sum(axis=0)
        w7 = v[-7:].sum(axis=0)
        d1 = v[-1]
        return w30, w7, d1, sub["LATITUDE"].to_numpy(), sub["LONGITUDE"].to_numpy()


def nearest_idx(alat, alon, lat, lon):
    ri = np.clip(np.searchsorted(alat, lat), 0, len(alat) - 1)
    ci = np.clip(np.searchsorted(alon, lon), 0, len(alon) - 1)
    return ri, ci


def main() -> int:
    mat = pd.read_csv(MATRIX_CSV)
    side = pd.read_csv(SIDECAR_CSV)
    assert len(mat) == len(side) == 2936, (len(mat), len(side))
    assert list(mat.columns)[:2] == ["zone_id", "time_window"]
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy(MATRIX_CSV, BACKUP / "feature_matrix.training.csv")
    shutil.copy(SIDECAR_CSV, BACKUP / "training_sidecar.csv")
    log("backup -> runs/rain_upgrade_backup/")

    y = mat["event"].to_numpy().astype(int)
    years = side["year"].to_numpy().astype(int)
    lat = side["lat"].to_numpy().astype(float)
    lon = side["lon"].to_numpy().astype(float)

    r30 = mat["rainfall_30d_mm"].to_numpy().astype(float).copy()
    r7 = mat["rainfall_7d_mm"].to_numpy().astype(float).copy()
    r1 = mat["rainfall_24h_mm"].to_numpy().astype(float).copy()
    src = np.full(len(mat), "climatology-1991-2020", dtype=object)
    ryr = np.zeros(len(mat), dtype=int)

    # --- tier 1: year-peak for dated positives --------------------------------
    pos_dated = (y == 1) & (years >= IMD_MIN_YEAR) & (years <= IMD_MAX_YEAR)
    log(f"dated positives in IMD range: {int(pos_dated.sum())}/{int((y==1).sum())}")
    for yr in sorted(np.unique(years[pos_dated]).tolist()):
        idx = np.where(pos_dated & (years == yr))[0]
        g30, g7, g1, alat, alon = year_grids(int(yr))
        ri, ci = nearest_idx(alat, alon, lat[idx], lon[idx])
        r30[idx] = np.round(g30[ri, ci], 1)
        r7[idx] = np.round(g7[ri, ci], 1)
        r1[idx] = np.round(g1[ri, ci], 1)
        src[idx] = "event-year-peak-imd"
        ryr[idx] = int(yr)
        log(f"  {yr}: {len(idx)} positives (jun {g30[ri,ci].min():.0f}-{g30[ri,ci].max():.0f}mm)")

    # --- tier 2: matched random-year peaks for negatives ----------------------
    pool = sorted(np.unique(years[pos_dated]).tolist())
    assert pool, "no dated positives to sample background years from"
    rng = np.random.default_rng(SEED)
    neg_idx = np.where(y == 0)[0]
    neg_years = rng.choice(np.array(pool), size=len(neg_idx))
    by_year: dict[int, list[int]] = {}
    for i, yy in zip(neg_idx.tolist(), neg_years.tolist()):
        by_year.setdefault(int(yy), []).append(i)
    for yr, members in sorted(by_year.items()):
        idx = np.array(members)
        g30, g7, g1, alat, alon = year_grids(int(yr))
        ri, ci = nearest_idx(alat, alon, lat[idx], lon[idx])
        r30[idx] = np.round(g30[ri, ci], 1)
        r7[idx] = np.round(g7[ri, ci], 1)
        r1[idx] = np.round(g1[ri, ci], 1)
        src[idx] = "background-year-peak-imd"
        ryr[idx] = int(yr)
    log(f"negatives matched to {len(by_year)} background years (seed {SEED})")

    # --- tier 3: exact-date overlay -------------------------------------------
    n_exact = 0
    for label, clat, clon, date in EXACT_DATES:
        yr = int(date[:4])
        if not (IMD_MIN_YEAR <= yr <= IMD_MAX_YEAR):
            log(f"  {label}: {date} outside IMD archive, skipped (tagged honest)")
            continue
        d = haversine_m(lat, lon, clat, clon)
        cand = np.where((y == 1) & (d <= EXACT_MATCH_M))[0]
        if len(cand) == 0:
            log(f"  {label}: no positive row within {EXACT_MATCH_M:.0f}m, skipped")
            continue
        w30, w7, d1, alat, alon = date_windows(yr, date)
        ri, ci = nearest_idx(alat, alon, lat[cand], lon[cand])
        r30[cand] = np.round(w30[ri, ci], 1)
        r7[cand] = np.round(w7[ri, ci], 1)
        r1[cand] = np.round(d1[ri, ci], 1)
        src[cand] = "event-imd-daily"
        ryr[cand] = yr
        n_exact += len(cand)
        log(f"  {label} {date}: {len(cand)} rows date-anchored "
            f"(24h {d1[ri,ci].min():.0f}-{d1[ri,ci].max():.0f}mm)")

    # --- write back (schema unchanged) -----------------------------------------
    mat["rainfall_30d_mm"] = r30
    mat["rainfall_7d_mm"] = r7
    mat["rainfall_24h_mm"] = r1
    assert not mat.isna().any().any()
    mat.to_csv(MATRIX_CSV, index=False)
    side["rain_source"] = src
    side["rain_year"] = ryr
    side.to_csv(SIDECAR_CSV, index=False)

    # stratified sample, same rng method as builder (stable row selection)
    header = pd.read_csv(FIXDIR / "feature_matrix.sample.csv", nrows=0).columns.tolist()
    assert len(header) == 22
    pi = rng.choice(np.where(y == 1)[0], size=min(10, int((y == 1).sum())), replace=False)
    ni = rng.choice(np.where(y == 0)[0], size=min(10, int((y == 0).sum())), replace=False)
    samp = mat.iloc[sorted(np.concatenate([pi, ni]).tolist())][header]
    assert not samp.isna().any().any() and "FILL" not in samp.to_csv()
    samp.to_csv(SAMPLE_CSV, index=False)

    # --- manifest ---------------------------------------------------------------
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    st = man.get("stats", {})
    st["matrix_sha256"] = sha256(MATRIX_CSV)
    st["sidecar_sha256"] = sha256(SIDECAR_CSV)
    st["sample_sha256"] = sha256(SAMPLE_CSV)
    st["rain_upgrade"] = {
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "event_imd_daily_rows": int((src == "event-imd-daily").sum()),
        "event_year_peak_rows": int((src == "event-year-peak-imd").sum()),
        "background_year_peak_rows": int((src == "background-year-peak-imd").sum()),
        "climatology_fallback_rows": int((src == "climatology-1991-2020").sum()),
        "note": "positives: exact-date windows where known, else that-year JJAS peak; "
                "negatives: seed-42 random-year peaks (matched design); undated/out-of-range "
                "keep 1991-2020 climatology. Month-anchored tier still TODO (PDF re-parse).",
    }
    man["stats"] = st
    feats = man.get("features", {})
    feats["rain"] = ("IMD 0.25deg daily rfp25 (LOCAL ONLY): exact-date trailing 30/7/1d windows "
                     "where event date known; that-year June-total->30d, max-trailing-7d-JJAS->7d, "
                     "max-daily-JJAS->24h for year-known rows; negatives matched to seed-42 random "
                     "positive-pool years; undated/out-of-range keep 1991-2020 climatology. "
                     "Per-row source in sidecar.rain_source (tagged).")
    man["features"] = feats
    man["honesty"] = (man.get("honesty", "") +
                      " Rain-fix Sep15: year-known rows use that-year IMD peaks (not 30-yr means); "
                      "exact-date rows use date-anchored windows; negatives use matched random years; "
                      "undated rows stay climatology (tagged per-row).")
    MANIFEST.write_text(json.dumps(man, indent=2), encoding="utf-8")

    log(f"done: daily={int((src=='event-imd-daily').sum())} year-peak={int((src=='event-year-peak-imd').sum())} "
        f"bg={int((src=='background-year-peak-imd').sum())} clim={int((src=='climatology-1991-2020').sum())}")
    log(f"sample {samp.shape} refreshed; manifest shas updated. NEXT: train -> ablate -> physics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
