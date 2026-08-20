"""Export the ML-facing handoff dataset from the FROZEN generator v1.4.0.

This is a HANDOFF/EXPORT step only -- it does NOT modify any physics,
generator logic, schema, or Phase 1E behavior. It reuses the existing,
unchanged `project_ml()` projection (12 frozen ML features) and appends the
target fields so the next ML phase can consume the dataset directly.

Outputs (ml_handoff/):
  seed_42_ml_features_targets.csv                       seed 42 only
  synthetic_ml_dataset_seeds_42_46.csv                  combined, with `seed` col
  README.md                                            manifest

Deliberately DEFERRED to the ML phase (nothing here):
  - train/validation/test splits
  - one-hot encoding / categorical handling
  - any scaling or preprocessing
  - any feature engineering
rock_type and crack_severity are exported with their existing categorical
values; no transformation.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from generator_v1 import build_timeline, build_internal_state, project_ml
from generator_schema import BASE_DIR, GENERATOR_VERSION, SCHEMA_VERSION

SEEDS = [42, 43, 44, 45, 46]
OUT_DIR = BASE_DIR / "data" / "processed" / "generator_v1" / "ml_handoff"
TARGET_COLS = ["fos", "instability_score", "risk_label"]
AUX_COLS = ["zone_id", "seed"]

MANIFEST = """# Talus Synthetic Mine States -- ML-Facing Handoff

## Status
HANDOFF / EXPORT ONLY. Produced by {script} from the FROZEN generator v1.4.0.
No physics, generator logic, schema, or Phase 1E behavior was modified to
produce this dataset.

## Source
- Generator version: {gen_version}
- Schema version: {schema_version}
- Synthetic: True (all rows are generated -- NOT measured mine data)
- Phases: 1A-1E complete
- Reference mine: Neyveli Mine-II (11.50N, 79.50E); synthetic operational states

## Files
- `seed_42_ml_features_targets.csv` -- seed 42 only, {rows_single} rows
- `synthetic_ml_dataset_seeds_42_46.csv` -- seeds {seeds}, {rows_all} rows
  (all seeds concatenated; `seed` column identifies the source draw)

## Row counts
- per seed (single year, 4 zones x 365 days): {rows_single}
- combined (5 seeds): {rows_all}

## Feature columns (12, frozen ML-facing schema)
{feature_desc}

## Target columns
{target_desc}

## Auxiliary/id columns
{aux_desc}

## Data flags
- rock_type and crack_severity are exported with their EXISTING categorical
  values. No one-hot encoding, dummy coding, or other transformation applied.
- prior_incident is a boolean (all False in the routine baseline year).
- No train/validation/test splits have been created.

## Deliberately DEFERRED to the ML phase (known handoff)
- Train / validation / test splits (temporal; no random shuffle before
  defining the audit protocol).
- Categorical handling (one-hot, ordinal encodings, etc.).
- Scaling / normalization of any numeric column.
- Feature selection or engineering.
- Leakage review (targets here are generated FROM the same physics chain the
  features describe -- the ML contract must treat FoS/score/label as the
  target and reason about causal ordering, per spec 7.5).
"""

FEATURE_DESCS = {
    "rainfall_24h_mm": "daily rainfall (mm), mine-wide",
    "rainfall_7d_mm": "7-day rolling rainfall accumulation (mm)",
    "slope_angle_deg": "bench slope angle (deg, fixed per zone; mine-engineering layer)",
    "slope_height_m": "bench slope height (m, fixed per zone)",
    "rock_type": "material class (static per zone; existing categorical values)",
    "crack_density": "crack density (accumulated damage state)",
    "crack_severity": "crack severity band (normal..critical; existing categorical values)",
    "blast_frequency_per_week": "zone weekly blast rate (latent production-derived)",
    "blast_vibration_ppv_mms": "PPV (mm/s), NIRM attenuation law; 0 on non-blast days",
    "days_since_inspection": "days since last inspection (scheduler field)",
    "prior_incident": "prior incident flag (boolean; False in routine baseline)",
    "groundwater_proxy": "wetland wetting-memory transient (mm; lagged groundwater response)",
}

TARGET_DESCS = {
    "fos": "factor of safety (infinite-slope / floor-uplift), capped ~2.5; continuous",
    "instability_score": "0-100 monotone transform of FoS; preferred REGRESSION target",
    "risk_label": "5-band risk (very_low/low/moderate/high/critical); discrete target",
}

AUX_DESCS = {
    "zone_id": "synthetic zone (ZONE_A..ZONE_D) -- grouping/id, NOT a feature",
    "seed": "generator seed -- identifies the stochastic draw (combined file only)",
}


def build_seed_table(seed):
    timeline = build_timeline("2024-01-01", 365)
    df = build_internal_state(timeline, seed)
    ml = project_ml(df)
    out = ml.copy()
    out["zone_id"] = df["zone_id"].astype(str)
    for c in TARGET_COLS:
        out[c] = df[c]
    out["seed"] = seed
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = {}
    for seed in SEEDS:
        frames[seed] = build_seed_table(seed)

    seed42 = frames[42]
    seed42_path = OUT_DIR / "seed_42_ml_features_targets.csv"
    seed42_path.write_text(
        seed42.drop(columns=["seed"]).to_csv(index=False), encoding="utf-8"
    )

    combined = pd.concat(frames.values(), ignore_index=True)
    combined_path = OUT_DIR / "synthetic_ml_dataset_seeds_42_46.csv"
    combined_path.write_text(combined.to_csv(index=False), encoding="utf-8")

    rows_single = len(seed42.drop(columns=["seed"]))
    rows_all = len(combined)

    manifest = MANIFEST.format(
        script=Path(__file__).name,
        gen_version=GENERATOR_VERSION,
        schema_version=SCHEMA_VERSION,
        rows_single=rows_single,
        rows_all=rows_all,
        seeds="-".join(str(s) for s in SEEDS),
        feature_desc="\n".join(f"  - {k}: {v}" for k, v in FEATURE_DESCS.items()),
        target_desc="\n".join(f"  - {k}: {v}" for k, v in TARGET_DESCS.items()),
        aux_desc="\n".join(f"  - {k}: {v}" for k, v in AUX_DESCS.items()),
    )
    (OUT_DIR / "README.md").write_text(manifest, encoding="utf-8")

    print(f"seed 42            -> {seed42_path} ({rows_single} rows)")
    print(f"combined 42-46     -> {combined_path} ({rows_all} rows)")
    print(f"manifest           -> {OUT_DIR / 'README.md'}")
    print(f"\nseed 42 target stats (regression target check):")
    print(seed42["instability_score"].describe().round(1).to_string())
    print("\ncombined risk_label counts:")
    print(combined["risk_label"].value_counts().to_string())


if __name__ == "__main__":
    main()