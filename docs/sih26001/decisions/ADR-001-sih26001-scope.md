# ADR-001: SIH26001 Scope — Migrate TALUS, Don't Fork

**Status:** Accepted — built 2026-09-04 · **Date:** 2026-09-03 · **Branch:** `SIH26001 @ 68c0c28`

## Context

TALUS v1 is frozen and working: two-engine pattern
(ML + physics scenario), isotonic calibration, SHAP, role decisions,
risk-weighted Dijkstra, missing-evidence discipline. SIH26001 (NER landslide,
MDoNER) asks for the same decision-support pattern over a different domain.
Full research: `docs/SIH26001_RESEARCH.md` (fact-checked, 5 rounds).

## Decision (proposed)

1. **Migrate the architecture, rewrite the data + physics.** NGEN replaces the
 synthetic generator; rainfall-infiltration replaces bench FoS; 17 NER
 features replace 12 mine features; 4 NER roles replace 4 mine roles.
2. **Track on branch `SIH26001`** with its own doc suite (`docs/sih26001/`),
 leaving v1 docs frozen. Merge strategy to `main` decided later (post-pilot).
3. **Train on real historical events** (GSI Bhusanket 37,903+ NER, COOLR/GLC,
 ISRO Atlas, published dated inventories, 40+ yr IMD rainfall) — the
 strongest structural upgrade over v1's synthetic-only evidence.
4. **Pilot-first:** one best-dated district cluster (Sikkim/Nagaland
 candidate) fully working before any 8-state talk.

## Alternatives considered

- **Clean-repo fork:** rejected for now — loses v1's reusable modules
 (calibration, SHAP, routing, decision patterns) and splits team history.
 Revisit if v2's NGEN/geo stack diverges irreconcilably.
- **Synthetic-first again:** rejected — real NER data exists and is verified
 accessible; synthetic would weaken the pitch.
- **8-state MVP:** rejected — thin coverage fails both demo and honesty bars.

## Consequences

- v1 stays demoable from `main`; v2 builds without breaking it.
- New geo/ML dependencies land on this branch first (rasterio/GDAL,
 geopandas, xgboost, i18n, SMS adapter).
- Freezes required before build: spatial unit, pilot extent, CRS/grid, map
 library, sampling/buffer rules, band edges (post-calibration).

## To-freeze list (frozen 2026-09-04)

- [x] Spatial unit — slope-point `S1-S4` `SCAFFOLD_CONTRACT_SEPT5.md:14` + training `T0000` `manifest.training.json:5` study area `88.06-88.96/27.08-27.999` (inside `n27_e088`)
- [x] Pilot extent — Gangtok `27.3389/88.6065` `27.315-27.345N/88.595-88.612E` `NGEN_PROVENANCE_S1.md:10`
- [x] CRS + grid + resampling — `EPSG:4326` demo, `111km*cos(lat)*res` anisotropic `extract_usgs.py:1`, `bilinear` elev
- [x] Map library — Leaflet `frontend/package.json:1` `leaflet 1.9.4` + `react-leaflet`
- [x] Positive/negative sampling + buffer + date-window — `>300m` `seed 42` `50:50` `season-window` `approximate` + year rescue `16` clusters `build_training_matrix.py:294`, `35/73 dated` temporal `metrics.md:32`
- [x] SMS provider adapter + language matrix — `en/hi/ne` fixture `alerts.json:1` `adapter` `02_ARCHITECTURE:155`
- [x] v2 API spec — `POST /reports` + `PATCH` + `queue?status` `main.py:389`, `GET /zones` etc. v1 shapes intact
