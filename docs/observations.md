# Talus — Observations Log (SIH26001 · 2025-11-14)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


Running record of NER data-grounding findings. 2025-11-15 truth — replaces Neyveli Mine-II era (11.50°N,79.50°E) retained in git history.

---

## 1. Data sources (locked 2025-11-14)

| Signal | Source | Provenance |
|---|---|---|
| Rain historical | IMD 0.25° daily NetCDF `ind*_rfp25.nc` 1901–2024 (135×129, 6.5–38.5°N × 66.5–100°E), `RAINFALL[TIME,LATID,LONID]` float32 mm/day | `data/raw/imd/` + `gangtok_rainfall_2024.csv` + 30-yr climatology |
| Rain live | Open-Meteo 7d 1h cache + IMD data.gov.in district live (gated `IMD_API_KEY`, fallback Open-Meteo) | `GET /api/forecast/live` + `/api/forecast/imd-live` |
| Soil | ESA CCI COMBINED v09.2 daily 1978–2024 `C3S-SOILMOISTURE-*.nc` 0.25° (`flag` kill-bits 4/8/16/32, `sm` m³/m³) + SWI 3-tank `L1=15 L2=60 L3=60` | `data/raw/soil/v09.2/` + `backend/app/swi.py` |
| DEM | SRTM v3 30m tile `n27_e088_1arc_v3.tif` (GLO-30) | `data/sih26001/evidence/usgs_s234.json` |
| Terrain | slope/aspect/curvature/TWI/SPI via Horn-1981 + D8 priority-flood from SRTM | `usgs_s234.json` + `catchment_s234.json` |
| Imagery | Sentinel-2 L2A `S2B_45RXL 2023-11-15 vs 2024-11-29` + WorldCover 10m N27E087 | `s234_ndvi/lulc.json` + `wound_map.json` 2 scars |
| Lithology | Bhukosh WFS PROXY-published-map `lingtse_granite_gneiss` / `darjeeling_gneiss` uniform (timeout 15s, omitted from X) | `s234_lithology.json` |
| Roads/rivers | OSM Overpass 1014/226/504 ways (`roads_osm_provenance.json`) | `out center` + `NH310A trunk` |
| Quakes | USGS 26 M5+ | `usgs_quakes.json` + seismic feats ×3 |
| Inventory | GSI Bhusanket 30,842 pts + 777 PDF rows → 764 Sikkim + 693 Sikkim `sikkim_join` + WB Darjeeling → training 1468+1468 | `manifest.training.json` |

## 2. NGEN corridors (12 slopes, per-corridor monsoon windows)

| Corridor | Zones | Window (wettest-7d) | Rain cells (nearest 0.25°) |
|---|---|---|---|
| Gangtok | S1 Tathangchen, S2 Chandmari, S3 Tadong, S4 Ranipool | 2024-06-16 | 27.25°N, 88.50°E |
| Lachung | N1 Yumthang approach, N2 NH-310A cut, N3 River Bend, N4 Valley | 2024-06-17 | 27.75°N, 88.75°E |
| Darjeeling | D1 Ghoom, D2 Hill Cart Rd, D3 Lebong, D4 Valley | 2024-07-08 | 27.00°N, 88.25°E |

Each NGEN row = 17 numeric + lulc, REAL/PROXY zero STUBs (`feature_matrix.sample.csv`, `manifest.sample.json` validator-green). `previous_landslide` excluded by leakage rule; `event` season-window proxy `approximate`.

## 3. Training matrix (2936×22)

- `data/sih26001/processed/feature_matrix.training.csv` — 1468 pos (Sikkim + Darjeeling-hills >300m negatives 1468, 1:1, seed 42), merged via `scripts/build_training_matrix.py --rebuild`.
- X: 17 numeric `slope_angle, elevation, aspect, curvature, twi, spi_log(log1p), rainfall_24h/7d/30d, soil_moisture, ndvi, distance_to_road, distance_to_river, lineament_density 0.8, drain_density, seismic_n50_rate/dist_km/years_since` + `lulc` one-hot (`drop_first`); `lithology` uniform omitted.
- Validation: `GroupKFold(8)` KMeans-8 on coords → **RF 0.9338 / XGB 0.9418 / LGBM 0.9406** (LR 0.8914), **Brier 0.0971** isotonic (raw 0.118), temporal `673/73` dated n=807 → **RF 0.8568** (`metrics.md`, `calibration.md`, TreeSHAP 5 pts).

## 4. Warning & SWI model

- **Effective rain** `rainfall_7d + 0.3*rainfall_30d` — Monga 390 separator, per-zone thresholds frozen `warning_thresholds.json`: Gangtok `S1 385 S2 395 S3 410 S4 375`, Lachung `N1 380 N2 390 N3 405 N4 370`, Darjeeling `D1 400 D2 410 D3 420 D4 390` (median +20 Taiwan-style, update `0.9*old+0.1*event`).
- **SWI 3-tank** JMA `swi.py`: `L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01` → `tanh(SWI/100)`. Scoring frozen on CCI `soil_moisture` (0.27-class window mean); SWI overlays warning only.
- **Warning state** 6-state `NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE` (reason-stamped: effective rain, SWI, wound BigGIS 2 scars, forecast Open-Meteo, quake 25% threshold drop) — `GET /api/warning/state` + `GET /api/isolation` (R4 bottleneck ISOLATED/MAY_ISOLATE) + `RiskTrendChart` NOW line.

