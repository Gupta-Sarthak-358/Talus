# TALUS v2 Feature Schema — SIH26001 (ML-facing contract)

**Status:** Draft (freezes before training; changes need ADR) · **Trace to:**
`03_DATA_PLAN_SIH26001.md` · **Source:** `docs/SIH26001_RESEARCH.md` §7.3

This is the **frozen ML-facing contract**. NGEN may carry richer internal
fields; only these cross the boundary into training/inference. Internal-vs-ML
boundary rule inherited from v1 (`docs/05_FEATURE_SCHEMA.md` pattern).

Spatial unit (`zone_id` grain: pixel / slope unit / admin zone) is **not yet
frozen** — freezes in ADR before NGEN completion. All features below are per
`zone_id` + time window.

---

## Features (17 + 2 keys)

| # | Feature | Type | Unit / values | Source |
|---|---|---|---|---|
| — | `zone_id` | key | string | NGEN grid |
| — | `time_window` | key | date / season-window | NGEN |
| 1 | `slope_angle` | float | degrees | SRTM-derived |
| 2 | `elevation` | float | m | SRTM |
| 3 | `aspect` | float | degrees 0–360 | SRTM-derived |
| 4 | `curvature` | float | dimensionless | SRTM-derived |
| 5 | `twi` | float | dimensionless (Topographic Wetness Index) | SRTM-derived |
| 6 | `spi` | float | dimensionless (Stream Power Index) | SRTM-derived |
| 7 | `rainfall_24h_mm` | float | mm (triggering) | IMD |
| 8 | `rainfall_7d_mm` | float | mm (antecedent) | IMD |
| 9 | `rainfall_30d_mm` | float | mm (antecedent) | IMD |
| 10 | `soil_moisture` | float | 0–1 volumetric (reanalysis proxy — tagged) | ERA5/SMAP |
| 11 | `ndvi` | float | −1 to 1 | Sentinel-2 |
| 12 | `lulc` | categorical | class code (codebook frozen with schema) | Sentinel-2 |
| 13 | `lithology` | categorical | class code (GSI Bhukosh codebook) | GSI |
| 14 | `distance_to_road` | float | m | OSM |
| 15 | `distance_to_river` | float | m | DEM-derived network |
| 16 | `lineament_density` | float | km/km² | GSI + DEM derived |
| 17 | `drain_density` | float | km/km² | DEM derived |
| 18 | `previous_landslide` | binary | 0/1 (+ `evidence_quality` tag) | Inventories |

## Target

| Field | Type | Definition |
|---|---|---|
| `event` | binary | 1 = landslide in unit + window (dated events; season-window positives tagged) |
| `severity_band` | derived | 5-band mapping of calibrated score (edges frozen post-calibration) |

## Missingness contract

- Any feature may be null. Nulls are **reported** (`missing_evidence`), never
  silently imputed in the response path. (Imputation inside the model, if any,
  is documented in the model card and surfaced as lowered confidence.)
- Proxy/incompleteness tags that must flow to `missing_evidence`:
  `soil_moisture:reanalysis-proxy`, `previous_landslide:inventory-incomplete`,
  `distance_to_road:osm-qa-unverified`, season-window positives:
  `event-date:approximate`.

## Boundary rule

NGEN internal fields (checksums, tile IDs, raw reflectances, join distances)
do **not** cross into ML. If a consumer needs a new field, the schema is
amended by ADR first, then code. Same rule as v1.
