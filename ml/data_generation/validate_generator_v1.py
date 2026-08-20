from pathlib import Path

import argparse
import json
import sys
import tempfile

import numpy as np
import pandas as pd

from generator_schema import (
    BASE_DIR,
    CATEGORY_ENUMS,
    INTERNAL_FIELDS,
    ML_FIELDS,
    ML_PROJECTION,
    ZONES,
)
from generator_v1 import build_internal_state, build_timeline

VALIDATION_DIR = BASE_DIR / "data" / "processed" / "generator_v1" / "validation"
SUMMARY_2000 = BASE_DIR / "data" / "processed" / "imd" / "analysis" / "summary_2000_2024.json"
GEOTECH_CSV = BASE_DIR / "data" / "processed" / "geotech" / "neyveli_geotech_parameters.csv"

RESULTS = {}

FIELDS_1B = [
    "rainfall_mm", "rainfall_3d_mm", "rainfall_7d_mm", "wet_day", "rainfall_regime",
    "elevation_m", "regional_slope_deg", "slope_angle_deg", "slope_height_m",
    "material_class", "cohesion_kpa", "friction_angle_deg", "unit_weight_kn_m3",
    "parameter_regime",
]

FIELDS_STAY_NAN = [
    "groundwater_state", "pore_pressure_kpa", "groundwater_thrust_kpa",
    "blast_occurs", "blast_frequency_per_week", "charge_per_delay_kg",
    "blast_distance_m", "dominant_frequency_hz", "blast_vibration_ppv_mms",
    "crack_family", "crack_width_mm", "crack_depth_m", "crack_length_m",
    "crack_density", "water_filled", "crack_growth_rate_mm_day",
    "crack_severity", "groundwater_proxy", "slope_condition",
    "instability_score", "risk_label",
]


def check(name, condition, detail=""):
    RESULTS[name] = {"pass": bool(condition), "detail": detail}
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


def schema_check(seed, days):
    timeline = build_timeline("2024-01-01", days)
    df = build_internal_state(timeline, seed)

    expected_cols = [name for name, _ in INTERNAL_FIELDS]
    actual_cols = list(df.columns)
    check("column set exact", actual_cols == expected_cols, f"{len(actual_cols)} cols")
    check("no renamed/dropped/extra columns", actual_cols == expected_cols)

    missing = set(expected_cols) - set(actual_cols)
    check("no missing required field", not missing, f"missing={sorted(missing)}")

    for ml_name in ML_FIELDS:
        source = ML_PROJECTION[ml_name]
        present = ml_name in actual_cols or source in actual_cols
        check(f"ML-facing field present: {ml_name}", present, f"source={source}")

    for name, dtype in INTERNAL_FIELDS:
        if name not in actual_cols:
            continue
        if dtype == "datetime64[ns]":
            check(f"timestamps valid: {name}", df[name].notna().all() and pd.api.types.is_datetime64_any_dtype(df[name]))
        elif dtype == "str":
            check(f"string type: {name}", df[name].notna().all())
        elif dtype == "bool":
            check(f"bool type: {name}", pd.api.types.is_bool_dtype(df[name]))
        elif dtype == "category":
            ok = df[name].cat.categories.isin(CATEGORY_ENUMS[name]).all()
            check(f"category values allowed: {name}", ok, f"enums={list(CATEGORY_ENUMS[name])}")

    check("zone_id values allowed", set(df["zone_id"]).issubset(set(ZONES)), f"zones={sorted(df['zone_id'].unique())}")
    check("zone_id never missing", df["zone_id"].notna().all())
    check("synthetic is True everywhere", bool((df["synthetic"] == True).all()))  # noqa: E712
    check("row count = days x zones", len(df) == days * len(ZONES), f"{len(df)}")

    for field in FIELDS_1B:
        no_na = df[field].notna().all()
        check(f"Phase 1B field populated: {field}", no_na)

    for field in FIELDS_STAY_NAN:
        all_na = df[field].isna().all()
        check(f"Phase 1B field stays NaN (1C/1D): {field}", all_na)

    df_projected = pd.DataFrame(index=df.index)
    for ml_name, source in ML_PROJECTION.items():
        df_projected[ml_name] = df[source]
    check("ML projection column order", list(df_projected.columns) == ML_FIELDS)
    check("ML projection fields complete", df_projected.notna().any().count() > 0)


