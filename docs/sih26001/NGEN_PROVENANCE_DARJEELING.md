# NGEN Provenance — Darjeeling Corridor (D1–D4) — 2025-11-14 Truth

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


Closes the Darjeeling gap: D rows in `feature_matrix.sample.csv` 12 rows (S1–S4 frozen 89/78/66/52 + D1–D4 + N1–N4) are measured extracts, not S1 clones. Same methods as Gangtok (`NGEN_PROVENANCE_S1.md`), new coordinates from `slopes.darjeeling.json`. 12 rows ×22 cols, 17 numeric + lulc, 0 STUBs, `validate_ngen_sample.py` OK, `check_scaffold.py` SCAFFOLD OK 17-feature. IMD 1901-2024 + TWI/SPI + `lingtse_granite_gneiss` (Gangtok S) vs Darjeeling `darjeeling_gneiss` — PROXY-published-map `bhukosh_vector_attempt.json` WFS timeout.

Script: `scripts/extract_darjeeling_ngen.py` (`--only local` / `--only network`).
Frozen output: `data/processed/terrain/darjeeling_ngen.json` (sha256 `8a494f03ee30014b9d24407c03abe6abaae55f9c99a020371a60fdc28f0ec81c`).

## Zone points (single source: slopes.darjeeling.json geometry)

| zone | lat | lon | site | frozen* |
|---|---|---|---|---|
| D1 | 27.047 | 88.263 | Ghoom (upper) | scaffold 89/78/66/52 is S-only; D uses same band logic live |
| D2 | 27.040 | 88.275 | Hill Cart Rd road-cut | — |
| D3 | 27.027 | 88.2695 | Lebong (mid) | — |
| D4 | 27.017 | 88.258 | Valley staging | — |

*Frozen 89/78/66/52 bands are Gangtok S1–S4 (`SCAFFOLD_CONTRACT_SEPT5.md:14`); Darjeeling shifts R1–R4 per corridor but R2-avoidance deterministic (`RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2`).

## Per-feature pedigree (17/17 REAL/PROXY, zero STUBs)

| # | feature | D value(s) | source | tag |
|---|---|---|---|---|
| 1 | slope_angle | 18.9 / 29.8 / 27.0 / 40.6° | USGS SRTMGL1 v3 tile `n27_e088` (inside 88–89E/27–28N), Horn-1981 anisotropic | REAL |
| 2 | elevation | 2019 / 1715 / 1970 / 2306 m bilinear | same tile | REAL |
| 3 | aspect | 238 / 43 / 145 / 126° downslope | same tile | REAL |
| 4 | curvature | 0.0026 / 0.0066 / -0.0013 / -0.0211 Laplacian | same tile | REAL |
| 5 | twi | 5.08 / 5.48 / 5.38 / 4.57 D8 priority-flood on Darjeeling window lat 27.00–27.07/lon 88.23–88.29 | same tile | REAL |
| 6 | spi | 18.9 / 78.7 / 56.0 / 70.9 → log1p at model | same window a·tanB | REAL |
| 7–9 | rainfall 24h/7d/30d | **20.4 / 397.0 / 1209.2** mm, IMD 0.25° nearest cell (27.00, 88.25), wettest trailing-7d of 2024 ends **2024-07-08** (per-corridor; S stays 2024-06-16) | LOCAL `ind2024_rfp25.nc` 1901–2024 + live `GET /api/forecast/live:1154` Open-Meteo 7d + `GET /api/forecast/imd-live:1124` IMD_API_KEY gated | REAL (hist) + live blend |
| 10 | soil_moisture | **0.297 all D** (S 0.271 via `extract_soil_cci.py` 7/7 valid) | CCI COMBINED TCDR v09.2 June 10–16 window-mean, 7/7 valid, cell (27.125, 88.375) `extract_soil_cci.py` 1901-2024 | REAL |
| 11 | ndvi | 0.688 / 0.848 / 0.880 / 0.821, `S2B_45RXK_20241129` (sibling granule of Gangtok `45RXL`, same date cloud 0.02%), all scl=4 | Element84 STAC + COG | REAL quasi-static |
| 12 | lulc | FOREST all D (WC-10, 3×3 agree 9/9) | SAME WorldCover tile N27E087 76.7% (covers Darjeeling) | REAL |
| 13 | lithology | `darjeeling_gneiss` all D uniform | DRAP p71/p118 names Darjeeling Gneiss as regional unit | PROXY-published-map uniform |
| 14 | distance_to_road | 71 / 29 / 354 / 6 m (retries for rate-limit) | Overpass 504 ways Darjeeling `roads_osm_provenance.json:1` | counts proven, demo topology |
| 15 | distance_to_river | 234 / 520 / 314 / 326 m | Overpass | measured |
| 16 | lineament_density | 0.8 all D uniform | Himalayan-50K literature; **Darjeeling figure NOT consulted** | PROXY-regional (Bhuvan WB-clip = upgrade) |
| 17 | drain_density | 0.0 all D (no ≥1 km² channel cells within 300 m) | same USGS accumulation grids | PROXY-window measured |
| + | `seismic_*` ×3 | per-zone from 26 USGS M5+ 1965–2024 `usgs_quakes.json:1` | `sih26001_model.py:_seismic_lookup` 59y window | REAL |
| L1 | previous_landslide | D2=1 (WB/DAR/78A08/2015/78 @242.7 m INIT 2007), D3=1 (WB/DAR/78A08/2015/59 @231.9 m INIT 2007), D1/D4=0 | LOCAL GSI shapefile 1862 WB rows 300 m rule | REAL-cited |
| L2 | event | 0 all (INITIATION year-only) | — | honest 0 |
| Q | evidence_quality | `approximate` (D2/D3), `dated-only-negative` (D1/D4) | same rule | tag |
| Q | time_window | 2024-07-08 (per-corridor) | IMD | REAL date |

## Honesty notes

- D4 slope 40.6°/elev 2306 m steep but inside gate (Tiger Hill 2590 m 3 km south). Measured, not tuned.
- Same-cell: rain (27.00,88.25) + soil (27.125,88.375) serve all D (0.25° limit).
- Granule lesson: Gangtok `45RXL` did **not** cover D3/D4 — picker now requires single-scene full-D coverage (`45RXK`, same date).
- Warning thresholds (overlay, scoring frozen): `warning_thresholds.json:1` darjeeling **D1 400 D2 410 D3 420 D4 390**, effective `r7+0.3*r30`, SWI `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12, 6-state NORMAL→EVACUATE, quake ×0.75.
- OSM Darjeeling **504** required 429/504 backoff (proven count); R1–R4 deterministic per corridor for R2-avoidance `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2`.
- Wound Darjeeling 0 candidates (Gangtok 2 total); runout screening capped 400/zone (`runout_exposure.json:1` total 253, Darjeeling D1 46 D2 0 D3 34 D4 0; Gangtok S2 max 85 buildings).
- Training n=2936 1468+1468 RF 0.9338 XGB 0.9418 Brier isotonic 0.0971 applies corridor-wide (spatial GroupKFold8 `train_sih26001.py:129`).