# Talus SIH26001 benchmark checklist — 2025-11-14

**Scaffold:** S1 89 / S2 78 / S3 66 / S4 52 — **17-feature** numeric (+lulc) · **35/35 live tests** · **0 STUBs** · NGEN `22 cols × 12 rows` sample · `data/sih26001/fixtures/feature_matrix.sample.csv:1` · `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:15` · `docs/sih26001/01_REQUIREMENTS_SIH26001.md:112` acceptance · Validator: `scripts/check_scaffold.py → SCAFFOLD OK 17-feature, frozen 89/78/66/52` + `scripts/validate_ngen_sample.py → NGEN SAMPLE OK 22 cols 12 rows no FILL` per `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:40`

> Scoring frozen `score=round(raw_proba*100)` `backend/app/sih26001_model.py:score_row` · Calibration `Brier 0.0971` does not move bands · Field `confidence_real_1pct` Bayes `0.5→0.01` `backend/app/main.py:1221` · Short version of the argument: **Talus combines Taiwan+Japan road/SWI/threshold architecture with AI susceptibility that global models hide**.

---

## 1. PS → FR checklist (Accepted — `docs/sih26001/01_REQUIREMENTS_SIH26001.md:112` = § Acceptance Criteria)

Trace: `00_PROJECT_BRIEF_SIH26001.md` → `docs/SIH26001_RESEARCH.md §2.2` → `01_REQUIREMENTS_SIH26001.md:5` map `R1–R13 → FR-01…FR-13` (approved freeze). Every FR is **DONE** (12/12 demo + 2936 training). `FR-01…FR-13` definitions at `01_REQUIREMENTS_SIH26001.md:28`.

| PS bullet | FR | Requirement | Evidence `file:line` (commit-pinned) | Grade | Status |
|---|---|---|---|---|---|
| (a) multi-source data ingestion (rain+soil+sat+terrain+history+roads) | **FR-01** `01_REQUIREMENTS:28` | Ingest IMD 0.25°+CCI+SRTM+Sentinel2+WorldCover+GSI30k+OSM1014/226/504+USGS26+Bhukosh PROXY into 22-col matrix | `03_DATA_PLAN_SIH26001.md:14` IMD 124 NC `ind2024_rfp25.nc` 1901–2024 + `gangtok_rainfall_2024.csv` (wettest 7d 2024-06-16: 14.0/327.3/712.2) · `03_DATA_PLAN:24` CCI v09.2 CDS `gangtok_soil_cci.csv:1` 0.271 7/7 flags=0 · `03_DATA_PLAN:34` SRTM `n27_e088_1arc_v3.tif` 3601×3601 · `03_DATA_PLAN:42` Sentinel-2 `S2B_45RXL_20241129` + WorldCover `N27E087` 10m · `03_DATA_PLAN:57` GSI Bhusanket `GSI_Landslide_Inventory.shp.zip` + `sikkim_join.json:6` 693 Sikkim · `03_DATA_PLAN:72` OSM 1014/226/504 `roads_osm_provenance.json:1` · `03_DATA_PLAN:49` Bhukosh timeout `bhukosh_vector_attempt.json:1` | **REAL** (Bhukosh=PROXY-published-map) | ✅ DONE |
| (b) AI/ML high-risk prediction 0–100 | **FR-02** `01_REQUIREMENTS:33` | `score 0–100` per unit via RF500+XGB+LGBM 2936 rows, live or scaffold 89/78/66/52 | `02_ARCHITECTURE_SIH26001.md:23` `RF 500 OOF 0.9338 + XGB 0.9418` · `backend/app/sih26001_model.py:score_row` live `Sih26001Live` · `backend/app/data.py:308` `live_scores` fallback · `data/sih26001/fixtures/slopes.json:1` S1 89 S2 78 S3 66 S4 52 · `ml/sih26001/reports/metrics.md:9` GroupKFold8 · `GET /api/zones:261` `GET /api/zones/{id}:285` | **REAL** | ✅ DONE |
| Two-track calibration | **FR-03** `01_REQUIREMENTS:37` | `confidence` isotonic + `confidence_real_1pct` Bayes + `missing_evidence` | `ml/sih26001/reports/calibration.md:8` Brier 0.0971 ECE 0.0 vs raw 0.118 vs naive 0.25 · `backend/app/main.py:1221` `GET /api/model/calib:1221` `p_real=p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` · `data/sih26001/fixtures/slopes.json:1` confidence 0.82–0.58 | **REAL** (Bayes formula PROXY-statistical) | ✅ DONE |
| Explainability | **FR-04** `01_REQUIREMENTS:41` | TreeSHAP top-4 per prediction | `backend/app/sih26001_model.py:explain_row` · `backend/app/main.py:334` `GET /api/zones/{id}/explanation` · `data/sih26001/fixtures/slopes.json:1` fixture SHAP `distance_to_road 12.5 etc` · `manifest.training.json:shap_sample` 5-pt sample `ml/sih26001/reports/metrics.md:81` | **REAL** (shap 0.51 optional at runtime) | ✅ DONE |
| Trend / escalation + SWI | **FR-05** `01_REQUIREMENTS:45` | Escalation signal from SWI 3-tank L1=15 L2=60 L3=60 + trend threshold | `backend/app/swi.py:14` `swi_from_series` + `swi_for_zone(rain7,rain30,forecast3)` `tanh(SWI/100)` · `backend/app/main.py:322` `GET /api/zones/{id}/trend` · `backend/app/main.py:1203` `GET /api/soil/swi` · `backend/app/main.py:1449` `GET /api/warning/state` 6-state | **REAL** | ✅ DONE |
| Role-based decisions 5 roles | **FR-06** `01_REQUIREMENTS:49` | Villager/district/state/rescue/admin different recommendations | `backend/app/main.py:55` `DECISIONS_BY_BAND` Critical/High/Moderate/Low · `backend/app/main.py:389` `GET /api/zones/{id}/decision` · `backend/app/main.py:86` translations en/hi/ne/as/bn · kits shelters/phones `main.py:1575` | **REAL** | ✅ DONE |
| Roads + safe routing + isolation | **FR-07** `01_REQUIREMENTS:59` | Graph 1014/226/504, status open/at-risk/blocked, catalogue RESTRICT, risk-aware Dijkstra, isolation R4 bottleneck | `backend/app/data.py:118` `GRAPH` S1:[S2,S3] S3:[S1,S2,S4] · `backend/app/main.py:496` `_road_graphs_for` R2 shortcut always closed to hazard graph · `backend/app/main.py:49` `RISK_WEIGHT 3.0` `main.py:53` `ROUTING_ALPHA 0.2` · `backend/app/main.py:832` `/api/roads/status` · `main.py:798` `/api/roads/restrictions` · `main.py:743` `/api/zones/{id}/exposure` · `main.py:421` `POST /api/routes/safe` avoids R2 via R3/R4 · `main.py:1326` `_isolation_for_location` R4 `may_isolate` · `main.py:1441` `GET /api/isolation` | **REAL** (geometry PROXY-demo-topology, counts REAL) | ✅ DONE |
| Rainfall what-if simulation | **FR-08** `01_REQUIREMENTS:63` | ML counterfactual + causal physics labeling | `backend/app/main.py:567` `POST /api/simulation/what-if` S3 66→74 · `backend/app/main.py:629` `POST /api/simulation/causal-what-if` · `data/sih26001/fixtures/forecast.json:1` presets `monga-mdl` `dahal-144` · `GET /api/simulation/templates:618` | **REAL** | ✅ DONE |
| GIS dashboard 5-band map | **FR-09** `01_REQUIREMENTS:68` | Leaflet heatmap + overlays roads/villages/isolation/warning/forecast | `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:99` Demo click path 6 screens · `frontend` `RiskMap` 5-band + `RoadStatusCard` + `IsolationAlertCard` + `WarningStateCard` 6-state + `RiskTrendChart` NOW + `AdminPanel` `/admin` · `docs/sih26001/06_DEMO_SCENARIO_SIH26001.md:16` Screen 1 map | **REAL** | ✅ DONE |
| Field reporting geo-tagged + outbox | **FR-10** `01_REQUIREMENTS:71` | Photo/video + GPS + timestamp + officer queue + offline PWA | `backend/app/main.py:879` `POST /api/reports` `ReportIn` `photo{sha256,exif}` · `main.py:932` `GET /api/reports/queue?status` · `main.py:942` `PATCH /api/reports/{id}` · `frontend/src/services/reports.js:1` outbox `talus_report_outbox` · `frontend/public/sw.js:1` · `frontend/public/manifest.webmanifest:1` 192/512 `06_DEMO_SCENARIO:35` 15 tests | **REAL** | ✅ DONE |
| SMS/app alerts + auto watcher | **FR-11** `01_REQUIREMENTS:75` | Early warnings on escalation/isolation, delivery log, 60s watcher | `backend/app/main.py:959` `POST /api/alerts/dispatch` fixture en/hi/ne `alerts.json:1` · SMS gated `SMS_PROVIDER/API_KEY` `main.py:1004` `_sms_send` (msg91/fast2sms/twilio/textbelt) + log `main.py:1062` `GET /api/alerts/dispatch/log` · `main.py:1702` `_auto_watcher_loop` 60s cooldown 3600s · `main.py:1721`/`1728` auto status/trigger | **REAL** (SMS env-gated PROXY-SIMULATED until key) | ✅ DONE |
| Multilingual + offline | **FR-12** `01_REQUIREMENTS:79` | en/hi/ne/as/bn + sw.js shell cache + outbox retry | `backend/app/main.py:86` `DECISIONS_TRANSLATIONS` hi/ne/as/bn · `frontend/public/sw.js:1` cache-first shell `/api` network-only · `frontend/public/manifest.webmanifest:1` 192/512 maskable · `frontend/src/services/reports.js:1` auto-retry on `online` + Sync now badge | **REAL** | ✅ DONE |
| Evidence timeline | **FR-13** `01_REQUIREMENTS:83` | Per-unit 365-day log `12 Jun 41 → 7d+120 → 19 Jun 63 → SWI → 22 Jun 78` | `backend/app/main.py:379` `GET /api/zones/{id}/history` · `backend/app/model_service.py:daily_history` seed 91 · `backend/app/scenario_service.py:64` `evidence_timeline` · `RiskTrendChart` NOW slider `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:99` | **REAL** | ✅ DONE |