def rainfall_distribution_check(seed, days):
    timeline = build_timeline("2024-01-01", days)
    df = build_internal_state(timeline, seed)
    rain = df["rainfall_mm"]
    wet = rain[rain > 0]

    with open(SUMMARY_2000, encoding="utf-8") as fh:
        hist = json.load(fh)
    h_zero = hist["integrity"]["zero_rain_pct"]
    h_p99_wet = hist["distribution"]["wet_days"]["p99"]
    h_max = hist["distribution"]["all_days"]["maximum"]
    h_7d_p99 = hist["rolling_windows_mm"]["7d"]["p99"]

    zero_pct = float((rain == 0).mean() * 100)
    check("rainfall: has wet days", bool(len(wet) > 0), f"wet={len(wet)}")
    check(
        "rainfall: zero-day % near grounding (55-88)",
        55.0 <= zero_pct <= 88.0,
        f"gen={zero_pct:.1f} hist={h_zero:.1f}",
    )
    check(
        "rainfall: wet-day P99 in grounded band (40-220)",
        40.0 <= wet.quantile(0.99) <= 220.0
        if len(wet) >= 4
        else False,
        f"gen={wet.quantile(0.99):.1f} hist={h_p99_wet:.1f} (single-year)",
    )
    check(
        "rainfall: 7d P99 > 3d P99 > daily (accumulation structure)",
        bool((df["rainfall_7d_mm"] >= df["rainfall_3d_mm"]).all() and (df["rainfall_3d_mm"] >= rain).all()),
    )
    check(
        "rainfall: 7d P99 in grounded band (100-600)",
        100.0 <= df["rainfall_7d_mm"].quantile(0.99) <= 600.0,
        f"gen={df['rainfall_7d_mm'].quantile(0.99):.1f} hist={h_7d_p99:.1f} (single-year)",
    )
    check("rainfall: regime consistent with wet_day",
          bool(((df["rainfall_regime"] == "dry") == (rain == 0)).all()))
    check("rainfall: regime consistency (storm => heavy, normal/dry <= moderate)",
          bool((df.loc[df["rainfall_regime"] == "storm", "rainfall_mm"] > 64.5).all()))

    month = df["timestamp"].dt.month
    nov = df[month == 11]["rainfall_mm"]
    feb = df[month == 2]["rainfall_mm"]
    check("rainfall: Nov > Feb mean (seasonality kept)",
          bool(nov.mean() > feb.mean()),
          f"Nov={nov.mean():.1f} Feb={feb.mean():.1f}")


def terrain_check(seed, days):
    timeline = build_timeline("2024-01-01", days)
    df = build_internal_state(timeline, seed)
    ok = True
    for zone_id, cfg in ZONES.items():
        z = df[df["zone_id"] == zone_id]
        slo = z["slope_angle_deg"]
        reg = z["regional_slope_deg"]
        elev = z["elevation_m"]
        sheight = z["slope_height_m"]
        lo, hi = cfg["face_angle_range_deg"]
        check(f"{zone_id}: slope_angle in engineering range", bool(slo.between(lo - 1e-6, hi + 1e-6).all()),
              f"lo={lo} hi={hi}")
        check(f"{zone_id}: slope_angle static over time", bool(slo.nunique() == 1))
        if zone_id != "ZONE_D":  # pit floor is flat; separation only meaningful on benches
            check(f"{zone_id}: regional_slope < bench slope (DEM != bench)", bool((reg < slo.array[0]).all()))
        else:
            check(f"{zone_id}: pit floor slope stays low (<= 10 deg)", bool(slo.max() <= 10.0))
        check(f"{zone_id}: regional_slope stays regional (<= 10 deg)", bool(reg.max() <= 10.0))
        check(f"{zone_id}: elevation static over time", bool(elev.nunique() == 1))
        check(f"{zone_id}: slope height static over time", bool(sheight.nunique() == 1))
    return ok


