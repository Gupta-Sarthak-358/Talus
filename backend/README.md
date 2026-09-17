# backend — Talus SIH26001 (2025-11-15)

FastAPI backend serving the 12-slope NER decision-support API. Frozen, 35/35 green, scaffold 89/78/66/52, `live_scores` when weights present else honest fixture. **2025-11-15 WILL→PARTIAL:** Panchayat 100 tiles `GET /api/panchayat/tiles`, Copernicus `GET /api/terrain/copernicus` S1 28.3→28.7 Δ0.4, AWS 12 gauges `GET /api/aws/gauges`, PostGIS `GET /api/db/status`, CBE `POST /api/alerts/cbe`.

## Run it

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # http://127.0.0.1:8000  GET /health  GET /api/zones
python -m pytest -q                        # 35/35  (scaffold 89/78/66/52 lives in data/sih26001/fixtures/slopes.json)
```

## Endpoints (frozen 2025-11-15)

```
GET  /health                                            (stores gangtok/lachung/darjeeling + fixture presence)
GET  /api/zones?location=gangtok|lachung|darjeeling     (scaffold 89/78/66/52 or live-rf via sih26001_model.py)
GET  /api/zones/{id} /features /trend /history /decision  (legacy grouping + lang en/hi/ne/as/bn)
GET  /api/zones/{id}/explanation                        (TreeSHAP top-5 live via shap.TreeExplainer or fixture)
GET  /api/zones/{id}/exposure                           (operational risk: runout 85 buildings + wound 2 scars + isolation R4)

GET  /api/warning/state?location=                       (6-state NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE)
                                                        effective=rainfall_7d+0.3*30d per-zone thresholds warning_thresholds.json
                                                        (S1 385 S2 395 S3 410 S4 375 … N1 380 … D1 400; plus SWI 3-tank swi.py L1=15 L2=60 L3=60 tanh(SWI/100)
                                                         wound BigGIS Sentinel-2 2 scars + forecast Open-Meteo + quake 25% drop)
GET  /api/isolation?location=                           (R4 bottleneck ISOLATED/MAY_ISOLATE)
GET  /api/soil/swi?location=                            (JMA 3-tank per zone, forecast blend)

GET  /api/roads/status?location=                        (R1–R4 shifted per corridor; OSM proven 1014/226/504 ways, geometry demo topology)
GET  /api/roads/restrictions?location=                  (catalogue + evaluation; road_restriction_catalogue.json)

GET  /api/forecast/live?location=                       (Open-Meteo 7d, 1h cache)
GET  /api/forecast/imd-live?location=                   (IMD_API_KEY gated data.gov.in, fallback Open-Meteo)

POST /api/alerts/dispatch?channel=app|sms&lang=&zone_id=&message=  (env-gated msg91/fast2sms/twilio/textbelt, logged runs/alert_dispatch.jsonl)
GET  /api/alerts/dispatch/log?limit=   POST /api/alerts/ack  GET /api/alerts/ack
GET  /api/alerts/auto/status  POST /api/alerts/auto/trigger (AUTO_ALERT_ENABLED interval 60s cooldown 3600s)

POST /api/reports  GET /api/reports/queue?status=  PATCH /api/reports/{id}  (20/session cap, consent, EXIF >200m flagged, outbox talus_report_outbox)
GET  /api/db/status                               (fixture vs postgis:16-3.4, docs/LIVE_HOST_EVIDENCE.md)
GET  /api/panchayat/tiles                       (100 tiles 10×10 26.95-28.05/88.05-89.0)
GET  /api/terrain/copernicus                    (COP30 vs SRTM S1 28.3→28.7 Δ0.4)
GET  /api/aws/gauges                            (Dense AWS 10-min 12 gauges MQTT QA)

GET  /api/live/feed  GET /api/live/audit?limit=        (simulator or live_feed.sample.json)
GET  /api/replay/series  GET /api/runout/exposure  GET /api/wounds  GET /api/model/calib?pi_real=0.01  (Bayes 0.5→0.01)
POST /api/alerts/cbe                           (bearer, simulated until DoT, docs/CBE_CONTRACT.md)

POST /api/risk/predict  POST /api/routes/safe  POST /api/simulation/what-if  POST /api/simulation/causal-what-if
GET  /api/simulation/templates  GET /api/forecast/rainfall
```

Scoring: `sih26001_model.py` Sih26001Live — RF 500 + isotonic (`ml/models/sih26001_rf_v1.joblib`, `sih26001_iso_v1.joblib`) → `score=round(p_raw*100)` 5-band 85/66/41/21, `confidence=isotonic P`, `confidence_real_1pct=Bayes(p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98))`. Weights absent → honest fixture fallback 89/78/66/52 `check_scaffold.py`. Warning/isolation overlay never changes score.

## Structure

- `app/main.py` — FastAPI 0.1.0 (`35/35`): all routes above + CORS + `DECISIONS_BY_BAND` en/hi/ne/as/bn + road graphs per corridor + rate limiting.
- `app/sih26001_model.py` — live scorer: loads RF+isotonic, `live_scores` flag, `explain_row()` TreeSHAP top-5.
- `app/data.py` — `ZoneStore` per location (gangtok/lachung/darjeeling), `risk_band()`, `missing_evidence()`, `distance()`, `interpolate()`, `ZoneCenters/Graph` per corridor.
- `app/swi.py` — JMA 3-tank SWI `L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 tanh(SWI/100)`.
- `app/schemas.py` — Pydantic (17 numeric + lulc, `ZoneSummary/Detail/Features/Trend/Explanation/Decision/Route/Report`).
- `app/model_service.py` / `scenario_service.py` — legacy model/scenario compat shims.
- `tests/` — `test_api.py`, `test_reports.py`, `test_warning_state.py`, `test_live_feed.py`, `test_wounds.py`, `test_runout_exposure.py`, `test_multiloc_routes_roads.py`, `test_alerts_ack.py`, `test_causal.py` (`35/35`).
- `../data/sih26001/` — `fixtures/` (slopes 89/78/66/52, roads R2 at-risk, reports, forecast, manifest 12 rows zero STUBs) + `evidence/` (roads_osm_provenance 1014/226/504, warning_thresholds S1 385…, wound 2, runout 85, usgs 26, soil/rain extracts).

## What is live vs fixture

- **Live when weights present:** `sih26001_model.py` RF 500 + isotonic + TreeSHAP top-5 (`live_scores=true` in `/health` + `scoring: live-rf` in `/api/zones` + `QuickStatsBar` LIVE badge).
- **Fixture when absent:** `slopes.json` 89/78/66/52 + recorded SHAP (honest fallback, validator `check_scaffold.py`).
- **Env-gated:** SMS (`SMS_PROVIDER=SMS_API_KEY`, `AUTO_ALERT_ENABLED`, `AUTO_ALERT_SMS`), IMD live (`IMD_API_KEY`, else fallback Open-Meteo labeled, `IMD_API_KEY` required live source), `DATABASE_URL` (PostGIS postgis extension, else file-backed `ZoneStore`).
- **Honesty tags:** lithology PROXY uniform omitted from X (Bhukosh timeout 15s), OSM demo topology (counts 1014/226/504 proven), SWI warning-only, quarantine proxies `approximate`, wound review queue.

## Cloud

`Dockerfile` (`curl /health` healthcheck) + `docker-compose.yml` + `docker-compose.prod.yml` (postgis `CREATE EXTENSION postgis`) → `docs/DEPLOY_CLOUD.md`. Health probes: `GET /health` + `GET /api/isolation` + `GET /api/alerts/auto/status`.

See `docs/CURRENT_SYSTEM.md` (single source of truth, 2025-11-15), `docs/RECALIBRATION_NOTE.md` (Bayes), `ml/sih26001/reports/metrics.md` (0.9338) + `calibration.md` (0.0971).