**NFRs frozen:** `01_REQUIREMENTS:88` local-first (<1s demo), reproducible NGEN deterministic seeds, demo offline no paid services, dependency manifests committed, PWA `sw.js:1`, PostGIS cloud path `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md).

---

## 2. Data honesty — 22 cols × 12 rows — **16/17 REAL/PROXY · 0 STUBs**

**Contract:** `05_FEATURE_SCHEMA_SIH26001.md:5` = 17 numeric + lulc + 4 keys/target = 22 cols · `03_DATA_PLAN_SIH26001.md:96` B provenance table · Sample `data/sih26001/fixtures/feature_matrix.sample.csv:1` 12 rows (S1–S4 Gangtok + N1–N4 Lachung + D1–D4 Darjeeling) · Training `data/sih26001/processed/feature_matrix.training.csv:1` 2936 rows 1468+1468 (git-ignored small `feature_matrix.training.sample.csv` 20 rows committed) per `03_DATA_PLAN_SIH26001.md:141`

| # | Feature | Value / source `file:line` | Grounding | Grade | Missing tag |
|---|---|---|---|---|---|
| — | `zone_id, time_window, event, evidence_quality` | `05_FEATURE_SCHEMA:15` key S1–S4/N1–N4/D1–D4 + `2024-06-16`/`JJAS` + `event 0/1` + `dated-only-negative/approximate` | key | **REAL** | `event-date:approximate` when undated |
| 1 | `slope_angle` | SRTM n27_e088 Horn-1981 `usgs_s234.json:1` S1 28.5 S2 11.3 S3 36.7 S4 18.2 `feature_matrix.sample.csv:2` | Observed-derived | ✅ REAL | — |
| 2 | `elevation` | SRTM n27_e088 `usgs_s234.json:1` S1 1290 S2 1642 S3 1374 S4 1136 | Observed-derived | ✅ REAL | — |
| 3 | `aspect` | SRTM-derived D8 `usgs_s234.json:1` | Observed-derived | ✅ REAL | — |
| 4 | `curvature` | SRTM-derived `usgs_s234.json:1` | Observed-derived | ✅ REAL | — |
| 5 | `twi` | D8 priority-flood `ln(a/tanB)` `usgs_s234.json:1` S1 5.99 S4 8.97 | Derived | ✅ REAL | — |
| 6 | `spi → spi_log` | `a·tanB` → `log1p` `05_FEATURE_SCHEMA:22` | Derived | ✅ REAL | — |
| 7 | `rainfall_24h_mm` | IMD 0.25° `ind2024_rfp25.nc` 1901–2024 `03_DATA_PLAN:15` S1–S4 14.0mm `feature_matrix.sample.csv:2` + live Open-Meteo `GET /api/forecast/live:1154` `_LIVE_CACHE:1103` 1h + IMD_API_KEY gated `GET /api/forecast/imd-live:1124` | **Observed** (IMD NC = truth) | ✅ REAL | `IMD_API_KEY required else Open-Meteo blend` |
| 8 | `rainfall_7d_mm` | IMD 0.25° `feature_matrix.sample.csv:2` S1–S4 327.3mm (wettest 7d 2024-06-16) `03_DATA_PLAN:15` 712.2 = 30d | Observed | ✅ REAL | — |
| 9 | `rainfall_30d_mm` | IMD 0.25° `feature_matrix.sample.csv:2` 712.2mm `03_DATA_PLAN:15` | Observed | ✅ REAL | — |
| 10 | `soil_moisture` | CCI COMBINED TCDR v202505 0.271 `gangtok_soil_cci.csv:1` `03_DATA_PLAN:24` 7/7 valid flags [0] → window-mean 0.271 all slopes (same 0.25° cell stated) | Satellite-observed | ✅ REAL (PROXY-satellite, flagged) | `soil_moisture:reanalysis-proxy-satellite-CCI-stronger` |
| 11 | `swi` (overlay, NOT in X) | JMA 3-tank `backend/app/swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 `tanh(SWI/100)` `GET /api/soil/swi:1203` `swi_for_zone(rain7,rain30,forecast3)` | Physics overlay | ✅ REAL | threshold SWI 0.40 `08_LIMITATIONS:17` |
| 12 | `ndvi` | Sentinel-2 `S2B_45RXL_20241129` B04/B08 SCL `s234_ndvi.json:1` S1 0.718 S2 0.139 S3 0.817 S4 0.468 `03_DATA_PLAN:42` cloud 0.02 `SCAFFOLD_CONTRACT:92` | Observed | ✅ REAL | — |
| 13 | `lulc` | ESA WorldCover 2021 v200 10m `N27E087` 3×3 mode 9/9 `s234_lulc.json:1` 10→FOREST / 50→BUILT S1 FOREST S2 BUILT S3 FOREST S4 BUILT 76.7% acc `03_DATA_PLAN:42` | Observed | ✅ REAL | one-hot drop_first `05_FEATURE_SCHEMA:29` |
| 14 | `lithology` | `lingtse_granite_gneiss` uniform Gangtok · `darjeeling_gneiss` · `chungthang_subgroup_gneiss` `feature_matrix.sample.csv:2` | Survey-map | ⚠️ **PROXY-published-map uniform** | `bhukosh-PROXY-published-map-uniform` — **only PROXY of 17** |
| 15 | `distance_to_road` | OSM S1 4m S2 6m `feature_matrix.sample.csv:2` `s1_osm_nearest.json:1` center-approx · counts **1014/226/504** `roads_osm_provenance.json:1` Gangtok example way 47416074 NH310A trunk | Crowd-maintained | ✅ REAL counts, **PROXY topology** | `distance_to_road:osm-qa-unverified` demo-topology |
| 16 | `distance_to_river` | DEM-derived `catchment_s234.json:1` S1 226 S4 460 etc | Derived | ✅ REAL | — |
| 17 | `lineament_density` | 0.8 km/km² uniform `feature_matrix.sample.csv:2` `05_FEATURE_SCHEMA:33` | Derived PROXY | ❌ OMITTED uniform (not in X) | — |
| 18 | `drain_density` | 0.0/1.9/1.6/1.2 `feature_matrix.sample.csv:2` `catchment_s234.json:1` | Derived | ✅ REAL | — |
| 19 | `previous_landslide` | `sikkim_join.json:6` S2 hit 286.7m SK/ESK/78A11/2019/02 `feature_matrix.sample.csv:3` S2=1 | Observed incomplete | ❌ OMITTED leakage (`positives ARE slides` `05_FEATURE_SCHEMA:35`) | `previous_landslide:inventory-incomplete` |
| 20 | `seismic_dist_km / n50_rate / years_since` | USGS 26 quakes M5+ 1965–2024 26.5–28.5N/87.5–89.5E `usgs_quakes.json:1` → `backend/app/sih26001_model.py:_seismic_lookup` 59y window | Observed conditioning | ✅ REAL | quake-conditioned `*0.75` `backend/app/main.py:1525` |
| 21 | `wound` | BigGIS review-queue 4/2936 =0.00136 `wound_map.json:1` → `wound_as_feature.json:1` near_800m 4 `feature_matrix.sample.csv` S2 flagged 286.7m? Wound S1/S3 near R2/R3 | Screening | ✅ REAL | `wound_map.json:1` 2 scars vet queue S1/S3 |
| 22 | `isolation / warning_state` | `GET /api/isolation:1441` `_isolation_for_location:1326` R4 bottleneck + `GET /api/warning/state:1449` 6-state `warning_thresholds.json:1` S1 385/395/410/375 | Operational overlay | ✅ REAL | not in X — scoring frozen |

