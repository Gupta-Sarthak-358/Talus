# TALUS Architecture — SIH26001

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Status:** Built — frozen 2025-11-15 · **Trace to:** `01_REQUIREMENTS_SIH26001.md`, `docs/SIH26001_RESEARCH.md` §8

v1 diagrams live in `docs/02_ARCHITECTURE.md` and stay authoritative for the mine track. This doc records the v2 mapping and deltas only.

---

## 1. System data flow (v2 — 2025-11-15 truth)

```text
Real NER sources (12-slope demo, 2936-row training)
 IMD 0.25° 1901–2024 │ CCI soil v09.2 1978–2024 │ SRTM n27_e088 │ Sentinel-2 NDVI │ WorldCover LULC
 GSI Bhusanket 30k + report PDF │ OSM roads/rivers 1014/226/504 (provenance.json) │ USGS 26 quakes
 Bhukosh PROXY uniform (timeout evidence) │ Open-Meteo 7-day live │ IMD_API_KEY gated district API
  ↓
NGEN PIPELINE (replaces synthetic generator)
 fetch → reproject → align grid → derive terrain → join → label → version
  (22-col sample, 17 numeric + lulc, wound feature 4/2936, per-zone thresholds)
  ↓
Feature Processing (12 demo rows ×22 cols + 2936 training)
  ↓
TALUS RISK ENGINE (live or fixture fallback) — FROZEN per E12+E14 (`EXPERIMENTS_E_LADDER.md`)
 ONE global scorer + regional calibration + regional warning policy (E14 collapsed
 the South branch: no operational edge at calibrated operating points).
 No specialists, no ensembles. RF500/XGB prod parity. Family (RF vs XGB) TBD.
  score 0–100 (frozen scaffold 89/78/66/52) + confidence + confidence_real_1pct
  → regional calibration → regional warning → hazard → exposure/risk → decision
  ↓
 Explainability (TreeSHAP top-4, backend/app/sih26001_model.py:explain_row)
 Isolation (_isolation_for_location:1326, R4 bottleneck, may_isolate)
 Warning 6-state (NORMAL→EVACUATE, SWI 3-tank L1=15 L2=60 L3=60)
 SWI (backend/app/swi.py:14) + Trend + Exposure operational risk
  ↓
Decision Engine (Yellow/Red kits, shelters/phones per corridor)
 Role-based actions · Road-status + risk-aware routing + restriction catalogue
  ↓
Field reports ↑↓ Alerts (SMS/app env-gated, multilingual en/hi/ne/as/bn, auto watcher 60s)
  ↓
NER GIS Dashboard (React + Leaflet) + Admin Panel (/admin PINs) + PWA field app (sw.js)
```

## 2. Module mapping (v1 → v2)

| v1 module | v2 module | Change |
|---|---|---|
| Generator (physics sim) | **NGEN** (NER data pipeline) | Complete rewrite — real data (IMD 0.25°, CCI v09.2, SRTM n27_e088, WorldCover, OSM 1014/226/504) |
| ML predictor | ML predictor | One global scorer + regional calibration (E14 collapsed E12 south branch: no operational FAR edge); 2936 rows 1468+1468 + E1.5b/E1.5c top-ups (experiment lane); OOF RF 0.9338 XGB 0.9418, temporal Brier 0.0978 |
| SHAP | SHAP | Same module, live TreeSHAP top-4 `sih26001_model.py:explain_row` |
| Calibration (isotonic) | Calibration | Same approach + Bayes prevalence correction 0.5→0.01 `GET /api/model/calib:1221` |
| Trend / escalation | Trend + SWI + Warning | New: SWI `swi.py:14` + 6-state warning + local thresholds 385/395/410/375 |
| Decision engine (4 mine roles) | Decision engine (4 NER roles + admin) | New role matrix + Yellow/Red kits + isolation-aware EVACUATE |
| Routing (zone graph) | Routing + Isolation (OSM graph) | New graph 1014/226/504 provenance + segment risk + R4 bottleneck isolation |
| Scenario engine (storm replay) | Scenario engine (rainfall + SWI + forecast) | New physics: Monga/Dahal + SWI blend + observed vs forecast separation |
| Evidence card | Evidence card | New provenance: CCI, WorldCover, OSM counts, Bhukosh timeout, quake conditioning |
| Alert system | Alert system + Auto watcher | SMS gateway env-gated + i18n en/hi/ne/as/bn + offline queue + `_auto_watcher_loop:1702` |
| Dashboard (mine map) | Dashboard (GIS heatmap + isolation + warning) | Rebuild: RiskMap 5-band + RoadStatusCard + IsolationAlertCard + WarningStateCard 6 + RiskTrendChart NOW |
| Backend API (FastAPI) | Backend API | Extended; live-rf vs fixture fallback, 35/35 tests |
| — | Field-reporting app | New: camera/GPS, offline PWA `sw.js`/`manifest.webmanifest` 192/512, officer queue |
| — | Admin panel | New: `/admin` health/isolation/log/provenance, PINs 9999/1111/2222/3333 |
| — | Cloud | New: `docker-compose.prod.yml:1` PostGIS 16-3.4 |

