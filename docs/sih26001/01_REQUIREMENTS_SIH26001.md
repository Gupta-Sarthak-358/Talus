# TALUS Requirements — SIH26001

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Status:** Built — frozen 2025-11-15 · **Trace to:** `00_PROJECT_BRIEF_SIH26001.md`, `docs/SIH26001_RESEARCH.md` §2.2

These requirements define what the software **must** do. They are the feature-creep firewall. New requirements require updating this document and the ADR. R1–R13 are PS order (research §2.2); FR-01…FR-13 are system-layer order — the map between them:

| PS req | FR | Note |
|---|---|---|
| R1 multi-source ingest | FR-01 | |
| R2 AI/ML prediction | FR-02 | |
| R3 GIS dashboard | FR-09 | shares FR with R4 |
| R4 severity levels | FR-09 | 5-band map |
| R5 roads + connectivity | FR-07 | + isolation FR-07 ext |
| R6 weather forecasts | FR-05, FR-08 | trend + what-if + SWI |
| R7 emergency prioritisation | FR-06 | warning state machine |
| R8 field reporting | FR-10 | + outbox/PWA |
| R9 SMS/app alerts | FR-11 | auto watcher gated |
| R10 multilingual | FR-12 | shares FR with R11 |
| R11 offline | FR-12 | sw.js + outbox |
| R12 explainability | FR-04 | TreeSHAP |
| R13 calibrated confidence | FR-03 | isotonic + Bayes 0.5→0.01 |
| — (Tier 2) | FR-13 | timeline (NOW built: slider) |

---

## Functional Requirements

### FR-01: Multi-source data ingestion (R1)

The system shall ingest and join: rainfall (IMD 0.25° gridded 1901–2024 + Open-Meteo live 7-day + IMD_API_KEY gated district API), soil moisture (CCI v09.2 1978–2024, ERA5 path documented but unused), satellite imagery (Sentinel-2 NDVI + ESA WorldCover LULC), terrain/slope (SRTM n27_e088 derivatives), historical landslide records (GSI Bhusanket 30k + report PDF, USGS 26 quakes, OSM roads/rivers 1014/226/504), and Bhukosh lithology (PROXY uniform, timeout evidence) into a unified per-unit feature matrix (17 numeric + lulc, 22 cols sample). Every value carries provenance.

### FR-02: AI/ML susceptibility prediction (R2)

The system shall produce a **0–100 susceptibility score** per spatial unit (pilot point S1–S4 + N1–N4 + D1–D4 = 12 demo slopes, frozen in `05_FEATURE_SCHEMA_SIH26001.md` + `slopes.json:1`) from RF + XGBoost (+LGBM candidate) trained on 2936 rows 1468+1468. Live scoring via `backend/app/sih26001_model.py:score_row` when weights present, else frozen scaffold 89/78/66/52.

### FR-03: Confidence + missing evidence (R13)

The system shall expose a calibrated probability per score (isotonic, Brier/ECE-reported, Brier 0.0971 vs 0.25 `calibration.md:1`). When evidence is missing, the system shall list it as missing evidence alongside confidence. Additional Bayes prevalence-corrected view `confidence_real_1pct` (0.5→0.01, `GET /api/model/calib:1221` + `sih26001_model.py:score_row`) documents field rarity. No bare black-box numbers.

### FR-04: Explainability (R12)

The system shall display the major feature contributions to a unit's score using **TreeSHAP** (per-prediction, `sih26001_model.py:explain_row` top-4, fallback to fixture SHAP `slopes.json:1` + `manifest.training.json:shap_sample`).

### FR-05: Trend / escalation (R6)

