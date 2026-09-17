# TALUS — Evidence & Backup Slides (SIH26001 NER)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Companion to the main deck. Every chart/number below is from committed artifacts (metrics.md, evidence bundles) — regenerate via scripts/train_sih26001.py + evidence builders. Use when a judge asks to "see the data." Each exhibit ends with the one sentence to say.**

---

## Exhibit 1 — Model family convergence (no architecture bottleneck)

**What it shows:** GroupKFold(8) spatial OOF on 2936 rows — RF 0.9338, XGB 0.9418, LGBM 0.9406, LR 0.8914. 7-family study (Neyveli) converged ±0.02; NER trees again converge.

**Say:** *"The ceiling is feature information, not architecture. Trees are explainable, fast, tabular-appropriate — XGB 0.94 is the honest spatial OOF."*

Source: `ml/sih26001/reports/metrics.md:11-16` — GroupKFold(8) KMeans on coords.

---

## Exhibit 2 — Why spatial splitting matters

**What it shows:** per-held-out-cluster AUC (leave-one-cluster-out) — cluster_1 0.84-0.87, cluster_5 0.79-0.80, cluster_2 0.81-0.82 (lower), cluster_3/4 >0.98 (easy). Naive row shuffle would leak.

**Say:** *"We split by spatial clusters, not rows — nearby slopes aren't independent. The cluster table is the honesty proof."*

Source: `metrics.md:19-28` — per-cluster table.

---

## Exhibit 3 — Calibration (FR-03, recalibrated)

**What it shows:** Isotonic RF Brier 0.0971 vs raw 0.118 (OOF); per metrics the calibrated confidence is measured, not decorative. Bayes field correction `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` shown in `/api/model/calib?pi_real=0.01`.

**Say:** *"Confidence is calibrated P(elevated susceptibility) under the prototype window — and we show the field-corrected ~1% view separately. Never 'probability of landslide tomorrow'."*

Source: `ml/sih26001/reports/calibration.md:5-9`, `docs/RECALIBRATION_NOTE.md`, `GET /api/model/calib`.

---

## Exhibit 4 — Feature importance (screening)

**What it shows:** Permutation importance (in-sample screening, RF full-data) — elevation, seismic_n50_rate, distance_to_road dominate; many NER features ≈0 in that screening. TreeSHAP top-4 per zone (live) agrees directionally with physics.

**Say:** *"Drivers match intuition — elevation/road proximity/seismic history — but the per-zone SHAP is what the officer sees."*

Caveat: inventory-season proxy confounds dynamic drivers; quasi-static soil tagged approximate.

Source: `metrics.md:38-60` + live `GET /api/zones/{id}/explanation (TreeSHAP)` and `GET /api/zones/{id}/exposure`, `sih26001_model.py` live_scores, `RECALIBRATION_NOTE.md` (Bayes p_real 0.5→0.01) and swi overlay.

---

## Exhibit 5 — Threshold consistency (Dahal/Monga screens)

**What it shows:** June-total 390mm separator (8736 pts above), median JJAS daily-max 546.8mm; Dahal 144mm is event-intensity, not daily-max climatology — hence 19.07% exceedance is a screen, not validation.

**Say:** *"We screen thresholds, we don't claim we beat Dahal with a climatology proxy."*

Source: `metrics.md:31-37`.

---

## Exhibit 6 — One corridor year / trend (Zone detail)

**What it shows:** deterministic histories per zone (slopes.json histories, `GET /api/zones/{id}/history?seed=91` for Neyveli lineage; NER trend is live `rapidly_increasing` vs stable) plus RiskTrendChart observed ◀ vs forecast ▶ (NOW line, thresholds 75/85).

**Say:** *"Trend rises are scored live; the replay bundle (`GET /api/replay/series`) proves causality (inputs available ON each date only)."*

Source: `GET /api/replay/series`, `GET /api/zones/{id}/trend`.

---

## Exhibit 7 — Warning state vs score (the escalation demo)

**What it shows:** `GET /api/warning/state (now NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE with reason stamps: effective rain 390 local thresholds warning_thresholds.json, SWI 3-tank swi.py L1=15 L2=60 L3=60, wound BigGIS, forecast Open-Meteo, quake 25% threshold drop)` — per-zone 6 states. `GET /api/isolation`, `GET /api/soil/swi`, `GET /api/roads/status` + `GET /api/roads/restrictions (catalogue)`, `GET /api/forecast/live` + `GET /api/forecast/imd-live (IMD_API_KEY gated, fallback Open-Meteo)`, `POST /api/alerts/dispatch (channel app|sms, env-gated msg91/fast2sms/twilio/textbelt, logged to runs/alert_dispatch.jsonl)`, `GET /api/zones/{id}/explanation (TreeSHAP)` + `GET /api/zones/{id}/exposure` exposed live. Isolation overlay pushes to RESTRICT/EVACUATE.

**Say:** *"Acute shock ≠ accumulated deterioration — the warning layer knows the difference, and it never mutates the frozen score."*

Source: `backend/app/main.py` `_WARN_STATES`, `_warning_exposure`, `data/sih26001/evidence/warning_thresholds.json`, `backend/app/swi.py`.

---

## Exhibit 8 — GIS honesty (OSM proven, geometry demo)

