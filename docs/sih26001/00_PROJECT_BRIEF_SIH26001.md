# TALUS Project Brief — SIH26001

**Status:** Built — frozen 2025-11-15 · **Branch:** `SIH26001` · **Context:** SIH 2026, SIH26001 track · **Date:** 2026-09-03 → 2025-11-15 · **Trace to:** `docs/SIH26001_RESEARCH.md` §1–§2

This is the **scope firewall for the SIH26001 track**. If a proposal conflicts with this brief, this document wins until amended via ADR.

---

## Problem

The North Eastern Region (8 states: Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura) faces frequent monsoon landslides, flash floods, road blockages, and slope failures from heavy rainfall, fragile terrain, and unplanned hill cutting. Incidents disrupt connectivity, damage infrastructure, delay emergency response, and isolate remote villages for days.

The current state:

- **Reactive monitoring** — dependent on manual reporting after events.
- **Threshold-only forecasting** — GSI RLFS uses rainfall thresholds; no AI/ML, no soil moisture, no satellite, no per-slope prediction.
- **No decision layer** — no role-based emergency prioritisation, no road connectivity tracking, no risk-aware routing, no offline support.

GSI has publicly listed "integration of AI/ML as a decision-support layer" as their next advancement initiative. That gap is this project.

## Problem Statement

**AI-Based Early Warning and Landslide Risk Monitoring System in NER** (SIH26001, MDoNER, Disaster Management, Software).

## Solution

TALUS converts scattered NER geospatial signals into **explainable susceptibility** and **actionable emergency decisions**.

TALUS produces a slope/zone-level susceptibility score with stated confidence, explains *why* (TreeSHAP), tracks monsoon-driven escalation, and converts the result into **role-specific actions**:

- Villager / community → early warning in local language (en/hi/ne/as/bn), avoid-route guidance + Yellow/Red kit
- District officer → intervention / evacuation coordination, road closure / RESTRICT calls via warning state machine
- State manager → resource allocation, emergency prioritisation across corridors
- Rescue team → risk-aware access routing, deployment sequencing + isolation-aware rerouting

It also computes **road-status-aware routes** (risk-weighted Dijkstra over OSM-derived graph, R4 bottleneck), **isolation** (which village loses egress to valley/plains), and **rainfall-threshold what-if simulation** so an officer can test how forecast rain shifts risk. Observed vs forecast are separated: IMD 0.25° historical truth (1901–2024) vs Open-Meteo 7-day live blend (IMD_API_KEY gated).

## Core Differentiation

From:

> "What is the risk?"

To:

> "What should we do now — which road to avoid, which village first, where to send rescue, is anyone isolated, what data are we missing, and what if it rains tonight?"

Every susceptibility score carries **confidence** (calibrated + Bayes 0.5→0.01 field view) and a **list of missing evidence** — no bare black-box numbers. Who gets told what, in what words and language, and what action follows is part of the product, not an afterthought.

## System Philosophy

```text
Detect → Understand → Escalate → Decide → Act
```

(Unchanged from v1. The pattern survives; the data and physics change.)

## Core Modules

