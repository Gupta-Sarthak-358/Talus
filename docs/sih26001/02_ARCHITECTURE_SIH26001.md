# TALUS Architecture — SIH26001

**Status:** Built — freeze 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · **Trace to:** `01_REQUIREMENTS_SIH26001.md`,
`docs/SIH26001_RESEARCH.md` §8

v1 diagrams live in `docs/02_ARCHITECTURE.md` and stay authoritative for the
mine track. This doc records the v2 mapping and deltas only.

---

## 1. System data flow (v2)

```text
Real NER sources
 IMD rainfall │ ERA5/SMAP soil moisture │ SRTM DEM │ Sentinel-2 │ GSI geology
 OSM roads/rivers │ landslide inventories │ IMD forecast API
 Sensor feeds (AWS/ARG gauges, soil-moisture probes — via adapter; fixture in demo)
 ↓
NGEN PIPELINE (replaces synthetic generator)
 fetch → reproject → align grid → derive terrain → join → label → version
 ↓
Feature Processing
 (17 NER features per spatial unit, with missingness + provenance)
 ↓
TALUS RISK ENGINE (same pattern, retrained)
 RF + XGBoost (+LGBM) → calibrated probability → score 0–100 + confidence
 ↓
 Explainability (SHAP) Trend / monsoon escalation
 ↓
Decision Engine
 Role-based actions · Road-status + risk-aware routing · Rainfall what-if
 ↓
Field reports ↑↓ Alerts (SMS/app, multilingual, offline-sync)
 ↓
NER GIS Dashboard (React + Leaflet/Mapbox) + Field app (camera/GPS/offline)
```

## 2. Module mapping (v1 → v2)

| v1 module | v2 module | Change |
|---|---|---|
| Generator (physics sim) | **NGEN** (NER data pipeline) | Complete rewrite — real data, not synthetic |
| ML predictor | ML predictor | Retrain on 17 NER features; same RF/XGB pattern |
| SHAP | SHAP | Same module, new feature names |
| Calibration (isotonic) | Calibration | Same approach, new target (event / no-event) |
| Trend / escalation | Trend / escalation | Same logic, monsoon temporal patterns |
| Decision engine (4 mine roles) | Decision engine (4 NER roles) | New role matrix + message templates |
| Routing (zone graph) | Routing (OSM road graph) | New graph source + segment risk weights |
| Scenario engine (storm replay) | Scenario engine (rainfall thresholds) | New physics: Monga 2026 / Dahal–Hasegawa |
| Evidence card | Evidence card | New provenance: satellite, reanalysis, crowd |
| Alert system | Alert system | **Add:** SMS gateway, i18n, offline queue |
| Dashboard (mine map) | Dashboard (GIS heatmap + roads + villages) | Rebuild views on same API pattern |
| Backend API (FastAPI) | Backend API | Extend contract; keep v1 shapes where possible |
| — | Field-reporting app | **New:** camera/GPS, offline tiles, officer queue |

What survives unchanged: two-engine pattern (ML + physics scenario),
isotonic calibration methodology, SHAP framework, role-escalation pattern,
risk-weighted Dijkstra, missing-evidence transparency, test structure,
offline-first philosophy.

## 3. Component deltas

### Backend (FastAPI) — built endpoints (frozen 2026-09-04)

```text
GET /api/zones · GET /api/zones/{id} · GET /api/zones/{id}/features|/trend|/explanation|/decision|/history
POST /api/risk/predict
POST /api/simulation/what-if (ML counterfactual 66→74) · POST /api/simulation/causal-what-if (physics)
GET /api/simulation/templates (monga-mdl + dahal-144)
GET /api/roads/status (open / at-risk / blocked — R2 at-risk)
POST /api/routes/safe (risk-aware avoids R2)
POST /api/reports (ReportIn: zone_id/type/text/lat/lon/captured_at/reporter_role/photo{sha256,exif}+consent → queued|flagged)
GET /api/reports/queue?status= (queued|verified|dismissed|flagged) · PATCH /api/reports/{id} (review)
POST /api/alerts/dispatch (en/hi/ne fixture) · GET /api/forecast/rainfall
```

Live `backend/app/main.py:389` `ReportIn/Out` + `15 tests` `test_reports.py:1`, fixtures `reports.json:1`, validator `check_scaffold.py:92`. v1 shapes intact.

### Frontend