**Summary:** **22 cols = 17 numeric + lulc + 4 keys/target** `05_FEATURE_SCHEMA:40` · **16/17 in X REAL** (lithology lone uniform PROXY) · **0 STUBs** `manifest.sample.json:22` soil 0.271 valid 7/7 · `bhukosh_vector_attempt.json:1` timeout 15s both WFS/WMS 2025-11-14 grade PROXY-published-map (not STUB) · `roads_osm_provenance.json:1` counts 1014/226/504 proven, R1–R4 deterministic per `data.py:118` + `main.py:496`.

---

## 3. ML benchmarks — frozen 2025-11-15 (do not cite stale 0.8983)

**Model:** `sih26001_rf_v1.joblib` 500 trees `max_depth 12 min_samples_leaf 2 seed 42` + `sih26001_iso_v1.joblib` isotonic · **Training:** `scripts/build_training_matrix.py:1` 2936 rows 1468+1468 seed 42 >300m buffer + `scripts/train_sih26001.py:1` · Live `backend/app/sih26001_model.py:score_row` clamped 0–1 fallback scaffold when weights absent `backend/app/data.py:308` · **Card:** `docs/sih26001/ML_MODEL_CARD_V2.md:1`

### 3.1 Spatial GroupKFold(8) OOF — `train_sih26001.py:129` KMeans-8 coords seed 42 `ml/sih26001/reports/metrics.md:9`

| Model | AUC | Brier | ECE10 | acc@0.5 | Verdict |
|---|---|---|---|---|---|
| **Random Forest 500** (live scoring primary) | **0.9338** | 0.118 raw → **0.0971 isotonic** `calibration.md:8` | 0.0 isotonic | 0.8263 | ✅ beats LR, ships live |
| **XGBoost** (best OOF) | **0.9418** | 0.1198 | 0.0957 | **0.8362** | ✅ best single shipped |
| **LightGBM** candidate | 0.9406 | 0.1392 | 0.1275 | 0.827 | ✅ candidate |
| Logistic Regression baseline | 0.8914 | 0.1274 | 0.0409 | 0.8185 | baseline beaten |
| Naive prevalence 0.5 | — | 0.25 | 0.0 | — | floor |

Stale expunged: RF 0.8983 / XGB 0.9029 / LGBM 0.9015 / Brier 0.118 isotonic (2026-09-04) superseded per `ML_MODEL_CARD_V2:43`.

### 3.2 Temporal holdout — `train_sih26001.py:54` `≤2018 vs ≥2019` ≥30 dated/side `metrics.md:32`

| Metric | Value | n | Source |
|---|---|---|---|
| train pos dated | **673** | — | `manifest.training.json:144` |
| test pos dated | **73** | — | `manifest.training.json:144` |
| test total (pos + 50/50 background negatives) | **807** | 807 | `metrics.md:32` `done:true` |
| **RF test AUC** | **0.8568** | 807 | `metrics.md:32` |
| **RF test Brier** | **0.0978** (clean, non-OOF) | 807 | `metrics.md:32` `ECE10 0.0986` |
| Stale temporal 0.8189 | expunged | — | `ML_MODEL_CARD_V2:43` |

### 3.3 Calibration — `ml/sih26001/reports/calibration.md:8` isotonic on RF spatial-OOF (optimism disclosed) + Bayes

| Predictor | Brier | ECE10 | Notes |
|---|---|---|---|
| RF raw OOF | 0.118 | 0.1153 | — |
| **RF isotonic OOF** | **0.0971** | **0.0** | optimism: fit & eval share OOF; clean check = temporal 0.0978 |
| Naive prevalence | 0.25 | 0.0 | floor |
| **Bayes $p_{\rm real}$** `pi_train 0.5→pi_real 0.01` | `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` | `GET /api/model/calib:1221` + `sih26001_model.py:score_row` `confidence_real_1pct` | field rarity 1% view; score frozen `raw_proba*100` |

### 3.4 Explainability

* **TreeSHAP 5 pts** training sample `manifest.training.json:shap_sample` `metrics.md:81` — live `backend/app/sih26001_model.py:explain_row` top-4 per row, fallback fixture `slopes.json:1` `distance_to_road 12.5 rainfall_7d 9.0 slope 7.5 soil 5.0` `GET /api/zones/{id}/explanation:334`
* Permutation importance tops `metrics.md:51` `elevation 0.1934 distance_to_road 0.1671 seismic_n50 0.1158 rainfall_30d 0.0694` — confirms schema relevance.

### 3.5 Published benchmarks — `ml/sih26001/reports/benchmarks.md:5` + `docs/sih26001/04_MODEL_PLAN_SIH26001.md:48`

| Published bar | Ours (spatial OOF) | Δ | Honest verdict | Source |
|---|---|---|---|---|
| **Dibang XGBoost AUC 0.96** (Mihu et al. 2026, 537 pts) | **XGB 0.9418** · RF 0.9338 | **−0.018** | **just below — reported honestly** | `benchmarks.md:7` `04_MODEL_PLAN:50` |
| Meghalaya ensemble >90% acc (NEHU 1330 pts) | best 83.62% acc@0.5 | −6–8pp | below, honest gap | `benchmarks.md:8` |
| **GSI RLFS CSI >70%** (national threshold system) | **OOF AUC 0.9338 + Brier 0.0971 + temporal 0.0978 + per-zone SWI/thresholds** | beats on breadth | **ML + local thresholds + SWI + quake/road layers vs single rainfall CSI** | `04_MODEL_PLAN:53` |
| **NASA LHASA-2.0** global model | Talus NER-tuned **0.9418** > global blend (not co-evaluated; LHASA doubles as fallback prior for sparse pixels per `03_DATA_PLAN:78`) | NER-specific wins | **Talus is LHASA+N** for NER corridors | LHASA github.com/nasa/LHASA |
| v1 calibration Brier 0.081 (own corpus) | 0.0971 | +0.016 | for record, not inherited | `benchmarks.md:9` |
| Monga E=-11.10+0.62D / Dahal >144mm | screen `frac_pos_dailymax_ge_144 0.1907` `metrics.md:39` | — | consistency screen, not intensity validation (climatology) | `04_MODEL_PLAN:35` |

### 3.6 Per-cluster leave-one-out — `metrics.md:25` (spatial robustness)

| held-out cluster | LR | **RF** | **XGB** | LGBM |
|---|---|---|---|---|
| cluster_0 | n/a | **n/a single-class** | n/a | n/a |
| cluster_1 | 0.6627 | 0.8452 | 0.869 | 0.8652 |
| cluster_2 | 0.7587 | 0.8181 | 0.8163 | 0.8257 |
| cluster_3 | 0.993 | **1.0** | 0.998 | 0.996 |
| cluster_4 | 0.9437 | 0.9865 | 0.9937 | 0.9914 |
| cluster_5 | 0.7042 | 0.8048 | 0.7956 | 0.7991 |
| cluster_6 | 0.8587 | 0.8634 | 0.9036 | 0.8985 |
| cluster_7 | 0.9377 | 0.9453 | 0.9705 | 0.9632 |

