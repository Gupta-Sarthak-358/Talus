"""Phase 1B rainfall sampler.

Ports the validated prototype_v0 architecture (monthly wet/dry Markov chain +
empirical intensity resampling) into the generator. Rainfall is a single
mine-wide daily weather state: all zones within the same grid cell receive the
same daily rainfall, so the timeline is simulated once and shared across zones.

Neither the year-scale conditioning nor the storm-persistence templates from
the research freeze are implemented here -- those are Phase 1B+ enhancements
that layer extreme-event character onto this empirical core.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from generator_schema import BASE_DIR

RAINFALL_CSV = BASE_DIR / "data" / "processed" / "imd" / "neyveli_rainfall_2000_2024.csv"

ROLL_WINDOWS = {"3d": 3, "7d": 7}

# IMD intensity boundaries (mm/day), from analysis summary heavy_rain_threshold.
REGIME_DRY = 0.0
REGIME_NORMAL_MAX = 35.5  # IMD "moderate"
REGIME_WET_MAX = 64.5  # IMD "rather heavy / heavy rain" threshold (summary_2000_2024.json)

# Sub-stream tag so rainfall draws never collide with per-zone rng streams.
RAINFALL_STREAM = 1000


def build_month_models(hist):
    """Per-month wet/dry Markov + per-month empirical intensity pools."""
    df = hist.copy()
    df["state"] = df["rainfall_mm"] > 0
    month = df["timestamp"].dt.month
    prev_state = df["state"].shift(1)
    global_wet = df.loc[df["state"], "rainfall_mm"].values

    models = {}
    for m in range(1, 13):
        sel = df[month == m]
        wet_vals = sel.loc[sel["state"], "rainfall_mm"].values
        p_wet = float(sel["state"].mean()) if len(sel) else 0.0

        idx = df.index[(month == m) & prev_state.notna()]
        if len(idx):
            prev = prev_state.loc[idx].astype(bool)
            cur = df.loc[idx, "state"].astype(bool)
            n_wet_prev = int(prev.sum())
            n_dry_prev = int((~prev).sum())
            p_gw = float(((prev & cur).sum()) / n_wet_prev) if n_wet_prev else float("nan")
            p_gd = float(((~prev & cur).sum()) / n_dry_prev) if n_dry_prev else float("nan")
        else:
            p_gw = float("nan")
            p_gd = float("nan")

        models[m] = {
            "p_wet": p_wet,
            "p_wet_given_wet": p_gw,
            "p_wet_given_dry": p_gd,
            "wet_values": wet_vals,
            "n_wet": int(len(wet_vals)),
        }
    return models, global_wet


def _simulate_day_series(timeline, models, global_wet, rng):
    n = len(timeline)
    states = np.zeros(n, dtype=bool)
    rain = np.zeros(n, dtype=float)
    for t in range(n):
        model = models[timeline[t].month]
        if t == 0:
            p = model["p_wet"]
        else:
            p = model["p_wet_given_wet"] if states[t - 1] else model["p_wet_given_dry"]
            if not np.isfinite(p):
                p = model["p_wet"]
        states[t] = rng.random() < p
        if states[t]:
            pool = model["wet_values"] if len(model["wet_values"]) else global_wet
            rain[t] = 0.0 if len(pool) == 0 else float(rng.choice(pool))
    return rain


def classify_regime(m):
    if m <= REGIME_DRY:
        return "dry"
    if m <= REGIME_NORMAL_MAX:
        return "normal"
    if m <= REGIME_WET_MAX:
        return "wet"
    return "storm"


def generate_rainfall(timeline, seed):
    """Simulate one deterministic mine-wide daily rainfall series.

    Returns DataFrame with columns [timestamp, rainfall_mm, rainfall_3d_mm,
    rainfall_7d_mm, wet_day, rainfall_regime], fully populated (partial rolling
    windows accumulate from day 1, so there are no NaNs).
    """
    hist = pd.read_csv(RAINFALL_CSV, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    models, global_wet = build_month_models(hist)

    rng = np.random.default_rng(np.random.SeedSequence([seed, RAINFALL_STREAM]))
    rain = _simulate_day_series(pd.DatetimeIndex(timeline), models, global_wet, rng)

    out = pd.DataFrame({"timestamp": timeline, "rainfall_mm": rain})
    for name, win in ROLL_WINDOWS.items():
        out[f"rainfall_{name}_mm"] = out["rainfall_mm"].rolling(win, min_periods=1).sum()
    out["wet_day"] = out["rainfall_mm"] > 0
    out["rainfall_regime"] = out["rainfall_mm"].map(classify_regime).astype("category")
    return out[["timestamp", "rainfall_mm", "rainfall_3d_mm", "rainfall_7d_mm", "wet_day", "rainfall_regime"]]