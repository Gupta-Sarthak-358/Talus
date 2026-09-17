# Talus — Risk-Aware Decision Support

**`SIH26001` — NER Landslide Risk Intelligence (MDoNER, Disaster Management, Software)**
*Single track, single source of truth. No legacy track mentioned as current.*

Talus converts scattered NER geospatial signals into explainable risk and actionable safety decisions.

### Core Flow

**Detect → Understand → Escalate → Decide → Act**

### What Talus Does

1. Collects multi-source NER signals: IMD rainfall 0.25° 1901–2024 + Open-Meteo live, CCI soil v09.2 1978–2024, SRTM 30m n27_e088_1arc_v3.tif + derivatives (TWI/SPI), Sentinel-2 NDVI / WorldCover LULC, USGS 26 quakes M5+, OSM roads/rivers (1014/226/504 ways proven), wound BigGIS (2 scars), per-zone seismic memory.
2. Produces slope-level susceptibility `0–100` + calibrated confidence (`confidence` + `confidence_real_1pct` Bayes 0.5→0.01) + `missing_evidence` — live RF or honest fixture fallback.
3. Explains *why* (TreeSHAP top-5) per prediction (`GET /api/zones/{id}/explanation` + `GET /api/zones/{id}/exposure` operational risk).
4. Detects escalation via warning state `NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE` (effective rain per-zone thresholds warning_thresholds.json — S1 385, S2 395, S3 410, S4 375 etc + SWI 3-tank swi.py L1=15 L2=60 L3=60 + wound BigGIS + forecast Open-Meteo + quake 25% threshold drop) and isolation `ISOLATED/MAY_ISOLATE` (R4 bottleneck).
5. Generates role-specific actions (villager / district_officer / state_manager / rescue_team) + 5 langs (en/hi/ne/as/bn) + risk-aware routing (Dijkstra avoids R2 deterministically) + SMS/app dispatch.
6. Supports what-if (ML counterfactual + causal replay `replay_series`) and geo-tagged field reporting (`POST /api/reports` + queue + outbox `talus_report_outbox`).
7. Serves offline-first PWA (sw.js + manifest 192/512) GIS dashboard + live road status + forecast live badge + live feed audit.

The key differentiation: from **"What is the risk?"** → **"What should we do now, and what are we missing?"**

### MVP — Built & Frozen 2025-11-15 (adds WILL→PARTIAL)