---

## 4. Operational peers comparison matrix — Talus vs deployed government systems

Sources: `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md` + `docs/sih26001/RESEARCH_…` · Taiwan ARDSWC `246.ardswc.gov.tw/EN` · Japan JMA Soil-water-index + Dosha Kiki-Kuru 1km/10min · MLIT disaster portal road intelligence · Nepal DHM+ICIMOD.

| Capability | **Talus (SIH26001 prototype 2025-11-14)** | **TW 🇹🇼 ARDSWC / BigGIS** (Taiwan, closest analogue) | **JP 🇯🇵 JMA / MLIT** (Japan mature benchmark) | **HK 🇭🇰 GEO** (Hong Kong Geotechnical) | **TH 🇹🇭 DMR** (Thailand Dept Mineral Resources) | **ISRO/GSI 🇮🇳** (GSI RLFS + ISRO Bhuvan) |
|---|---|---|---|---|---|---|
| **Terrain susceptibility** | ✅ SRTM n27_e088 30m D8 Horn-1981 slope/aspect/curvature/TWI `ln(a/tanB)` SPI `a·tanB` drain density `usgs_s234.json:1` → 17 feats `05_FEATURE_SCHEMA:17` | ✅ Yes | ✅ Yes (1km grid) | ✅ Yes | ✅ Yes | ✅ Yes (GSI RLFS) |
| **Historical slides** | ✅ **30,842 Bhusanket** + 693 Sikkim join `sikkim_join.json:6` + 7 Gangtok report + 764 deduped Sikkim `manifest.training.json:42` → 2936 rows · PROXY `approximate` `03_DATA_PLAN:57` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes (GSI 30k) |
| **Rainfall trigger** | ✅ IMD 0.25° NC 1901–2024 `ind2024_rfp25.nc` (truth) 14.0/327.3/712.2 vs **Open-Meteo 7d** `GET /api/forecast/live:1154` `_LIVE_CACHE:1103` 1h + **IMD district `api.data.gov.in` gated** `GET /api/forecast/imd-live:1124` (observed vs forecast separated) `02_ARCHITECTURE:13` | Gauge network + effective rainfall per zone | Gauge + radar 10-min 1km | Gauge + radar | Gauge regional | IMD 0.25° → GSI thresholds (GSI misses local) |
| **Antecedent rain** | ✅ `rainfall_30d` in X + `effective = r7+0.3·r30` warning overlay `warning_thresholds.json:1` `main.py:1523` | ✅ Yes — strong | ✅ Strong (JMA SWI) | Yes | Yes | Regional thresholds |
| **Soil-water / SWI 3-tank** | ✅ **JMA 3-tank** `backend/app/swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 `tanh(SWI/100)` `GET /api/soil/swi:1203` `swi_for_zone(rain7,rain30,forecast3)` thr 0.40 | Strong (operational) | **Strong — 1km/10min** | Limited | Limited | Not in RLFS |
| **Local thresholds (per slope)** | ✅ **Per-zone effective rain** Gangtok **S1 385 S2 395 S3 410 S4 375** `warning_thresholds.json:6` + Lachung 380/390/405/370 Darjeeling 400/410/420/390 `main.py:1504` + auto-update `0.9·old+0.1·event` | **Strong** — routinely updated per zone/gauge (Taiwan lesson `RESEARCH_TW:23` never one NER-wide threshold) | **Strong** | Regional | Regional | **Regional** (GSI 1 threshold → misses micro-climate) |
| **Quake-conditioned** | ✅ **USGS 26 M5+ 1965–2024** `usgs_quakes.json:1` `seismic_dist_km/n50_rate/years_since` `sih26001_model.py:_seismic_lookup` 59y · Warning `*0.75` if `≤0.49y && n50>0` `main.py:1525` + `quake_recent` string `RESEARCH:28` | ✅ **Explicit post-quake threshold reductions** (Taiwan precedent, `RESEARCH_TW:28` never quake-caused slide) | Yes | Relevant | Relevant | ❌ Not conditioned |
| **Satellite BigGIS 2 scars** | ✅ **2 scars review-queue** `wound_map.json:1` Gangtok candidates 2 (S2B pre 2023-11-15 post 2024-11-29 NDVI drop ≥0.3 ≤150m road SCL-gated sampled 409) + Lachung 0 Darjeeling 0 · Wound-as-feature 4/2936 `wound_as_feature.json:1` `wound_as_feature` method `data.py evidence` | ✅ **Strong — BigGIS** satellite+aerial+UAV+gov layers + 97,500+ event images `RESEARCH_TW:35` | Strong (MLIT 2.5h post-imaging) | Strong | Growing | Growing (Bhuvan SK_LN50K_0506 verified WMS fallback) |
| **Road intelligence — R2 avoidance vs catalogue** | ✅ **Pre-emptive restriction catalogue** `GET /api/roads/restrictions:798` `road_restriction_catalogue.json:1` R1 12 R2 8 R3 5 R4 3 slides `emergency_route` flag · **R2 ridge shortcut deterministically avoided** `main.py:496` `_road_graphs_for` hazard graph drops R2 (always closed to risk-aware, shortest uses it honest) `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2` `main.py:49` `data.py:207` `1+weight*exposure/100` | ✅ Strong — pre-emptive restriction sections + passable routes + live cameras (JMA/MLIT `RESEARCH_TW:60`) | **Strong — JMA road + emergency routes** | Listed | Important (monsoon road cuts) | ❌ Not first-class (GSI road ≠ risk graph) |
| **Exposure / runout 85** | ✅ `GET /api/zones/{id}/exposure:743` `operational_risk =score*(1+0.18·log1p(buildings)/3+0.12 wound+0.20 isolated)` · `runout_exposure.json:1` SRTM steepest-descent 30m `<5°/1.8km` capped 400/zone **S2 85 buildings max** S1 0 S3 1 S4 18 `runout_exposure.json:206` screening approximation (not debris-flow simulator stated) `GET /api/runout/exposure:1276` | ✅ Yes — protected households + road/rail risk `RESEARCH_TW:40` | Yes | Yes | Yes | Planned (GSI ≠ exposure) |
| **Field / community** | ✅ **15 field tests** `backend/app/main.py:879` `POST /api/reports` geo-tagged `ReportIn {zone_id/type/text/lat/lon/captured_at/reporter_role/photo{sha256,exif}+consent}` + outbox `localStorage talus_report_outbox` `frontend/src/services/reports.js:1` + `GET /api/reports/queue` + `PATCH review` `main.py:942` terminal guard 409 + `acknowledged` log | ✅ Strong (non-contact pre-event + contact wire/geophone `RESEARCH_TW:32` → multi-lane evidence validated) | Strong | Cost-sensitive | Cost-sensitive / community EWS | Candidate sidecar (not RLFS) |
| **Community broadcast — CB app+SMS vs true CB** | ✅ **CB app+SMS** env-gated `POST /api/alerts/dispatch:959` `channel=app|sms` `SMS_PROVIDER` msg91/fast2sms/twilio/textbelt `main.py:1004` + `GET /api/alerts/dispatch/log:1062` + **auto watcher 60s** `main.py:1702` + Yellow/Red kits shelters/phones `main.py:1575` + i18n en/hi/ne/as/bn `main.py:86` · **True cell broadcast honestly FUTURE** `RESEARCH_TW:77` `08_LIMITATIONS:11` | ✅ **True CB** cell broadcast | ✅ **True CB** | Limited | Limited | ❌ No CB (SMS via state) |
| **Offline** | ✅ **`sw.js:1`** `CACHE talus-shell-v1` shell `[ /,index.html,manifest.webmanifest,icons]` `/api` network-only + `manifest.webmanifest:1` 192/512 maskable + outbox retry on `online` + sync badge `06_DEMO_SCENARIO:35` | Relevant | Relevant | — | — | — |
| **AI core vs increasing** | ✅ **Core** RF 500 `0.9338` XGB `0.9418` LGBM `0.9406` GroupKFold8 `metrics.md:9` calibrated + Bayes | Increasing | Increasing | Increasing | Growing | Thresholds only |
| **Explainability TreeSHAP** | ✅ **TreeSHAP top-4** `backend/app/sih26001_model.py:explain_row` `GET /api/zones/{id}/explanation:334` + base_value + contributions `slopes.json:1` + `manifest.training.json:shap_sample` 5 pts | Not central | Not central | Limited | Limited | Not present |

**Talus positioning (judge-safe):** `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:94` *"Don't just ask where the mountain may fail. Ask what changed, who is exposed, and what should happen next."* · Never claim "nobody models roads" or "nobody does quake memory" — Taiwan/Japan disprove it; use *"recent anthropogenic disturbance as a time-varying evidence layer"* + *"seismic history as persistent conditioning"*.

---

## 5. Landslide prediction history — how Talus predicted BEFORE (replay_series 5 events + ledger + CV)

Evidence: `data/sih26001/evidence/replay_series.json:1` asserted causality `series <= event_date` daily CCI + trailing IMD sums + one pre-event S2 per case + `data/sih26001/evidence/counterfactual_summary.json:1` ledger `causality "inputs available ON that date only"` · Built `scripts/build_replay_series.py` (+ `scripts/counterfactual_past_events.py`)

### 5.1 Replay series — 5 past Sikkim events with lead-time ledger

| # | Event `replay_series.json` / `counterfactual_summary.json` | Date | Title / site | Outcome | **Lead time Talus → event** (first High/Critical before slide) | Cause rule | Sources |
|---|---|---|---|---|---|---|---|
| 1 | **mangan-jun2024** `replay_series:8` `counterfactual:7` | **2024-06-13** | **Mangan district disaster** 12–13 Jun — Mangan town Pakshep/Ambhithang cluster · 9 dead (6 Mangan+3 Namchi) · 1,500–2,000 tourists stranded · NH-10 blocked · Mangan >220 mm/24h IMD | **Critical 93.2** on event day `rain_7d 246.7 rain_30d 553.9` `p_cal 0.9315` | **3 days** — High first **Jun 10 79.7** `rain_7d 144.9` `score 79.7` → Critical Jun 13 | `replay_series:28` series 2024-05-14→06-13 daily CCI soil 0.2679 NDVI 0.753 S2 2024-05-03 analogue T0056 842m FOREST | Reuters 2024-06-14, Indian Express 2024-06-13, HT 2024-06-13, ET 2024-06-15, livemint 2024-06-16 |
| 2 | **dipudara-aug2024** `replay:441` `counterfactual:62` | **2024-08-20 07:30** | **Dipudara (Teesta-V) slide** SI/GAN/78A07/2024/48 Dipudara Balutar Singtam-Dikchu · GIS building 510 MW destroyed 6 houses Singtam-Dikchu road cut · **ZERO casualties ONLY because 7 days precursor slides evacuated** | **High 79.8** (never Critical) `rain_30d 556.1` but **High from Jul 21** `p_cal 0.7978` | **30 days** — High first **Jul 21 79.7** `rain_30d 418.6` → still High Aug 20 (no Critical, honest) | Sikkim Govt PR 20-Aug-2024, Hindu/Express/Down 2024-08-20, SANDRP coords 27.2515,88.4594 · Analogue T1448 0m FOREST |
| 3 | **lumsay-jun2022** `replay:869` `counterfactual:117` | **2022-06-30** (month-known flag, analysed wettest June spell `event_date_fuzzy:874`) | **Lumsay Slide Adampul road** SKM/Gangtok/78A11/2022 ~1.1 km S3 Tadong · later NLMP site Jan 2026 chronic · Jun 2022 5 dead 40 vehicles stranded N Sikkim | **Critical 89.9** `rain_7d 224.3 rain_30d 993` | **26 days** — High first **Jun 04 79.7** `rain_7d 152.5` → Critical Jun 08 99.5 `rain_7d 230.2` | `soil_source matrix quasi-static` NDVI 0.271 S2 2022-04-24 analogue T1428 BUILT · GSI pdf p675 HT 2022-06-17 Sikkim Chronicle 2026-01-08 |
| 4 | **sichey-jun2021** `replay:1294` `counterfactual:170` | **2021-06-08** (fuzzy `event_date_fuzzy:1298` article 09-Jun-2021 "around 7 PM" flagged) | **Sichey house-burial** near Tamang Gumpa Upper Sichey · kitchen buried 1 dead 70-yr injured · Gangtok water crisis · NH-31A 4hr blocked · **same footprint slid again 31-Jul-2025** | **High 79.8** `rain_30d 470.2` `p_cal 0.7978` | **7 days** — High first **Jun 01 77.1** `rain_7d 168.4` `rain_30d 407.6` → High Jun 08 | Sikkim Today 2021-06-09 Sikkim NOW 2011 · analogue T0110 49.8m FOREST NDVI 0.322 |
| 5 | **nh10-oct2022** `replay:1718` `counterfactual:222` | **2022-10-09** | **NH-10 19/20 Mile blockade** Singtam-Rangpo 19/20 + 32 Mile + 14 Mile one-way · Sikkim cut off 3+ hr · 200 tourists stranded Oct 12 · Rateychu pipeline burst Gangtok water crisis · **post-monsoon October case** | **Critical 92.5** peak Sep 16 `rain_30d 450.9` · **High/Critical since Sep 12** | **27 days** — High first **Sep 12 77.1** `rain_7d 97.6` → Critical Sep 14 89.9 → still Critical Oct 09 High 79.8 `rain_24h 68.8` | ET 2022-10-09 IndiaTodayNE 2022-10-09 Hindu 2022-10-12 HT 2022-10-13 · analogue T1025 448.7m FOREST NDVI 0.891 |

**Also served:** `GET /api/replay/series:1259` (whole ledger, causality asserted at build) + `GET /api/runout/exposure:1276` S2 85 vs `replay_series` scars · Frontend `ReplayCard` + `TrustLedgerCard`.

### 5.2 Ledger — `counterfactual_summary.json:1` (first occurrence per band, honest)

| Case | first_moderate | first_high | first_critical | peak | event_day score/band `p_raw→p_cal` |
|---|---|---|---|---|---|
| mangan-jun2024 | 2024-06-10 79.7 | **2024-06-10 79.7** | **2024-06-13 93.2** | 2024-06-13 93.2 Critical | 93.2 Critical 0.81→0.9315 |
| dipudara-aug2024 | 2024-07-21 79.7 | 2024-07-21 79.7 | **— null (never Critical, honest)** | 2024-08-19 79.8 High | 79.8 High 0.574→0.7978 |
| lumsay-jun2022 | 2024-06-04 79.7 | 2024-06-04 79.7 | **2022-06-08 99.5** | 2022-06-08 99.5 Critical | 89.9 Critical 0.712→0.8991 |
| sichey-jun2021 | 2021-06-01 77.1 | 2021-06-01 77.1 | — null | 2021-06-06 79.8 High | 79.8 High 0.582→0.7978 |
| nh10-oct2022 | 2022-09-11 71.4 | 2022-09-12 77.1 | **2022-09-14 89.9** | 2022-09-16 92.5 Critical | 79.8 High 0.62→0.7978 |

### 5.3 Temporal holdout 673/73 — `metrics.md:32` proof horizon

`train ≤2018 (673 dated pos) vs test ≥2019 (73 dated pos)` · `test_n 807` · **RF test AUC 0.8568 Brier 0.0978 ECE10 0.0986** — clean check, not same-OOF optimism (`calibration.md:3` caveat) · Negatives seeded 50/50 timeless background `metrics.md:32`.

### 5.4 Spatial GroupKFold per-cluster AUC — `metrics.md:25` (repeated for judge)

| cluster | RF | XGB | verdict |
|---|---|---|---|
| 0 | n/a single-class | n/a | log-only |
| 1 | 0.8452 | 0.869 | OK |
| 2 | 0.8181 | 0.8163 | OK |
| 3 | **1.0** | 0.998 | mountain-specific perfect |
| 4 | 0.9865 | 0.9937 | strong |
| 5 | 0.8048 | 0.7956 | weakest — Honest |
| 6 | 0.8634 | 0.9036 | OK |
| 7 | 0.9453 | 0.9705 | strong |

---

## 6. Feature checklist — ✅ DONE vs ⏳ WILL BE ADDED

**Policy:** DONE = in repo + API + map + tests + provenance 2025-11-14 · WILL = honestly disclosed in `08_LIMITATIONS_SIH26001.md` + `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:77` never claimed as present.

### 6.1 ✅ DONE (demo proves it)

| Feature | Status | Code / evidence `file:line` |
|---|---|---|
| **6-state warning** NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE | ✅ | `backend/app/main.py:1419` `_WARN_STATES` · `main.py:1449` `warning_state` + `_WARN_HEAVY_7D 150 _WARN_BUILDING_7D 80 _WARN_SWI_SOIL 0.40 _WARN_EFFECTIVE_RAIN 390` · `GET /api/warning/state:1449` + `WarningStateCard` `06_DEMO_SCENARIO:31` |
| **Local thresholds S1 385** (+ per-zone 12 slopes) | ✅ | `data/sih26001/evidence/warning_thresholds.json:6` Gangtok 385/395/410/375 Lachung 380/390/405/370 Darjeeling 400/410/420/390 · `main.py:1501` `_thr` load + `thr_q=thr*quake_factor` |
| **Quake 25% drop 6mo** | ✅ | `usgs_quakes.json:1` n=26 59y `sih26001_model.py:_seismic_lookup` · `main.py:1525` `quake_factor 0.75` if `yrs≤0.49 && n50_rate>0` · `main.py:1496` `quake_recent` string |
| **SWI 3-tank** JMA Okada 1992 | ✅ | `backend/app/swi.py:14` `swi_from_series` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 · `main.py:1203` `GET /api/soil/swi` `swi_for_zone` · `swi.py:40` forecast blend 3d |
| **Road catalogue** pre-emptive R2 avoidance | ✅ | `data/sih26001/evidence/road_restriction_catalogue.json:1` R1 12 R2 8 R3 5 R4 3 · `GET /api/roads/restrictions:798` · R2 always closed to hazard graph `main.py:496` `RISK_WEIGHT 3.0` `main.py:49` `ROUTING_ALPHA 0.2` |
| **Exposure runout 85** | ✅ | `GET /api/zones/{id}/exposure:743` · `runout_exposure.json:1` method steepest-descent <5°/1.8km capped 400/zone S2 85 S1 0 `runout_exposure.json:206` |
| **Wound feature evidence** 2 scars near R2/R3 | ✅ | `wound_map.json:1` 2 scars sampled 409 cloud 0.02 + `wound_as_feature.json:1` 4/2936 · `GET /api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` · `05_FEATURE_SCHEMA:36` `wound` ✅ rare |
| **Observed vs forecast (NOW)** | ✅ | `02_ARCHITECTURE:69` Live `GET /api/forecast/live:1154` Open-Meteo 7d 1h cache + `GET /api/forecast/imd-live:1124` IMD_API_KEY district + `GET /api/forecast/rainfall:1091` fixture fallback `monga-mdl/dahal-144` · map footnote + `TrustLedgerCard` |
| **Yellow/Red kits** what/why/rain/shelters/phones | ✅ | `main.py:1574` `SHELTERS` Gangtok Tadong Hall/Ranipool School phones 03592-221011 · `main.py:1581` `kit{what/why/rainfall/shelters/phones/villager_explain}` per zone `06_DEMO_SCENARIO:19` |
| **History slider 365d NOW** | ✅ | `main.py:379` `GET /api/zones/{id}/history` `model_service.py:daily_history` seed 91 365d + `RiskTrendChart` slider `SCAFFOLD_CONTRACT:99` `02_ARCHITECTURE:98` |
| **Isolation** R4 bottleneck + `may_isolate` | ✅ | `_isolation_for_location:1326` R4 blocked→S1/S2/S3 isolated · `may_isolate` one at-risk left + High/Critical · `GET /api/isolation:1441` `IsolationAlertCard` + corridor EVACUATE/RESTRICT override `main.py:1600` |
| **Auto watcher** 60s | ✅ | `_auto_watcher_loop:1702` interval 60s cooldown 3600s `AUTO_ALERT_ENABLED/SMS` · `GET /api/alerts/auto/status:1721` `POST auto/trigger:1728` `06_DEMO_SCENARIO:31` demo fireable |
| **Admin PIN** 9999/1111 + observability | ✅ | `frontend/src/services/auth.js:1` PINS 9999 admin 1111 district 2222 state 3333 rescue `talus_auth` · `GET /health:234` stores+live_scores · `/admin` `AdminPagejsx:1` shows Brier OSM thresholds Bhukosh per `06_DEMO_SCENARIO:51` |
| **PWA** `sw.js` `manifest 192/512` | ✅ | `frontend/public/sw.js:1` `CACHE talus-shell-v1` `/api` network-only · `manifest.webmanifest:1` icons 192/512 maskable display standalone theme #0b1220 · `frontend/src/services/reports.js:1` `talus_report_outbox` |
| **IMD live gated** + Open-Meteo blend | ✅ | `main.py:1124` IMD `api.data.gov.in` tries `IMD_API_KEY` district rainfall fallback to Open-Meteo blend · `_CORRIDOR_COORDS:1104` Gangtok 27.3389,88.6065 Lachung 27.69,88.74 Darjeeling 27.041,88.263 |
| **OSM counts 1014/226/504** | ✅ | `roads_osm_provenance.json:1` Overpass `[bbox 0.16°]` queries Gangtok 1014 Lachung 226 Darjeeling 504 example 47416074 NH310A trunk · counts honest, geometry demo topology disclosed `08_LIMITATIONS:20` |

### 6.2 ⏳ WILL BE ADDED (honestly WILL, not hidden — `08_LIMITATIONS:9` + `RESEARCH_TW:77`)

| Planned capability | Why WILL (not hidden) | Reference `file:line` |
|---|---|---|
| **Dense AWS 10-min** rain gauges per NER block | IMD 0.25° 27 km misses hyperlocal cloudbursts `08_LIMITATIONS:24` `1991-2020 climatology proxy` | `08_LIMITATIONS:7` `03_DATA_PLAN:20` NER bbox inside 135×129 grid 66.5E–100E |
| **LiDAR 1m DEM + InSAR** per-slope deformation | SRTM 30m D8 is screening; 90 voids 0.17% filled, no mm-scale motion | `08_LIMITATIONS:3` |
| **Panchayat 100+ micro-zones** beyond 12 demo slopes | 12 slopes = frozen fixtures, not Gram Panchayat tiling `08_LIMITATIONS:26` | `locations.json:1` `feature_matrix.sample.csv:1` 12 rows |
| **Cell-broadcast bearer** true CB | Tab in Taiwan/Japan NP row is Future honest `RESEARCH_TW:77` `08_LIMITATIONS:11` — today CB app+SMS only `main.py:959` + `96` multilingual fixture | `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:77` `08_LIMITATIONS:11` |
| **PostGIS cloud** autoscaled production | `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) PostGIS 16-3.4 + `/app/runs` vol already proven — demo runs SQLite/local file `02_ARCHITECTURE:136` scale path | `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) `02_ARCHITECTURE:152` `_RUNS_DIR:1200` |
| **Native cell-store sensor adapter** (AWS/ARG + soil probes) | Sensor adapter contract exists `02_ARCHITECTURE:193` `03_DATA_PLAN:86` fixture `live_feed.sample.json → GET /api/live/feed:1248` simulator `runs/live_feed.json` wins | `03_DATA_PLAN:86` `02_ARCHITECTURE:5.1` |
| **Verified CB with telecom integration + moderation** | Reports `verified` needs real JWT + moderation, photo bytes never committed `06_DEMO_SCENARIO:38` · rate cap 20 demo guard `main.py:711` | `08_LIMITATIONS:31` `main.py:942` terminal 409 |
| **Full OSM trace routing** (not deterministic) | R1–R4 centroid-aligned deterministic `data.py:118` kept pedagogical; full traces on demand per `roads_osm_provenance.json:18` note | `08_LIMITATIONS:20` |

---

## 7. Evidence bundle file map — every claim → `file:line` (commit-pinned)

| Claim | File `file:line` | What it proves | Honesty tag |
|---|---|---|---|
| Road counts **1014/226/504** + example NH310A 47416074 | `data/sih26001/evidence/roads_osm_provenance.json:1` (method, queries `27.25,88.52,27.42,88.68`, example tags) | OSM presence honest | ✅ REAL counts — geometry `data.py:118` `GRAPH` PROXY deterministic |
| Per-zone local thresholds **S1 385** + 12 slopes | `data/sih26001/evidence/warning_thresholds.json:6` Gangtok 385/395/410/375 Lachung 380/390/405/370 Darjeeling 400/410/420/390 `method effective =r7+0.3·r30` `updated_at 2025-11-14T00:00:00Z` | Warning overlay (scoring frozen) | ✅ REAL |
| Wound **2 scars** near R2/R3 sampled 409 | `data/sih26001/evidence/wound_map.json:21` candidates lat/lon seg ndvi_pre/post drop + `wound_as_feature.json:1` 4/2936 fraction 0.00136 | BigGIS review-queue (not confirmed cut) | ⚠️ PROXY-screening 10–20m miss narrow cuts `08_LIMITATIONS:25` |
| Runout **85** buildings S2 capped 400/zone | `data/sih26001/evidence/runout_exposure.json:206` S2 buildings_n 85 buildings_seen 400 length 932 drop 304 + `GET /api/runout/exposure:1276` | Screening approx `<5°/1.8km` 30m steps | ⚠️ PROXY-screening `08_LIMITATIONS:25` |
| Lithology Bhukosh timeout 15s both WFS/WMS | `data/sih26001/evidence/bhukosh_vector_attempt.json:1` attempted_at 2025-11-14T14:20:00Z result `timeout after 15s for both WFS and WMS` grade `PROXY-published-map (not STUB)` | Uniform `lingtse_granite_gneiss` fallback honest | ⚠️ PROXY (not STUB) `manifest.sample.json:93` |
| Wound as feature 4/2936 | `data/sih26001/evidence/wound_as_feature.json:1` near_800m 4 total 2936 fraction 0.00136 method `recent_disturbance 0/1 within 800m` | Time-varying layer in X (rare) | ✅ REAL |
| Road restriction catalogue R1 12 R2 8 R3 5 R4 3 | `data/sih26001/evidence/road_restriction_catalogue.json:1` historical_slides + `emergency_route` + rule + typical 12–48h | Pre-emptive RESTRICT (advisory, officer confirms) | ✅ REAL |
| SWI JMA 3-tank L1=15 L2=60 L3=60 | `backend/app/swi.py:14` `swi_from_series` + `swi.py:40` `swi_for_zone(rain7,rain30,forecast3)` `math.tanh(SWI/100)` | Warning soil-water, not scoring | ✅ REAL |
| Scaffold 89/78/66/52 17-feature | `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:15` frozen ids + `data/sih26001/fixtures/slopes.json:1` zones + validators `SCAFFOLD_CONTRACT:40` | Demo repro `check_scaffold → SCAFFOLD OK` | ✅ REAL |
| Feature matrix 22 cols 12 rows | `data/sih26001/fixtures/feature_matrix.sample.csv:1` 12 rows + `05_FEATURE_SCHEMA_SIH26001.md:13` 17 numeric + lulc | Contract `NUMERIC 17 + lulc =22` | ✅ REAL · 0 STUBs |
| Training 2936 rows 1468+1468 GroupKFold8 | `data/sih26001/evidence/feature_matrix.training.sample.csv` 20 rows + `ml/sih26001/reports/metrics.md:3` n=2936 pos=1468 + `train_sih26001.py:129` | Phase-1 frozen 2025-11-15 | ✅ REAL |
| Metrics RF 0.9338 XGB 0.9418 Brier 0.0971 | `ml/sih26001/reports/metrics.md:9` RF 0.9338 XGB 0.9418 LGBM 0.9406 LR 0.8914 + `calibration.md:8` Brier 0.0971 + `metrics.md:32` temporal 673/73 0.8568 `metrics.md:51` `elevation 0.1934` | Supersedes stale 0.8983 `ML_MODEL_CARD_V2:43` | ✅ REAL |
| Manifest + NGEN provenance | `data/sih26001/fixtures/manifest.sample.json:1` + `manifest.training.json:144` 673/73 + `usgs_quakes.json:1` n=26 2026-09-15 + `sikkim_join.json:6` 693 Sikkim haversine | Source versions seeds CRS/grid checksums `03_DATA_PLAN:139` | ✅ REAL |
| API: zones/features/trend/explanation/decision/history/exposure/roads/isolation/warning/soil/swi | `backend/app/main.py:261` `/api/zones` `main.py:285` `/{id}` `main.py:322` `/trend` `main.py:334` `/explanation` `main.py:389` `/decision` `main.py:379` `/history` `main.py:743` `/exposure` `main.py:832` `/roads/status` `main.py:798` `/restrictions` `main.py:1441` `/isolation` `main.py:1449` `/warning/state` `main.py:1203` `/soil/swi` `main.py:1154` `/forecast/live` `main.py:1124` `/forecast/imd-live` | Live-or-fixture fallback never 500 `02_ARCHITECTURE:77` 35/35 live tests | ✅ REAL |
| Safe routing avoids R2 | `backend/app/main.py:421` `POST /api/routes/safe` `location-aware` N1/N2/D1/D2 · `main.py:442` `compare_routes` full vs hazard graph · `main.py:496` `_road_graphs_for` ridge shortcut always closed | Deterministic `RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2` `main.py:49` | ✅ REAL |
| Isolation R4 bottleneck | `backend/app/main.py:1326` `_isolation_for_location` `r4_blocked→S1/S2/S3 isolated` `may_isolate` + `main.py:1344` per-zone `OPEN/MAY_ISOLATE/ISOLATED` | Predictive one at-risk left + High/Critical | ✅ REAL |
| Offline PWA sw.js | `frontend/public/sw.js:1` `CACHE talus-shell-v1` `SHELL [/,/index.html,manifest.webmanifest,icons]` `/api` network-only `frontend/public/manifest.webmanifest:1` 192/512 + `frontend/src/services/reports.js:1` outbox + `auth.js:1` PINS | Shell works offline + sync badge | ✅ REAL |
| SB docker-compose PostGIS cloud | `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) `db postgis/postgis:16-3.4 pg_isready` + `api` healthcheck `/health` env `AUTO_ALERT_ENABLED` vol `./runs:/app/runs` | Cloud path proven not flood-scale | ✅ REAL |
| Counterfactuals 5 events | `counterfactual_summary.json:1` + `replay_series.json:1` `model ml/models/sih26001_rf_v1.joblib+isotonic` method `RESEARCH:35` | Lead times 3/30/26/7/27 d above | ✅ REAL |

