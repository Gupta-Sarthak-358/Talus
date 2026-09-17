# frontend — Talus SIH26001 (2025-11-15)

React + Vite + Leaflet + Tailwind PWA dashboard for the 12-slope NER decision-support system. Live-only, no mocks — `VITE_USE_LIVE_API=true` consumes `backend/app/main.py` live scores or honest fixture fallback 89/78/66/52. **2025-11-15 WILL→PARTIAL:** Panchayat 100 tiles `GET /api/panchayat/tiles`, Copernicus `GET /api/terrain/copernicus` S1 Δ0.4, AWS 12 gauges `GET /api/aws/gauges`, PostGIS `GET /api/db/status`, CBE `POST /api/alerts/cbe`.

## Run it

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173  (VITE_API_URL=http://localhost:8000/api)
npm run build  # offline PWA shell + sw.js + manifest 192/512
```

## Components (2025-11-15)

- `src/components/RiskMap/RiskMap.jsx` — 5-band heatmap (`RISK_BANDS` 85/66/41/21) + roads OSM proven 1014/226/504 ways (`roads_osm_provenance.json`, `NH310A trunk`) geometry **demo topology** for deterministic R2 avoidance + **PanchayatTiles** overlay `GET /api/panchayat/tiles` (100 tiles 10×10 26.95-28.05/88.05-89.0, frozen 12 untouched) + **CopernicusOverlay** `GET /api/terrain/copernicus` S1 28.3→28.7 Δ0.4; Leaflet `MapContainer` + `TileLayer` OSM, corridor centers shifted per `locations.js` (gangtok/lachung/darjeeling).
- `src/components/WarningStateCard/` — 6-state `NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE` from `GET /api/warning/state` with `STATE_STYLE` + reason stamps (effective rain per-zone `warning_thresholds.json` S1 385 etc + SWI 3-tank `swi.py` L1=15 L2=60 L3=60 + wound 2 scars + forecast Open-Meteo + quake 25% drop).
- `src/components/IsolationAlertCard` — `GET /api/isolation` R4 bottleneck `ISOLATED/MAY_ISOLATE` alongside roads.
- `src/components/RiskTrendChart` — observed vs forecast separation with **NOW** line + 75/85 thresholds + causality label; consumes `/api/replay/series` + live feed audit.
- `src/components/RoadStatusCard` — clean R1–R4 status per corridor from `GET /api/roads/status` (+ restrictions flag from `/api/roads/restrictions` catalogue).
- `src/components/QuickStatsBar` — LIVE forecast badge from `GET /api/forecast/live` (Open-Meteo 1h cache) + scoring badge `live-rf` vs `fixture` 89/78/66/52 + **AWS live** `GET /api/aws/gauges` 10-min.
- `src/components/RiskScoreGauge` — clean % gauge (villager words vs officer %).
- `src/components/AlertPanel` — 5 langs **en/hi/ne/as/bn** + channel toggle `app|sms|CB` → `POST /api/alerts/dispatch?channel=` (env-gated msg91/fast2sms/twilio/textbelt + auto watcher 60s/3600s) + `POST /api/alerts/cbe` bearer simulated + dispatch log.
- `src/components/AdminPanel` → `/admin` — health (`/health` checks `store:gangtok live_scores` + fixtures) + isolation/log/queue/provenance; auth via `services/auth.js` PINs **9999 admin / 1111 district / 2222 state / 3333 rescue** + `talus_auth` localStorage.
- `src/components/RoleSelector` + `src/components/LoginModal` — PIN gate `services/auth.js` before role dashboards; 4 roles villager/district_officer/state_manager/rescue_team (`DECISIONS_BY_BAND` translations en/hi/ne/as/bn).
- `src/context/TalusContext.jsx` — corridor + live feed + warning/isolation state; `services/api.js` (`apiRequest`) + `VITE_API_URL`.

## GIS & provenance

SRTM n27_e088 30m + derivatives (slope/TWI/SPI), CCI v09.2 1978–2024 soil (+ SWI 3-tank warning overlay), IMD 1901–2024 + Open-Meteo live (+ IMD-live `IMD_API_KEY` gated fallback), Sentinel-2 2 scars `wound_map.json`, runout 85 buildings `runout_exposure.json`, USGS 26 quakes `usgs_quakes.json`. OSM highways 1014/226/504 + waterways 226/504 proven `roads_osm_provenance.json` (counts honest, geometry demo topology). 12 NGEN slopes S1–S4 Gangtok + N1–N4 Lachung + D1–D4 Darjeeling (`feature_matrix.sample.csv` 17 numeric + lulc, zero STUBs).

## How exposure & warning flow (no mock)

`RiskMap` reads `GET /api/zones?location=` (score 89/78/66/52 scaffold or `sih26001_model.py` live TreeSHAP top-5 + Bayes `confidence_real_1pct` 0.5→0.01) → `GET /api/zones/{id}/exposure` (runout 85 + wound + isolation) → bands 85/66/41/21 → `RiskScoreGauge` + role `DECISIONS_BY_BAND`. `WarningStateCard` reads `GET /api/warning/state` 6-state; `IsolationAlertCard` reads `GET /api/isolation` R4; `RiskTrendChart` reads `GET /api/replay/series` + `/api/live/feed` + `/api/soil/swi` + `/api/forecast/live|imd-live`; `RoadStatusCard` reads `GET /api/roads/status|restrictions`; `AlertPanel` posts `GET /api/alerts/dispatch` + `GET /api/alerts/auto/status`.

## Offline

PWA shell `public/sw.js` (cache-first for shell, network-first for `/api/*`) + `public/manifest.webmanifest` (icons 192/512) + report outbox `talus_report_outbox` (localStorage queue per `PILOT_REVIEW.md`) + `TalusContext` sync flag. When `navigator.onLine===false`, field reports queue offline and flush on reconnect (`Sync` button). Map tiles require connectivity; everything else is local. Install prompt via `manifest`.

## Env

```
VITE_API_URL=http://localhost:8000/api
VITE_USE_LIVE_API=true
VITE_MAP_STYLE=osm
```

Auth: `services/auth.js` exports `authenticate(pin)` → `talus_auth` `{role, pin}`; guards `RoleSelector` + `AdminPanel`. Production DB path via `DATABASE_URL` handled backend — frontend unchanged (checks `live_scores` badge).

See `docs/CURRENT_SYSTEM.md` (2025-11-15 truth), `docs/RECALIBRATION_NOTE.md` (Bayes 0.5→0.01), `ml/sih26001/reports/metrics.md` (RF 0.9338 Brier 0.0971), `backend/README.md` (35/35 endpoints).