The system shall detect **escalating susceptibility over the monsoon season** (antecedent rainfall accumulation, SWI 3-tank `backend/app/swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 saturation trajectory, soil-moisture proxy) and raise an escalation signal when the trend threshold is crossed (`GET /api/zones/{id}/trend:322` + `GET /api/soil/swi:1203` + `GET /api/warning/state:1449`).

### FR-06: Role-based decisions (R7)

The system shall produce different recommendations for the same risk event depending on role:

- Villager / community (Yellow/Red kit: what/why/rain/shelters/phones)
- District officer
- State manager
- Rescue team
- Admin (observability via `/admin` PIN-gated panel, not field-facing)

### FR-07: Road connectivity + safe routing + isolation (R5)

The system shall maintain a **road network graph** (OSM counts 1014/226/504, demo topology deterministic R1–R4 `roads_osm_provenance.json:1` + `data.py:118` `GRAPH`), report **road connectivity status** (open / at-risk / blocked `GET /api/roads/status:832`), catalogue **pre-emptive restrictions** (`GET /api/roads/restrictions:798`), exposure operational risk (`GET /api/zones/{id}/exposure:743`), and calculate a **risk-aware route** between two points (risk-weighted Dijkstra, `POST /api/routes/safe:421` avoids R2 via R3/R4 + `_road_graphs_for:496`). It shall compute **village isolation** — does road status cut egress to valley/plains? — via `_isolation_for_location:1326` (R4 bottleneck, `may_isolate` predictive, `GET /api/isolation:1441`) and surface it on the map and warning state (RESTRICT/EVACUATE overrides).

### FR-08: Rainfall what-if simulation (R6)

The system shall allow a simulated change to rainfall inputs (forecast totals, threshold scenarios, SWI-fed effective rain per Monga 2026 / Dahal & Hasegawa + forecast blend) and recompute score, confidence, explanation, map state, and isolation/warning. ML counterfactuals must be labeled as such (`POST /api/simulation/what-if:567` S3 66→74); causal claims go through the scenario engine only (`POST /api/simulation/causal-what-if:629`).

### FR-09: GIS dashboard (R3, R4)

The system shall display unit-level susceptibility on an NER GIS map, color-coded by 5-band severity (very low / low / moderate / high / very high), with overlays for roads, villages, infrastructure, isolation, warning states, and weather-linked forecast (observed vs forecast separated). Dashboard shows: risk severity, road status, warning 6-state, isolation, weather-linked forecast, emergency prioritisation. Components: `RiskMap` 5-band Leaflet, `RoadStatusCard`, `IsolationAlertCard`, `WarningStateCard` 6 states, `RiskTrendChart` NOW history slider, `AdminPanel`.

### FR-10: Field reporting (R8)

The system shall accept geo-tagged photo/video field reports (cracks, slope movement, blocked roads) with GPS + timestamp, queued for officer review and usable as candidate labels/provenance. Offline capture with later sync via PWA `sw.js` + `manifest.webmanifest` 192/512 + `localStorage talus_report_outbox`.

### FR-11: Alerts (R9)

The system shall deliver **SMS/app-based early warnings** to district administrations, disaster authorities, and subscribed communities on escalation/isolation events, with delivery status. Env-gated provider (`SMS_PROVIDER`/`SMS_API_KEY`, `POST /api/alerts/dispatch:959`, log `GET /api/alerts/dispatch/log:1062`), auto watcher thread (`_auto_watcher_loop:1702` interval 60s cooldown 3600s, `GET /api/alerts/auto/status:1721`, `POST /api/alerts/auto/trigger:1728`, `AUTO_ALERT_ENABLED/SMS`).

### FR-12: Multilingual + offline (R10, R11)

The system shall support **multilingual notifications** (en/hi/ne/as/bn, `main.py:86` `DECISIONS_TRANSLATIONS`) and **low-network/offline functionality** (PWA `sw.js:1` cache-first shell / network-only `/api`, cached manifest, queued outbox `frontend/src/services/reports.js:1`) for remote areas.

### FR-13: Evidence timeline (Tier 2 → built)

The system shall maintain a per-unit log of how susceptibility evolved (e.g. "12 Jun score 41 → 7-day rain +120 mm → 19 Jun score 63 → SWI saturated → 22 Jun score 78"). Built: `GET /api/zones/{id}/history:379` 365-day `daily_history` (deterministic seed 91, `model_service.py:daily_history`) + `evidence_timeline` `scenario_service.py:64`, rendered by `RiskTrendChart` with slider (NOW).

---

## Non-Functional Requirements

- **Local-first development** — core pipeline + demo run on a standard laptop; no paid services required for the prototype (live forecast is best-effort gated, fixtures remain fallback).
- **Fast API response for demo** — unit/score/route/isolation/warning endpoints respond quickly (target < 1 s) for the 12-zone extent.
- **Reproducible pipeline** — NGEN deterministic (fixed seeds, versioned configs, pinned dataset versions `manifest.sample.json:1`); every record tagged with source version.
- **Reproducible demo** — fixed 3-corridor extent + fixed scenario, known outputs in advance (see `06_DEMO_SCENARIO_SIH26001.md` once frozen, scaffold 89/78/66/52).
- **No live-service dependency during demo** — all data and models local; network not required to run the demo (live IMD/Open-Meteo shown as recorded fixture + gated adapter, not a silent hard dependency; `/api/forecast/rainfall` fixture always available).
- **Reproducible environment** — dependency manifests committed.
- **Traceable data** — every feature maps to a provenance entry in `03_DATA_PLAN_SIH26001.md` + `warning_thresholds.json:1` + `roads_osm_provenance.json:1`.
- **PWA offline** — `public/sw.js:1` + `manifest.webmanifest:1` 192/512 icons, app shell cached, `/api` never served stale.
- **Cloud path proven** — `docker-compose.prod.yml:1` PostGIS 16-3.4 + api healthcheck + AUTO env.

### Real-time definition (prototype targets — frozen at build)

The PS says "real-time" four times; the prototype is explicit about what that means without live sensors:

- **Ingest cadence:** daily IMD/GPM batch + Open-Meteo 7-day blend (1h cache `main.py:1103` `_LIVE_TTL_S`), IMD_API_KEY district feed gated; optional 3-hourly GPM pass during active monsoon escalation.
- **Escalation latency:** < 30 min from ingest completion to decision output + isolation/warning + alert-queue entry (auto watcher 60s poll).
- **Dashboard refresh:** on every ingest, plus push on any escalation / isolation / warning transition.
- **SMS dispatch:** < 15 min from escalation (env-gated adapter, otherwise fixture logged as SIMULATED with provenance; real gateway is post-hackathon work).
- **Not claimed:** continuous sensor streaming. "Real-time" in the prototype = daily ingest + event-driven escalation + live forecast blend, never a silent batch delay.

---

## Acceptance Criteria (built — verified 2025-11-14, 35/35 live tests)

| Requirement | Definition of done | Status |
|---|---|---|
| FR-01 | NGEN run reproduces the feature matrix from pinned sources; provenance present per value. | ✅ `feature_matrix.sample.csv:1` 12 rows ×22 cols (17 numeric+lulc) + `feature_matrix.training.csv:1` 2936 rows, `manifest.sample.json:1` (IMD 0.25° + CCI v09.2 + SRTM n27_e088 + Sentinel2 + WorldCover + GSI 30k + OSM 1014/226/504 + USGS 26 quakes + Bhukosh timeout), `sih26001_model.py:score_row` live or fixture fallback |
| FR-02 | API returns 0–100 score per unit; map colors update. | ✅ `GET /api/zones` → `S1 89 S2 78 S3 66 S4 52` `slopes.json:1` (fixture), live RF when weights present `data.py:308` `live_scores`, `check_scaffold` `SCAFFOLD OK` |
| FR-03 | Score response includes `confidence` + `confidence_real_1pct` and `missing_evidence`; calibration report (Brier/ECE) committed. | ✅ `confidence 0.82-0.58` `slopes.json:1`, `calibration.md:8` `Brier 0.0971`, `GET /api/model/calib:1221` Bayes 0.5→0.01, `metrics.md:9` RF 0.9338 XGB 0.9418 |
| FR-04 | `GET /api/units/{id}/explanation` returns SHAP contributions. | ✅ `GET /api/zones/{id}/explanation` `main.py:334` TreeSHAP top-4 `sih26001_model.py:explain_row` + `manifest.training.json:shap_sample` 5 pts |
| FR-05 | Trend + SWI + warning endpoints flag escalation on held-out monsoon data. | ✅ `GET /api/zones/{id}/trend` `main.py:322`, `GET /api/soil/swi` `swi.py:14` JMA 3-tank, `GET /api/warning/state` 6 states + local thresholds `warning_thresholds.json:6` |
| FR-06 | Decision endpoint returns role-specific message per NER role + kits. | ✅ `GET /api/zones/{id}/decision` `main.py:389` 5 roles `villager/district_officer/state_manager/rescue_team/admin` en/hi/ne/as/bn + kit shelters/phones |
| FR-07 | Road-status + isolation + routing endpoints work; risk-aware avoids R2, isolation flags via R4 bottleneck. | ✅ `GET /api/roads/status` `main.py:832` R2 at-risk demo topology, `GET /api/isolation` `_isolation_for_location:1326` R4 bottleneck `may_isolate`, `GET /api/roads/restrictions` catalogue, `GET /api/zones/{id}/exposure` operational risk, `POST /api/routes/safe` avoids R2 via R3/R4 `roads.json:1` |
| FR-08 | What-if endpoint returns updated risk for changed rainfall; ML vs causal labeling present. | ✅ `POST /api/simulation/what-if` counterfactual `66→74` `forecast.json:1` + `POST /causal-what-if` physics `main.py:629` + SWI/forecast blend |
| FR-09 | Dashboard renders NER heatmap + road/village/warning/isolation overlays from API data. | ✅ `RiskMap` 5-band + `RoadStatusCard` + `IsolationAlertCard` + `WarningStateCard` 6 states + `RiskTrendChart` NOW slider + `AdminPanel` `/admin` PINs; PWA `sw.js`/`manifest.webmanifest` |
| FR-10 | Field-report endpoint accepts geo-tagged upload; appears in officer queue + outbox. | ✅ `POST /api/reports` `ReportIn` `photo {sha256,exif}` + `PATCH review` + `GET /queue?status` `main.py:879` + `reports.js:1` outbox `talus_report_outbox` + `sw.js:1` |
| FR-11 | Alert pipeline delivers to test subscriber list; auto watcher fires on isolation. | ✅ `POST /api/alerts/dispatch` fixture en/hi/ne `alerts.json:1` `main.py:959` + SMS gated `SMS_PROVIDER` + auto watcher 60s `main.py:1702` + log `main.py:1062` |
| FR-12 | Notification renders in ≥2 languages; offline PWA demonstrated. | ✅ en/hi/ne/as/bn `main.py:86`, `sw.js:1` + `manifest.webmanifest:1` 192/512, `talus_report_outbox` auto-retry on `online` + sync badge |
| FR-13 | Timeline endpoint returns ordered per-unit history with slider. | ✅ `GET /api/zones/{id}/history` `main.py:379` 365-day `daily_history` `model_service.py:daily_history` + `RiskTrendChart` NOW handle |

---

*Susceptibility ≠ probability of a specific landslide. Scores are model outputs under the prototype target definition; thresholds are prototype operational bands, not calibrated safety standards. Field rate ~1% view is `confidence_real_1pct` via Bayes, not the frozen 0–100 score.*