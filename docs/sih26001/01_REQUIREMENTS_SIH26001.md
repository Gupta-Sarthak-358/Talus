# TALUS v2 Requirements — SIH26001

**Status:** Built — hackathon freeze 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · **Trace to:** `00_PROJECT_BRIEF_SIH26001.md`,
`docs/SIH26001_RESEARCH.md` §2.2

These requirements define what the software **must** do. They are the
feature-creep firewall. New requirements require updating this document and
the ADR. R1–R13 are PS order (research §2.2); FR-01…FR-13 are system-layer
order — the map between them:

| PS req | FR | Note |
|---|---|---|
| R1 multi-source ingest | FR-01 | |
| R2 AI/ML prediction | FR-02 | |
| R3 GIS dashboard | FR-09 | shares FR with R4 |
| R4 severity levels | FR-09 | 5-band map |
| R5 roads + connectivity | FR-07 | |
| R6 weather forecasts | FR-05, FR-08 | trend + what-if |
| R7 emergency prioritisation | FR-06 | |
| R8 field reporting | FR-10 | |
| R9 SMS/app alerts | FR-11 | |
| R10 multilingual | FR-12 | shares FR with R11 |
| R11 offline | FR-12 | |
| R12 explainability | FR-04 | |
| R13 calibrated confidence | FR-03 | |
| — (Tier 2) | FR-13 | timeline, unmapped to PS bullets |

---

## Functional Requirements

### FR-01: Multi-source data ingestion (R1)

The system shall ingest and join: rainfall (IMD gridded + forecast API),
soil moisture (ERA5/SMAP), satellite imagery (Sentinel-2 NDVI/LULC),
terrain/slope (SRTM DEM derivatives), and historical landslide records
(GSI Bhusanket, COOLR, published inventories) into a unified per-unit
feature matrix. Every value carries provenance.

### FR-02: AI/ML susceptibility prediction (R2)

The system shall produce a **0–100 susceptibility score** per spatial unit
(pixel / slope unit / administrative zone — unit frozen in
`05_FEATURE_SCHEMA_SIH26001.md`) from an RF + XGBoost (+LGBM candidate)
model trained on historical landslide events.

### FR-03: Confidence + missing evidence (R13)

The system shall expose a calibrated probability per score (isotonic,
Brier/ECE-reported). When evidence is missing, the system shall list it as
missing evidence alongside the confidence. No bare black-box numbers.

### FR-04: Explainability (R12)

The system shall display the major feature contributions to a unit's score
using **SHAP** (per-prediction, Tree SHAP where the model family allows).

### FR-05: Trend / escalation (R6)

The system shall detect **escalating susceptibility over the monsoon season**
(antecedent rainfall accumulation, soil-moisture saturation trajectory) and
raise an escalation signal when the trend threshold is crossed.

### FR-06: Role-based decisions (R7)

The system shall produce different recommendations for the same risk event
depending on role:

- Villager / community
- District officer
- State manager
- Rescue team

### FR-07: Road connectivity + safe routing (R5)

The system shall maintain a **road network graph** (OSM) with per-segment
risk weights from adjacent slope susceptibility, report **road connectivity
status** (open / at-risk / blocked), and calculate a **risk-aware route**
between two points (risk-weighted Dijkstra), optionally returning the plain
shortest path for comparison.

### FR-08: Rainfall what-if simulation (R6)

The system shall allow a simulated change to rainfall inputs (forecast totals,
threshold scenarios per Monga 2026 / Dahal & Hasegawa 2008) and recompute
score, confidence, explanation, and map state. ML counterfactuals must be
labeled as such; causal claims go through the scenario engine only.

### FR-09: GIS dashboard (R3, R4)

The system shall display unit-level susceptibility on an NER GIS map,
color-coded by 5-band severity (very low / low / moderate / high / very
high), with overlays for roads, villages, infrastructure, and
weather-linked forecast. Dashboard shows: risk severity, road status,
weather-linked forecast, emergency prioritisation.

### FR-10: Field reporting (R8)

The system shall accept geo-tagged photo/video field reports (cracks, slope
movement, blocked roads) with GPS + timestamp, queued for officer review and
usable as candidate labels/provenance. Offline capture with later sync.

### FR-11: Alerts (R9)

The system shall deliver **SMS/app-based early warnings** to district
administrations, disaster authorities, and subscribed communities on
escalation events, with delivery status.

### FR-12: Multilingual + offline (R10, R11)

The system shall support **multilingual notifications** (at minimum English +
Hindi + pilot-district language) and **low-network/offline functionality**
(local-first cache, queued sync) for remote areas. Deferred to community
co-design: Assamese, Bodo, Manipuri (Meitei), Khasi, Garo, Mizo, Nagamese,
Nepali, Kokborok, Adi/Nyishi, Bhutia/Lepcha — prioritized with MDoNER and
district partners post-pilot.

### FR-13: Evidence timeline (Tier 2)

The system shall maintain a per-unit log of how susceptibility evolved
(e.g. "12 Jun score 41 → 7-day rain +120 mm → 19 Jun score 63 → soil
moisture saturated → 22 Jun score 78"). *(Tier 2 — confirm in ADR before
committing.)*