## 5. Roads / runout / wound / quakes

- **Roads**: OSM 1014/226/504 ways (`roads_osm_provenance.json`, NH310A trunk) → demo topology R1–R4 (`roads.json` R2 at-risk) for deterministic avoidance; honest counts, not traced geometry.
- **Runout**: SRTM steepest-descent + OSM exposure → `runout_exposure.json` 85 buildings downstream (`GET /api/runout/exposure` + `GET /api/zones/{id}/exposure` operational risk).
- **Wound**: Sentinel-2 NDVI loss `wound_map.json` 2 scars near R2/R3 (`GET /api/wounds`).
- **Quakes**: USGS 26 M5+ `usgs_quakes.json` → `seismic_n50_rate, dist_km, years_since` + 25% warning threshold drop when recent within window.

## 6. Backend / frontend truth

- **Backend** `app/main.py` 35/35: `/health`, `/api/zones`, `/explanation` (TreeSHAP top-5 live or fixture), `/exposure` (runout+wound+isolation), `/warning/state` 6-state, `/isolation` R4, `/soil/swi`, `/roads/status` + `/roads/restrictions` catalogue, `/forecast/live` + `/imd-live` (`IMD_API_KEY` gated), `/alerts/dispatch` app|sms (`msg91/fast2sms/twilio/textbelt` + auto watcher 60s/3600s `auto/status`), `/reports` + `/live/feed` + `/replay/series` + `/runout/exposure` + `/wounds` + `/model/calib` Bayes 0.5→0.01.
- **Frontend** `VITE_USE_LIVE_API=true`: `RiskMap` 5-band 1014/226/504 OSM proven geometry demo topology, `IsolationAlertCard`, `WarningStateCard` 6 states, `RiskTrendChart` NOW separation, `RoadStatusCard`, `QuickStatsBar` LIVE badge, `AlertPanel` en/hi/ne/as/bn + sms, `RiskScoreGauge`, `AdminPanel /admin` PIN 9999/1111/2222/3333, `RoleSelector` PIN gate `services/auth.js`, `LoginModal`; PWA `sw.js` + `manifest 192/512` + `talus_report_outbox`.

## 7. Decision ledger (SIH26001 entries)

### Entry 1 — NER real data beats synthetic

- **Observation:** 37k+ NER Bhusanket points + 1901–2024 IMD + CCI + SRTM + Sentinel-2 exist.
- **Decision:** Ship 2936×22 real inventory training (GroupKFold 0.9338) — no generator world needed; synthetic R² 0.998 ledger archived.

### Entry 2 — 17-feat contract, no stubs

- **Observation:** NGEN 17 numeric + lulc covers rain×3 + terrain×6 + soil + NDVI + LULC + road/river/drain + seismic×3; lithology/lineament uniform.
- **Decision:** Freeze contract `feature_matrix.sample.csv` validator-enforced (89/78/66/52), lithology omitted honestly.

### Entry 3 — SWI warning-only

- **Observation:** CCI soil quasi-static (0.27 window mean) — single-event soil upgrade would break scoring continuity.
- **Decision:** Scoring frozen on `soil_moisture`; SWI 3-tank overlays warning state only (`RECALIBRATION_NOTE.md`).

### Entry 4 — Per-zone thresholds 385…420

- **Observation:** Monga 390 separator is regional — per-slope vulnerability needs local thresholds.
- **Decision:** `warning_thresholds.json` per-zone 375–420 (median+20), updated 0.9×old+0.1×event.

### Entry 5 — Lithology PROXY, road demo topology

- **Observation:** Bhukosh WFS timeout 15s; OSM road tracing would fabricate stranded counts.
- **Decision:** Lithology uniform PROXY (honestly labeled, omitted from X); roads demo topology with proven 1014/226/504 counts (deterministic R2 avoidance).

### Entry 6 — Bayes 0.5→0.01 + PWA

- **Observation:** Balanced training over-states field P(landslide) at ~1% hillslope-day prevalence.
- **Decision:** `confidence_real_1pct = Bayes(p_cal*0.02/(…))` added, score frozen, SWI/wound/quake overlays warning only; PWA offline `sw.js` + `talus_report_outbox` for remote field use.

## 8. Current checkpoint (frozen 2025-11-15)

- **Locked:** NGEN 12 rows (3 corridors), 2936 training, GroupKFold 0.9338 / Brier 0.0971, TreeSHAP top-5, 6-state warning + SWI 3-tank + thresholds S1 385 etc, 35/35 tests, scaffold 89/78/66/52, OSM 1014/226/504, runout 85 buildings, wound 2 scars, USGS 26 quakes, PWA 192/512, Docker curl /health + postgis.
- **Deferred:** per-corridor isotonic (<200 dated/corridor), CV crack imagery closed loop, real Bhukosh overlay, daily soil upgrade (CCI refresh via `download_cci_soil.py`).
- **Next experiment (when new files land):** `python scripts/download_cci_soil.py --probe 2024` → `python scripts/build_training_matrix.py --rebuild` → `python scripts/train_sih26001.py` → re-ablate `no_soil` delta (currently −0.0074) vs SWI.