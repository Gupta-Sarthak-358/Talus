"""ML Feature Schema V2: temporal/predictive trend features (Member 2 Phase 2-4).

Causality contract (Phase 3, MANDATORY):
    Every feature at time t may use observations from {t, t-1, t-2, ...} only.
    Rolling windows are trailing and INCLUDE t (today is observable).
    No feature may access any row after its prediction timestamp.
    Enforced by selftest_causality(); Experiment F aborts if it fails.

Groups (Phase 4 separation):
    STATIC            slope/geology/geometry
    CURRENT_STATE     V1 snapshot features (the frozen 12)
    TEMPORAL_RAIN     accumulation / persistence / recency of rain
    TEMPORAL_GW       wetting-memory direction of movement
    TEMPORAL_CRACK    damage rate / acceleration / accumulated growth
    TEMPORAL_BLAST    recent exposure history

V1 columns are never modified; V2 = V1 + temporal groups.
"""
import numpy as np
import pandas as pd

HEAVY_RAIN_MM = 25.0

STATIC = ["slope_angle_deg", "slope_height_m", "rock_type"]
CURRENT_STATE = ["rainfall_24h_mm", "rainfall_7d_mm", "groundwater_proxy",
                 "crack_density", "crack_severity", "blast_frequency_per_week",
                 "blast_vibration_ppv_mms", "days_since_inspection", "prior_incident"]
TEMPORAL_RAIN = ["rainfall_3d_mm", "rainfall_14d_mm", "max_rainfall_7d_mm",
                 "consecutive_wet_days", "days_since_heavy_rain"]
TEMPORAL_GW = ["gw_delta_1d", "gw_delta_3d", "gw_delta_7d", "gw_rise_rate_7d"]
TEMPORAL_CRACK = ["crack_growth_1d", "crack_growth_3d", "crack_growth_7d",
                  "crack_accel_3d", "cum_growth_30d"]
TEMPORAL_BLAST = ["ppv_max_3d", "ppv_max_7d", "blast_count_3d", "blast_count_7d",
                  "cum_ppv_7d", "days_since_last_blast"]

GROUPS = {"STATIC": STATIC, "CURRENT_STATE": CURRENT_STATE,
          "TEMPORAL_RAIN": TEMPORAL_RAIN, "TEMPORAL_GW": TEMPORAL_GW,
          "TEMPORAL_CRACK": TEMPORAL_CRACK, "TEMPORAL_BLAST": TEMPORAL_BLAST}
V2_TEMPORAL = TEMPORAL_RAIN + TEMPORAL_GW + TEMPORAL_CRACK + TEMPORAL_BLAST
V1 = CURRENT_STATE + STATIC
V2 = V1 + V2_TEMPORAL


def _consecutive_wet(wet):
    out = np.zeros(len(wet), dtype=float)
    run = 0
    for i, w in enumerate(wet):
        run = run + 1 if w else 0
        out[i] = run
    return out


def _days_since(mask):
    out = np.zeros(len(mask), dtype=float)
    last = -1
    for i, m in enumerate(mask):
        if m:
            last = i
        out[i] = i - last if last >= 0 else i + 1.0
    return out