```text
GIS Dashboard
 ├── RiskHeatmap (5-band susceptibility, Leaflet/Mapbox)
 ├── RoadOverlay (status colors + closures)
 ├── VillageLayer (settlements + priority flags)
 ├── RiskPanel (score + confidence + missing evidence)
 ├── SHAPPanel (feature contributions)
 ├── TrendChart (monsoon trajectory)
 ├── AlertPanel (role-based, multilingual)
 ├── RouteView (shortest vs risk-aware)
 └── ScenarioPanel (rainfall sliders + threshold presets)
Field app (progressive web app first — reporting lane LIVE on backend, UI pending frontend merge)
 ├── Capture (photo/video + GPS + timestamp, offline — ReportForm + PhotoMeta {sha256,exif_lat,exif_lon} + consent + pilot-bbox gate)
 ├── Queue (pending sync — GET /api/reports/queue?status= + PATCH review queued|flagged→verified|dismissed, terminal guard)
 └── Alerts (cached warnings, local language)
```

### NGEN (new — no v1 equivalent)

```text
ngen/
 ├── fetch/ (IMD, CDS/ERA5, USGS/SRTM, Copernicus, Bhusanket, OSM, Zenodo,
 │ sensor-adapter: AWS/ARG + soil-probe feed format — fixture in demo)
 ├── preprocess/ (reproject to pilot CRS, resample, cloud-mask, QA)
 ├── terrain/ (slope, aspect, curvature, TWI, SPI, drain density)
 ├── join/ (spatial join to unit grid + temporal join to events)
 ├── label/ (positive = event location+date window; negative = >300 m buffer sampling)
 └── version/ (manifest: source versions, dates, seeds, checksums)
```

Deterministic: fixed seeds, pinned source versions, manifest committed.
Raw downloads stay out of git (see data rules in `03_DATA_PLAN_SIH26001.md`).

## 4. Deployment (prototype)

```text
Browser / field device
 │
 ▼
React GIS dashboard + PWA field app
 │ REST / JSON
 ▼
FastAPI (local)
 ├── Susceptibility model (RF + XGB)
 ├── SHAP + calibration + trend + decisions + routing
 ├── NGEN artifacts (feature matrix + manifest, local files)
 └── Alert fixture (no live SMS in demo)
 ▼
Local data (SQLite default; PostGIS optional for GIS-heavy work)
```

Demo runs fully offline; live APIs appear as recorded fixtures.

---

## Tech stack deltas (proposed)

| Layer | v1 | v2 delta |
|---|---|---|
| Frontend map | Leaflet | Leaflet or Mapbox GL (decide in ADR; heatmap + overlays needed) |
| Backend | FastAPI | Same; new endpoints |
| ML | RF + SHAP | RF + XGBoost (+LGBM candidate); SHAP stays |
| Geo | — | rasterio / GDAL, geopandas, (GEE optional for prototyping, not demo) |
| Alerts | in-app | SMS gateway adapter (fixture in demo) + i18n framework |
| Mobile | — | PWA first; native deferred |
| Data | synthetic CSV | NGEN outputs (Parquet/GeoPackage, git-ignored) |

Decisions to freeze before build: spatial unit (pixel vs slope unit vs admin
zone), map library, CRS + grid, SMS provider adapter, language matrix. Each
gets an ADR or a line in `07_ASSUMPTIONS_SIH26001.md` promoted to decision.

---

## 5. Production interfaces: sensor adapter + cloud path (PS compliance)

The PS Expected Solution names three things the prototype does not run live:
sensor data, production IMD/satellite feeds, and cloud architecture. This
section records the interfaces so evaluators see they were designed, not
ignored. Nothing here is built in the prototype beyond recorded fixtures.

### 5.1 Sensor Ingestion Adapter

```text
AWS/ARG gauges ─┐
 ├─▶ Sensor Adapter ─▶ NGEN fetch/ ─▶ rainfall_24h/7d, soil_moisture
Soil probes ────┘ (validate → normalize → provenance-tag `source=sensor`)
 │ fixture in demo (recorded feed file, same parser)
 │ live later (connector swap, no schema/model change)
```

Contract: timestamped + geo-tagged observations → existing feature names in
`05_FEATURE_SCHEMA_SIH26001.md`. Sensor-present values override
gridded/reanalysis values; sensor gaps fall back silently in value but loudly
in `missing_evidence`. See `03_DATA_PLAN_SIH26001.md` §A (Sensor feeds).

### 5.2 Cloud scale path (prototype-local → cloud)

```text
PROTOTYPE (demo) PRODUCTION (designed, not built)
FastAPI (local) ─▶ API service (containerized, autoscaled)
SQLite / local files ─▶ Postgres/PostGIS + object store (rasters, models)
Alert adapter (fixture) ─▶ SMS gateway + push + multilingual templates
Dashboard (localhost) ─▶ CDN-cached map tiles + hosted frontend
Field queue (local file) ─▶ Cloud sync API, offline-first (queued uploads,
 delta downloads, conflict = server-wins + flag)
```

Migration is config, not rewrite: schemas are PostGIS-ready, artifact paths
are object-store URIs, the SMS path sits behind the adapter interface. Cloud
build + field testing are post-hackathon work (see
`08_LIMITATIONS_SIH26001.md`).
