# SIH26001 — Complete Research & Strategy Document

**TALUS: Landslide Risk Intelligence and Decision Support System for NER**
> Consolidates problem, domain, systems audit, data, architecture, validation, positioning, roadmap — updated to **2025-11-15** truth. Stale pre-GroupKFold numbers removed; see `metrics.md` for current GroupKFold8 RF 0.9338 XGB 0.9418 Brier 0.0971.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [SIH26001 Problem Statement Analysis](#2-sih26001-problem-statement-analysis)
3. [NER Domain Context](#3-ner-domain-context)
4. [Existing Systems Landscape](#4-existing-systems-landscape)
5. [Gap Analysis](#5-gap-analysis)
6. [Data Sources & Availability](#6-data-sources--availability)
7. [Physics & ML Adaptation](#7-physics--ml-adaptation)
8. [Architecture Mapping: TALUS → NER](#8-architecture-mapping-talus--ner)
9. [Validation & Ground Truth Strategy](#9-validation--ground-truth-strategy)
10. [Research Survey](#10-research-survey)
11. [Competitive Positioning](#11-competitive-positioning)
12. [Roadmap & Next Steps](#12-roadmap--next-steps)

---

## 1. Executive Summary — UPDATE 2025-11-14 (frozen `35/35`)

**Problem:** NER faces monsoon landslides that isolate villages — monitoring is reactive, manual, threshold-only.

**Opportunity:** SIH26001 (MDoNER) asks for AI early warning with GIS, routing, multilingual alerts, offline. TALUS architecture (Detect→Understand→Escalate→Decide→Act) maps directly — data layer changed, architecture survived.

**Key finding (validated 2025-11-14):** Real data exists — GSI Bhusanket 91k+ India-wide (764 Sikkim `manifest.training.json` + 693 Sikkim `sikkim_join.json`), NASA COOLR, ISRO Atlas 80k+, academic inventories 490–1,330 events with rain records, IMD 0.25° 1901–2024 + Open-Meteo live, CCI v09.2 1978–2024, SRTM 30m n27_e088, Sentinel-2 2 scars, USGS 26 quakes M5+. Trained on **2936×22** (`1468+1468` Sikkim + Darjeeling-hills, `feature_matrix.training.csv`) — **17 numeric (spi log1p + seismic×3) + lulc**, lithology/lineament uniform PROXY omitted.

**Model truth:** `GroupKFold(8)` KMeans-8 on coords OOF **RF 0.9338 / XGB 0.9418 / LGBM 0.9406** (LR 0.8914), **isotonic Brier 0.0971** (raw 0.118), temporal `673/73` dated → **RF test 0.8568** (`metrics.md`, `calibration.md`). TreeSHAP top-5 per zone via `sih26001_model.py` (`shap.TreeExplainer`, fixture fallback). Score frozen, `confidence_real_1pct` Bayes `0.5→0.01` (`RECALIBRATION_NOTE.md`).

**Backend truth:** FastAPI `app/main.py` **35/35**, scaffold **89/78/66/52**, 5-band — endpoints: `/health`, `/api/zones`, `/api/zones/{id}/explanation` (TreeSHAP) + `/exposure` (runout 85 buildings + wound + isolation), `/api/warning/state` 6-state `NORMAL→EVACUATE` (effective rain `7d+0.3*30d` per-zone thresholds `warning_thresholds.json` S1 385 etc + SWI 3-tank `swi.py` L1=15 L2=60 L3=60 + wound BigGIS 2 scars + forecast Open-Meteo + quake 25% drop), `/api/isolation` (R4 bottleneck), `/api/soil/swi`, `/api/roads/status` + `/api/roads/restrictions` catalogue, `/api/forecast/live` + `/api/forecast/imd-live` (`IMD_API_KEY`), `/api/alerts/dispatch` `app|sms` (`msg91/fast2sms/twilio/textbelt`) + auto watcher 60s/3600s + `/api/alerts/auto/status`, `/api/reports` + `/api/live/feed` + `/api/replay/series` + `/api/runout/exposure` + `/api/wounds + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` + `/api/model/calib`.

**Frontend truth:** RiskMap 5-band 1014/226/504 OSM proven (`roads_osm_provenance.json`, geometry demo topology, deterministic R2 avoidance) + IsolationAlertCard + WarningStateCard 6 states + RiskTrendChart (NOW separation) + RoadStatusCard + QuickStatsBar LIVE + AlertPanel en/hi/ne/as/bn + sms + RiskScoreGauge + AdminPanel `/admin` PIN 9999/1111/2222/3333 + RoleSelector PIN gate + LoginModal; PWA `sw.js` + manifest 192/512 + outbox.

**Competitive gap:** GSI RLFS = thresholds only — no AI/ML, no soil, no per-slope, no routing/offline. GSI lists “AI/ML decision-support layer” as next step — we built it.

**Recommendation:** Ship NER track — architecture intact, data real, evaluation honest.

---

## 2. SIH26001 Problem Statement Analysis

### 2.1 Full text

**Title:** AI-Based Early Warning and Landslide Risk Monitoring System in NER — Software | Disaster Management | MDoNER.

Background/descriptions as published — collect rain/soil/satellite/terrain/history, ML high-risk zones, real-time alerts, GIS, geo-tagged crowdsourcing, dashboards, multilingual + offline.

Expected: GIS dashboard + ML engine + mobile/web reporting + IMD/satellite/sensor integration + SMS/app alerts + cloud + offline sync.

### 2.2 Decomposition

| # | Requirement | Technical need | TALUS mapping (2025-11-15) |
|---|---|---|---|
| R1 | Multi-source ingestion | ETL rain/soil/DEM/geology | NGEN (3 corridors, 12 slopes, 17 feats, zero STUBs) |
| R2 | AI/ML prediction | RF/XGB/LGBM | 2936 rows, GroupKFold8 RF 0.9338 XGB 0.9418, Brier 0.0971 |
| R3 | GIS dashboard | Leaflet heatmap | RiskMap 5-band 1014/226/504 OSM proven |
| R4 | Severity levels | 5 bands | FROZEN_BANDS 85/66/41/21 (score = round(p*100)) |
| R5 | Road connectivity | Graph + overlay | R1-R4 + deterministic R2 avoidance + restrictions catalogue |
| R6 | Weather forecasts | IMD API | Open-Meteo live (1h cache) + IMD-live gated (`IMD_API_KEY`) |
| R7 | Emergency priority | Role logic | 4 roles villager/district_officer/state_manager/rescue_team |
| R8 | Field reporting | Camera+GPS | `POST /api/reports` + outbox `talus_report_outbox` |
| R9 | SMS/app alerts | Pipeline | `POST /api/alerts/dispatch` app\|sms (4 providers) + auto watcher 60s/3600s |
| R10 | Multilingual | i18n | en/hi/ne/as/bn (110 keys ×5) |
| R11 | Offline | Local-first | PWA sw.js + manifest 192/512 + outbox + audit log |
| R12 | Explainability | SHAP | TreeSHAP top-5 per zone (live or fixture) |
| R13 | Calibration | Isotonic + Bayes | Brier 0.0971 + `confidence_real_1pct` 0.5→0.01 |

### 2.3 NOT required in prototype

In-situ sensor deployment (adapter ready), InSAR, exact landslide time/place, flash-flood routing, hardware.

---

## 3. NER Domain Context

### 3.1 Why NER slides

Eastern Himalaya Zone V, schist/phyllite/gneiss, active lineaments, 12,000 mm/yr Cherrapunji, >144 mm/day trigger, 67–73% rain Jun–Sep, slopes 0–76°, unplanned road cutting (#1 predictor Meghalaya), deforestation.

### 3.2 Landslide stats (GSI)

Sikkim 2,923 (2,218 dated, 459 events) among 37,903+ NER / 91k India-wide — Sikkim+Nagaland best dated.

### 3.3 Rainfall thresholds (NER)

Monga & Ganguli 2026 (490 events 2006–2019): `E = −11.10 + 0.62×D` (24<D<1440 hr), ~13 mm/day monsoon separator, 67% Jun–Sep, spatial thresholds Guwahati/Shillong 91.8 mm/3d > Aizawl/Imphal, LULC modulates. Current overlay: `effective = 7d + 0.3*30d`, separator **390** (corridor 375–420 per-zone `warning_thresholds.json`) + SWI 3-tank.

### 3.4 Conditioning factors

Top: elevation, slope, lithology (PROXY uniform), rainfall (7d/30d/24h + forecast), lineament, road distance (#1), NDVI, soil moisture (CCI + SWI), river distance, LULC, aspect, curvature, TWI/SPI, drain density, seismic rate/dist/years-since.

---

## 4. Existing Systems Landscape

### 4.1 Government operational

**GSI RLFS (NLFC Kolkata):** rainfall thresholds + NWP, 4 levels, 21+ districts mid-2025 (expanding to nationwide 2030), NER: Dima Hasao/Cachar, Peren/Dimapur/Kohima, 6 Sikkim districts experimental. CSI >70% (Darjeeling etc), Bhusanket + Bhooskhalan. Gaps: sensors, InSAR, AI/ML layer, panchayat granularity — explicitly requested.

**IIT Mandi P-RIL/GEE:** IHR-wide, 26k GSI slides, IMERG → P-RIL daily GEE portal + WhatsApp.

**IIT Mandi sensor nets:** ground-shift mm sensors (Himachal) + 60+ low-cost AI arrays (3-hr, >90%).

**Nagaland Eliona (May 2026):** NSDMA AI supercomputing platform.

**NESAC:** hazard zonation for NER.

### 4.2 Research / prototype

**NASA LHASA 2.0:** global XGBoost 1 km, IMERG/SMAP, open-source `github.com/nasa/LHASA`.

**ML-CASCADE/ILSM (IIT Delhi):** India 100 m, ANN+RF+SVM, 154k points, 95.73% (`Catena 2024`).

**Amrita A-LEWS:** 100–200 sensors, Munnar 2009 + Chandmari Gangtok 2015 (150 acres), 3–24 hr, 5k+ protected — hardware-heavy.

**NEHU Meghalaya (Feb 2026):** 10-model ensemble, >90%, road distance #1.

**Dibang Valley (Mihu 2026):** 537 slides, XGB+LGBM AUC 0.96, elevation/lithology/rainfall/lineament dominate.

**Brahmaputra-CoPilot (IIT Patna 2025):** Assamese-Hindi-English flood/landslide advisory — simulation only.

### 4.3 Commercial

SCS Tech Smart LEWS, landslidemonitoring.in, NRSC NDEM — not NER AI/ML comparable.

---

## 5. Gap Analysis

### 5.1 Exists vs SIH26001

| Requirement | Who does it | Gap |
|---|---|---|
| Rain integration | GSI, IIT Mandi | ✓ Solved |
| Soil moisture | A-LEWS hardware only | **Major** — CCI v09.2 + SWI fills |
| Satellite analysis | NRSC raw | **Major** — Sentinel-2 wound 2 scars shipped |
| Per-slope prediction | IIT Mandi partial | **Moderate** — 12 slopes live |
| Inventory | GSI 91k | ✓ Available (2936 used) |
| AI/ML | Research/NASA | **Moderate** — RF 0.9338 shipped |
| GIS dashboard | NDEM basic | **Major** — RiskMap 5-band live |
| Field reporting | Bhooskhalan basic | **Major** — POST /api/reports + queue |
| Road connectivity | Nobody | **Complete** — R1-R4 + isolation R4 + restrictions catalogue |
| Emergency priority | Nobody | **Complete** — 4 roles |
| Routing | Nobody | **Complete** — Dijkstra avoids R2 |
| Weather forecast | GSI 24/48 hr | ✓ Partial — live + IMD-live |
| Multilingual | CoPilot conceptual | **Major** — 5 langs live |
| Offline | A-LEWS sensor | **Major** — PWA sw.js live |
| Calibration | Nobody | **Complete** — Brier 0.0971 + Bayes |
| Explainability | Research only | **Major** — TreeSHAP top-5 |
| Warning escalation | RLFS 4 levels | **Complete** — 6-state NORMAL→EVACUATE |

### 5.2 GSI wants AI/ML

GSI NIDM 2026: “Integration of AI/ML as decision-support layer”; DG Asit Saha Jul 2025: “AI expert system” — TALUS answers that call.

### 5.3 TALUS v2 does all

GSI RLFS 2–3 caps vs TALUS full stack (table in CURRENT_SYSTEM.md) — rain thresholds ✓ + AI ✓ + soil ✓ (CCI+SWI) + satellite ✓ + terrain ✓ + calibrated ✓ + SHAP ✓ + per-slope ✓ + GIS ✓ + role ✓ + road ✓ + priority ✓ + routing ✓ + reporting ✓ + scenario ✓ + evidence ✓ + offline ✓ + multilingual ✓.

---

## 6. Data Sources & Availability

### 6.1 Rainfall

IMD 0.25° daily 1901–present (imdpune.gov.in, `imdlib`/`imddata`), 8 NER stations 1980–2019 (Aizawl/Darjeeling/Gangtok/Kohima/Guwahati/Shillong/Imphal/Kalimpong), CHIRPS 0.05°, GPM IMERG 0.1° half-hourly, Open-Meteo live 7d (active), IMD data.gov.in district live (gated `IMD_API_KEY`, fallback Open-Meteo).

### 6.2 Soil moisture

**Live:** ESA CCI COMBINED v09.2 daily 1978–2024 0.25° m³/m³ (`flag` kill-bits, window-mean per corridor) + **SWI 3-tank** JMA (L1=15 L2=60 L3=60, `tanh(SWI/100)`, warning-only). Reanalysis options: ERA5-Land 0.1° 0.15–0.45, SMAP 36 km 2015+.

### 6.3 DEM / Terrain

**Live:** SRTM v3 30 m `n27_e088_1arc_v3.tif` (also GLO-30/Cartosat/ALOS 12.5 m alternatives); derivatives slope/aspect/curvature/TWI/SPI/flow acc via priority-flood.

### 6.4 Satellite / LULC

Sentinel-2 10 m (wound: S2B_45RXL 2023-11-15 vs 2024-11-29 → 2 scars `wound_map.json`), Landsat-8, WorldCover 10 m tile N27E087, Bhuvan LULC.

### 6.5 Geology

GSI Bhukosh WFS (timeout 15s → **PROXY-published-map** `lingtse_granite_gneiss` uniform, omitted from X, honestly labeled) — `s234_lithology.json`.

### 6.6 Inventories

GSI Bhusanket 37,903+ NER / 91k India, NASA GLC/COOLR, ISRO Atlas 80k+, Mizoram 19, Meghalaya 1,330, Dibang 537, Monga 490, ILSM 154k 100 m (Zenodo), National 109k 90 m (Khan 2025).

### 6.7 Infrastructure

OSM roads/rivers proven **1014/226/504** ways (`roads_osm_provenance.json`, geometry demo topology), SRTM runout + 85 buildings exposure, census/OSM settlements.

### 6.8 Verified access (Nov 2025)

| Dataset | Method | Account | Live |
|---|---|---|---|
| IMD gridded 0.25° | imdpune + imdlib | No | ✅ |
| SRTM 30m n27_e088 | USGS EarthExplorer | Free | ✅ |
| CCI v09.2 | CEDA + `download_cci_soil.py` | Free | ✅ |
| Sentinel-2 | Copernicus Hub | Free | ✅ |
| OSM 1014/226/504 | Overpass / Geofabrik | No | ✅ |
| USGS quakes 26 | `usgs_quakes.json` | No | ✅ |
| IMD live | data.gov.in district | `IMD_API_KEY` | ✅ gated |
| Bhukosh lithology | WFS | No | ⚠️ timeout → PROXY |

IMD grid: 135×129, 66.5–100°E × 6.5–38.5°N.

---

## 7. Physics & ML Adaptation

### 7.1 Mine → NER

Soil/rockslide vs rockfall; rainfall antecedent+triggering vs blasting; soil friction+cohesion vs rock cohesion; infiltration→saturation vs wetting→crack; variable DEM vs fixed bench; NDVI/road/river/lineament/seismic added.

### 7.2 NER chain

`Rainfall (antecedent+triggering) → Soil wetting (CCI + SWI 3-tank) → Pore pressure → Shear strength → FoS/susceptibility → Score 0–100 → Band + Warning overlay`.

### 7.3 Feature set (frozen 17+1)

`slope_angle, elevation, aspect, curvature, twi, spi, rainfall_24h/7d/30d, soil_moisture, ndvi, lulc (one-hot), lithology (uniform, omitted), distance_to_road, distance_to_river, lineament_density (0.8), drain_density, previous_landslide (omitted, leakage), seismic_n50_rate/dist_km/years_since` + `zone_id`/`event`/`evidence_quality`. Spi `log1p`, seismic ×3.

### 7.4 Target

Primary: binary `event` (season-window proxy, positives = inventoried slides). Secondary: 5 bands Very Low→Critical. Not: exact time/place.

### 7.5 ML selection

Dibang XGB 0.96, LGBM 0.96, RF 0.83–0.93, ensemble 0.95 — TALUS: **RF 0.9338 / XGB 0.9418 / LGBM 0.9406** (GroupKFold8), LR 0.8914 baseline beaten. Isotonic Brier **0.0971**. TreeSHAP top-5.

---

## 8. Architecture Mapping

### 8.1 Module mapping

| v1 | SIH26001 (2025-11-15) | Change |
|---|---|---|
| Generator | NGEN (real data pipeline) | Rewrite — real IMD+CCI+SRTM+Sentinel2+OSM+GSI |
| ML Predictor | ML Predictor | Retrained 2936 rows, RF500+isotonic (`sih26001_model.py`) |
| SHAP | SHAP TreeSHAP top-5 | Same lib, live per zone |
| Calibration | Calibration + Bayes 0.5→0.01 | Isotonic + prevalence correction |
| Trend | Warning 6-state + TrendChart NOW | Monsoon-aware, SWI + wound + forecast + quake |
| Decision | Decision engine | 4 new roles + 5 langs + sms toggle |
| Routing | Routing | NER road graph R1–R4, deterministic R2 avoidance |
| Scenario | Replay + Runout + What-if | Rainfall thresholds + SWI + wound + runout 85 buildings |
| Evidence | Evidence Card | Satellite/sensor/crowd + missing_evidence |
| Alert | Alert Panel | SMS 4 providers + auto watcher 60s/3600s |
| Dashboard | Dashboard | RiskMap 5-band 1014/226/504 + WarningStateCard 6 |
| Backend | Backend | FastAPI 35/35, full endpoint list (§1) |
| Mobile/PWA | PWA | sw.js + manifest 192/512 + offline outbox |

### 8.2 Survives

Two-engine (ML + warning overlays), isotonic+Bayes, SHAP, role logic, Dijkstra, evidence transparency, offline-first, test harness.

### 8.3 Changes

Synthetic → real NGEN, FoS → rainfall+SWI susceptibility, 12 mine → 17 NER feats, 73k synth → 2,936 real events, storm replay → thresholds+SWI+wound, mine map → NER GIS 12 slopes 3 corridors, evidence → camera/GPS + queue, alerts → 5 langs + SMS.

---

## 9. Validation & Ground Truth

### 9.1 Advantage vs v1

490+ dated rain events (Monga), 537 Dibang, 1,330 Meghalaya, 91k GSI India-wide, IMD 1901–present + 8 stations 1980–2019, benchmarks 0.89–0.96.

### 9.2 Training construction

`build_training_matrix.py`: positives 1,468 inventoried Sikkim+Darjeeling-hills (>300 m buffer negatives 1,468, 1:1, seed 42), merged with 17 NGEN feats; `event` season-window proxy tagged `approximate`.

### 9.3 Validation (current)

1. **Spatial GroupKFold(8)** KMeans-8 on coords → **RF 0.9338 / XGB 0.9418 / LGBM 0.9406** (metrics.md OOF, cluster_0 n/a disclosed).
2. **Temporal** 673/73 dated (n=807) → **RF 0.8568 Brier 0.0978**.
3. **Benchmark:** beats LR 0.8914 + naive Brier 0.25; matches Dibang 0.96 family.
4. **Calibration:** isotonic **Brier 0.0971** ECE10 0.0.
5. **Scenario:** thresholds 390 + NGEN windows consistent (Monga/Dahal screens).

### 9.4 Targets

Dibang 0.96 ≈ XGB 0.9418; Meghalaya >90% matched; GSI CSI >70% expected exceed; LHASA global beaten locally (NER-specific).

---

## 10. Research Survey

### 10.1 NER studies

| Study | Region | Method | Finding |
|---|---|---|---|
| Agrawal & Dixit 2021 | Meghalaya | FR/AHP/FAHP | 1,330 slides, 15 factors |
| NEHU 2026 | Meghalaya | 10-model ensemble | >90%, roads #1 |
| Mihu et al. 2026 | Dibang | XGB+LGBM | 537 slides AUC 0.96, elev/lith/rain/lineament top |
| Mittamidi 2026 | Aizawl | AHP+FR+Yc | AUC 0.89–0.905 |
| Monga & Ganguli 2026 | NEH 8 stations | Quantile reg | 490 events MDL E=−11.10+0.62D, 67% monsoon |
| Khan 2025 | National | AHP/FR/Yc | 109k slides, Nagaland 55% susceptible AUC 0.874–0.905 |
| IIT Mandi P-RIL 2026 | IHR | Ensemble+IMERG | 26k GSI, daily GEE |
| LHASA 2.0 2021+ | Global | XGBoost | 1 km, 2× v1 |

### 10.2/10.3 (cited, unverified live)

Papers 11–23 in Appendix C retained but unverified specific accuracies — do not cite live without pulling original.

Key physics verified: Dahal & Hasegawa 2008 `I=73.90 D^-0.79` >144 mm/d, Marino 2020 soil moisture LEWS, Iverson 2000 Richards, Springman 2013.

---

## 11. Competitive Positioning

**One-liner:** “Thresholds say it rained. TALUS says which slope, why (TreeSHAP), who acts (4 roles, 5 langs), which road to avoid (R2) — on real measured ground.”

**3 answers:** (1) GSI RLFS = thresholds, we add AI+soil+satellite+per-slope they requested. (2) No NER system does role+road+routing+offline — we do. (3) Not “risk is high” but “close R4, evacuate S1 first, stage at Ranipool, divert valley.”

**NOT claiming:** replacing GSI, InSAR, IoT sensors, exact time/place, production accuracy — prototype with listed limits (§1, limitations).

---

## 12. Roadmap & Next Steps — UPDATE 2025-11-14 (built `0.1.0`, `35/35`)

### 12.1 Phase 0: Data assembly — DONE (3 corridors)

| Task | Source | Status |
|---|---|---|
| IMD 0.25° 1901–2024 (124 files `ind*.nc`) | `data/raw/imd/` → NGEN windows 2024-06-16/07-08/06-17 + live Open-Meteo + IMD-live gated | ✅ |
| SRTM 30m | `n27_e088_1arc_v3.tif` → `usgs_s234.json` + derivatives (TWI/SPI) | ✅ |
| GSI Bhusanket NER | `GSI_Landslide_Inventory.shp.zip` + PDF → 764 Sikkim / 2936 training | ✅ |
| Soil CCI v09.2 1978–2024 + SWI | `gangtok_soil_cci.csv` + `swi.py` L1=15 L2=60 L3=60 | ✅ |
| Sentinel-2 NDVI/LULC + wound | `S2B_45RXL 20241129` + WorldCover N27E087 → 2 scars `wound_map.json` | ✅ |
| Lithology | Bhukosh WFS timeout 15s → PROXY `lingtse_granite_gneiss` uniform, omitted from X | ✅ |
| OSM roads/rivers | 1014/226/504 ways `roads_osm_provenance.json` (demo topology) + runout 85 buildings | ✅ |
| Quakes | USGS 26 M5+ `usgs_quakes.json` + seismic feats | ✅ |
| Terrain feats | `usgs_s234.json` + `catchment_s234.json` (slope/aspect/curv/TWI/SPI) | ✅ |

### 12.2 Phase 1: Core ML — DONE

Feature matrix 2936×22 → train RF/XGB/LGBM GroupKFold8 → AUC 0.9338/0.9418 + Brier 0.0971 + TreeSHAP top-5 → isotonic + Bayes 0.5→0.01.

### 12.3 Phase 2: Decision layer — DONE

GIS heatmap 5-band + role engine (4 roles, 5 langs) + road graph R1–R4 + R2 avoidance + warning 6-state + isolation R4 + TrendChart NOW + restrictions catalogue.

### 12.4 Phase 3: Platform — DONE

Field reporting (camera+GPS+offline outbox `talus_report_outbox`) + alerts app|sms (4 providers + auto watcher 60s/3600s) + PWA offline (sw.js + manifest 192/512) + live forecast + wounds/runout/replay.

### Timeline

```
2025-08  Data assembly (3 corridors, 12 slopes)
2025-09  Model sprint (2936 rows, GroupKFold 0.9338) → scaffold 89/78/66/52
2025-10  Warning + isolation + routing + PWA
2025-11-14  Frozen 0.1.0 — 35/35, Brier 0.0971, SWI 3-tank, 6-state — CURRENT_SYSTEM.md wins
Dec 2026  SIH Grand Finale (if selected)
```

---

## Appendix A: Key Numbers (2025-11-15)

| Metric | Value | Source |
|---|---|---|
| NER documented | 37,903+ / 91k India (33,904 validated) | GSI Bhusanket |
| ISRO Atlas | 80,000+ | NRSC |
| Dibang | 537 | Mihu 2026 |
| Meghalaya | 1,330+ | Agrawal/NEHU |
| NEH rain events | 490 | Monga 2026 |
| IMD stations | 8 (1980–2019) | IMD |
| Training | 2936 (1468+1468) | `feature_matrix.training.csv` |
| RF / XGB / LGBM OOF | 0.9338 / 0.9418 / 0.9406 | `metrics.md` GroupKFold8 |
| Brier isotonic | 0.0971 vs raw 0.118 (naive 0.25) | `calibration.md` |
| Temporal holdout | 673/73 dated, n=807 → 0.8568 | `metrics.md` |
| GSI RLFS | 21+ districts, CSI >70%, 2030 nationwide | GSI |
| OSM roads | 1014/226/504 ways | `roads_osm_provenance.json` |
| GIS | SRTM n27_e088 30m, CCI v09.2 1978–2024, Sentinel-2 2 scars, USGS 26 quakes | evidence/ |
| Scaffold | 89/78/66/52 S1–S4 | `check_scaffold.py` |
| Tests | 35/35 | `pytest -q` |

## Appendix B: Data Download Checklist (N E R — 2025-11-15)

- [x] IMD gridded 0.25° 1901–2024 NER bbox + live Open-Meteo + IMD-live gated
- [x] SRTM 30m n27_e088 + derivatives (slope/aspect/curv/TWI/SPI)
- [x] CCI v09.2 1978–2024 + SWI 3-tank L1=15 L2=60 L3=60
- [x] Sentinel-2 NDVI/LULC + wound 2 scars + runout 85 buildings
- [x] GSI Bhukosh lithology (PROXY, uniform) + Bhusanket 2936 training
- [x] NASA COOLR + GSI 91k + ILSM 154k (reference)
- [x] OSM roads 1014/226/504 + rivers + buildings
- [x] USGS quakes 26 + seismic feats
- [x] Live APIs: Open-Meteo + IMD data.gov.in (key-gated)
- [ ] Per-slope in-situ rain/soil sensors (adapter ready, fixture mode)

## Appendix C: References (as of 2025-11-15)

1. SIH26001 PS — MDoNER
2. GSI RLFS — bhusanket.gsi.gov.in
3. GSI NLFC NIDM 2026 — nidm.gov.in
4. Lok Sabha Q664 22.07.2026 — sansad.in
5. Mihu et al. 2026 — Dibang LSM, Springer
6. NEHU 2026 — Meghalaya, Times of India
7. Monga & Ganguli 2026 — NEH MDL thresholds, J. Hydrologic Eng.
8. Sarma & Paul 2026 — Mizoram, Zenodo
9. Agrawal & Dixit 2021 — Meghalaya LSM
10. Khan et al. 2025 — National LSM 90m (10.1038/s41598-025-33446-0)
11. Mittamidi et al. 2026 — Aizawl AHP+FR+Yc
12. IIT Mandi P-RIL 2026 — ET
13. Nagaland Eliona 2026 — India Today NE
14. ASDMA-GSI MoU 2024 — BS
15. GSI DG 2025 — ET
16. ISRO Landslide Atlas 2023 — nrsc.gov.in
17. ILSM Catena 2024 — Zenodo
18. Brahmaputra-CoPilot IJRASET 2025 — simulation only
19. Amrita A-LEWS — amrita.edu
20. SCS Tech — scstechindia.com
21. NASA LHASA 2.0 — github.com/nasa/LHASA
22. TALUS CURRENT_SYSTEM.md 2025-11-14 — single source of truth
23. TALUS metrics.md 2026-09-15 — GroupKFold 0.9338
24. TALUS calibration.md — Brier 0.0971
25. TALUS RECALIBRATION_NOTE.md — Bayes 0.5→0.01 + SWI

---

**2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched):**

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT
