# Feature Schema Summary (docs/05_FEATURE_SCHEMA.md)

Status: **FROZEN**. This is the single source of truth for feature names shared
by the generator, the Random Forest, the backend, and the frontend.
Your API must accept and return these **exact names** — never rename, retype,
or re-enumerate them.

## The 12 ML-facing fields (frozen)

| # | Field | Type | Range/Enum | What it is |
|---|---|---|---|---|
| 1 | `rainfall_24h_mm` | float | ≥ 0 | Rain in last 24h (mm) |
| 2 | `rainfall_7d_mm` | float | ≥ 0 | Rain in last 7 days (mm) |
| 3 | `slope_angle_deg` | float | 0–75+ | Steepness of mine wall |
| 4 | `slope_height_m` | float | ≥ 0 | Height of the slope |
| 5 | `rock_type` | category | see enums below | Material class (e.g. sandstone, clay) |
| 6 | `crack_density` | float | 0–1 | Crack segments per zone |
| 7 | `crack_severity` | category | `normal` `minor` `moderate` `severe` `critical` | Severity (not width alone) |
| 8 | `blast_frequency_per_week` | float | ≥ 0 | How often blasting happens |
| 9 | `blast_vibration_ppv_mms` | float | ≥ 0 | Vibration from blasting (PPV) |
| 10 | `days_since_inspection` | int | ≥ 0 | Days since zone last inspected |
| 11 | `prior_incident` | 0/1 | {0, 1} | Whether an incident happened before |
| 12 | `groundwater_proxy` | float | 0–1 | Water in the ground (derived) |

## `rock_type` enum (Neyveli material classes)

```
lateritic_soil
sandstone
clayey_sandstone
clay
variegated_sandy_clay
carbonaceous_clay
aquifer_sand
lignite
overburden_mixed
```

## Rules that matter for you

1. **Missing evidence** is handled via the `missing_features` array in the API
   — never by changing field types or deleting fields.
2. The generator has many **internal** fields (e.g. `charge_per_delay_kg`,
   `crack_depth_m`, `pore_pressure_kpa`) that do **NOT** cross the boundary.
   Only the 12 above reach the API.
3. Any schema change requires updating this doc + API spec + data plan in the
   same commit, with a version bump. Treat this as "never".
4. Field names in `docs/05_API_SPEC.md` JSON must match this doc **exactly**.

## Practical tip

When you build Pydantic models in FastAPI, define one `ZoneFeatures` model with
these exact 12 names. Then `/risk/predict`, `/features`, and `/what-if` all
reuse it — no divergence possible.