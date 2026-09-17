# TALUS Feature Schema — SIH26001 (ML-facing contract)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Status:** Frozen — built 2025-11-14 · **Trace to:** `03_DATA_PLAN_SIH26001.md` · **Source:** `docs/SIH26001_RESEARCH.md` §7.3

This is the **frozen ML-facing contract**. NGEN may carry richer internal fields; only these cross the boundary into training/inference. Internal-vs-ML boundary rule inherited from v1 (`docs/05_FEATURE_SCHEMA.md` pattern).

Spatial unit (`zone_id` grain: pilot point S1–S4 + Lachung N1–N4 + Darjeeling D1–D4 = 12 demo slopes + 2936 training grid) frozen to **slope-point** `NGEN_PROVENANCE_S1.md:10` `27.315–27.345N/88.595–88.612E` + `manifest.training.json:5` study area `88.06–88.96/27.08–27.999` (inside `n27_e088`, 3 corridors `locations.json:1`). All features below are per `zone_id` + `time_window` `2024-06-16` / `JJAS` season-window proxy. Sample has 22 cols (`feature_matrix.sample.csv:1`).

---

## Features (17 numeric + lulc + 4 keys/target = 22 cols)

| # | Feature | Type | Unit / values | Source | In X? |
|---|---|---|---|---|---|
| — | `zone_id` | key | string S1–S4/N1–N4/D1–D4/T0000 | NGEN grid `locations.json:1` | key |
| — | `time_window` | key | date 2024-06-16 / season-window | NGEN | key |
| 1 | `slope_angle` | float | degrees | SRTM-derived `usgs_s234.json:1` | ✅ |
| 2 | `elevation` | float | m | SRTM n27_e088 | ✅ |
| 3 | `aspect` | float | degrees 0–360 | SRTM-derived | ✅ |
| 4 | `curvature` | float | dimensionless | SRTM-derived | ✅ |
| 5 | `twi` | float | dimensionless (Topographic Wetness Index) | SRTM-derived D8 | ✅ |
| 6 | `spi` → `spi_log` | float | dimensionless → log1p(SPI) | SRTM-derived → transformer | ✅ as spi_log |
| 7 | `rainfall_24h_mm` | float | mm (triggering) | IMD 0.25° historical truth (observed) | ✅ |
| 8 | `rainfall_7d_mm` | float | mm (antecedent) | IMD 0.25° | ✅ |
| 9 | `rainfall_30d_mm` | float | mm (antecedent) | IMD 0.25° | ✅ |
| 10 | `soil_moisture` | float | 0–1 volumetric (CCI satellite-observed, tagged) | CCI v09.2 `gangtok_soil_cci.csv:1` 0.271 | ✅ |
| 11 | `ndvi` | float | −1 to 1 | Sentinel-2 S2B_45RXL | ✅ |
| 12 | `lulc` | categorical | FOREST/BUILT/BARREN/WATER/WETLAND (WorldCover map 10→FOREST etc, codebook frozen with schema `s234_lulc.json:1`) | ESA WorldCover N27E087 | ✅ one-hot drop_first |
| 13 | `lithology` | categorical | GSI Bhukosh code (lingtse_granite_gneiss) | GSI PROXY-published-map uniform | ❌ omitted uniform `manifest.training.json:263` `bhukosh_vector_attempt.json:1` |
| 14 | `distance_to_road` | float | m | OSM 1014/226/504 `roads_osm_provenance.json:1` | ✅ |
| 15 | `distance_to_river` | float | m | DEM-derived network `catchment_s234.json:1` | ✅ |
| 16 | `lineament_density` | float | km/km² | GSI + DEM derived PROXY uniform | ❌ omitted uniform 0.8 |
| 17 | `drain_density` | float | km/km² | DEM derived | ✅ |
| 18 | `previous_landslide` | binary | 0/1 (+ `evidence_quality` tag) | Inventories `sikkim_join.json:6` | ❌ omitted leakage (`positives ARE` inventory slides) |
| 19–21 | `seismic_dist_km`, `seismic_n50_rate`, `seismic_years_since` | float | km / rate / years since M5.5 <50km (60y cap) | USGS 26 quakes `usgs_quakes.json:1` → `sih26001_model.py:_seismic_lookup` 59y window | ✅ |
| 22 | `wound` | binary | 0/1 (review-queue NDVI loss ≥0.3 ≤150m road, 4/2936) | `wound_map.json:1` → `wound_as_feature.json:1` | ✅ rare |
| 23 | `swi` (warning overlay, frozen scoring) | float | 0–1 tanh(SWI/100) JMA 3-tank | `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 | ❌ overlay only, not in X |
| 24 | `effective_rain` + `isolation`/`warning_state` | derived | mm effective = r7+0.3*r30, isolation/warning | `warning_thresholds.json:1` + `_isolation_for_location:1326` | ❌ operational overlay |

**NUMERIC 17** + lulc categ = as-shipped encoder input (17 numeric after spi→spi_log + seismic 3 + wound + road/river/drain + rainfall 3 + soil + ndvi + slope/elev/aspect/curv/twi/drain). Total 22 cols including keys `zone_id/time_window/event/evidence_quality`.

## Target

| Field | Type | Definition |
|---|---|---|
| `event` | binary | 1 = landslide in unit + window (dated events; undated season-window positives tagged `approximate`) |
| `severity_band` | derived | 5-band mapping of calibrated score via `model_service.band_for_score` (edges frozen post-calibration, scaffold 89/78/66/52) |
| `evidence_quality` | tag | `approximate` / `dated-only-negative` per row, flows to `missing_evidence` |

## Missingness contract

- Any feature may be null. Nulls are **reported** (`missing_evidence`), never silently imputed in the response path. (Imputation inside the model, if any, is documented in the model card and surfaced as lowered confidence + `confidence_real_1pct`.)
- Proxy/incompleteness tags that must flow to `missing_evidence` / `missing_features`:
  `soil_moisture:reanalysis-proxy-satellite-CCI-stronger` (still 0.25° cell), `previous_landslide:inventory-incomplete` (when exposed), `distance_to_road:osm-qa-unverified` (demo topology, counts proven 1014/226/504 `roads_osm_provenance.json:1`), season-window positives: `event-date:approximate`, lithology: `bhukosh-PROXY-published-map-uniform`, IMD live: `IMD_API_KEY required else Open-Meteo blend`.

## Boundary rule

NGEN internal fields (checksums, tile IDs, raw reflectances, join distances, wound candidate lat/lon before thresholding, quake catalog beyond 26 events, road OSM full traces) do **not** cross into ML. If a consumer needs a new field, the schema is amended by ADR first, then code. Same rule as v1. Scoring frozen: `score = round(raw_proba*100)`, `swi`/`isolation`/`warning_state` are operational overlays, not features in the frozen RF.