What survives unchanged: two-engine pattern (ML + physics scenario), isotonic calibration methodology, SHAP framework, role-escalation pattern, risk-weighted Dijkstra, missing-evidence transparency, test structure, offline-first philosophy.

## 3. Component deltas

### Backend (FastAPI) — built endpoints (frozen 2025-11-15)

```text
Health:  GET /health · GET /
Zones:   GET /api/zones?location=  GET /api/zones/{id}  GET /api/zones/{id}/features|/trend|/explanation|/decision|/history|/exposure
Live:    GET /api/live/feed  GET /api/live/audit  GET /api/forecast/rainfall (fixture)  GET /api/forecast/live (Open-Meteo 7d, 1h cache)  GET /api/forecast/imd-live (IMD_API_KEY gated)
Soil/Warn: GET /api/soil/swi  GET /api/warning/state (6 states, local thresholds, quake −25%)  GET /api/model/calib?pi_real=0.01 (Bayes)
Roads:   GET /api/roads/status?location=  GET /api/roads/restrictions  POST /api/routes/safe (R2 avoidance)  GET /api/isolation  GET /api/runout/exposure  GET /api/wounds
Risk/Sim: POST /api/risk/predict  POST /api/simulation/what-if (ML 66→74)  POST /api/simulation/causal-what-if  GET /api/simulation/templates  GET /api/replay/series
Reports: POST /api/reports (ReportIn: zone_id/type/text/lat/lon/captured_at/reporter_role/photo{sha256,exif}+consent → queued|flagged)  GET /api/reports/queue?status=  PATCH /api/reports/{id}
Alerts:  POST /api/alerts/dispatch?channel=app|sms  GET /api/alerts/dispatch/log  POST /api/alerts/ack  GET /api/alerts/ack  GET /api/alerts/auto/status  POST /api/alerts/auto/trigger
```

Live `backend/app/main.py:1` + `data.py:1` + `sih26001_model.py:1` + `swi.py:14`, `15` tests in `test_reports.py:1` + `60` funcs across 9 suites, validator `check_scaffold`. 35/35 live tests. v1 shapes intact.

Key engines:
- **Isolation** `main.py:1326` `_isolation_for_location` — per location `(full_graph, hazard_graph)` via `_road_graphs_for:496` (R2 ridge shortcut dropped from hazard graph), bottleneck R4 (`status R4==blocked ⇒ upstream S1/S2/S3 isolated`), `may_isolate` when `open_exits==0 && at-risk==1 && band High/Critical` or `R2 at-risk + upper High/Critical`.
- **SWI** `swi.py:14` JMA 3-tank `swi_from_series` + `swi_for_zone(rain7,rain30,forecast3)` — L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01, normalized `tanh(SWI/100)`, warning threshold 0.40.
- **Warning** `main.py:1449` 6 states, per-zone thresholds `warning_thresholds.json:1` (Gangtok 385/395/410/375), effective rain `r7+0.3*r30`, quake-conditioned `*0.75` if `seismic_years_since ≤0.49y && n50_rate>0` (26 USGS events), forecast exceedance (50mm day /150mm week), wound proximity, exposure stamping. Isolation overrides to EVACUATE/RESTRICT.
- **Recalibration** `sih26001_model.py:score_row` + `main.py:1221` — `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` for field 1% prevalence; score frozen from raw `p*100`, confidence stays prototype-calibrated.

### Frontend