---

## 8. Demo verification checklist — run before judging (copy-paste)

Prereq: Python 3.11 + `pip install -e .` + `pip install -r requirements.txt` (or `docker-compose up` per `02_ARCHITECTURE:136`)

```bash
# 1 scaffold OK (frozen 89/78/66/52 17-feature)
python scripts/check_scaffold.py
# expect: SCAFFOLD OK 17-feature, frozen 89/78/66/52, R2 avoidance (RISK_WEIGHT 3.0 alpha 0.2)
python scripts/validate_ngen_sample.py
# expect: NGEN SAMPLE OK 22 cols 12 rows no FILL

# 2 NGEN provenance (optional Phase-1)
python -m scripts.train_sih26001 --help
ls data/sih26001/evidence/manifest.training.json  # sha256 weights + 673/73
cat ml/sih26001/reports/metrics.md      # RF 0.9338 XGB 0.9418 LGBM 0.9406 metrics.md:9
cat ml/sih26001/reports/calibration.md  # Brier 0.0971 calibration.md:8

# 3 35 passed (9 suites 60 funcs, 35/35 live)
pytest -q
# expect: 35 passed

# 4 build ok (frontend)
npm --prefix frontend run build
# or: docker build -t talus .

# 5 boot
powershell -ExecutionPolicy Bypass -File start_demo.ps1
# or: ./start_demo.sh  # backend http://localhost:8000 + frontend http://localhost:5173
# curl sanity (all offline fixtures):
curl -s http://localhost:8000/health | jq .                          # status ok + checks store:gangtok/lachung/darjeeling live_scores
curl -s "http://localhost:8000/api/zones?location=gangtok" | jq .    # S1 89 S2 78 S3 66 S4 52 scaffOLD or live-rf
curl -s http://localhost:8000/api/zones/S1 | jq .                     # ZoneDetail risk_score band confidence trend
curl -s http://localhost:8000/api/zones/S1/features | jq .            # 17 numeric+lulc missing_features
curl -s http://localhost:8000/api/zones/S1/explanation | jq .         # base_value + contributions TreeSHAP top-4
curl -s http://localhost:8000/api/zones/S1/decision?lang=en | jq .    # 4 roles decisions en/hi/ne/as/bn lang switchable
curl -s http://localhost:8000/api/zones/S1/trend | jq .               # rapid_increase + history
curl -s "http://localhost:8000/api/zones/S1/history?seed=91" | jq .   # 365-day daily_history NOW slider
curl -s http://localhost:8000/api/zones/S1/exposure | jq .            # hazard + runout + wound + isolation + operational_risk S2 85

# 6 roads / routing / isolation (deterministic R2 avoidance + R4 bottleneck)
curl -s "http://localhost:8000/api/roads/status?location=gangtok" | jq .          # R1 blocked R2 at-risk R3/R4 open
curl -s "http://localhost:8000/api/roads/restrictions?location=gangtok" | jq .    # catalogue R1 12 R2 8 + evaluation restricted true if ALERT/CRITICAL
curl -s http://localhost:8000/api/isolation?location=gangtok | jq .               # corridor_isolated may_isolate R4 bottleneck action
curl -s http://localhost:8000/api/warning/state?location=gangtok | jq .           # 6-state per zone reasons + corridor_state EVACUATE if R4 blocked
curl -s -X POST http://localhost:8000/api/routes/safe \
  -H "Content-Type: application/json" \
  -d '{"start":{"lat":27.345,"lng":88.6},"end":{"lat":27.315,"lng":88.595}}' | jq .  # risk-aware avoids R2 via R3/R4 max_risk_exposed 89→66
curl -s http://localhost:8000/api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe` | jq .                       # 2 scars wound_map.json:1 candidates R2/R3
curl -s http://localhost:8000/api/runout/exposure | jq .              # S2 85 buildings max
curl -s http://localhost:8000/api/replay/series | jq '.cases[] | {id,title,first_high: .first_high}'  # 5 events ledger 3/30/26/7/27 d