- NGEN over 3 corridors (`S1-S4` Gangtok + `D1-D4` Darjeeling + `N1-N4` Lachung, 12 slopes, per-corridor windows) — `17 numeric + lulc` REAL/PROXY, zero STUBs (`feature_matrix.sample.csv`, `manifest.sample.json`)
- Inventory-scale training `2936×22` (`1468+1468` Sikkim + Darjeeling-hills) — `GroupKFold(8) OOF RF 0.9338 XGB 0.9418 LGBM 0.9406` `ml/sih26001/reports/metrics.md`, `temporal 807 → RF test 0.8568`, isotonic `Brier 0.0971` `calibration.md`, TreeSHAP top-5
- Recalibration (RECALIBRATION_NOTE.md): Bayes `pi_train 0.5 → pi_real 0.01` — score frozen, `confidence_real_1pct` added; SWI 3-tank `L1=15 L2=60 L3=60` overlays warning state only (scoring unchanged)
- **2025-11-15 WILL→PARTIAL:** Panchayat 100 tiles 10×10 26.95-28.05/88.05-89.0 `panchayat_tiles.json` heuristic/live-RF `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4 `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` → `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT
- FastAPI `backend/app/main.py` (`35/35` tests, scaffold `89/78/66/52`) — `/health` + `GET /api/db/status` (fixture/postgis), `GET /api/zones`, `GET /api/zones/{id}/explanation` (TreeSHAP), `GET /api/zones/{id}/exposure` (runout 85 + wound + isolation), `/api/warning/state` (6-state `NORMAL→EVACUATE` effective rain `rainfall_7d+0.3*30d` S1 385 `warning_thresholds.json`, SWI 3-tank `swi.py` `tanh(SWI/100)` L1=15 L2=60 L3=60, wound 2 scars, forecast Open-Meteo, quake 25% drop), `/api/isolation` (R4 bottleneck), `/api/soil/swi`, `GET /api/roads/status` + `GET /api/roads/restrictions` (catalogue), `GET /api/panchayat/tiles` (100), `GET /api/terrain/copernicus`, `GET /api/aws/gauges`, `GET /api/forecast/live` + `GET /api/forecast/imd-live` (`IMD_API_KEY` gated), `POST /api/alerts/dispatch` (app|sms env-gated `msg91/fast2sms/twilio/textbelt` `runs/alert_dispatch.jsonl` + auto 60s/3600s) + `POST /api/alerts/cbe` (simulated), `/api/reports` + `GET /api/live/feed` + `GET /api/replay/series` + `GET /api/runout/exposure` (85) + `GET /api/wounds` (2) + `GET /api/model/calib` (Bayes 0.5→0.01), `/api/routes/safe`
- React + Leaflet: `RiskMap.jsx` 5-band heatmap + roads OSM proven 1014/226/504 ways `roads_osm_provenance.json` (geometry demo topology, deterministic R2 avoidance), `IsolationAlertCard`, `WarningStateCard` 6 states, `RiskTrendChart` observed vs forecast separation (NOW line), `RoadStatusCard` clean, `QuickStatsBar` LIVE forecast badge, `AlertPanel` 5 langs en/hi/ne/as/bn + channel toggle (app|sms), `RiskScoreGauge` clean, `AdminPanel` at `/admin` (PIN 9999/1111/2222/3333) with health/isolation/log/queue/provenance, `RoleSelector` PIN gate via `services/auth.js`, `LoginModal`
- GIS: SRTM `n27_e088_1arc_v3.tif` 30m, CCI v09.2 1978–2024, IMD 1901–2024 + live Open-Meteo/IMD, Sentinel-2 2 scars, USGS 26 quakes
- Offline: PWA `sw.js` + `manifest.webmanifest` 192/512, outbox `talus_report_outbox`; Cloud: `Dockerfile` (`curl /health`) + `docker-compose.prod.yml` (postgis) + `DEPLOY_CLOUD.md`

### Important Limitation

Prototype is **not a live warning system**. Validates decision-support architecture on **real documented Sikkim events** (`2936` rows, CCI v09.2 1978–2024, SRTM 30m n27_e088, Sentinel-2 wound 2 scars, SRTM runout 85 buildings, USGS 26 quakes, WorldCover, IMD 1901–2024) with calibrated quasi-static proxies (`approximate`). In-situ rain/soil sensors are **adapter-fixture ready**; Bhukosh WFS lithology timed out 15s → **PROXY-published-map** (uniform, omitted from X, honestly labeled); road geometry OSM demo topology (counts proven 1014/226/504); IMD live needs `IMD_API_KEY` else fallback Open-Meteo (labeled); lithology uniform. See `docs/CURRENT_SYSTEM.md` and `RECALIBRATION_NOTE.md`.

### Repository Structure