```text
GIS Dashboard (React + Leaflet + Recharts)
 ├── RiskMap (5-band susceptibility, Leaflet polygons, RISK_BANDS)
 │    + RoadOverlay (status colors open/at-risk/blocked, deterministic R2 avoidance)
 │    + VillageLayer (settlements + priority flags + isolation badges)
 │    + Wound overlay (candidates from wound_map.json)
 │    + Runout screening (steepest descent, buildings downstream)
 ├── RiskSummaryCards / QuickStatsBar (corridor counts)
 ├── RiskScoreGauge (0–100 + confidence + confidence_real_1pct)
 ├── ShapChart (TreeSHAP top-4, live or fixture fallback)
 ├── MissingEvidenceCard (proxy/incompleteness tags)
 ├── RiskTrendChart NOW (365-day slider, GET /api/zones/{id}/history:379)
 ├── RoleActionCard (Yellow/Red kit: what/why/rain/shelters/phones)
 ├── RoadStatusCard (segments + restriction catalogue evaluation)
 ├── RouteComparisonCard / SafeRouteModal (shortest vs risk-aware, haversine km, avoided_zones)
 ├── WarningStateCard (6 states NORMAL→EVACUATE, reasons stamped, isolation override)
 ├── IsolationAlertCard (OPEN/MAY_ISOLATE/ISOLATED per zone, bottleneck R1–R4, action)
 ├── WarningStateCard + IsolationAlertCard → corridor_state badge
 ├── TrustLedgerCard + ReplayCard + LiveFeedCard (observed vs forecast ledgers)
 ├── Simulation / WhatIfDrawer + SimulationDiffCard (baseline/simulated, flagged off-manifold)
 └── AdminPanel (/admin, PIN 9999/1111/2222/3333, health + isolation + dispatch log + provenance)

Field app (PWA — reporting lane LIVE on backend, UI via reports.js outbox)
 ├── Capture (photo/video + GPS + timestamp, offline — ReportModal + PhotoMeta {sha256,exif_lat,exif_lon} + consent + pilot-bbox gate)
 ├── Queue (pending sync — GET /api/reports/queue?status= + PATCH review queued|flagged→verified|dismissed, terminal guard)
 └── Alerts (cached warnings, local language) + sw.js cache-first shell

Offline: public/sw.js:1 (CACHE talus-shell-v1, SHELL [/,/index.html,manifest.webmanifest,icons], /api network-only)
        public/manifest.webmanifest:1 (name TALUS, icons 192/512 maskable, display standalone, theme #0b1220)
        frontend/src/services/reports.js:1 (PHOTO_STORE_KEY + OUTBOX_KEY talus_report_outbox, auto-retry on online + Sync now)
        frontend/src/services/auth.js:1 (PINS villager ''/1111/2222/3333/9999, localStorage talus_auth)
```

### NGEN (no v1 equivalent)

```text
ngen/
 ├── fetch/ (IMD 0.25° ind2024_rfp25.nc 1901–2024, CCI v09.2 CDS 1978–2024, SRTM n27_e088, Sentinel-2 S2B_45RXL, WorldCover N27E087, Bhusanket 30k + report PDF, OSM Overpass 1014/226/504 + provenance.json, USGS quakes 26, Bhukosh WFS timeout probe)
 │         + live: Open-Meteo 7-day (daily precipitation_sum/probability_max, 1h cache) + IMD_API_KEY data.gov.in district rainfall gated
 ├── preprocess/ (reproject to EPSG:4326, resample, cloud-mask SCL, QA flag bits 4|8|16|32)
 ├── terrain/ (Horn-1981 slope/aspect, curvature, TWI D8 priority-flood ln(a/tanB), SPI a*tanB, drain density — usgs_s234.json)
 ├── join/ (spatial join to 12 demo points + 2936 training grid, temporal join JJAS season-window proxy tagged approximate)
 ├── label/ (positive = event location+season window; negative = >300m buffer seed 42, 1468+1468)
 ├── features/ (spi→spi_log, encoder ColumnTransformer, 17 numeric + lulc one-hot drop_first → sih26001_rf_v1.joblib + iso)
 └── version/ (manifest.sample.json:1 + manifest.training.json + warning_thresholds.json + roads_osm_provenance.json + bhukosh_vector_attempt.json + usgs_quakes.json, seeds, CRS/grid, checksums)
```

Deterministic: fixed seeds 42, pinned source versions, manifests committed. Raw downloads out of git (`.gitignore` LOCAL ONLY), small samples in-repo (`feature_matrix.sample.csv:1` 22 cols, `feature_matrix.training.sample.csv` 20 rows).

## 4. Deployment (prototype → cloud)

```text
Browser / field device (PWA: sw.js shell cached, /api network-only, outbox talus_report_outbox)
 │
 ▼
React GIS dashboard + Admin /admin + PWA field app
 │ REST / JSON (CORS_ORIGINS *)
 ▼
FastAPI (local or containerized)
 ├── Live RF+isotonic (ml/models/sih26001_*v1.joblib, sklearn 1.9 pickle compat shim)
 ├── Isolation (_isolation_for_location, R4 bottleneck) + Warning (SWI 3-tank) + Routing (hazard graph)
 ├── SWI (backend/app/swi.py) + Exposure + Wound + Replay + Runout ledgers
 ├── NGEN artifacts (feature matrix + manifest, local files) + Auto watcher thread (60s)
 └── Alert fixture + env-gated SMS (SMS_PROVIDER/API_KEY/SMS_TO) + IMD_API_KEY adapter
 ▼
Local data (SQLite default; PostGIS 16-3.4 via docker-compose.prod.yml:1 db healthcheck pg_isready, api healthcheck /health)
 ▼
Runs (./runs:/app/runs live_feed.json + alert_dispatch.jsonl + sim_audit.jsonl)
```

