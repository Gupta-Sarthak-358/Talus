# TALUS v2 Project Brief — SIH26001

**Status:** Built — hackathon freeze 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · **Context:** SIH 2026, SIH26001
track · **Date:** 2026-09-03 → 2026-09-04 · **Trace to:** `docs/SIH26001_RESEARCH.md` §1–§2

This is the **scope firewall for the SIH26001 track**. If a proposal conflicts
with this brief, this document wins until amended via ADR.

---

## Problem

The North Eastern Region (8 states: Arunachal Pradesh, Assam, Manipur,
Meghalaya, Mizoram, Nagaland, Sikkim, Tripura) faces frequent monsoon
landslides, flash floods, road blockages, and slope failures from heavy
rainfall, fragile terrain, and unplanned hill cutting. Incidents disrupt
connectivity, damage infrastructure, delay emergency response, and isolate
remote villages for days.

The current state:

- **Reactive monitoring** — dependent on manual reporting after events.
- **Threshold-only forecasting** — GSI RLFS uses rainfall thresholds; no
  AI/ML, no soil moisture, no satellite, no per-slope prediction.
- **No decision layer** — no role-based emergency prioritisation, no road
  connectivity tracking, no risk-aware routing, no offline support.

GSI has publicly listed "integration of AI/ML as a decision-support layer" as
their next advancement initiative. That gap is this project.

## Problem Statement

**AI-Based Early Warning and Landslide Risk Monitoring System in NER**
(SIH26001, MDoNER, Disaster Management, Software).

## Solution

TALUS v2 converts scattered NER geospatial signals into **explainable
susceptibility** and **actionable emergency decisions**.

TALUS v2 produces a slope/zone-level susceptibility score with stated
confidence, explains *why* (SHAP), tracks monsoon-driven escalation, and
converts the result into **role-specific actions**:

- Villager / community → early warning in local language, avoid-route guidance
- District officer → intervention / evacuation coordination, road closure calls
- State manager → resource allocation, emergency prioritisation across districts
- Rescue team → risk-aware access routing, deployment sequencing

It also computes **road-status-aware routes** (risk-weighted Dijkstra over the
NER road graph instead of plain shortest path) and supports **rainfall-threshold
what-if simulation** so an officer can test how forecast rain shifts risk, live.

## Core Differentiation

From:

> "What is the risk?"

To:

> "What should we do now — which road to avoid, which village first, where to
> send rescue, and what data are we missing?"

Every susceptibility score carries **confidence** and a **list of missing
evidence** — no bare black-box numbers. Who gets told what, in what words and
language, and what action follows is part of the product, not an afterthought.

## System Philosophy

```text
Detect → Understand → Escalate → Decide → Act
```

(Unchanged from v1. The pattern survives; the data and physics change.)

## Core Modules

1. **NGEN data pipeline** — IMD rainfall, ERA5/SMAP soil moisture, SRTM DEM
   derivatives, Sentinel-2 NDVI/LULC, GSI lithology, OSM roads/rivers,
   historical landslide inventories → unified feature matrix.
2. **Feature processing** — 17 NER features per spatial unit, with missingness.
3. **Risk engine** — susceptibility score + calibrated confidence.
4. **Explainability** — SHAP feature contributions per prediction.
5. **Trend detection** — monsoon-season escalation signals.
6. **Decision engine** — role-specific recommendations (4 NER roles).
7. **Risk-aware routing** — Dijkstra over road graph weighted by slope risk.
8. **Rainfall scenario engine** — threshold-based what-if (Monga 2026,
   Dahal & Hasegawa 2008).
9. **Field reporting** — geo-tagged photo/video upload (camera + GPS, offline).
10. **Alerts** — SMS/app, multilingual, offline-sync capable.
11. **Dashboard** — NER GIS heatmap: risk bands, road status, villages,
    weather-linked forecast, emergency priority.

## MVP (built — frozen 2026-09-04, `SIH26001 @ 68c0c28`)

- NGEN pipeline over Gangtok pilot (S1–S4) — 16/17 REAL/PROXY, zero STUBs, `feature_matrix.sample.csv:1` + `manifest.sample.json:1`
- RF + XGB + LGBM (RF OOF AUC 0.921, XGB 0.9256, LGBM 0.9207) `ml/sih26001/reports/metrics.md:9`, isotonic Brier 0.1019 `calibration.md:8`, SHAP TreeExplainer 5-pt sample `manifest.training.json:shap_sample`
- Trend / escalation detection + role-based decisions (4 NER roles) + risk-aware routing (R2 at-risk avoided) — live `backend/app/main.py:254` + `data/sih26001/fixtures/roads.json:1`
- Rainfall-threshold scenario engine (Monga/Dahal) + tracker + `POST /api/simulation` + `GET /api/forecast/rainfall` fixtures `forecast.json:1`
- Geo-tagged field reporting `POST /api/reports` + `PATCH review` + `GET /queue?status` + photo `sha256/exif` + consent + `flagged` (`backend/app/main.py:389`, `reports.json:1`, `15 tests`)
- React + Leaflet GIS dashboard + FastAPI backend (v1 contract intact, `S1-S4 89/78/66/52`)
- Training on **real historical landslide events** — `1528 rows 764+764` inventory-scale `feature_matrix.training.csv:1` season-window proxy `manifest.training.json:24`, temporal holdout now `35/73 dated → RF test AUC 0.9264`

## Explicitly Out of Scope

- Physical IoT sensor deployment (prototype uses satellite/reanalysis proxies;
  a sensor-ingestion adapter is API-ready — see `02_ARCHITECTURE_SIH26001.md` §5)
- InSAR ground-deformation monitoring (requires hardware)
- Flash-flood prediction (needs a hydrological routing model; rainfall here is
  a landslide-trigger proxy only — road blockages are covered as a derived
  road-status overlay, not flood mapping)
- Exact location/time prediction of individual landslides (we predict
  susceptibility, not specific events)
- Hardware installation (PS is Software category)
- Replacing GSI RLFS — we complement it with the AI/ML layer GSI asked for
- Production-grade safety certification
- Claiming field-validated production accuracy (prototype honesty rules apply)

## Data Honesty (do not remove)

Unlike v1 (synthetic-only), v2 trains on **real documented events**: GSI
Bhusanket (37,903+ NER → `693` Sikkim `sikkim_join.json:6` + `764` deduped Sikkim `manifest.training.json:42` + `7` Gangtok report `sikkim_report_gangtok.csv:1`), NASA COOLR/GLC, ISRO Landslide Atlas (80,000+),
published inventories (Dibang 537, Meghalaya 1,330+, NEH 490 with rainfall
records), IMD 0.25° gridded rainfall (1901–present) + daily records at 8 NER
stations (1980-2019). `1528`-row inventory-scale matrix `feature_matrix.training.csv:1` season-window proxy `manifest.training.json:24` + `4`-row pilot `feature_matrix.sample.csv:1` (16/17 REAL/PROXY) underpin the `RF 0.921 XGB 0.9256` `metrics.md:9` and `temporal test AUC 0.9264`. *The prototype validates the decision-support
architecture on real data; it is not a production-calibrated warning system.
Final operational decisions remain with qualified authorities.*
