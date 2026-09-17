# NGEN Provenance — S1 (Gangtok Pilot) — 2025-11-15 Truth

**Status:** Built — 2025-11-15 truth · **Sample:** `feature_matrix.sample.csv` 12 rows (S1–S4 + D1–D4 + N1–N4) × 22 cols, 17 numeric + lulc · **Validators:** `validate_ngen_sample.py` OK + `check_scaffold.py` SCAFFOLD OK 17-feature · **Zero STUBs**
**Trace to:** `SCAFFOLD_CONTRACT_SEPT5.md:1` · `05_FEATURE_SCHEMA_SIH26001.md:16` · `03_DATA_PLAN_SIH26001.md:1`

---

## 1. Pilot location (frozen for demo)

Centre `27.3389, 88.6065` CRS `EPSG:4326`. Frozen scores/bands unchanged.

| Slope | Village | Lat | Lon | Band | Score |
|---|---|---|---|---|---|
| S1 | Tathangchen (upper) | 27.3450 | 88.6000 | Critical | 89 |
| S2 | Chandmari (road-cut) | 27.3380 | 88.6120 | High | 78 |
| S3 | Tadong (mid) | 27.3250 | 88.6065 | Moderate | 66 |
| S4 | Ranipool (valley) | 27.3150 | 88.5950 | Low | 52 |

Full 12-row matrix adds Lachung N1–N4 (`NGEN_PROVENANCE_LACHUNG.md:12`) and Darjeeling D1–D4 (`NGEN_PROVENANCE_DARJEELING.md:12`) — same 22-col schema, per-corridor honest windows (S 2024-06-16, N 2024-06-17, D 2024-07-08).

---

## 2. Sample shape — 12×22, 0 STUBs

`feature_matrix.sample.csv:1` header frozen order (22 cols). `validate_ngen_sample.py:1` checks header order, ≤20 rows (12 passes), S1–S4 present, zone unique, numeric/categorical types, no `FILL`, manifest Gangtok+EPSG:4326. `check_scaffold.py:1` checks frozen IDs/scores/bands/roles + R2 avoidance.

| Check | Result |
|---|---|
| Rows | 12 (S1–S4 gangtok + D1–D4 darjeeling + N1–N4 lachung) |
| Cols | 22 = 17 numeric (slope/elev/aspect/curv/twi/spi/log + rain 24h/7d/30d + soil + ndvi + road/river/drain + seismic×3 + wound) + lulc + zone_id/time_window/event/evidence_quality |
| `evidence_quality` | `dated-only-negative` (S1/S3/S4) / `approximate` (S2 out-of-window 2019 slide) — all dated rows honest |
| STUBs | **0** — every cell REAL or PROXY-published-map/window |

---

## 3. Per-feature pedigree — Gangtok S1–S4 (all slopes same pattern, values differ)