Demo runs fully offline-capable; live Open-Meteo/IMD appear as best-effort gated blend with 1h cache, fixtures remain fallback (`GET /api/forecast/rainfall` + `GET /api/forecast/live:1154` + `GET /api/forecast/imd-live:1124`).

```yaml
# docker-compose.prod.yml:1
services:
  db: { image: postgis/postgis:16-3.4, POSTGRES_DB: talus, healthcheck: pg_isready }
  api: { build: ., env_file: .env, DATABASE_URL: postgres://talus@db:5432/talus, AUTO_ALERT_ENABLED: "true", depends_on: [db], volumes: ["./runs:/app/runs"] }
```

Frontend served by api static (frontend/dist) — no separate service needed.

---

## Tech stack deltas (final)

| Layer | v1 | v2 (frozen 2025-11-15) |
|---|---|---|
| Frontend map | Leaflet | Leaflet (RiskMap) + Recharts (trend),lucide icons, PWA sw.js + manifest.webmanifest |
| Backend | FastAPI | Same; 30+ endpoints (zones/live/soil/warning/roads/isolation/risk/sim/reports/alerts) |
| ML | RF + SHAP | RF 500/XGB/LGBM (OOF 0.9338/0.9418/0.9406), isotonic Brier 0.0971 + Bayes 0.5→0.01, TreeSHAP top-4 |
| Geo | — | rasterio/GDAL, geopandas, Overpass bbox queries (1014/226/504), SRTM 30m D8, WorldCover 10m |
| Alerts | in-app | SMS gateway env-gated (msg91/fast2sms/twilio/textbelt) + auto watcher + i18n en/hi/ne/as/bn |
| Auth | — | Frontend PINs (9999/1111/2222/3333, talus_auth) + backend /health isolation/warning observability |
| Mobile | — | PWA (`sw.js:1` + `manifest.webmanifest:1` 192/512), outbox localStorage, no native |
| Data | synthetic CSV | NGEN 22-col sample + 2936 training Parquet/GeoPackage (git-ignored), CCI v09.2, OSM provenance |
| DB | SQLite | SQLite default, PostGIS 16-3.4 via docker-compose.prod.yml |
| Live | — | Open-Meteo 7-day + IMD_API_KEY data.gov.in gated, 1h cache, SWI 3-tank |

---

## 5. Production interfaces: sensor adapter + cloud path (PS compliance)

The PS Expected Solution names three things the prototype does not run live at scale: sensor data, production IMD/satellite feeds, and cloud architecture. This section records the interfaces so evaluators see they were designed, not ignored.

### 5.1 Sensor Ingestion Adapter

```text
AWS/ARG gauges ─┐
 ├─▶ Sensor Adapter ─▶ NGEN fetch/ ─▶ rainfall_24h/7d, soil_moisture + SWI
Soil probes ────┘ (validate → normalize → provenance-tag source=sensor)
 │ fixture in demo (recorded feed file, same parser, live_feed.sample.json)
 │ live later (connector swap, no schema/model change)
 │ SWI already blends forecast: swi_for_zone(rain7,rain30,forecast3)
```

Contract: timestamped + geo-tagged observations → existing feature names in `05_FEATURE_SCHEMA_SIH26001.md`. Sensor-present values override gridded/reanalysis; sensor gaps fall back silently in value but loudly in `missing_evidence`. See `03_DATA_PLAN_SIH26001.md` §A.

### 5.2 Cloud scale path (prototype-local → cloud: proven)

```text
PROTOTYPE (demo)              PRODUCTION (docker-compose.prod.yml:1, built)
FastAPI (local)          ─▶   API service (containerized, healthcheck /health, autoscaled)
SQLite / local files     ─▶   Postgres/PostGIS 16-3.4 + object store (rasters, models)
Alert adapter (fixture)  ─▶   SMS gateway env-gated + push + multilingual templates + auto watcher
Dashboard (localhost)    ─▶   CDN-cached map tiles + hosted frontend (api static frontend/dist)
Field queue (local file) ─▶   Cloud sync API, offline-first (queued uploads, delta downloads, conflict = server-wins + flag)
SWI / Warning (local)    ─▶   Same swi.py + warning_thresholds.json overlay, scoring frozen
```

Migration is config, not rewrite: schemas are PostGIS-ready, artifact paths are object-store URIs, the SMS/IMD paths sit behind env-gated adapters. Cloud build + field testing are post-hackathon work (see `08_LIMITATIONS_SIH26001.md`). Live IMD requires `IMD_API_KEY`; otherwise Open-Meteo blend + fixtures keep the demo honest.