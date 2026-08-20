from pathlib import Path

import argparse
import json

import numpy as np
import pandas as pd

from generator_schema import (
    BASE_DIR,
    GENERATOR_VERSION,
    GROUNDING_VERSION,
    INTERNAL_FIELDS,
    ML_FIELDS,
    ML_PROJECTION,
    PHASES_COMPLETED,
    RESEARCH_FREEZE,
    SCHEMA_VERSION,
    ZONES,
)

OUTPUT_DIR = BASE_DIR / "data" / "processed" / "generator_v1"
DEFAULT_SEED = 42
DEFAULT_START = "2024-01-01"
DEFAULT_DAYS = 365
INSPECTION_CADENCES = (7, 14, 21, 30)


def parse_args():
    parser = argparse.ArgumentParser(description="Talus Generator v1 Phase 1A skeleton")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--start", default=DEFAULT_START, help="YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--out", default=str(OUTPUT_DIR))
    return parser.parse_args()


def build_timeline(start, days):
    return pd.date_range(start=start, periods=days, freq="D")


def build_internal_state(timeline, seed):
    rows = []
    for zone_idx, (zone_id, zone_cfg) in enumerate(ZONES.items()):
        rng = np.random.default_rng(np.random.SeedSequence([seed, zone_idx]))
        cadence = int(rng.choice(INSPECTION_CADENCES))
        offset = int(rng.integers(0, cadence))
        for idx, ts in enumerate(timeline):
            rows.append(
                {
                    "timestamp": ts,
                    "zone_id": zone_id,
                    "bench_height_m": zone_cfg["bench_height_m"],
                    "bench_face_angle_deg": zone_cfg["bench_face_angle_deg"],
                    "distance_to_crest_m": zone_cfg["distance_to_crest_m"],
                    "days_since_inspection": int((idx + offset) % cadence),
                    "prior_incident": False,
                    "synthetic": True,
                }
            )
    df = pd.DataFrame(rows)
    df = df.reindex(columns=[name for name, _ in INTERNAL_FIELDS])
    for name, dtype in INTERNAL_FIELDS:
        if name in df.columns:
            continue
        if dtype == "category":
            df[name] = pd.Series(dtype="category")
        elif dtype == "bool":
            df[name] = pd.Series(dtype="boolean")
        else:
            df[name] = np.nan
    for name, dtype in INTERNAL_FIELDS:
        if name in df.columns and df[name].dtype != "object":
            if dtype == "bool":
                df[name] = df[name].astype("boolean", errors="ignore")
            else:
                df[name] = df[name].astype(dtype, errors="ignore")
    return df


def project_ml(df):
    out = pd.DataFrame(index=df.index)
    for ml_name, internal_name in ML_PROJECTION.items():
        out[ml_name] = df[internal_name]
    return out[ML_FIELDS]


def build_summary(timeline, seed, out_dir):
    return {
        "dataset": "talus_synthetic_mine_states",
        "generator_version": GENERATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "synthetic": True,
        "grounding_version": GROUNDING_VERSION,
        "phases_completed": PHASES_COMPLETED,
        "research_freeze": RESEARCH_FREEZE,
        "timeline_start": str(timeline[0].date()),
        "timeline_end": str(timeline[-1].date()),
        "days": int(len(timeline)),
        "zones": {z: ZONES[z]["role"] for z in ZONES},
        "rows_per_zone": int(len(timeline)),
        "total_rows": int(len(timeline) * len(ZONES)),
        "ml_facing_fields": ML_FIELDS,
        "internal_field_count": len(INTERNAL_FIELDS),
        "phase_1A_placeholder_policy": "physics fields are NaN until Phase 1B-1D; scenario fields are seed-scoped; see docs/GENERATOR_V1_SPEC.md 7.1",
        "output_files": {
            "states": str(out_dir / "synthetic_mine_states.csv"),
            "summary": str(out_dir / "generator_summary.json"),
        },
    }


def write_outputs(df, summary, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    validation_dir = out_dir / "validation"
    validation_dir.mkdir(exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "synthetic_mine_states.csv", index=False)
    with open(out_dir / "generator_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)


def main():
    args = parse_args()
    out_dir = Path(args.out)
    timeline = build_timeline(args.start, args.days)
    df = build_internal_state(timeline, args.seed)
    summary = build_summary(timeline, args.seed, out_dir)
    write_outputs(df, summary, out_dir)
    print(f"rows={len(df)} cols={len(df.columns)} zones={len(ZONES)}")
    print(f"summary={summary['output_files']['summary']}")


if __name__ == "__main__":
    main()
