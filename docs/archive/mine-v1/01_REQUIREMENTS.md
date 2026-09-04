> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Requirements

**Status:** Frozen for MVP · Trace to: `docs/00_PROJECT_BRIEF.md`

These requirements define what the software **must** do. They are the feature-creep firewall. New requirements require updating this document and the ADR.

---

## Functional Requirements

### FR-01: Zone Risk

The system shall calculate a risk value for each mine zone on the mine map.

### FR-02: Risk Score

The system shall produce a **0–100 prototype risk score** per zone.

### FR-03: Confidence

The system shall expose a prediction confidence for each risk score, derived from a calibrated probability. When evidence is missing, the system shall list it as missing evidence alongside the confidence.

### FR-04: Explainability

The system shall display the major feature contributions to a zone's risk using **SHAP**.

### FR-05: Trend / Escalation

The system shall detect **rapidly increasing zone risk** and raise an escalation signal when the trend threshold is crossed.

### FR-06: Role-Based Decisions

The system shall produce different recommendations for the same risk event depending on role:

- Worker
- Safety Officer
- Mine Manager
- Rescue Team

### FR-07: Safe Routing

The system shall calculate a **risk-aware route** between two points, weighting edge cost by the risk of adjacent zones (risk-weighted Dijkstra), and may also return the plain shortest path for comparison.

### FR-08: What-if Simulation

The system shall allow a simulated change to risk factors (e.g. rainfall, blast frequency, crack density) and recompute risk, confidence, explanation and map state for the changed inputs.

### FR-09: Map

The system shall display zone-level risk on a mine map, color-coded by risk band, in the React + Leaflet dashboard.

### FR-10: Risk Evidence Timeline

The system shall maintain a per-zone log of how risk evolved over time (e.g. "09:00 risk 41 → rainfall increased → 10:00 risk 48 → crack detected → 11:00 risk 61"). *(Tier 2 — see ADR-001.)*

---

## Non-Functional Requirements

- **Local development** — everything runs on a standard laptop; no external paid services required.
- **Fast API response for demo** — zone/risk/route endpoints respond quickly (target < 1 s) for up to ~100 zones.
- **Reproducible synthetic dataset** — the generator is deterministic (fixed seed + versioned config).
- **Reproducible demo scenario** — the demo uses a fixed seed and a fixed scenario, so output is known in advance (see `06_DEMO_SCENARIO.md`).
- **No dependency on live external services during demo** — all data and models are local; network is not required for the demo to run.
- **Reproducible environment** — dependency manifests committed (e.g. `requirements.txt` / `package.json`).
- **Traceable data** — every feature maps to a provenance entry in `03_DATA_PLAN.md`.

---

## Acceptance Criteria (MVP)

| Requirement | Definition of done |
|---|---|
| FR-01/02 | API returns a 0–100 score per zone; map colors update. |
| FR-03 | Score response includes `confidence` and `missing_evidence`. |
| FR-04 | `GET /api/zones/{id}/explanation` returns SHAP contributions. |
| FR-05 | Trend endpoint flags zones crossing the rapid-increase threshold. |
| FR-06 | Decision endpoint returns role-specific message per role. |
| FR-07 | Route endpoint returns a path that avoids a high-risk zone where feasible. |
| FR-08 | What-if endpoint returns updated risk for changed inputs. |
| FR-09 | Dashboard renders zones from API data. |
| FR-10 | Timeline endpoint returns an ordered per-zone risk history. |

---

*Note: Risk thresholds are prototype thresholds, not calibrated safety standards. Final operational decisions remain with qualified personnel.*