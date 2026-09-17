# NGEN Provenance — Lachung Corridor (N1–N4) — 2025-11-14 Truth

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


Closes the Lachung gap: N rows in `feature_matrix.sample.csv` 12 rows (S1–S4 frozen 89/78/66/52 + D1–D4 + N1–N4) are measured extracts, not S1 clones. Same methods as Gangtok (`NGEN_PROVENANCE_S1.md`), new coordinates from `slopes.lachung.json`. 12 rows ×22 cols, 17 numeric + lulc, evidence_quality `dated-only-negative`/`approximate` (S is approx, Lachung dated-only-negative), 0 STUBs, `validate_ngen_sample.py` OK, `check_scaffold.py` SCAFFOLD OK 17-feature. IMD 1901-2024 + TWI/SPI + `lingtse_granite_gneiss` (Gangtok S) vs Lachung `chungthang_subgroup_gneiss` — Bhukosh PROXY-published-map `bhukosh_vector_attempt.json` WFS timeout.

Script: `scripts/extract_lachung_ngen.py` (`--only local` / `--only network`; Overpass retries; single-scene full-N coverage required).
Frozen output: `data/processed/terrain/lachung_ngen.json` (sha256 `0764f5a2d9c69ee23299fcdb8e5781bf0a5625311b1d88d031f6809be28113a9`).

## Zone points (single source: slopes.lachung.json geometry)

| zone | lat | lon | site | frozen score* |
|---|---|---|---|---|
| N1 | 27.695 | 88.735 | Upper (Yumthang approach) | demo 89/78/66/52 scaffold applies to S only; N scores live/model or clone display via `slopes.lachung.json` |
| N2 | 27.688 | 88.747 | Road-cut (NH-310A) | — |
| N3 | 27.678 | 88.7415 | Mid (River Bend) | — |
| N4 | 27.665 | 88.730 | Valley staging | — |

*Frozen 89/78/66/52 bands are Gangtok S1–S4 scaffold (`SCAFFOLD_CONTRACT_SEPT5.md:14`); Lachung carries same band logic live. R2-avoidance demo uses shifted R1–R4 topology per corridor (`main.py:49` `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2`).

## Per-feature pedigree (17/17 REAL/PROXY, zero STUBs)

| # | feature | N value(s) | source | tag |
|---|---|---|---|---|
| 1 | slope_angle | 35.9 / 24.4 / 37.9 / 27.9° | USGS SRTMGL1 v3 tile `n27_e088` (local), Horn-1981 anisotropic | REAL |
| 2 | elevation | 3095 / 2686 / 2685 / 2542 m bilinear | same tile | REAL |
| 3 | aspect | 46 / 265 / 346 / 163° downslope | same tile | REAL |
| 4 | curvature | -0.0586 / -0.0067 / 0.0080 / 0.0040 Laplacian | same tile | REAL |
| 5 | twi | 4.33 / 5.20 / 4.66 / 5.05 D8 priority-flood on Lachung window lat 27.64–27.72/lon 88.68–88.80 | same tile | REAL |
| 6 | spi | 39.6 / 37.3 / 64.0 / 43.4 → log1p at model | same window a·tanB | REAL |
| 7–9 | rainfall 24h/7d/30d | **43.2 / 314.5 / 669.8** mm, IMD 0.25° nearest cell (27.75, 88.75), wettest trailing-7d of 2024 ends **2024-06-17** (per-corridor honest window; S stays 2024-06-16) | LOCAL `ind2024_rfp25.nc` 1901-2024 + live `GET /api/forecast/live:1154` Open-Meteo 7d + `GET /api/forecast/imd-live:1124` IMD_API_KEY gated | REAL (hist) + live blend |
| 10 | soil_moisture | **0.264 all N** (S 0.271 via `extract_soil_cci.py` 7/7 valid) | CCI COMBINED TCDR v09.2 `extract_soil_cci.py` June 10–16 window-mean, 7/7 valid flags=[0], cell (27.625, 88.625) same flag mask; Gangtok 0.271 1901-2024 | REAL |
| 11 | ndvi | 0.605 / 0.122 / 0.782 / 0.645, S2B_45RXL_20241129 (**same** Gangtok granule covers all N), N2 scl=5 bare rest scl=4 | Element84 STAC + COG /vsicurl/ | REAL quasi-static |
| 12 | lulc | FOREST / BUILT / FOREST / AGRI (WC-10 9/9, WC-50 7/9, WC-10 9/9, WC-30 6/9) | SAME WorldCover tile N27E087 76.7% | REAL |
| 13 | lithology | `chungthang_subgroup_gneiss` all N | CGWB 2025: Chungthang = North-Sikkim country rock; nearest verified map Gangtok town | PROXY-published-map uniform |
| 14 | distance_to_road | 784 / 15 / 519 / 17 m (same filters/radii, retries) | Overpass 226 ways total Lachung `roads_osm_provenance.json:1` | counts proven, demo topology |
| 15 | distance_to_river | 986 / 285 / 381 / 154 m | Overpass | measured |
| 16 | lineament_density | 0.8 all N uniform | literature; Lachung INSIDE verified Bhuvan SK_LN50K_0506 bbox 88.035/27.073–88.892/28.061, no per-slope clip | PROXY-regional (Bhuvan clip = upgrade) |
| 17 | drain_density | 0.97 / 1.07 / 2.81 / 3.39 (≥1 km² channel cells within 300 m) | same USGS accumulation grids | PROXY-window measured |
| + | `seismic_*` ×3 | per-zone from 26 USGS M5+ 1965–2024 `usgs_quakes.json:1` | `sih26001_model.py:_seismic_lookup` 59y window | REAL |
| L1 | previous_landslide | 0 all N (nearest 800 m+: N1/N2 SKM/NS/78A10/2017/206 @1026/832 m, N3/N4 SKM/NS/78A10/2017/205 @801/1245 m) | LOCAL GSI shapefile 693 Sikkim rows 300 m rule | REAL-cited negatives (omitted from X) |
| L2 | event | 0 all (INITIATION year-or-0) | — | honest 0 |
| Q | evidence_quality | `dated-only-negative` all N | same rule | tag |
| Q | time_window | 2024-06-17 | IMD per-corridor | REAL date |

## Honesty notes

- High-Himalaya SRTM voids: **28,011 void cells** in Lachung window (vs 0 Darjeeling) neighbour-mean filled; per-slope derivatives read off filled grid (logged). N1's own 3×3 contained a void.
- N1 elev 3095 m inside gate 1800–3200 m (Yumthang genuinely high). Measured, not tuned.
- Same-cell: rain (27.75,88.75), soil (27.625,88.625) serve all N (0.25° limit, as Gangtok/Darjeeling).
- Warning thresholds (overlay, scoring frozen): `warning_thresholds.json:1` lachung **N1 380 N2 390 N3 405 N4 370**, effective `r7+0.3*r30`, SWI `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12, 6-state NORMAL→EVACUATE, quake ×0.75.
- OSM Lachung 226 sparse Himalayan network honest count (not missing data); R1–R4 geometry deterministic per corridor for R2-avoidance `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2`.
- Wound Lachung 0 candidates; runout screening capped 400/zone (see `runout_exposure.json:1` total 253, Lachung N1 0 N2 47 N3 1 N4 21).
- Training n=2936 1468+1468 RF 0.9338 XGB 0.9418 Brier isotonic 0.0971 applies corridor-wide (GroupKFold8, not per-corridor retrain).