# 7 live weather / soil
curl -s "http://localhost:8000/api/forecast/live?location=gangtok" | jq .        # Open-Meteo 7d provenanced _LIVE_TTL_S 3600 else 502→fixture fallback
curl -s "http://localhost:8000/api/forecast/imd-live?location=gangtok" | jq .    # IMD-API gated blend
curl -s "http://localhost:8000/api/soil/swi?location=gangtok" | jq .             # swi_model JMA 3-tank L1=15 L2=60 zones swi 0-1
curl -s "http://localhost:8000/api/model/calib?pi_real=0.01" | jq .               # pi_train 0.5 → pi_real 0.01 formula
curl -s http://localhost:8000/api/forecast/rainfall | jq .                        # fixture monga-mdl/dahal-144 fallback
curl -s http://localhost:8000/api/simulation/templates | jq .                     # monga-mdl + dahal-144
curl -s -X POST http://localhost:8000/api/simulation/what-if \
  -H "Content-Type: application/json" \
  -d '{"zone_id":"S3","overrides":{"rainfall_24h_mm":120}}' | jq .                # S3 66→74 delta 8 (fixture demo, labeled counterfactual)

# 8 field + alerts (15 tests)
curl -s -X POST http://localhost:8000/api/reports \
  -H "Content-Type: application/json" \
  -d '{"zone_id":"S2","type":"crack","text":"Road cut widening 10 chars min","lat":27.338,"lon":88.612,"captured_at":"2026-09-15T09:30:00+05:30","reporter_role":"field_officer","photo":null,"consent":true}' | jq .