```text
talus/
├── README.md (2025-11-15)
├── docs/
│   ├── CURRENT_SYSTEM.md          ← single source of truth (NER, 2025-11-15)
│   ├── PROJECT_HANDBOOK.md        ← 30-sec pitch + full Q&A
│   ├── RECALIBRATION_NOTE.md      ← Bayes 0.5→0.01 + SWI overlay
│   ├── DEPLOY_CLOUD.md            ← Docker + PostGIS (postgis:16-3.4) + env
│   ├── PRESENTATION_EVIDENCE.md   ← backup slides (real numbers)
│   ├── REALTIME_SHOWCASE_MEMO.md  ← one-laptop + one-phone demo
│   ├── CBE_CONTRACT.md            ← CBE bearer (POST /api/alerts/cbe)
│   └── LIVE_HOST_EVIDENCE.md      ← https://talus-sih26001.onrender.com/health
├── data/sih26001/
│   ├── fixtures/        ← committed samples (S1–S4/N1–N4/D1–D4, roads, reports, forecast, manifests, slopes*.json)
│   ├── evidence/        ← panchayat_tiles.json (100), copernicus_dem_comparison.json (S1 Δ0.4), roads_osm_provenance.json (1014/226/504), warning_thresholds.json (S1 385...), wound/runout/replay/usgs_quakes
│   └── processed/       ← DEM/rain/soil extracts + training matrix (git-ignored except .training.sample.csv)
├── ml/sih26001/
│   ├── reports/         ← metrics.md (GroupKFold 0.9338, Brier 0.0971) / calibration.md
│   └── models/          ← sih26001_*_v1.joblib (git-ignored, honest fallback)
├── backend/
│   ├── app/main.py      ← FastAPI 35/35, sih26001_model.py (live_scores), swi.py (L1=15 L2=60 L3=60), aws_ingest.py (12 gauges)
│   └── tests/           ← test_reports / warning_state / live_feed / wounds / runout / multiloc / alerts_ack
├── frontend/
│   ├── src/components/RiskMap/RiskMap.jsx (+ WarningStateCard, IsolationAlertCard, RiskTrendChart, PanchayatTiles, AdminPage)
│   ├── public/sw.js + manifest.webmanifest + icons 192/512
│   └── services/auth.js (PINS: 9999/1111/2222/3333)
├── Dockerfile (+ healthcheck curl /health) + docker-compose.yml + docker-compose.prod.yml (postgis:16-3.4)
└── scripts/             ← build_training_matrix.py, train_sih26001.py, local_sensor_sim.py, check_scaffold.py (89/78/66/52)
```

### Running Locally

```text
# Backend (live RF when weights present, else fixture 89/78/66/52)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # http://127.0.0.1:8000  GET /health  GET /api/zones
python -m pytest -q                        # 35/35 (backend) — scaffold 89/78/66/52

# Frontend (live-only, no mocks)
cd frontend
npm install
npm run dev                               # http://localhost:5173  (VITE_API_URL=http://localhost:8000/api)

# One-command demo (backend + frontend)
powershell -ExecutionPolicy Bypass -File ./start_all.ps1  # :8000/docs + :5173

# Training (other terminal — venv with xgb/lgbm/shap)
python scripts/build_training_matrix.py
python scripts/train_sih26001.py          # GroupKFold 0.9338 XGB 0.9418 Brier 0.0971 → ml/sih26001/reports/
```

### Related Docs

- [Current System](docs/CURRENT_SYSTEM.md) — live architecture + frozen artifacts (2025-11-15)
- [Project Handbook](docs/PROJECT_HANDBOOK.md) — 30-sec pitch + warning/isolation + Q&A
- [Recalibration Note](docs/RECALIBRATION_NOTE.md) — Bayes 0.5→0.01 + SWI 3-tank
- [Deploy Cloud](docs/DEPLOY_CLOUD.md) — Dockerfile healthcheck + docker-compose + postgis
- [Presentation Evidence](docs/PRESENTATION_EVIDENCE.md) — backup slides (GroupKFold 0.9338, no stale numbers)
- [Realtime Memo](docs/REALTIME_SHOWCASE_MEMO.md) — one laptop + one phone (PWA + auto alerts)

**New to the project?** Start with `docs/CURRENT_SYSTEM.md` and `PROJECT_HANDBOOK.md`.

---

*Team Sangyan — SIH 2026 — SIH26001 (MDoNER) — NER Landslide Risk Intelligence — Phase-1 built, 35/35 green, GroupKFold RF 0.9338 XGB 0.9418 Brier 0.0971.*