1. **NGEN data pipeline** — IMD 0.25° rainfall (1901–2024) + Open-Meteo live + IMD_API_KEY gated, CCI soil moisture v09.2 1978–2024 (ESA), SRTM DEM n27_e088, Sentinel-2 NDVI, ESA WorldCover LULC, GSI 30k landslide inventory + report PDF, OSM roads/rivers (1014/226/504 provenanced), USGS 26 quakes 1965–2024 → unified feature matrix.
2. **Feature processing** — 17 numeric + lulc categorical per spatial unit (22 cols sample, `feature_matrix.sample.csv:1`), wound feature 4/2936, missingness + provenance.
3. **Risk engine** — RF + XGB susceptibility score 0–100 + calibrated confidence + `confidence_real_1pct` (Bayes 0.5→0.01, `backend/app/sih26001_model.py:score_row` + `GET /api/model/calib`).
4. **Explainability** — TreeSHAP per prediction (top-4, `sih26001_model.py:explain_row`), isotonic calibration.
5. **Trend detection** — monsoon-season escalation + daily history slider (365-day `GET /api/zones/{id}/history:379` → `RiskTrendChart` NOW).
6. **Decision engine** — role-specific recommendations (4 NER roles + admin, `main.py:55` `DECISIONS_BY_BAND`) with Yellow/Red kits.
7. **Road graph + isolation** — OSM graph with per-segment status (open/at-risk/blocked), risk-aware routing (`POST /api/routes/safe:421`), isolation engine (`_isolation_for_location:1326` R4 bottleneck, may_isolate predictive), restriction catalogue (`GET /api/roads/restrictions:798`), exposure operational risk (`GET /api/zones/{id}/exposure:743`).
8. **Warning state machine** — 6 states NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE (`GET /api/warning/state:1449`), per-zone local thresholds 385/395/410/375 Gangtok (`warning_thresholds.json:6`), SWI 3-tank (`backend/app/swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01), quake-conditioned thresholds −25% for 6 mo after M5.5 <50km (USGS 26 events).
9. **Rainfall scenario engine** — threshold-based what-if (Monga 2026, Dahal & Hasegawa) + auto watcher (`AUTO_ALERT_*`, `_auto_watcher_loop:1702`).
10. **Field reporting** — geo-tagged photo/video upload (camera + GPS, offline outbox + `sw.js`/`manifest.webmanifest` 192/512) → `POST /api/reports:879` + `PATCH review`.
11. **Alerts** — SMS/app via env-gated provider (`POST /api/alerts/dispatch:959`, `GET /log:1062`), multilingual, offline-sync capable.
12. **Dashboard** — NER GIS heatmap 5-band (`RiskMap:RiskMap.jsx:1`), road status (`RoadStatusCard`), isolation (`IsolationAlertCard`), warning (`WarningStateCard` 6 states), history slider, admin panel (`/admin` PINs 9999/1111/2222/3333).

## MVP (built — frozen 2025-11-15)

- NGEN pipeline over 3 corridors — Gangtok S1–S4 + Lachung N1–N4 + Darjeeling D1–D4 = 12 demo slopes, `feature_matrix.sample.csv:1` 12 rows ×22 cols + `manifest.sample.json:1`
- FR-01..13 all built · 35/35 live tests (60 test funcs across 9 suites, scaffold contract S1 89 S2 78 S3 66 S4 52 frozen `slopes.json:1`, `check_scaffold` determinism)
- RF OOF 0.9338 XGB 0.9418 (`ml/sih26001/reports/metrics.md:9`), isotonic Brier 0.0971 vs naive 0.25 (`calibration.md:8`), temporal 673/73 test Brier 0.0978 (`metrics.md:32`), TreeSHAP top-4 per zone (`sih26001_model.py:explain_row`)
- Isolation engine R4 bottleneck (`main.py:1326`), SWI JMA 3-tank (`swi.py:14`), warning 6 states + local thresholds 385/395/410/375 (`warning_thresholds.json:6`), quake −25% (`usgs_quakes.json:1` 26 events), road catalogue, exposure operational risk, wound feature, observed vs forecast separation, Yellow/Red kits, history slider (`main.py:379`)
- React + Leaflet GIS + PWA offline (`public/sw.js:1` cache-first shell, network-only `/api`, `manifest.webmanifest:1` 192/512) + FastAPI (v1 contract intact, live-rf scoring when `ml/models/sih26001_*v1.joblib` present else fixture fallback)
- Cloud: `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) PostGIS 16-3.4 + auto-watcher + IMD_API_KEY-gated live adapter

## 2025-11-15 — WILL→PARTIAL (frozen 12 untouched)

- Panchayat tiling 100 tiles 10×10 26.95-28.05/88.05-89.0 `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF `GET /api/panchayat/tiles`
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4 `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` → `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT

## Explicitly Out of Scope

- Physical IoT sensor deployment (prototype uses satellite/reanalysis + recorded live fixture; a sensor-ingestion adapter is API-ready — see `02_ARCHITECTURE_SIH26001.md` §5)
- InSAR ground-deformation monitoring (requires hardware)
- Flash-flood prediction (needs hydrological routing; rainfall here is a landslide-trigger proxy — road blockages are covered as derived road-status + isolation, not flood mapping)
- Exact location/time prediction of individual landslides (we predict susceptibility, not specific events)
- Hardware installation (PS is Software category)
- Replacing GSI RLFS — we complement it with the AI/ML layer GSI asked for
- Production-grade safety certification
- Claiming field-validated production accuracy (prototype honesty rules apply)
- Gram Panchayat-scale mapping from 12 demo slopes (Limitation §8)

## Data Honesty (do not remove)

Talus trains on **real documented events**: GSI Bhusanket (30,842+ all-India → 693 Sikkim `sikkim_join.json:6` + 764 deduped Sikkim + 7 Gangtok report `sikkim_report_gangtok.csv:1`), USGS 26 quakes 1965–2024 (`usgs_quakes.json:1`), IMD 0.25° gridded 1901–2024 `ind2024_rfp25.nc` + Open-Meteo live blend (IMD_API_KEY gated `GET /api/forecast/imd-live:1124`), CCI soil v09.2 1978–2024 `gangtok_soil_cci.csv:1` 0.271, SRTM n27_e088 `usgs_s234.json:1`, Sentinel-2 `S2B_45RXL_20241129` + WorldCover N27E087 10m, OSM 1014/226/504 `roads_osm_provenance.json:1` (geometry remains demo topology, counts prove presence), lithology PROXY-published-map uniform `lingtse_granite_gneiss` (Bhukosh timeout `bhukosh_vector_attempt.json:1`). `2936` rows 1468+1468 NUMERIC 17 + lulc 22-col matrix `feature_matrix.training.csv:1` underpins `RF 0.9338 XGB 0.9418` `metrics.md:9` and temporal `Brier 0.0978`. *The prototype validates the decision-support architecture on real data; it is not a production-calibrated warning system. Final operational decisions remain with qualified authorities.*
