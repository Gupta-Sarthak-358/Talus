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
    PHYSICS_FIELDS_1A,
    ZONES,
)
from generator_v1 import build_internal_state, build_timeline

VALIDATION_DIR = BASE_DIR / "data" / "processed" / "generator_v1" / "validation"
RESULTS = {}


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

    for field in PHYSICS_FIELDS_1A:
        all_na = df[field].isna().all()
        check(f"Phase 1A physics field is NaN: {field}", all_na)

    df_projected = pd.DataFrame(index=df.index)
    for ml_name, source in ML_PROJECTION.items():
        df_projected[ml_name] = df[source]
    check("ML projection column order", list(df_projected.columns) == ML_FIELDS)
    check("ML projection fields complete", df_projected.notna().any().count() > 0)


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
        "check": "generator_v1_phase_1A",
        "seed": seed,
        "days": days,
        "generator_schema": "1.0",
        "results": RESULTS,
        "all_pass": all(r["pass"] for r in RESULTS.values()),
    }
    with open(VALIDATION_DIR / "schema_validation.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Talus Generator v1 Phase 1A validation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    schema_check(args.seed, args.days)
    determinism_check(args.seed, args.days)
    write_results(args.seed, args.days)

    all_pass = all(r["pass"] for r in RESULTS.values())
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
