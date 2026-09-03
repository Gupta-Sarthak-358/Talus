# TALUS v2 Requirements — SIH26001

**Status:** Draft · **Trace to:** `00_PROJECT_BRIEF_SIH26001.md`,
`docs/SIH26001_RESEARCH.md` §2.2

These requirements define what the software **must** do. They are the
feature-creep firewall. New requirements require updating this document and
the ADR. IDs R1–R13 trace to the PS decomposition (research §2.2).

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
Hindi + pilot-district language; full NER language matrix deferred) and
**low-network/offline functionality** (local-first cache, queued sync) for
remote areas.

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

---

## Acceptance Criteria (MVP proposal)

| Requirement | Definition of done |
|---|---|
| FR-01 | NGEN run reproduces the feature matrix from pinned sources; provenance present per value. |
| FR-02 | API returns 0–100 score per unit; map colors update. |
| FR-03 | Score response includes `confidence` and `missing_evidence`; calibration report (Brier/ECE) committed. |
| FR-04 | `GET /api/units/{id}/explanation` returns SHAP contributions. |
| FR-05 | Trend endpoint flags units crossing the escalation threshold on held-out monsoon data. |
| FR-06 | Decision endpoint returns role-specific message per NER role. |
| FR-07 | Road-status endpoint + route endpoint avoids a high-risk segment where feasible. |
| FR-08 | What-if endpoint returns updated risk for changed rainfall; ML vs causal labeling present. |
| FR-09 | Dashboard renders NER heatmap + road/village overlays from API data. |
| FR-10 | Field-report endpoint accepts geo-tagged upload; appears in officer queue. |
| FR-11 | Alert pipeline delivers to a test subscriber list on escalation fixture. |
| FR-12 | Notification renders in ≥2 languages; offline capture→sync demonstrated. |
| FR-13 | Timeline endpoint returns ordered per-unit history (if committed). |

---

*Susceptibility ≠ probability of a specific landslide. Scores are model
outputs under the prototype target definition; thresholds are prototype
operational bands, not calibrated safety standards.*
