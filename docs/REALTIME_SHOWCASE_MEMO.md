# Real-time showcase memo — one laptop + one judge phone (SIH26001, 2025-11-14)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Goal:** 5-minute live demo on one laptop + one phone (same hotspot) — no Render mocks, no fake successes. Every dispatch is logged; every live lane has provenance and fallback.

## Decision: local-first live, cloud-ready

Render free-tier cold-starts break the demo. Host locally; cloud (`Dockerfile` + `docker-compose.prod.yml` postgis) is for audit, not for the judge's 5 minutes.

1. **Live forecast** — `GET /api/forecast/live` (Open-Meteo 7d, 1h cache) + `GET /api/forecast/imd-live` (IMD_API_KEY gated data.gov.in, fallback Open-Meteo with labeled provenance)
2. **Warning + isolation** — `GET /api/warning/state` (6 states, reason-stamped) + `GET /api/isolation` (R4 bottleneck) — live on frozen scores
3. **Auto alerts** — `AUTO_ALERT_ENABLED` watcher (60s interval, 3600s cooldown) → `POST /api/alerts/dispatch` (app|sms) + `runs/alert_dispatch.jsonl`
4. **PWA + offline** — `frontend/public/sw.js` + `manifest.webmanifest` (192/512) — judge phone installs from laptop URL; `/api` network-only (never stale)
5. **Outbox reports** — `talus_report_outbox` + `talus_report_photo_bg` (localStorage) — offline queue, flush on reconnect

## What was built (current)

- **Backend (35/35):** FastAPI at `backend/app/main.py` with 35/35 tests, endpoints: `/health`, `/api/zones`, `/api/zones/{id}/explanation (TreeSHAP)`, `/api/zones/{id}/exposure`, `/api/warning/state (now NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE with reason stamps: effective rain 390 local thresholds warning_thresholds.json, SWI 3-tank swi.py L1=15 L2=60 L3=60, wound BigGIS, forecast Open-Meteo, quake 25% threshold drop)`, `/api/isolation`, `/api/soil/swi`, `/api/roads/status` + `/api/roads/restrictions (catalogue)`, `/api/forecast/live` + `/api/forecast/imd-live (IMD_API_KEY gated, fallback Open-Meteo)`, `/api/alerts/dispatch (channel app|sms, env-gated msg91/fast2sms/twilio/textbelt, logged to runs/alert_dispatch.jsonl)`, auto watcher (`AUTO_ALERT_ENABLED`, interval 60s, cooldown 3600s, `/api/alerts/auto/status`+`trigger`), `/api/reports`, `/api/live/feed`, `/api/replay/series`, `/api/runout/exposure`, `/api/wounds`, `/api/model/calib (Bayes p_real 0.5→0.01)` — plus `+ swi.py` + `sih26001_model.py` RF 500 + XGB 400 + LGBM 400 + isotonic, 2936 rows (1468+1468), 17 numeric + lulc, GroupKFold(8) OOF RF 0.9338 XGB 0.9418, `sih26001_model.py` live_scores or fixture fallback, TreeSHAP top-4, RECALIBRATION_NOTE.md (Bayes 0.5→0.01) and swi overlay
  - Warning 6-state `NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE` — effective rain `r7+0.3*r30` vs per-zone 375-420 (warning_thresholds.json, 390 Monga separator) + SWI 3-tank (L1=15 L2=60 L3=60, `swi.py`) + wound BigGIS (2 scars) + forecast Open-Meteo + quake 25% threshold drop (USGS 26 M5+)
  - Isolation `GET /api/isolation` (deterministic, shifts for gangtok/lachung/darjeeling)
  - Roads `GET /api/roads/status|restrictions` (R1-R4 demo topology, OSM provenance 1014/226/504)
  - Forecast `GET /api/forecast/live` + `imd-live` (IMD_API_KEY env-gated, honest fallback)
  - Alerts `POST /api/alerts/dispatch?channel=app|sms` (msg91/fast2sms/twilio/textbelt via SMS_PROVIDER+SMS_API_KEY+SMS_TO, else SIMULATED) + log + ack + auto watcher + `/api/alerts/auto/status|trigger`
  - Evidence: `GET /api/replay/series` (causality ON-date), `GET /api/runout/exposure`, `GET /api/wounds`, `GET /api/model/calib`, `GET /api/soil/swi`
  - Live feed: `GET /api/live/feed` (simulator `runs/live_feed.json` wins, else `live_feed.sample.json`, else 404) + `GET /api/live/audit`
