> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Feature Schema (Interface Contract)

**Status:** Research Freeze · Owner: Member 2 (Data / Generator) · Consumers: Member 3+ (ML / UI)

This is the **single source of truth for feature names** used between the generator, the Random Forest, the backend, and the frontend. It splits every field into two groups at the **interface boundary**:

- **Internal generator fields** — rich physics state inside the generator. They can evolve freely during development.
- **ML-facing fields** — the stable external schema. **Names and semantics are frozen** for Member 3. Changes require an explicit schema-change note (see §4).

Trace to: `docs/03_DATA_PLAN.md`, `docs/04_MODEL_PLAN.md`, `docs/GENERATOR_V1_SPEC.md`, `docs/05_API_SPEC.md`.

---

## 1. Interface boundary

```text
GENERATOR v1
  ┌───────────────────────────────────────────────┐
  │  internal fields (latent, rich, evolving)     │
  │  e.g. charge_per_delay_kg, crack_depth_m,     │
  │       water_filled, pore_pressure_kpa, ...    │
  └───────────────────┬───────────────────────────┘
                      │  derive / aggregate / map     ← only stable names cross
                      ▼
  ┌───────────────────────────────────────────────┐
  │  ML-facing schema  (FROZEN — 05_FEATURE_SCHEMA)│
  │  the 12 fields below                           │
  └───────────────────────────────────────────────┘
                      │
                      ▼
          Random Forest · API · Frontend
```

The generator is free to compute as much physics as it needs internally; only the frozen ML-facing names are exported to the model and API (`docs/05_API_SPEC.md`).

---

## 2. ML-facing schema (FROZEN)

| # | Field | Type | Range / Enum | Derivation | Kind |
|---|---|---|---|---|---|
| 1 | `rainfall_24h_mm` | float | ≥ 0 | IMD-grounded rain model (24h accumulation) | observed/sourced |
| 2 | `rainfall_7d_mm` | float | ≥ 0 | IMD-grounded rain model (7d accumulation) | observed/sourced |
| 3 | `slope_angle_deg` | float | 0–75+ | TERRAIN: DEM regional + mine bench layer (tagged by source_type) | observed/sourced |
| 4 | `slope_height_m` | float | ≥ 0 | TERRAIN bench layer (6–25 m benches; DEM macro) | observed/sourced |
| 5 | `rock_type` | categorical | Neyveli material classes (`lateritic_soil`, `sandstone`/`clayey_sandstone`, `clay`, `variegated_sandy_clay`, `carbonaceous_clay`, `aquifer_sand`, `lignite`, `overburden_mixed`) | GEOLOGY lithological sampling | observed/sourced |
| 6 | `crack_density` | float | 0–1 (per unit length/area) | CRACKS state (cumulative crack segments per zone) | derived-physical |
| 7 | `crack_severity` | categorical | `normal` `minor` `moderate` `severe` `critical` | CRACKS severity decision surface (NOT width alone) | derived-physical |
| 8 | `blast_frequency_per_week` | float | ≥ 0 | BLAST: production-derived weekly Poisson latent (14–28/wk prior) | synthetic latent |
| 9 | `blast_vibration_ppv_mms` | float | ≥ 0 | BLAST: NIRM attenuation **PPV = 858.90·(D/√W)^(−1.58)** at nearest exposed structure | derived-physical |
| 10 | `days_since_inspection` | integer | ≥ 0 | Scenario design | synthetic/scenario |
| 11 | `prior_incident` | 0/1 | {0, 1} | Scenario design | synthetic/scenario |
| 12 | `groundwater_proxy` | float | 0–1 | Derived from rainfall + time-since-last-rain (+ crack water-fill state) | derived-physical |

Notes:

- `rock_type` retains its **schema name** even though internally the generator samples a richer `material_type` + parameters (cohesion, friction, density, permeability). The GEOLOGY parameter regime is `total_undrained` (see `docs/03_DATA_PLAN.md` §A).
- `crack_severity` is exported as an **ordinal enum**; the CRACKS decision surface also computes `crack_growth_rate_mm_day` internally (see §3).
- Missing evidence is handled OUTSIDE the schema via the `missing_features` array in the API (`docs/05_API_SPEC.md`), not by changing field types.

---

## 3. Internal generator fields (EVOLVING — not part of the contract)

Rich physics state that does NOT cross the boundary (unless a documented schema change promotes one to ML-facing).

| Field | Description | Track |
|---|---|---|
| `charge_per_delay_kg` | Max charge per delay draw (~100–600 kg, mode 300) | BLAST |
| `blast_distance_m` | Distance from synthetic blast point to zone/nearest structure | BLAST |
| `dominant_frequency_hz` | Left-skewed 5–27 Hz draw (P(<8 Hz) ≈ 0.45) | BLAST |
| `ppv_raw_mms` | Pre-scatter attenuation value | BLAST |
| `water_filled` | Crack water-fill state (rainfall) → hydrostatic wall pressure | CRACKS/RAIN |
| `crack_depth_m` | Sampled depth, bench-bounded (**≤ ⅓–½ slope height**) | CRACKS |
| `crack_width_mm`, `crack_length_m`, `crack_segment_spacing_m` | Crack geometry draws | CRACKS |
| `crack_growth_rate_mm_day` | Temporal growth rate; >20 mm/day → failure in 6–12 days | CRACKS |
| `pore_pressure_kpa` | From rainfall/groundwater + aquifer state | RAIN/GEOLOGY |
| `groundwater_thrust_kpa` | Confined aquifer upward thrust (490–785 kPa) | GEOLOGY |
| `material_type` + `cohesion_kpa` + `friction_phi_deg` + `density_kg_m3` + `perm_m_s` | Sampled GEOLOGY parameters behind `rock_type` | GEOLOGY |
| `slope_height_layer` | Flag: `dem` / `bench` provenance of slope fields | TERRAIN |
| `rolling_7d_grounded` (storm templates, year-condition), zone geometry, seeds | Sampler machinery state | RAIN/GENERATOR |

These fields are what the generator **validates against** (§4 of this doc; `docs/GENERATOR_V1_SPEC.md` §10). They may be promoted to ML-facing later only via a schema-change note.

---

## 4. Schema-change rules

- **ML-facing fields are frozen.** Renaming, retyping, or re-enumerating any of the 12 fields requires:
  1. Update THIS doc + `docs/05_API_SPEC.md` + `docs/03_DATA_PLAN.md` in the same commit.
  2. State the change in the commit message.
  3. Bump the schema version (this doc's header date).
- **Internal fields are free to converge** during generator development.
- Feature names that exist in `docs/05_API_SPEC.md` JSON must match this document exactly (single source of truth: this file).