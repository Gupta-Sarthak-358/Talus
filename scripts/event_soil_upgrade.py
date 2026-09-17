"""Event-anchored soil upgrade for the SIH26001 training matrix (soil-fix lane).

Problem (ablation proof): soil_moisture is one June-2024 week for ALL rows
(including 1965 slides), so the model can't learn wetness (no_soil -0.0074).
Fix: year- and date-anchored v09.2 CCI daily values where the archive allows.

Single-version rule: the overlap check (v09.2 vs v202505, June 10-16 2024,
study bbox) showed mean abs diff 0.022 / max 0.056 — small on average but
one cell 25% off. So EVERYTHING below is v09.2; no version mixing per-row.

Tiers (per-row sidecar.soil_source, never invented):
  event-soil-daily        exact event date known: trailing-7d mean at nearest
                          cell from v09.2 dailies (Mangan/Dipudara/NH10).
  event-year-window-soil  year known (>=1978): June 10-16 window-mean of THAT
                          year at nearest cell (same calendar window as the
                          old quasi-static, year-specific).
  background-year-window  negatives: seed-42 random year from the positive
                          year pool (>=1978), same window extraction.
  quasistatic-v092-fallback undated / pre-1978 / missing-file / all-NaN-cell:
                          v09.2 June 10-16 2024 window-mean (gap chain:
                          cell days -> bbox spatial mean -> global fallback,
                          counts logged).

Schema: unchanged 22 columns, same order. Matrix + sidecar git-ignored;
stratified 20-row sample + manifest shas regenerated (same rng method,
stable row selection). Backup to runs/soil_upgrade_backup/.

Run (py311, needs xarray): Python311/python.exe scripts/event_soil_upgrade.py
Then (mnemo venv): train -> ablate -> physics -> replays.
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
SOIL92 = REPO / "data" / "raw" / "soil" / "v09.2"
PROCDIR = REPO / "data/sih26001/processed"
EVIDDIR = REPO / "data/sih26001/evidence"
FIXDIR = REPO / "data/sih26001/fixtures"
MATRIX_CSV = PROCDIR / "feature_matrix.training.csv"
SIDECAR_CSV = PROCDIR / "training_sidecar.csv"
SAMPLE_CSV = EVIDDIR / "feature_matrix.training.sample.csv"
MANIFEST = REPO / "data/sih26001/manifest.training.json"
BACKUP = REPO / "runs" / "soil_upgrade_backup"
SEED = 42
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999
KILL = 4 | 8 | 16 | 32
WIN = [(6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16)]
V92_MIN_YEAR = 1978

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
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin(np.radians(lat2 - lat1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def day_files(year: int, dates: list[str]) -> list[Path]:
    out = []
    for d in dates:
        c = d.replace("-", "")
        hits = sorted(SOIL92.glob(f"ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-{c}*.nc"))
        out.extend(hits)
    return out


def window_grid(year: int, dates: list[str]):
    """(daily_stack, lat, lon) masked arrays for given dates; missing days skipped."""
    import xarray as xr
    files = day_files(year, dates)
    stack, alat, alon = [], None, None
    for fp in files:
        with xr.open_dataset(fp) as ds:
            sm = ds["sm"].sel(lat=slice(27.999, 27.00), lon=slice(LON0, LON1)).to_numpy().astype(float).squeeze()
            fl = ds["flag"].sel(lat=slice(27.999, 27.00), lon=slice(LON0, LON1)).to_numpy().squeeze()
            with np.errstate(invalid="ignore"):
                m = (fl.astype(float).astype(int) & KILL) == 0
            stack.append(np.where(m, sm, np.nan))
            if alat is None:
                alat = ds["lat"].sel(lat=slice(27.999, 27.00)).to_numpy()
                alon = ds["lon"].sel(lon=slice(LON0, LON1)).to_numpy()
    return np.array(stack), alat, alon, len(files)


def cell_means(stack: np.ndarray, ri: np.ndarray, ci: np.ndarray) -> np.ndarray:
    return np.array([np.nanmean(stack[:, r, c]) for r, c in zip(ri.tolist(), ci.tolist())])


def nearest_idx(alat, alon, lat, lon):
    return (np.clip(np.searchsorted(alat, lat), 0, len(alat) - 1),
            np.clip(np.searchsorted(alon, lon), 0, len(alon) - 1))


def main() -> int:
    mat = pd.read_csv(MATRIX_CSV)
    side = pd.read_csv(SIDECAR_CSV)
    assert len(mat) == len(side) == 2936
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy(MATRIX_CSV, BACKUP / "feature_matrix.training.csv")
    shutil.copy(SIDECAR_CSV, BACKUP / "training_sidecar.csv")
    log("backup -> runs/soil_upgrade_backup/")

    y = mat["event"].to_numpy().astype(int)
    years = side["year"].to_numpy().astype(int)
    lat = side["lat"].to_numpy().astype(float)
    lon = side["lon"].to_numpy().astype(float)
    soil = mat["soil_moisture"].to_numpy().astype(float).copy()
    src = np.full(len(mat), "quasistatic-v092-fallback", dtype=object)
    syr = np.zeros(len(mat), dtype=int)
    chain = {"cell": 0, "spatial": 0, "global": 0}

    jun_dates = lambda yr: [f"{yr}-06-{d:02d}" for _, d in WIN]  # noqa: E731
    ref_stack, ref_lat, ref_lon, ref_n = window_grid(2024, jun_dates(2024))
    ref_spatial = float(np.nanmean(ref_stack))
    log(f"reference v09.2 June-2024 window: {ref_n}/7 days, spatial mean {ref_spatial:.4f}")

    def resolve(stack, alat, alon, idx, tag, yr, lvl_note=""):
        nonlocal soil
        ri, ci = nearest_idx(alat, alon, lat[idx], lon[idx])
        vals = cell_means(stack, ri, ci)
        need = np.isnan(vals)
        if need.any():
            sp = np.array([np.nanmean(stack[:, r, c]) if False else np.nanmean(stack[:, :, :][:, max(0, r - 1):r + 2, max(0, c - 1):c + 2]) for r, c in zip(ri[need].tolist(), ci[need].tolist())])
            vals[need] = sp
            chain["spatial"] += int((~np.isnan(sp)).sum())
            still = np.isnan(vals)
            vals[still] = ref_spatial
            chain["global"] += int(still.sum())
        else:
            chain["cell"] += len(idx)
        soil[idx] = np.round(np.clip(vals, 0, 1), 4)
        src[idx] = tag
        syr[idx] = yr

    # tier 1: year-window positives
    pos_dated = (y == 1) & (years >= V92_MIN_YEAR)
    log(f"year-window positives (>=1978): {int(pos_dated.sum())}")
    for yr in sorted(np.unique(years[pos_dated]).tolist()):
        idx = np.where(pos_dated & (years == yr))[0]
        stack, alat, alon, n = window_grid(int(yr), jun_dates(int(yr)))
        if n == 0 or alat is None:
            log(f"  {yr}: no v09.2 June files -> fallback ({len(idx)} rows)")
            continue
        resolve(stack, alat, alon, idx, "event-year-window-soil", int(yr))

    # tier 2: matched negatives (pool restricted to v09.2 era, documented)
    pool = sorted(int(v) for v in np.unique(years[pos_dated]).tolist())
    rng = np.random.default_rng(SEED)
    neg_idx = np.where(y == 0)[0]
    neg_years = rng.choice(np.array(pool), size=len(neg_idx))
    by_year: dict[int, list[int]] = {}
    for i, yy in zip(neg_idx.tolist(), neg_years.tolist()):
        by_year.setdefault(int(yy), []).append(i)
    for yr, members in sorted(by_year.items()):
        idx = np.array(members)
        stack, alat, alon, n = window_grid(int(yr), jun_dates(int(yr)))
        if n == 0 or alat is None:
            continue
        resolve(stack, alat, alon, idx, "background-year-window-soil", int(yr))
    log(f"negatives matched to {len(by_year)} background years (seed {SEED}, pool>=1978)")

    # tier 3: exact-date trailing-7d overlays
    n_exact = 0
    for label, clat, clon, date in EXACT_DATES:
        yr = int(date[:4])
        end = pd.Timestamp(date)
        dates = [(end - pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        d = haversine_m(lat, lon, clat, clon)
        cand = np.where((y == 1) & (d <= EXACT_MATCH_M))[0]
        if len(cand) == 0:
            log(f"  {label}: no positive row within {EXACT_MATCH_M:.0f}m, skipped")
            continue
        stack, alat, alon, n = window_grid(yr, dates)
        if n == 0 or alat is None:
            log(f"  {label}: no v09.2 files in trailing window, skipped")
            continue
        resolve(stack, alat, alon, cand, "event-soil-daily", yr)
        n_exact += len(cand)
        log(f"  {label} {date}: {len(cand)} rows, {n}/7 days available")

    # tier 4: fallback = reference window for everyone still tagged fallback
    fb = np.where(src == "quasistatic-v092-fallback")[0]
    if len(fb):
        ri, ci = nearest_idx(ref_lat, ref_lon, lat[fb], lon[fb])
        vals = cell_means(ref_stack, ri, ci)
        need = np.isnan(vals)
        vals[need] = ref_spatial
        soil[fb] = np.round(np.clip(vals, 0, 1), 4)
        syr[fb] = 0
    log(f"fallback rows: {len(fb)} (undated/pre-1978/missing); gap chain cell={chain['cell']} "
        f"spatial={chain['spatial']} global={chain['global']}")

    mat["soil_moisture"] = soil
    assert not mat.isna().any().any()
    assert ((mat["soil_moisture"] >= 0) & (mat["soil_moisture"] <= 1)).all()
    mat.to_csv(MATRIX_CSV, index=False)
    side["soil_source"] = src
    side["soil_year"] = syr
    side.to_csv(SIDECAR_CSV, index=False)

    header = pd.read_csv(FIXDIR / "feature_matrix.sample.csv", nrows=0).columns.tolist()
    pi = rng.choice(np.where(y == 1)[0], size=min(10, int((y == 1).sum())), replace=False)
    ni = rng.choice(np.where(y == 0)[0], size=min(10, int((y == 0).sum())), replace=False)
    samp = mat.iloc[sorted(np.concatenate([pi, ni]).tolist())][header]
    assert not samp.isna().any().any() and "FILL" not in samp.to_csv()
    samp.to_csv(SAMPLE_CSV, index=False)

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    st = man.get("stats", {})
    st["matrix_sha256"] = sha256(MATRIX_CSV)
    st["sidecar_sha256"] = sha256(SIDECAR_CSV)
    st["sample_sha256"] = sha256(SAMPLE_CSV)
    st["soil_upgrade"] = {
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "version": "v09.2 single-version (overlap vs v202505: mean|diff| 0.0219, max 0.0559)",
        "event_soil_daily_rows": int((src == "event-soil-daily").sum()),
        "event_year_window_rows": int((src == "event-year-window-soil").sum()),
        "background_year_window_rows": int((src == "background-year-window-soil").sum()),
        "fallback_rows": int((src == "quasistatic-v092-fallback").sum()),
        "gap_chain": chain,
        "note": "June 10-16 window-mean per row-year (v09.2 CCI daily, kill-bits masked); "
                "exact dates get trailing-7d means; negatives seed-42 matched years (>=1978); "
                "gaps fall back cell-days -> bbox spatial -> reference mean (counts logged).",
    }
    man["stats"] = st
    feats = man.get("features", {})
    feats["soil"] = ("CCI COMBINED v09.2 daily (LOCAL ONLY, single-version): June 10-16 window-mean "
                     "of each row's year (kill-bits masked); exact-date rows get trailing-7d means; "
                     "negatives matched to seed-42 random positive-pool years (>=1978); undated/pre-1978/"
                     "all-NaN fall back to v09.2 June 2024 window. Per-row source in sidecar.soil_source.")
    man["features"] = feats
    man["honesty"] = (man.get("honesty", "") +
                      " Soil-fix Sep15: single-version v09.2 (overlap mean|diff| 0.0219 vs v202505); "
                      "year-window per dated row, matched years for negatives, tagged fallbacks.")
    MANIFEST.write_text(json.dumps(man, indent=2), encoding="utf-8")
    log(f"done: daily={int((src=='event-soil-daily').sum())} year={int((src=='event-year-window-soil').sum())} "
        f"bg={int((src=='background-year-window-soil').sum())} fb={int((src=='quasistatic-v092-fallback').sum())}")
    log("NEXT (mnemo venv): train -> ablate -> physics -> replays.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