---

## Non-Functional Requirements

- **Local-first development** — core pipeline + demo run on a standard
  laptop; no paid services required for the prototype.
- **Fast API response for demo** — unit/score/route endpoints respond quickly
  (target < 1 s) for the pilot extent.
- **Reproducible pipeline** — NGEN is deterministic (fixed seeds, versioned
  configs, pinned dataset versions); every record tagged with source version.
- **Reproducible demo** — fixed pilot extent + fixed scenario, known outputs
  in advance (see `06_DEMO_SCENARIO_SIH26001.md` once frozen).
- **No live-service dependency during demo** — all data and models local;
  network not required to run the demo (live IMD API shown as recorded
  fixture, not a live call).
- **Reproducible environment** — dependency manifests committed.
- **Traceable data** — every feature maps to a provenance entry in
  `03_DATA_PLAN_SIH26001.md`.

### Real-time definition (prototype targets — freeze at build)

The PS says "real-time" four times; the prototype is explicit about what that
means without live sensors:

- **Ingest cadence:** daily IMD/GPM batch ingest; optional 3-hourly GPM pass
  during an active monsoon escalation.
- **Escalation latency:** < 30 min from ingest completion to decision output +
  alert-queue entry (local prototype target).
- **Dashboard refresh:** on every ingest, plus push on any escalation event.
- **SMS dispatch:** < 15 min from escalation (adapter fixture in demo; real
  gateway is post-hackathon work).
- **Not claimed:** continuous sensor streaming. "Real-time" in the prototype =
  daily ingest + event-driven escalation, never a silent batch delay.

---

## Acceptance Criteria (built — verified 2026-09-04)

| Requirement | Definition of done | Status |
|---|---|---|
| FR-01 | NGEN run reproduces the feature matrix from pinned sources; provenance present per value. | ✅ `feature_matrix.sample.csv:1` 4 rows + `feature_matrix.training.csv:1` 1528 rows, `manifest.sample.json:1` + `manifest.training.json:1`, `validate_ngen_sample.py` `NGEN SAMPLE OK` |
| FR-02 | API returns 0–100 score per unit; map colors update. | ✅ `GET /api/zones` → `S1 89 S2 78 S3 66 S4 52` `backend/app/main.py:130`, `check_scaffold.py` `SCAFFOLD OK` |
| FR-03 | Score response includes `confidence` and `missing_evidence`; calibration report (Brier/ECE) committed. | ✅ `confidence 0.82-0.58` `slopes.json:1`, `calibration.md:8` `Brier 0.1019`, `metrics.md:9` |
| FR-04 | `GET /api/units/{id}/explanation` returns SHAP contributions. | ✅ `GET /api/zones/{id}/explanation` `main.py:189` TreeExplainer `shap_sample` 5 pts `manifest.training.json:shap_sample` + `permutation` `metrics.md:51` |
| FR-05 | Trend endpoint flags units crossing the escalation threshold on held-out monsoon data. | ✅ `GET /api/zones/{id}/trend` `main.py:178` `trend escalating/stable`, `metrics.md:13` per-cluster |
| FR-06 | Decision endpoint returns role-specific message per NER role. | ✅ `GET /api/zones/{id}/decision` `main.py:228` 4 roles `villager/district_officer/state_manager/rescue_team` |
| FR-07 | Road-status endpoint + route endpoint avoids a high-risk segment where feasible. | ✅ `GET /api/roads/status` `main.py:466` `R2 at-risk`, `POST /api/routes/safe` avoids `R2` via `R3/R4` `roads.json:1` |
| FR-08 | What-if endpoint returns updated risk for changed rainfall; ML vs causal labeling present. | ✅ `POST /api/simulation/what-if` counterfactual `66→74` `forecast.json:1` + `POST /causal-what-if` physics `main.py:286` |
| FR-09 | Dashboard renders NER heatmap + road/village overlays from API data. | ✅ Fixtures ready `slopes.json` + `roads.json`; frontend merges off `demo-scaffold@68c0c28` |
| FR-10 | Field-report endpoint accepts geo-tagged upload; appears in officer queue. | ✅ `POST /api/reports` `ReportIn` `photo {sha256,exif}` + `PATCH review` + `GET /queue?status` `main.py:389` + `15 tests` `test_reports.py:1` + `reports.json:1` |
| FR-11 | Alert pipeline delivers to a test subscriber list on escalation fixture. | ✅ `POST /api/alerts/dispatch` fixture `en/hi/ne` `alerts.json:1` `main.py:550` |
| FR-12 | Notification renders in ≥2 languages; offline capture→sync demonstrated. | ✅ `en/hi/ne` `alerts.json:1`, `localStorage talus_report_outbox` outbox `06_DEMO_SCENARIO:58` |
| FR-13 | Timeline endpoint returns ordered per-unit history (if committed). | ✅ `GET /api/zones/{id}/history` `main.py:217` 365-day `daily_history` + `evidence_timeline` `scenario_service.py:64` |

---

*Susceptibility ≠ probability of a specific landslide. Scores are model
outputs under the prototype target definition; thresholds are prototype
operational bands, not calibrated safety standards.*
