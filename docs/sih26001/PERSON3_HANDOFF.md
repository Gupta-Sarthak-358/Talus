# Person-3 Handoff — NGEN Labels + Remaining Features — Archived 2025-11-14 (Gangtok Pilot → Inventory)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**For:** the agent/teammate auditing the Person-3 lane · **Date:** 2026-09-04 (hackathon Sept 5) → **Archived 2025-11-14** (Phase-1 frozen, superseded by automated inventory pipeline)
**Base branch:** `feature/sih26001/ngen-pilot` (all work branches off this; PR into `feature/sih26001/demo-scaffold` → `SIH26001`)
**Contracts (law):** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md` · **Schema:** `05_FEATURE_SCHEMA_SIH26001.md` (22-col, 17 numeric + lulc, column order FROZEN `check_scaffold.py:24`) · **Model card:** `ML_MODEL_CARD_V2.md` (2025-11-14 frozen)
**Status map now:** `NGEN_PROVENANCE_S1.md` §2 + `manifest.training.json:144` + `ml/sih26001/reports/metrics.md:9` — STUB counts below are historic; final map is 17 numeric + lulc REAL except lithology/lineament omitted uniform.

## 0. Current REAL/STUB map — 2025-11-15 truth (audit from provenance + manifest)

Pilot start (2026-09-04):
REAL: S1–S4 rainfall 24h/7d/30d + `time_window`s (IMD 2024, 2024-06-16, same cell 27.25/88.50); S1 `distance_to_road`/`distance_to_river` (Overpass 2026-09-04).
PROXY: S1 slope/elev/aspect/curv (Terrarium mirror, NOT USGS).
STUB (your scope): `soil_moisture`, `ndvi`, `lulc`, `lithology`, S2–S4 road/river, `lineament_density`, `drain_density`, `twi`, `spi`, `previous_landslide`, `event`, `evidence_quality`.

**Frozen now:** All 17 numeric + lulc are **REAL or intentionally omitted uniform** — `sih26001_model.py` X input:
` slope_angle elevation aspect curvature twi spi_log rainfall_24h/7d/30d soil_moisture ndvi distance_to_road/river drain_density seismic_dist/n50/years_since` + `lulc` (one-hot) = 17 numeric in encoder; `lithology`/`lineament` uniform `lingtse_granite_gneiss`/0.8 (`bhukosh_vector_attempt.json:1` WFS/WMS 15s timeout) **omitted from X** (`manifest.training.json:263`), `previous_landslide` omitted leakage (positives ARE slides), `wound` 4/2936 rare kept. Soil is CCI `gangtok_soil_cci.csv:1` 0.271 + SWI `swi.py:14` overlay (not in X). Frozen bands 89/78/66/52 retained via `live_scores` fallback.

## 1. Workflow (every item — historic, now automated)

1. `git checkout feature/sih26001/ngen-pilot && git pull && git checkout -b feature/sih26001/person3-<item>` (historic; current repro is `scripts/build_training_matrix.py:1` + `scripts/train_sih26001.py:1`).
2. Fetch source → commit SMALL extract/sample (≤20 rows) + extraction script + sha256 to `manifest.sample.json` / `manifest.training.json`.
3. Update `feature_matrix.sample.csv` (column order FROZEN — `scripts/check_scaffold.py:24`).
4. Update manifest: replace `null`/`[]`/`not_available` with file/date/method/checksum. Never write `FILL`.
5. Flip rows in `NGEN_PROVENANCE_S1.md` §2 STUB→REAL/PROXY + §3 bullets; keep counts line true.
6. Gates: `check_scaffold.py` + `validate_ngen_sample.py` + `unittest` ALL green — paste in PR.
7. Push lane branch → PR into `feature/sih26001/demo-scaffold`. Never commit `docs/PILOT_BRIEFING.md`, datasets, weights (`ml/models/*.joblib` git-ignored `/.gitignore:78`), `.env`.

**2025-11-14 lanes are now automated extracts, not manual Overpass waits:** `extract_usgs.py` (USGS SRTM `n27_e088_1arc_v3.tif` D8), `extract_gangtok_rainfall.py` / rain upgrade (IMD 0.25° per-row year tagging), `extract_soil_cci.py` (CCI 0.271) + `swi.py:14` L1=15 L2=60 L3=60, `extract_s234_ndvi/lulc.py` (pinned `S2B_45RXL_20241129`), `extract_s234_osm.py` (local Geofabrik 1014/226/504 `roads_osm_provenance.json:1`), `usgs_quakes.json:1` (26 USGS events 59y), `wound_map.py` (4/2936), `build_training_matrix.py`, `train_sih26001.py`, `sih26001_model.py:score_row` (Bayes 0.5→0.01 `confidence_real_1pct`).

## 2. Item A — Labels: `previous_landslide` / `event` / `evidence_quality` + `sampling.ratio` — DONE (automated)

Source: GSI Bhusanket + 30,842-shapefile `GSI_Landslide_Inventory.shp.zip` + report `sikkim_report_gangtok.csv:1` → 2286 deduped 50 m → 1468 in study area 88.06–88.96/27.08–27.999.
`event: 1` season-window proxy tagged `approximate`; negatives >300 m seeded 1:1 (`negative_buffer_m:300`, `ratio:1.0` `manifest.training.json:21`). `previous_landslide` nearest-other ≤300 m — **omitted from X leakage** (logged `manifest.training.json:263`). Validation: GroupKFold-8 + `673/73 dated` temporal (`manifest.training.json:144` → `metrics.md:32` RF 0.8568).
Artifacts: `data/sih26001/processed/feature_matrix.training.csv` 2936×22 (git-ignored) + `feature_matrix.training.sample.csv` 20 rows + `training_sidecar.csv` per-row `rain_source/soil_source` + reports `ml/sih26001/reports/metrics.md:9` `calibration.md:8`.

## 3. Item B — `lithology` — DONE as documented uniform (Bhukosh attempted, not hidden)

Source: GSI Bhukosh `https://bhukosh.gsi.gov.in/Bhukosh/Public`.
Attempt: vector WFS + raster WMS both timeout 15s `bhukosh_vector_attempt.json:1` 2025-11-14. Logged as **PROXY-published-map uniform** `lingtse_granite_gneiss` (`manifest.training.json:34`) and **omitted from X**. Re-run `--wfs` when reachable; do not block scoring. Codebook `05_FEATURE_SCHEMA_SIH26001.md:30` frozen.

## 4. Item C — `lineament_density` / `drain_density` / `twi` / `spi` — DONE (USGS D8, no 64-px window)

Honest path taken: ≥5 km DEM context via `n27_e088_1arc_v3.tif` + priority-flood + D8 descending accumulation per 0.1-deg block → `twi=ln(a/tanB)` `spi=a*tanB` (tanB-floor 1e-4) + `drain_density` channel length/π·0.09 km² within 300 m, `twi`/`spi_log`/`drain_density` in X; `lineament_density` 0.8 uniform omitted (same PROXY note). No 64-px edge-corrupted compute.

## 5. Item D — `ndvi` / `lulc` — DONE

Source: Sentinel-2 via Element84 STAC → pinned `S2B_45RXL_20241129` SCL-gated `ndvi=(NIR-R)/(NIR+R)` + ESA WorldCover `N27E087` 3×3 mode frozen `s234_lulc.json:1` → `ndvi`/`lulc` in X (WorldCover → FOREST etc mapping codebook). 278 imputed median `manifest.training.json:46`, logged.

## 6. Item E — `soil_moisture` — DONE (CCI, plus SWI overlay)

CCI COMBINED TCDR v202505/v09.2 daily `gangtok_soil_cci.csv:1` 0.271 window-mean June 10–16 per row-year (7/7 valid) `manifest.training.json:31`; **SWI 3-tank** `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 → `tanh(SWI/100)` via `GET /api/soil/swi:1203` `swi_for_zone(rain7,rain30,forecast3)` warning threshold 0.40 `main.py:1423` (overlay, NOT in X, scoring frozen `p*100`).

## 7. Item F — S2–S4 `distance_to_road`/`distance_to_river` — DONE (local OSM, all 12 slopes)

Local Geofabrik Sikkim extract (not Overpass ×2k) → per-point haversine → 1014 Gangtok / 226 Lachung / 504 Darjeeling `roads_osm_provenance.json:1` (`extract_s234_osm.py`), geometry demo topology R1–R4 deterministic for R2 avoidance + R4 isolation (`data.py:118` `GRAPH`, `main.py:496` `_road_graphs_for` closes R2); counts proven, OSM demo topology tagged `osm-qa-unverified`. Per-slope reads only — never copy S1.

## 8. Definition of done (per PR — all passed 2025-11-14)

- [x] Validators + unittests green (9 suites 60 funcs, 35/35 live — paste in PR) · `check_scaffold.py` + `validate_ngen_sample.py`
- [x] No `FILL`, no invented dates; every value traces to committed file + manifest `sha256` + provenance row; wound/runout review-queue not training labels
- [x] `NGEN_VALIDATOR.md` counts + `validate_ngen_sample.py` banner match 17 numeric + lulc REAL (2 uniform omitted logged)
- [x] PR lists: files added, values changed, sources with dates, what stayed uniform/omitted and why (`manifest.training.json:263`)
- [x] File set additive; `slopes.json` 89/78/66/52, `roads.json` R1–R4, contract — UNTOUCHED; models `ml/models/*.joblib` git-ignored; reports `ml/sih26001/reports/metrics.md:9` `calibration.md:8` committed; evidence `warning_thresholds.json:1` `usgs_quakes.json:1` `wound_map.json:1` committed.

Judge line this lane now owns: *"Every label traces to a GSI Bhusanket ID or is tagged approximate — our docs and per-row sidecar show which. Lithology is the one uniform we disclose and omit."*