# TALUS — SIH26001 (NER Landslide Risk Intelligence)

**Branch:** `SIH26001` · **Problem statement:** AI-Based Early Warning and Landslide Risk Monitoring System in NER · **Org:** MDoNER, Disaster Management · **Category:** Software

This folder is the **single source of truth for the SIH26001 track**. TALUS v1 docs (`docs/00_*`–`08_*`, landslide, SIH26001) stay frozen on `main` and are referenced — never edited — from here.

## Relationship to TALUS v1

| Layer | v1 | v2 (NER landslide, frozen 2025-11-15) | Status |
|---|---|---|---|
| Architecture pattern (ML + physics sim, calibrated confidence, SHAP, role decisions, risk-weighted Dijkstra, missing-evidence) | mine | NER | **Survives intact** (+ isolation + SWI + warning 6-state) |
| Data pipeline | synthetic generator v1.4.0 | **NGEN** — real NER geospatial ETL (IMD 0.25° 1901–2024 + CCI v09.2 1978–2024 + SRTM n27_e088 + Sentinel-2 + WorldCover + GSI 30k + OSM 1014/226/504 + USGS 26 quakes) | Rewrite |
| Physics chain | bench FoS | rainfall → infiltration → **SWI JMA 3-tank** `swi.py:14` → pore pressure → FoS + isolation R4 bottleneck | Rewrite |
| Features | 12 mine | **17 numeric + lulc (22 cols sample)** `feature_matrix.sample.csv:1` (spi→spi_log + seismic 3 + wound 4/2936), lithology/lineament omitted uniform | New contract |
| Training labels | synthetic FoS | real historical landslide events 2936 rows 1468+1468, season-window proxy tagged `approximate` | Stronger evidence |
| Model | RF | **RF 0.9338 XGB 0.9418 LGBM 0.9406** `metrics.md:9` + isotonic Brier 0.0971 + Bayes 0.5→0.01 | Retrained live |
| Roles | worker / safety officer / mine manager / rescue | villager / district / state / rescue + **admin** `/admin` PINs (Yellow/Red kits) | Remapped |
| UI | mine zone map | GIS heatmap 5-band + RoadStatus + IsolationAlert + WarningState 6 + RiskTrend NOW + Admin | Rebuild on same pattern |
| Offline | — | **PWA** `sw.js:1` + `manifest.webmanifest:1` 192/512 + outbox `talus_report_outbox` | New |
| Cloud | — | **docker-compose.prod.yml (postgis:16-3.4, https://talus-sih26001.onrender.com/health via docs/LIVE_HOST_EVIDENCE.md):1** PostGIS 16-3.4 + auto watcher + IMD_API_KEY gated live | New |

## Doc map

| Doc | Purpose | Source |
|---|---|---|
| `00_PROJECT_BRIEF_SIH26001.md` | Scope firewall — what v2 is / is not (12 slopes, 35/35 tests, scaffold 89/78/66/52) | Research §2, §11 |
| `01_REQUIREMENTS_SIH26001.md` | FR/NFR + acceptance criteria (FR-01..13 all built, 35/35 live, scaffold frozen) | Research §2.2 |
| `02_ARCHITECTURE_SIH26001.md` | Module mapping, NGEN pipeline, isolation `/_isolation_for_location/`, SWI `swi.py`, warning 6-state, cloud PostGIS | Research §8 |
| `03_DATA_PLAN_SIH26001.md` | Sources, provenance 22-col, training construction (CCI v09.2 + WorldCover + OSM 1014/226/504 + Bhukosh timeout + USGS 26) | Research §6, §9.2 |
| `04_MODEL_PLAN_SIH26001.md` | Model selection, validation protocol (GroupKFold8 OOF 0.9338/0.9418, temporal 0.8568 Brier 0.0978) | Research §7.5, §9.3–9.4 |
| `05_FEATURE_SCHEMA_SIH26001.md` | Frozen 17 numeric+lulc / 22-col ML contract (wound 4/2936, SWI/warning overlays) | Research §7.3 |
| `06_DEMO_SCENARIO_SIH26001.md` | Demo narrative frozen 2025-11-15 (8 screens + Admin, history NOW slider, PWA offline proof) | — |
| `07_ASSUMPTIONS_SIH26001.md` | Working assumptions, each falsifiable (CCI, SRTM D8, OSM 1014/226/504 demo topology, Bhukosh timeout) | Research §6–§9 |
| `08_LIMITATIONS_SIH26001.md` | Honest limits — say proactively (Bhukosh PROXY, OSM demo topology, IMD live needs key, 12 slopes ≠ Panchayat) | Research §11.3–11.4 |
| `ML_MODEL_CARD_V2.md` | Model card 2025-11-14 (2936 1468+1468, NUMERIC 17, GroupKFold8 0.9338/0.9418, Brier 0.0971→0.0978, wound 4/2936) | — |
| `decisions/ADR-001-sih26001-scope.md` | Why migrate (not fork), why real data | Research §1, §9.1 |
| `../../SIH26001_RESEARCH.md` (in `docs/`) | Full research & strategy (fact-checked) | — |

## Endpoints (frozen 2025-11-15, 35/35 tests)

`GET /health / /api/zones /api/zones/{id}/features/trend/explanation/decision/history/exposure` · `POST /api/risk/predict /api/routes/safe /api/simulation/what-if /causal-what-if` · `GET /api/simulation/templates /api/roads/status /restrictions /api/isolation /api/warning/state /api/soil/swi /api/model/calib /api/forecast/rainfall /live /imd-live /api/replay/series /api/runout/exposure /api/wounds + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` · `POST+GET /api/reports/queue PATCH /api/reports/{id} POST /api/alerts/dispatch + log/ack + auto/status+trigger` (see `backend/app/main.py:1`).

## Roadmap (built — frozen 2025-11-15)

- **Phase 0 — done (3 corridors):** `124` IMD files `ind*.nc` 1901–2024 + USGS `n27_e088` + `30k` GSI inventory `+7` Gangtok PDF → `693` Sikkim join + `764` deduped + `26` USGS quakes `usgs_quakes.json:1`, `CCI soil v09.2 1978–2024` `0.271` `manifest.sample.json:22` + `SWI` `swi.py:14`, `WorldCover N27E087` `S2B_45RXL_20241129` 10m, `OSM 1014/226/504` `roads_osm_provenance.json:1` (+ demo topology R1–R4), `warning_thresholds.json:1` 385/395/410/375, `Bhukosh timeout` `bhukosh_vector_attempt.json:1`.
- **Phase 1 — done (2936):** `2936` rows `build_training_matrix.py:1` 1468+1468 17 numeric+lulc 22 cols → **RF 0.9338 XGB 0.9418** `metrics.md:9` + **Brier 0.0971** `calibration.md:8` + **temporal 673/73 Brier 0.0978** `metrics.md:32` + TreeSHAP top-4 `sih26001_model.py:explain_row` + wound 4/2936 `wound_as_feature.json:1` + Bayes 0.5→0.01 `GET /api/model/calib`.
- **Phase 2 — done (GIS):**Fixtures `S1 89 S2 78 S3 66 S4 52` `slopes.json:1` ×3 corridors `locations.json:1`, `RiskMap` 5-band + `RoadStatusCard` + `IsolationAlertCard` `_isolation_for_location:1326` R4 bottleneck `may_isolate` + `WarningStateCard` 6 states + `RiskTrendChart` 365-day NOW `main.py:379` + `AdminPanel` `/admin` PINs, rainfall-threshold `monga-mdl/dahal-144` + SWI `tanh`.
- **Phase 3 — done (field + live):** field reporting `POST /api/reports` + `PATCH review` + `queue?status` `photo {sha256,exif}` + `consent` + `flagged` (`test_reports.py:1` env-gated), SMS `en/hi/ne/as/bn` fixture `alerts.json:1` + env-gated `SMS_PROVIDER` + auto watcher `60s/3600s` `main.py:1702` + log, `Open-Meteo 7-day` `GET /api/forecast/live:1154` + `IMD_API_KEY` gated `GET /api/forecast/imd-live:1124` (1h cache), exposure `GET /api/zones/{id}/exposure` operational risk, PWA `sw.js:1` + `manifest.webmanifest:1` 192/512 + outbox `talus_report_outbox`, exposure/runout/wound/replay ledgers `evidence/*.json`.
- **Phase 4 — done (cloud):** `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) PostGIS 16-3.4 `pg_isready` + `AUTO_ALERT_*` + `DATABASE_URL` + `runs:/app/runs` vol + healthcheck; frontend served via api static `frontend/dist`.

## Rules (inherit from `/CONTRIBUTING.md`)

- This branch is the integration branch for the SIH26001 track. Feature work branches off it as `feature/sih26001/<name>`.
- Conventional commits (`feat:`, `fix:`, `docs:`, …).
- Never commit datasets or model weights — metadata only (`ml/models/*.joblib` git-ignored, sha256 in manifest, `sih26001_model.py` honest fallback to fixture when absent).
- If behavior changes, update the matching doc in this folder in the same PR.
- `docs/SIH26001_RESEARCH.md` is evidence; these docs are the build contract. If they conflict, the contract wins and the research doc gets a correction note.
- Do not cite stale numbers (0.8983/0.9029/0.118/0.8189). Current truth is **0.9338/0.9418/0.0971/0.8568 Brier 0.0978** (2025-11-14 `ml/sih26001/reports/metrics.md:9` `calibration.md:8`).

## Verifying the build

```bash
# 35/35 live tests (fixture path always passes; live forecast needs network or env-gated key)
py -m pytest backend/tests -q  # 9 suites 60 funcs inside, scaffold 89/78/66/52 contract enforced
# Run the app (live RF when ml/models/sih26001_*v1.joblib present, else fixture honestly)
# IMD live blend: IMD_API_KEY=... py -m uvicorn backend.app.main:app --reload
# PWA: frontend/dist must include public/sw.js + manifest.webmanifest + icons 192/512
# Cloud: docker compose -f docker-compose.prod.yml (postgis:16-3.4, https://talus-sih26001.onrender.com/health via docs/LIVE_HOST_EVIDENCE.md) up --build (PostGIS + auto watcher)
```