| # | Feature | S1 value | Source | Tag |
|---|---|---|---|---|
| 1 | `slope_angle` | 28.5° | SRTM `n27_e088_1arc_v3.tif` Horn-1981 anisotropic (`usgs_s234.json:1`) | REAL |
| 2 | `elevation` | 1290 m bilinear | same tile 3601×3601 EPSG:4326 | REAL |
| 3 | `aspect` | 289° downslope | same | REAL |
| 4 | `curvature` | 0.0111 Laplacian | same | REAL |
| 5 | `twi` | 5.99 D8 priority-flood ln(a/tanB) 7.7×5.9 km crop, 90 voids 0.17% filled | same | REAL |
| 6 | `spi` → `spi_log` | 120.9 → log1p at model | same a·tanB | REAL |
| 7–9 | `rainfall_24h/7d/30d` | 14.0 / 327.3 / 712.2 mm | IMD 0.25° `ind2024_rfp25.nc` nearest cell 27.25N 88.50E (~13 km), wettest trailing-7d 2024-06-16 (`extract_gangtok_rainfall.py` → `gangtok_rainfall_2024.csv` 366 rows) + **live** `GET /api/forecast/live:1154` Open-Meteo 7d 1h cache + `GET /api/forecast/imd-live:1124` IMD_API_KEY gated district API | REAL (hist truth) + live blend |
| 10 | `soil_moisture` | 0.271 | CCI COMBINED TCDR v09.2 `extract_soil_cci.py` nearest cell 27.375,88.625, flags 4|8|16|32 masked, **7/7 valid flags=[0]** window-mean | REAL satellite-observed |
| 11 | `ndvi` | 0.718 (S2 0.139 bare, S3 0.817, S4 0.468) | Sentinel-2 L2A `S2B_45RXL_20241129_0_L2A` cloud 0.02% Element84 STAC /vsicurl/ B04+B08+SCL DN red=390 nir=2380 scl=4 quasi-static post-monsoon (dated in manifest) | REAL |
| 12 | `lulc` | FOREST (S2 BUILT, S3 FOREST, S4 BUILT) | ESA WorldCover 2021 v200 tile `N27E087` 10 m 76.7% accuracy, 3×3 mode 9/9 centre-agree, 10→FOREST 50→BUILT (`s234_lulc.json:1`) | REAL |
| 13 | `lithology` | `lingtse_granite_gneiss` all S (uniform) | PROXY-published-map: NESAC Fig25/48 via DRAP p71/p118 + CGWB; Bhukosh WFS/WMS **timeout 15s both 2025-11-14** `bhukosh_vector_attempt.json:1` grade PROXY (not STUB) | PROXY-published-map |
| 14 | `distance_to_road` | 4 m (S2 6, S3 126, S4 66) | OSM Overpass 2025-11-14: **1014 gangtok / 226 lachung / 504 darjeeling** ways counted `roads_osm_provenance.json:1` ex 47416074 NH310A trunk; geometry R1–R4 centroid-aligned deterministic (topology demo) for R2 avoidance `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2` | REAL counts, demo topology |
| 15 | `distance_to_river` | 226 m (S2 183, S3 1093, S4 460) | same Overpass waterway=river|stream | REAL |
| 16 | `lineament_density` | 0.8 km/km² uniform all S | PROXY regional: Bhuvan `SK_LN50K_0506` verified WMS bbox 88.035/27.073–88.892/28.061, WFS disabled → uniform 0.8 (literature 0.3–1.4) | PROXY-regional |
| 17 | `drain_density` | 0.0 S1 (S2 1.9, S3 1.6, S4 1.2) | USGS accumulation ≥1 km² within 300 m | PROXY-window measured |
| 18 | `previous_landslide` | 0 (S2=1 SK/ESK/78A11/2019/02 @286.7 m + report SI/GTK/78A11/2025/03) | GSI Bhusanket 30,842 `sikkim_join.json:1` 693 Sikkim 300 m rule | REAL-cited (omitted from X leakage) |
| 19 | `event` | 0 all S (year-or-0 INITIATION, never dated in window) | honest 0 | REAL |
| Q | `evidence_quality` | `dated-only-negative` / `approximate` (S2) | — | tag |
| Q | `time_window` | 2024-06-16 | IMD wettest-7d | REAL date |
| + | `seismic_*` (3) | per-zone from 26 USGS M5+ 1965–2024 `usgs_quakes.json:1` | `sih26001_model.py:_seismic_lookup` 59 y window (dist / n50_rate / years_since) | REAL |
| + | `wound` | 0 S1 screening (2 candidates corridor-wide) | `wound_map.json:1` roadside NDVI loss ≥0.3 ≤150 m road SCL-gated pre 2023-11-15 → post 2024-11-29 | vet-queue 4/2936 training |
| + | `swi` (overlay) | tanh(SWI/100) | `swi.py:14` JMA 3-tank L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 | warning overlay |

Same-cell limits disclosed: rain cell 27.25/88.50, soil cell 27.375/88.625 serve all S (0.25°).

---

## 4. Source evidence (committed)