def build_v2(df):
    """Add V2_TEMPORAL columns to an internal-state frame.

    Input must contain the internal fields (rainfall_mm, rainfall_3d_mm,
    wet_day, groundwater_proxy, crack_density, blast_vibration_ppv_mms, ...)
    with rows ordered by day within each (seed, zone_id) group.
    Returns a new frame; V1 columns are passed through untouched.
    """
    g = df.copy()
    g["rainfall_24h_mm"] = g["rainfall_mm"]
    parts = []
    for _, grp in g.groupby(["seed", "zone_id"], sort=False):
        p = grp.sort_values("timestamp").copy() if "timestamp" in grp else grp.copy()
        rain = p["rainfall_mm"].astype(float)
        p["rainfall_3d_mm"] = rain.rolling(3, min_periods=1).sum()
        p["rainfall_14d_mm"] = rain.rolling(14, min_periods=1).sum()
        p["max_rainfall_7d_mm"] = rain.rolling(7, min_periods=1).max()
        p["consecutive_wet_days"] = _consecutive_wet(p["wet_day"].astype(bool).values)
        p["days_since_heavy_rain"] = _days_since((rain >= HEAVY_RAIN_MM).values)

        gw = p["groundwater_proxy"].astype(float)
        p["gw_delta_1d"] = gw.diff(1).fillna(0.0)
        p["gw_delta_3d"] = gw.diff(3).fillna(0.0)
        p["gw_delta_7d"] = gw.diff(7).fillna(0.0)
        p["gw_rise_rate_7d"] = p["gw_delta_7d"] / 7.0

        cd = p["crack_density"].astype(float)
        g1 = cd.diff(1).fillna(0.0)
        p["crack_growth_1d"] = g1
        p["crack_growth_3d"] = cd.diff(3).fillna(0.0)
        p["crack_growth_7d"] = cd.diff(7).fillna(0.0)
        p["crack_accel_3d"] = (g1 - g1.shift(3)).fillna(0.0)
        p["cum_growth_30d"] = g1.clip(lower=0).rolling(30, min_periods=1).sum()

        ppv = p["blast_vibration_ppv_mms"].astype(float)
        hit = (ppv > 0).astype(float)
        p["ppv_max_3d"] = ppv.rolling(3, min_periods=1).max()
        p["ppv_max_7d"] = ppv.rolling(7, min_periods=1).max()
        p["blast_count_3d"] = hit.rolling(3, min_periods=1).sum()
        p["blast_count_7d"] = hit.rolling(7, min_periods=1).sum()
        p["cum_ppv_7d"] = ppv.rolling(7, min_periods=1).sum()
        p["days_since_last_blast"] = _days_since(hit.values > 0)

        parts.append(p)
    out = pd.concat(parts, ignore_index=True)
    for c in V2_TEMPORAL:
        out[c] = out[c].astype(float)
    return out


def selftest_causality(df, n_checks=25, seed=0):
    """Phase 3 gate: features at time t must be identical when the future is deleted.

    For random (seed, zone) groups and random cut points t, rebuild V2 on the
    truncated group (rows <= t) and compare every V2_TEMPORAL value at t.
    Returns (ok: bool, failures: list[str]).
    """
    rng = np.random.default_rng(seed)
    built = build_v2(df)
    failures = []
    keys = list(pd.MultiIndex.from_frame(df[["seed", "zone_id"]].drop_duplicates()))
    for k in rng.choice(len(keys), size=min(n_checks, len(keys)), replace=False):
        s, z = keys[k]
        grp = df[(df.seed == s) & (df.zone_id == z)]
        n = len(grp)
        if n < 10:
            continue
        t = int(rng.integers(5, n))
        trunc = build_v2(grp.iloc[:t + 1])
        full_row = built[(built.seed == s) & (built.zone_id == z)].iloc[t]
        trunc_row = trunc.iloc[-1]
        for c in V2_TEMPORAL:
            a, b = float(full_row[c]), float(trunc_row[c])
            if not np.isclose(a, b, atol=1e-9):
                failures.append(f"seed={s} zone={z} t={t} {c}: full={a} truncated={b}")
                if len(failures) > 10:
                    return False, failures
    return len(failures) == 0, failures


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
    from generator_v1 import build_timeline, build_internal_state
    tl = build_timeline("2024-01-01", 365)
    df = build_internal_state(tl, 42)
    df["seed"] = 42
    ok, fails = selftest_causality(df, n_checks=15)
    print(f"causality selftest: {'PASS' if ok else 'FAIL'}")
    for f in fails:
        print(" ", f)
    v2 = build_v2(df)
    print(f"V2 columns added: {len(V2_TEMPORAL)}")
    print(v2[V2_TEMPORAL].describe().T[["mean", "std", "min", "max"]].round(3).to_string())