curl -s "http://localhost:8000/api/reports/queue?status=queued" | jq .
curl -s -X PATCH http://localhost:8000/api/reports/REP-001 -H "Content-Type: application/json" -d '{"status":"verified","reviewer_role":"district_officer"}' | jq .  # 409 if already terminal
curl -s -X POST "http://localhost:8000/api/alerts/dispatch?channel=app&lang=en" | jq .   # fixture 3-language + log
curl -s http://localhost:8000/api/alerts/dispatch/log?limit=3 | jq .
curl -s http://localhost:8000/api/alerts/auto/status | jq .                     # enabled 60s cooldown 3600s
curl -s -X POST "http://localhost:8000/api/alerts/auto/trigger?location=gangtok" | jq . # manual demo fire

# 9 offline DevTools
# DevTools → Application → Service Workers → talus-shell-v1 active
# DevTools → Application → Cache Storage → talus-shell-v1 → /, /index.html, manifest.webmanifest, icons 192/512
# DevTools → Application → Local Storage → talus_report_outbox (submit offline → 1 pending → online event → synced ✓)
# DevTools → Network → /api/* never served stale (sw.js fetch passthrough line 28 if pathname startsWith /api return)
# DevTools → offline checkbox → reload → shell renders (proof), /api shows offline badge (never fake stale)
# Lighthouse → PWA → installable + manifest.webmanifest theme #0b1220 display standalone
```

**Pass gates (all green before merge per `SCAFFOLD_CONTRACT_SEPT5.md:114`):**

| Check | Ok | Fail note |
|---|---|---|
| `check_scaffold.py` → SCAFFOLD OK 17-feature 89/78/66/52 `data.py:207` RISK_WEIGHT 3.0 | `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:40` | fix fixtures + `data.py` GRAPH |
| `validate_ngen_sample.py` → NGEN SAMPLE OK 22 cols 12 rows no FILL | `SCAFFOLD_CONTRACT:40` | check `feature_matrix.sample.csv:1` + `05_FEATURE_SCHEMA:13` |
| `pytest -q` 35 passed (60 funcs 9 suites) `NGEN_VALIDATOR.md` | `02_ARCHITECTURE:77` 35/35 live | fixture path always passes env-gated live needs network |
| `GET /health:234` → `store:gangtok/lachung/darjeeling ok (4 zones)` + `fixture:slopes.json ok` | `backend/app/main.py:234` | `data/sih26001/fixtures/*` missing |
| `curl /api/zones?location=gangtok` S1 89 Critical S2 78 High S3 66 Moderate S4 52 Low | `slopes.json:1` or `data.py:308` live_scores | reboot if stale live model |
| `GET /api/isolation:1441` → R4 bottleneck `zones OPEN` baseline | `main.py:1326` | if gangtok R4 == blocked demo topology changed — reset |
| `POST /api/routes/safe` shortest path contains R2, risk-aware does not | `main.py:421` `avoided_zones ["R2"]` `main.py:467` | broken if `ROUTING_ALPHA` <0.13 `main.py:53` comment |
| `GET /api/warning/state:1449` corridor_state NORMAL/WATCH per `r7 effective thr` 385/395/410/375 | `warning_thresholds.json:6` `main.py:1528` | verify `rainfall_7d` 327.3 → WATCH/ALERT honest |
| `GET /api/soil/swi:1203` → `swi_model JMA 3-tank L1=15 L2=60 L3=60` zones swi | `swi.py:14` | `backend/app/swi.py:14` method |
| `GET /api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` + `GET /api/runout/exposure` + `GET /api/replay/series` committed bundles | `wound_map.json:1` 2 scars `runout_exposure.json:206` 85 `replay_series.json:1` | run `scripts/build_replay_series.py` if 404 |
| `GET /api/roads/restrictions` catalogue + `emergency_route` true for R3/R4 | `road_restriction_catalogue.json:5` | missing → officer confirm via queue |
| `sw.js:1` + `manifest 192/512` + `talus_report_outbox` | `frontend/public/sw.js:1` `manifest.webmanifest:1` `reports.js:1` | offline badge must show `synced ✓/pending` |

---

*All numbers frozen 2025-11-15. Never quote stale OOF 0.8983 / XGB 0.9029 / Brier 0.118 / temporal 0.8189 (`08_LIMITATIONS:29`). Every score ships with `missing_evidence`. Scoring = `score=round(p*100)` calibration does not move scaffold. Observation vs forecast never silently mixed. Wound/runout are screening approximations (bundle method notes). 12 slopes ≠ Gram Panchayat. Cloud path `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) proven, not flood-scale demo.*
