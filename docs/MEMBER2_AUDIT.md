# Member 2 — Final Audit (SIH26001 · 2025-11-14)

Status: CLOSED. All items verified against 2025-11-15 truth. This replaces the Neyveli generator-era audit (synthetic worlds, FoS memoryless) — retained in git history only.

## 2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched)

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT

## Frozen artifacts (2025-11-15)

| Artifact | State | Reference |
|---|---|---|
| NGEN sample | FROZEN, 12 rows 17 numeric + lulc, zero STUBs | `data/sih26001/fixtures/feature_matrix.sample.csv` + `manifest.sample.json` |
| Training matrix | FROZEN, 2936×22 (1468+1468 Sikkim + Darjeeling-hills) | `data/sih26001/processed/feature_matrix.training.csv` (sample committed) |
| Model v1 | FROZEN (RF 500 trees + XGB 400 + LGBM 400 + isotonic) | `ml/models/sih26001_rf_v1.joblib` / `sih26001_iso_v1.joblib` / `ml/sih26001/reports/metrics.md` |
| Feature contract | FROZEN — 17 numeric (spi log1p + seismic×3) + lulc one-hot; lithology/lineament uniform PROXY omitted, previous_landslide omitted (leakage) | `manifest.training.json` + `CURRENT_SYSTEM.md` |
| Warning model | FROZEN — 6-state `NORMAL→EVACUATE`, per-zone thresholds `warning_thresholds.json` (S1 385 etc), SWI 3-tank `swi.py` L1=15 L2=60 L3=60, wound+forecast+quake overlays | `backend/app/swi.py` + `backend/app/main.py` |
| Recalibration | FROZEN — Bayes pi_train 0.5 → pi_real 0.01, score frozen, `confidence_real_1pct` added; SWI overlays warning only | `docs/RECALIBRATION_NOTE.md` + `GET /api/model/calib` |
| Scaffold | FROZEN — `89/78/66/52` S1-S4, 5-band 85/66/41/21, 4 roles | `data/sih26001/fixtures/slopes.json` + `scripts/check_scaffold.py` |
| GIS evidence | FROZEN — SRTM n27_e088 30m, CCI v09.2 1978-2024, IMD 1901-2024 + live, Sentinel-2 2 scars, USGS 26 quakes, OSM 1014/226/504 | `data/sih26001/evidence/` |
| Backend | FROZEN — FastAPI 35/35 live tests | `backend/app/main.py` + `backend/tests/` |
| Frontend | FROZEN — RiskMap 5-band 1014/226/504 OSM proven geometry demo topology, WarningStateCard 6 states, PWA sw.js + manifest 192/512 | `frontend/src/` |

## Evidence chain (2025-11-15)

