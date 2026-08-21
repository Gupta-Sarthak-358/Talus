# Requirements Summary (docs/01_REQUIREMENTS.md)

Status: **Frozen for MVP**. These are the "must do" rules — the feature-creep
firewall. If a new requirement appears, it needs an ADR update first.

## Functional requirements (the "what")

| ID | Requirement | Backend relevance |
|---|---|---|
| FR-01 | Calculate a risk value per mine zone | Core API |
| FR-02 | Risk score is **0–100** per zone | Used in every zone response |
| FR-03 | Score carries **confidence** + **missing evidence** list | `confidence` + `missing_evidence` fields |
| FR-04 | Explain risk with **SHAP** contributions | `/explanation` endpoint |
| FR-05 | Detect **rapidly increasing** risk (escalation flag) | `/trend` endpoint → `rapid_increase` |
| FR-06 | **Role-based decisions** for same event (worker / safety officer / mine manager / rescue team) | `/decision` endpoint |
| FR-07 | **Risk-aware routing** (risk-weighted Dijkstra), shortest path optional for comparison | `/routes/safe` endpoint |
| FR-08 | **What-if simulation**: change risk factors, recompute risk/confidence/explanation | `/simulation/what-if` endpoint |
| FR-09 | Map shows zone risk color-coded (React + Leaflet) | Frontend, but your JSON feeds it |
| FR-10 | Per-zone risk **timeline log** (Tier 2) | Defer unless demo needs it |

## Non-functional requirements (the "how")

- Everything runs **locally on a laptop**; no paid external services.
- **< 1 second** response for zone/risk/route endpoints at ~100 zones.
- Deterministic: fixed seed + versioned config → reproducible demo.
- **No network required during the demo.**
- Dependency manifests committed (`requirements.txt` / `package.json`).
- Every feature maps to a data provenance entry.

## Acceptance criteria = your test checklist

| Requirement | Done when |
|---|---|
| FR-01/02 | API returns 0–100 score per zone; map colors update |
| FR-03 | Response includes `confidence` and `missing_evidence` |
| FR-04 | `/explanation` returns SHAP contributions |
| FR-05 | Trend endpoint flags rapid-increase zones |
| FR-06 | Decision endpoint returns a message per role |
| FR-07 | Route endpoint avoids a high-risk zone where feasible |
| FR-08 | What-if returns updated risk for changed inputs |
| FR-09 | Dashboard renders zones from API data |
| FR-10 | Timeline endpoint returns ordered risk history |

> Note: risk thresholds are prototype thresholds, not calibrated safety
> standards. Final operational decisions remain with qualified personnel.