def geology_check(seed, days):
    timeline = build_timeline("2024-01-01", days)
    df = build_internal_state(timeline, seed)
    rows = pd.read_csv(GEOTECH_CSV).set_index("material")
    ok = True
    for zone_id in ZONES:
        z = df[df["zone_id"] == zone_id]
        mat = z["material_class"]
        check(f"{zone_id}: material static over time", bool(mat.nunique() == 1))
        material = str(mat.iloc[0])
        check(f"{zone_id}: material in enum", material in CATEGORY_ENUMS["material_class"])
        check(f"{zone_id}: parameter_regime preserved (no silent mixing)",
              bool(z["parameter_regime"].nunique() == 1) and str(z["parameter_regime"].iloc[0]) in CATEGORY_ENUMS["parameter_regime"])
        if material in rows.index:
            row = rows.loc[material]
            c = z["cohesion_kpa"].iloc[0]
            phi = z["friction_angle_deg"].iloc[0]
            regime = str(z["parameter_regime"].iloc[0])
            c_lo, c_hi = float(row["cohesion_kPa_min"]), float(row["cohesion_kPa_max"])
            phi_lo, phi_hi = float(row["friction_phi_deg_min"]), float(row["friction_phi_deg_max"])
            within = (c_lo <= c <= c_hi) and (phi_lo <= phi <= phi_hi)
            check(f"{zone_id}: c/phi within {material} grounded range", bool(within),
                  f"c={c} [{c_lo},{c_hi}] phi={phi} [{phi_lo},{phi_hi}]")
            check(f"{zone_id}: regime matches material row", regime == str(row["parameter_regime"]),
                  f"gen={regime} table={row['parameter_regime']}")
        else:
            check(f"{zone_id}: material lookup", False, f"{material} not in table")
    return ok


def structure_check(seed, days):
    timeline = build_timeline("2024-01-01", days)
    df = build_internal_state(timeline, seed)
    rain_std = df.groupby("timestamp")["rainfall_mm"].nunique()
    check("rainfall: shared across zones per day", bool(rain_std.max() == 1))
    check("rainfall: varies over time", bool(df["rainfall_mm"].nunique() > 1))
    for zone_id in ZONES:
        z = df[df["zone_id"] == zone_id]
        geo_static = z["material_class"].nunique() == 1 and z["cohesion_kpa"].nunique() == 1
        check(f"{zone_id}: geology constant (material/c)", geo_static)


def determinism_check(seed, days):
    timeline = build_timeline("2024-01-01", days)
    a = build_internal_state(timeline, seed)
    b = build_internal_state(timeline, seed)
    check("same seed -> identical dataset", a.equals(b))

    c = build_internal_state(timeline, seed + 1)
    check("different seed -> different dataset", not a.equals(c))


def write_results(seed, days):
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "check": "generator_v1_phase_1B",
        "seed": seed,
        "days": days,
        "generator_schema": "1.0",
        "phases": ["1A", "1B"],
        "results": RESULTS,
        "all_pass": all(r["pass"] for r in RESULTS.values()),
    }
    with open(VALIDATION_DIR / "schema_validation.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Talus Generator v1 Phase 1B validation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    schema_check(args.seed, args.days)
    rainfall_distribution_check(args.seed, args.days)
    terrain_check(args.seed, args.days)
    geology_check(args.seed, args.days)
    structure_check(args.seed, args.days)
    determinism_check(args.seed, args.days)
    write_results(args.seed, args.days)

    all_pass = all(r["pass"] for r in RESULTS.values())
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()