- **IMD:** `data/raw/imd/ind2024_rfp25.nc` 1901-2024 (1901–2024) → `gangtok_rainfall_2024.csv` + live `GET /api/forecast/live` (Open-Meteo) + gated `GET /api/forecast/imd-live` (IMD_API_KEY, api.data.gov.in district).
- **DEM derivatives:** Horn-1981 + TWI/SPI (also logged as twi/spi) on same tile.
- **Soil:** CDS 7 daily NC LOCAL ONLY → `extract_soil_cci.py` → `gangtok_soil_cci.csv` 0.271 + `swi.py:14` 3-tank.
- **DEM:** `n27_e088_1arc_v3.tif` LOCAL ONLY → `extract_usgs.py` → `usgs_s234.json` + `catchment_s234.json` (sha256 in `manifest.sample.json:33`).
- **Satellite:** `s1_sentinel2.json` + `s234_ndvi.json` (S2B_45RXL) + `s234_lulc.json` (WorldCover N27E087) — all /vsicurl/ no download.
- **Geology:** `s234_lithology.json` + `s234_lineament.json` + `bhukosh_vector_attempt.json:1` timeout proof.
- **OSM:** `s1_osm_nearest.json` + `s234_osm_nearest.json` + `roads_osm_provenance.json:1` 1014/226/504; `osm-qa-unverified` kept.
- **Labels:** `sikkim_gangtok_sample.csv` + `sikkim_join.json` 693-row haversine + `sikkim_report_gangtok.csv` corroboration.
- **Seismic:** `usgs_quakes.json:1` 26 events M5+ 1965–2024.
- **Wound/runout:** `wound_map.json:1` 2 scars gangtok + `runout_exposure.json:1` max 85 buildings S2 (steepest descent 30 m, <5°/1.8 km stop, 400/zone cap, 253 total screening).

---

## 5. Training + operational overlays (frozen 2025-11-15)

| Item | Truth |
|---|---|
| Training matrix | 2936 rows 1468+1468 seed 42 >300 m buffer `manifest.training.json:42` |
| CV | Spatial GroupKFold 8 (KMeans-8 coords seed 42) `train_sih26001.py:129` — no random split |
| Metrics | **RF 0.9338** / **XGB 0.9418** / LGBM 0.9406 ; Brier raw 0.118 → isotonic **0.0971** `calibration.md:8` ; temporal holdout `≤2018 vs ≥2019` 673/73 pos, test 807, RF test AUC 0.8568 Brier 0.0978 `metrics.md:32` |
| Scoring frozen | `score=round(raw_proba*100)` — 89/78/66/52 scaffold `slopes.json:1` when weights absent (`data.py:308`) |
| SWI | `swi.py:14` JMA 3-tank L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 → `tanh(SWI/100)` threshold 0.40 `GET /api/soil/swi:1203` |
| Warning | 6-state `NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE` `main.py:1449` per-zone effective_rain `r7+0.3*r30` `warning_thresholds.json:1` gangtok **S1 385 S2 395 S3 410 S4 375** (lachung/darjeeling tables inside), quake-conditioned ×0.75 if ≤0.49 y & n50>0, forecast 50 mm day /150 mm week, wound/isolation override |
| Routing | Deterministic R2 avoidance — `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2` `main.py:49,53` `data.py:207` risk-weighted Dijkstra `1+weight*exposure/100` on hazard graph (R2 dropped) `comparison.py` — R4 bottleneck `R4 blocked ⇒ S1/S2/S3 isolated` `main.py:1326` |
| Isolation | `_isolation_for_location:1326` OPEN/MAY_ISOLATE/ISOLATED, may_isolate = one at-risk road left + High/Critical |

---

## 6. Limitations (honest)

- Bhukosh vector not per-slope — timeout logged, uniform PROXY kept, omitted from X when uniform `manifest.training.json:263`.
- OSM counts proven (1014/226/504) but R1–R4 geometry demo deterministic for pedagogical R2 avoidance; full traces on demand.
- IMD grid ~13 km & CCI cell ~4 km same-cell consequence stated; hyperlocal cloudbursts missed.
- Wound = review queue (seasonal clearing vs cut), 10–20 m pixels; runout = screening (may run 200 m off-slope, capped 400/zone, S2 max 85).
- 12 slopes ≠ Gram Panchayat scale; bands are prototype operational bands, not safety standards.

---

**2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched):**

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT
