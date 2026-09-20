# TALUS — Current System (single source of truth)

Status: 2025-11-15. This document reflects what IS. If any other doc conflicts with this one, this one wins.

## Live architecture

```text
PREDICTION PATH (answers "what is the risk now?")
  12 NGEN rows (17 numeric + lulc, feature_matrix.sample.csv — REAL/PROXY, zero STUBs)
    -> sih26001_model.py Sih26001Live (RF 500 + isotonic) OR fixture fallback
       score = round(raw_proba*100), confidence = isotonic P, confidence_real_1pct = Bayes(pi_train 0.5→pi_real 0.01)
    -> FoS-derived risk band (Very Low <21 < Low <41 < Moderate <66 < High <85 < Critical)
    -> real TreeSHAP top-4 (shap.TreeExplainer) per zone — base_value + contributions

GIS + WARNING OVERLAY (scoring frozen, warning overlay only)
  effective_rain = rainfall_7d + 0.3*rainfall_30d  (Monga 390 separator, per-zone thresholds warning_thresholds.json)
  SWI 3-tank swi.py L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 -> tanh(SWI/100)
  wound BigGIS (Sentinel-2 NDVI loss) + forecast Open-Meteo + quake window (-25% thresholds)
  -> warning state NORMAL → WATCH → ALERT → CRITICAL → RESTRICT → EVACUATE (reason-stamped)

API (backend/app/main.py — FastAPI, 35/35 tests)
   GET  /health                                      (stores + fixture presence, version 0.1.0)
   GET  /api/db/status                               (fixture vs postgis:16-3.4, docs/LIVE_HOST_EVIDENCE.md)
   GET  /api/zones?location=gangtok|lachung|darjeeling
   GET  /api/zones  GET /api/zones/{id}/explanation (TreeSHAP)  GET /api/zones/{id}/exposure
   GET  /api/zones/{id} /features /trend /history /decision  (legacy grouping)
   GET  /api/warning/state (now NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE with reason stamps: effective rain 390 local thresholds warning_thresholds.json, SWI 3-tank swi.py L1=15 L2=60 L3=60, wound BigGIS, forecast Open-Meteo, quake 25% threshold drop)
   GET  /api/isolation?location=                     (R4 bottleneck, ISOLATED / MAY_ISOLATE / OPEN)
   GET  /api/soil/swi?location=                      (JMA 3-tank per zone, forecast blend)
   GET  /api/roads/status?location=                  (R1-R4 shifted per corridor)
   GET  /api/roads/restrictions?location=            (catalogue + evaluation)
   GET  /api/panchayat/tiles                         (100 tiles 10x10 26.95-28.05/88.05-89.0, frozen 12 untouched)
   GET  /api/terrain/copernicus                      (COP30 vs SRTM S1 28.3→28.7 Δ0.4)
   GET  /api/aws/gauges                              (Dense AWS 10-min 12 gauges MQTT QA)
   GET  /api/forecast/live?location=                 (Open-Meteo 7d, 1h cache)
   GET  /api/forecast/imd-live?location=             (IMD_API_KEY gated data.gov.in, fallback Open-Meteo)
   POST /api/alerts/dispatch?channel=app|sms&lang=&zone_id=&message=  (env-gated msg91/fast2sms/twilio/textbelt, logged to runs/alert_dispatch.jsonl)
   POST /api/alerts/cbe                             (bearer, simulated until DoT, logged runs/cbe_dispatch.jsonl, docs/CBE_CONTRACT.md)
   GET  /api/alerts/dispatch/log?limit=  POST /api/alerts/ack  GET /api/alerts/ack
   GET  /api/alerts/auto/status  POST /api/alerts/auto/trigger  (AUTO_ALERT_ENABLED, interval 60s, cooldown 3600s)
   POST /api/reports  GET /api/reports/queue?status=  PATCH /api/reports/{id}
   GET  /api/live/feed  GET /api/live/audit?limit=   (simulator or live_feed.sample.json)
   GET  /api/replay/series  GET /api/runout/exposure  GET /api/wounds  GET /api/model/calib?pi_real=0.01
   POST /api/risk/predict  POST /api/routes/safe  POST /api/simulation/what-if  POST /api/simulation/causal-what-if
   GET  /api/simulation/templates  GET /api/forecast/rainfall  (fixture fallback)
```

Frontend (VITE_USE_LIVE_API=true, PWA shell)
  RiskMap.jsx — 5-band heatmap (RISK_BANDS) + roads (OSM proven 1014/226/504 ways, roads_osm_provenance.json — geometry demo topology for deterministic R2 avoidance)
  IsolationAlertCard (GET /api/isolation), WarningStateCard (6 states, STATE_STYLE), RiskTrendChart (observed vs forecast, NOW line + 75/85 thresholds, causality label)
  RoadStatusCard (R1-R4 clean), QuickStatsBar (LIVE forecast badge from /api/forecast/live), AlertPanel (5 langs en/hi/ne/as/bn + channel app/sms toggle + dispatch log)
  RiskScoreGauge (villager words vs officer %), AdminPanel at /admin (PIN 9999 admin, 1111 district, 2222 state, 3333 rescue) — health / isolation / log / queue / provenance
  RoleSelector + LoginModal via services/auth.js (PINS, localStorage talus_auth)

GIS
  DEM: SRTM 30m n27_e088_1arc_v3.tif (GLO-30) · Soil: ESA CCI v09.2 1978-2024 · Rain: IMD 0.25° 1901-2024 historical (ind*_rfp25.nc) + Open-Meteo live
  Wound: Sentinel-2 L2A S2B_45RXL 2023-11-15 vs 2024-11-29 (2 scars near R2/R3, wound_map.json) · Runout: SRTM steepest-descent + OSM buildings/road meters · Quakes: USGS 26 M5+ (usgs_quakes.json)
  Panchayat: 100 tiles 10×10 26.95-28.05/88.05-89.0 panchayat_tiles.json · Copernicus: COP30 vs SRTM S1 28.7 Δ0.4 · AWS: 12 gauges 10-min aws_ingest.py

## 2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched)

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT

## Frozen artifacts

| Artifact | Location |
|---|---|
| NGEN sample (12 rows, 17+2 keys, zero STUBs) | `data/sih26001/fixtures/feature_matrix.sample.csv` + `manifest.sample.json` |
| Training matrix (2936 rows, 1468+1468) | `data/sih26001/processed/feature_matrix.training.csv` (git-ignored except .training.sample.csv) |
| Model v1 (RF 500 + XGB 400 + LGBM 400 + isotonic) | `ml/models/sih26001_rf_v1.joblib` + `sih26001_iso_v1.joblib` |
| Metrics | `ml/sih26001/reports/metrics.md` (GroupKFold(8) OOF RF 0.9338 XGB 0.9418) + `calibration.md` |
| Recalibration note | `docs/RECALIBRATION_NOTE.md` (Bayes 0.5→0.01, swi overlay warning-only) |
| SWI model | `backend/app/swi.py` (JMA 3-tank L1=15 L2=60 L3=60) |
| Warning thresholds | `data/sih26001/evidence/warning_thresholds.json` (per-zone effective rain 375-420) |
| OSM provenance | `data/sih26001/evidence/roads_osm_provenance.json` (1014/226/504 ways, NH310A trunk) |
| Panchayat tiling | `data/sih26001/evidence/panchayat_tiles.json` (100 tiles 10×10 26.95-28.05/88.05-89.0, GET /api/panchayat/tiles, frozen 12 untouched) |
| Copernicus COP30 | `data/sih26001/evidence/copernicus_dem_comparison.json` (S1 28.3→28.7 Δ0.4, GET /api/terrain/copernicus) |
| Dense AWS | `backend/app/aws_ingest.py` 12 gauges 10-min MQTT QA, GET /api/aws/gauges |
| PostGIS prod | `docker-compose.prod.yml` postgis:16-3.4 + GET /api/db/status → docs/LIVE_HOST_EVIDENCE.md https://talus-sih26001.onrender.com/health |
| CBE bearer | `docs/CBE_CONTRACT.md` POST /api/alerts/cbe → runs/cbe_dispatch.jsonl simulated until DoT |
| Offline | `frontend/public/sw.js` + `manifest.webmanifest` (icons 192/512) outbox `talus_report_outbox` |
| Cloud | `Dockerfile` (healthcheck curl /health) + `docker-compose.yml` + `docker-compose.prod.yml` (postgis:16-3.4) + `docs/DEPLOY_CLOUD.md` + `docs/LIVE_HOST_EVIDENCE.md` |

## Key results (real numbers — current OOF, no stale numbers)

- Training: 2936×22 (1468 pos Sikkim + Darjeeling-hills + 1468 background >300m), 17 numeric (spi log1p + seismic x3) + lulc one-hot.
- Spatial GroupKFold(8) (KMeans-8 on coords) OOF: RF 0.9338 / XGB 0.9418 / LGBM 0.9406 (Brier 0.118 / 0.1198 / 0.1392). LR baseline 0.8914.
- Temporal holdout (673/73 dated pos split): RF test AUC 0.8568.
- Calibration: isotonic RF Brier 0.0971 vs raw 0.118 (OOF). Confidence = calibrated P(elevated susceptibility), not landslide probability.
- Prevalence correction: `p_real = p_cal*0.02 / (p_cal*0.02 + (1-p_cal)*1.98)` — score frozen, `confidence_real_1pct` added. See RECALIBRATION_NOTE.md.
- Live scoring: `sih26001_model.py` live_scores via trained RF+isotonic; weights absent → honest fixture fallback (fixture scores from slopes.json).
- TreeSHAP: top-4 contributors per zone via shap.TreeExplainer (optional dep, fixture fallback when absent).

## Superseded / historical documents (do NOT implement from these)

| Doc | Status |
|---|---|
| docs/source/Talus_Data_Training_Plan.md | Historical; superseded by NGEN + metrics.md + this doc |
| docs/03_DATA_PLAN.md, 04_MODEL_PLAN.md, 05_API_SPEC.md (v1 Neyveli) | Historical — NER track (ml/sih26001, data/sih26001) is current |
| Old leakage / FoS / crack-chain notes (R² 0.998 etc.) | Neyveli generator era — not the NER landslide model |
| Any doc claiming old OOF numbers (pre-GroupKFold) | Stale — use metrics.md GroupKFold 0.9338/0.9418 above |

## Explicitly deferred

- CV crack imagery closed loop (offline-first field queue only).
- Real Bhukosh WFS lithology overlay (WFS timeout → PROXY-published-map; lithology uniform in X, omitted by design).
- Per-corridor isotonic reweight (<200 dated positives/corridor; needs region-specific calibration post-hackathon).
- Full POLARIMETRIC / InSAR validation.

## Known limitations (say before judges find them)

1. Bhukosh WFS timeout → lithology is PROXY-published map (uniform, excluded from X) — not hidden.
2. Road geometry is demo topology (centroid-aligned for deterministic R2 avoidance); OSM count 1014/226/504 is the honesty proof, not traced roads (roads_osm_provenance.json).
3. IMD live requires IMD_API_KEY (data.gov.in); absent → IMD-live falls back to Open-Meteo blend with labeled provenance.
4. Soil SWI overlays warning state only — scoring stays frozen on soil_moisture (CCI v09.2 quasi-static proxy).
5. Inventory 1991-2020 climatology / quasi-static proxies for time-varying inputs (tagged approximate); wound review queue (not confirmed cuts); in-situ rain/soil sensors are fixture/provenance-gated.
6. Temporal forecasting campaign CLOSED 2026-09-18 (M0 → VI-0 → VI-1 → VI-2 all falsified on the frozen 10-event held-out; sat-only AUC 0.500). The system is a spatial susceptibility + warning-decision system with explicit domain limits — it does not manufacture temporal certainty. See `docs/sih26001/EXPERIMENTS_E_LADDER.md` close-out + `docs/sih26001/FINAL_SCORECARDS_V1.md`.