- **Frontend:** `RiskMap.jsx` 5-band heatmap + roads OSM proven 1014/226/504 ways `roads_osm_provenance.json` geometry demo topology, `IsolationAlertCard`, `WarningStateCard` with 6 states, `RiskTrendChart` observed vs forecast separation (NOW line), `RoadStatusCard` clean, `QuickStatsBar` LIVE forecast badge, `AlertPanel` with 5 langs en/hi/ne/as/bn + channel toggle, `RiskScoreGauge` clean, `AdminPanel` at `/admin` (PIN 9999/1111/2222/3333) with health/isolation/log/queue/provenance, `RoleSelector` PIN gate via `services/auth.js`, `LoginModal` (also `RiskMap.jsx` + `IsolationAlertCard` + `WarningStateCard` + `RoadStatusCard` + `AlertPanel` + `RiskScoreGauge` + `AdminPanel` details above map)
- **GIS:** SRTM 30m `n27_e088_1arc_v3.tif`, CCI soil v09.2, IMD 0.25° historical + Open-Meteo live, Sentinel2 wound 2 scars, SRTM runout, USGS quakes 26 M5+
- **Offline:** PWA `sw.js` + `manifest.webmanifest` icons 192/512, outbox `talus_report_outbox`
- **Cloud:** `Dockerfile` healthcheck `curl /health`, `docker-compose.yml` + `docker-compose.prod.yml` postgis, `docs/DEPLOY_CLOUD.md`
- **Limitations:** Bhukosh WFS timeout → PROXY-published-map, OSM geometry demo topology, IMD live requires `IMD_API_KEY`, lithology uniform
- **PWA:** `sw.js` (talus-shell-v1, 6 SHELL files, skipWaiting/clients.claim) + `manifest.webmanifest` (theme #0b1220, maskable 192/512) — phone installs from `http://<laptop-ip>:5173`
- **Cloud:** `Dockerfile` healthcheck `curl /health`, `docker-compose.yml` + `docker-compose.prod.yml` (postgis), `docs/DEPLOY_CLOUD.md` (file-backed when DATABASE_URL absent)

## Judge flow (5 min)

1. Laptop: `powershell -ExecutionPolicy Bypass -File .\start_all.ps1` (or `docker-compose up`) → :8000/health ok, :5173 open
2. Phone: open `http://<laptop-ip>:5173` → install (PWA) → see map + WarningStateCard 6 states + Isolation banner + LIVE badge
3. Trigger: call `POST /api/alerts/auto/trigger?location=gangtok` or wait for watcher (ISOLATED/MAY_ISOLATE) → check Admin log (`/api/alerts/dispatch/log`) — no fake SENT unless SMS env set
4. Alerts: open AlertPanel → switch en→hi→ne→as→bn → toggle app→sms (SIMULATED badge when no key) → inspect zone
5. Field: submit report with photo → kill network → second report queues to `talus_report_outbox` → restore → `refreshReports()` flushes → Admin queue shows it
6. Kill forecast upstream: block internet briefly → QuickStatsBar LIVE badge empties, RiskTrendChart forecast side grays, `/api/forecast/imd-live` still returns fallback with provenance — offline honesty point.

## Honesty notes

- NGEN 12 rows are REAL/PROXY tagged, zero STUBs — nothing hidden.
- Everything live is labeled: `mode` provenance on forecast/wound/runout, `scoring` live-rf vs fixture, wound REVIEW QUEUE not confirmed cuts, Bhukosh PROXY-published-map, OSM demo topology.
- No real sensors claimed; `previous_landslide` excluded (LEAK); In-situ rain/soil are fixture/provenance-gated until partner feed.
- Phone install needs icons (192/512 shipped); QR uses same LAN URL; stale tile cache is app shell only — `/api` is network-only by sw.js.

## One-command check before the judge walks in

```powershell
curl http://localhost:8000/health
curl "http://localhost:8000/api/warning/state?location=gangtok" | Select-String "corridor_state"
curl "http://localhost:8000/api/isolation?location=gangtok"     | Select-String "corridor_isolated"
curl "http://localhost:8000/api/alerts/auto/status"
curl "http://localhost:8000/api/roads/status?location=gangtok"   | Select-String "R2"
```