| Claim | Evidence |
|---|---|
| 2936 real rows, not synthetic | `manifest.training.json: pos 1468 / neg 1468`, `metrics.md: n=2936` |
| GroupKFold(8) spatial OOF honest | `metrics.md: KMeans-8 on coords, RF 0.9338 XGB 0.9418 LGBM 0.9406, LR 0.8914` |
| Brier 0.0971 isotonic | `calibration.md: RF raw 0.118 → isotonic 0.0971` |
| Temporal 0.8568 on 807 | `metrics.md: 673/73 dated pos, test_n 807, rf_test AUC 0.8568 Brier 0.0978` |
| TreeSHAP live per zone | `sih26001_model.py: shap.TreeExplainer top-5, fixture fallback when shap absent` |
| Bayes 0.5→0.01 | `RECALIBRATION_NOTE.md: p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` |
| SWI 3-tank JMA | `swi.py: L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 tanh(SWI/100)` |
| Warning 6-state with reason stamps | `warning_thresholds.json: S1 385 S2 395 S3 410 S4 375… L1=15…` + `test_warning_state.py` |
| Quake 25% drop | `main.py: quake window → thresholds *0.75` |
| Roads 1014/226/504 proven | `roads_osm_provenance.json: OSM ways proven, geometry demo topology, R2 deterministic avoidance` |
| Isolation R4 bottleneck | `data.py: /api/isolation, ISOLATED/MAY_ISOLATE` |
| Roads restrictions catalogue | `road_restriction_catalogue.json → GET /api/roads/restrictions` |
| Forecast live + IMD-live | `GET /api/forecast/live (Open-Meteo 1h cache) + /api/forecast/imd-live (IMD_API_KEY, fallback Open-Meteo)` |
| Alerts app\|sms + auto watcher | `POST /api/alerts/dispatch channel app|sms (msg91/fast2sms/twilio/textbelt), AUTO_ALERT_ENABLED 60s/3600s, GET /api/alerts/auto/status` |
| Live feed + replay + runout + wounds | `GET /api/live/feed, /api/replay/series, /api/runout/exposure (85 buildings), /api/wounds (2 scars)` |
| 35/35 backend, scaffold 89/78/66/52 | `pytest -q 35 passed, check_scaffold.py EXPECTED_SCORES 89/78/66/52` |
| PWA offline + outbox | `frontend/public/sw.js + manifest.webmanifest 192/512, talus_report_outbox` |
| Docker curl /health + postgis | `Dockerfile HEALTHCHECK curl /health, docker-compose.prod.yml postgis` |

## Validation gates (final state 2025-11-14)

Backend `pytest -q`: **35/35 PASS** (`test_reports`, `test_warning_state`, `test_live_feed`, `test_wounds`, `test_runout_exposure`, `test_multiloc_routes_roads`, `test_alerts_ack`, `test_api`, `test_causal`).

Scaffold `python scripts/check_scaffold.py`: **Scaffold OK** — slopes 89/78/66/52 + bands 85/66/41/21, R2 at-risk + risk-aware avoids R2, alerts en/hi/ne, NGEN 17+5 cols.

NGEN `python scripts/validate_ngen_sample.py`: **12 rows, zero STUBs, 17 numeric + lulc**.

## Known limitations (shipped honestly, 2025-11-14)

1. Lithology uniform PROXY-published-map (Bhukosh WFS timeout 15s) — omitted from X by design.
2. Road geometry demo topology (counts 1014/226/504 proven, not traced) — deterministic R2 avoidance.
3. IMD live requires `IMD_API_KEY` (`data.gov.in`); absent → fallback Open-Meteo (labeled).
4. Soil SWI overlays warning state only — scoring stays frozen on CCI quasi-static `soil_moisture`.
5. Quasi-static proxies for time-varying inputs tagged `approximate`; wound review queue (not confirmed cuts); sensors fixture-ready.
6. 12 NGEN slopes — corridor pattern proven, region-wide tiling is next.

## Superseded

All Neyveli generator content (generator v1.4.0, 50-world corpus, FoS memoryless, V2 trends refuted, Scenario Engine v1.5 mine tracks, R² 0.998) is **historical** — see `docs/CURRENT_SYSTEM.md` Superseded table. Do not implement from it.

## Handoff to Member 3

- Prediction path: 12 NGEN rows → `sih26001_model.py` Sih26001Live (RF + isotonic) → `score = round(p_raw*100)`, `confidence = isotonic`, `confidence_real_1pct = Bayes` → 5-band + TreeSHAP top-5 → `GET /api/zones` / `explanation` / `exposure`.
- Warning/isolation path: effective rain + SWI 3-tank + wound + forecast + quake → `GET /api/warning/state` (6 states, reason-stamped) + `GET /api/isolation` (R4) → `WarningStateCard` + `IsolationAlertCard`.
- Integration contract: consume `live_scores` when `ml/models/sih26001_*_v1.joblib` present, else fixture `89/78/66/52`; never route scores around `sih26001_model.py`; routing via `routing/` risk-aware Dijkstra; roles via `DECISIONS_BY_BAND` en/hi/ne/as/bn + `services/auth.js` PINs (9999/1111/2222/3333).