**What it shows:** Overpass counts 1014 Gangtok (NH310A trunk verified), 226 Lachung, 504 Darjeeling — `roads_osm_provenance.json` (fetched 2025-11-14). R1-R4 geometry is centroid-aligned demo topology for deterministic R2 avoidance (shortest crosses R2, safe diverts). Count is proof, geometry is pedagogy.

**Say:** *"We proved roads exist — we drew them pedagogically so every demo deterministically avoids R2."*

Source: `data/sih26001/evidence/roads_osm_provenance.json`, `GET /api/roads/status?location=`.

---

## Quick-reference numbers (memorize — current, no stale numbers)

| Claim | Number | Source |
|---|---|---|
| Training | 2936 rows (1468+1468), 17 numeric + lulc | metrics.md:5 |
| Spatial GroupKFold(8) OOF | RF 0.9338 XGB 0.9418 LGBM 0.9406 LR 0.8914 | metrics.md:13-16 |
| Calibration | Brier 0.0971 isotonic vs 0.118 raw | calibration.md:8 |
| Temporal holdout | 673/73 dated → RF test 0.8568 | metrics.md:31-35 |
| Recalibration | pi 0.5→0.01 Bayes, score frozen | RECALIBRATION_NOTE |
| Warning | 6 states, effective rain 390 local, SWI 3-tank L1=15 L2=60 L3=60 | warning_thresholds.json, swi.py |
| Wound | 2 scars (R2 Δ0.457, R3 Δ0.436) Sentinel-2 matched | wound_map.json |
| OSM | 1014 / 226 / 504 ways | roads_osm_provenance.json |
| Backend tests | 35/35 (45 incl. routing/NGEN validator) | pytest |
| Field | POST /api/reports outbox talus_report_outbox, PWA 192/512 | sw.js, manifest |
| Cloud | Dockerfile curl /health, compose + prod postgis | DEPLOY_CLOUD.md |

## Regeneration

Metrics: `python scripts/train_sih26001.py` (needs xgb/lgbm/shap). Evidence: `scripts/wound_map.py`, `runout_exposure.py`, `build_replay_series.py` (committed bundles). OSM: Overpass queries in `roads_osm_provenance.json`.

## Claims policy (read before improvising)

REAL/PROXY tagged per feature, zero STUBs · confidence = calibrated P(elevated susceptibility) + Bayes field view (RECALIBRATION_NOTE.md 0.5→0.01) · bands prototype · SHAP explains model not slope · Bhukosh WFS timeout → PROXY-published-map · OSM geometry demo topology · IMD live requires IMD_API_KEY · lithology uniform · final decisions with qualified personnel.

Frontend: `RiskMap.jsx` 5-band heatmap + roads OSM proven 1014/226/504 ways `roads_osm_provenance.json` geometry demo topology · `IsolationAlertCard` · `WarningStateCard` with 6 states · `RiskTrendChart` observed vs forecast separation (NOW line) · `RoadStatusCard` clean · `QuickStatsBar` LIVE forecast badge · `AlertPanel` with 5 langs en/hi/ne/as/bn + channel toggle · `RiskScoreGauge` clean · `AdminPanel` at `/admin` (PIN 9999/1111/2222/3333) with health/isolation/log/queue/provenance, `RoleSelector` PIN gate via `services/auth.js`, `LoginModal` · GIS: SRTM 30m `n27_e088_1arc_v3.tif`, CCI soil v09.2, IMD 0.25° historical + Open-Meteo live, Sentinel2 wound 2 scars, SRTM runout, USGS quakes 26 M5+ · Offline: PWA `sw.js` + `manifest.webmanifest` icons 192/512, outbox `talus_report_outbox` · Cloud: `Dockerfile` healthcheck `curl /health`, `docker-compose.yml` + `docker-compose.prod.yml` postgis, `docs/DEPLOY_CLOUD.md`.

Backend truth (2025-11-15): FastAPI at `backend/app/main.py` with 35/35 tests, endpoints: `/health`, `/api/zones`, `/api/zones/{id}/explanation (TreeSHAP)`, `/api/zones/{id}/exposure`, `/api/warning/state (now NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE with reason stamps: effective rain 390 local thresholds warning_thresholds.json, SWI 3-tank swi.py L1=15 L2=60 L3=60, wound BigGIS, forecast Open-Meteo, quake 25% threshold drop)`, `/api/isolation`, `/api/soil/swi`, `/api/roads/status` + `/api/roads/restrictions (catalogue)`, `/api/forecast/live` + `/api/forecast/imd-live (IMD_API_KEY gated, fallback Open-Meteo)`, `/api/alerts/dispatch (channel app|sms, env-gated msg91/fast2sms/twilio/textbelt, logged to runs/alert_dispatch.jsonl)`, auto watcher (`AUTO_ALERT_ENABLED`, interval 60s, cooldown 3600s, `/api/alerts/auto/status`+`trigger`), `/api/reports`, `/api/live/feed`, `/api/replay/series`, `/api/runout/exposure`, `/api/wounds`, `/api/model/calib (Bayes p_real 0.5→0.01)` · Model: RF 500 + XGB 400 + LGBM 400 + isotonic, 2936 rows (1468+1468), 17 numeric + lulc, GroupKFold(8) OOF RF 0.9338 XGB 0.9418, `sih26001_model.py` live_scores or fixture fallback, TreeSHAP top-4.