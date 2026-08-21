# Architecture Summary (docs/02_ARCHITECTURE.md)

## Where the backend sits in the pipeline

```text
Data Sources (env / geo / operational / visual / historical)
        ↓
Feature Processing (one feature vector per zone, with missingness)
        ↓
TALUS RISK ENGINE (Random Forest → calibrated probability → score 0–100 + confidence)
        ↓
Explainability (SHAP)        Trend / escalation detection
        ↓
Decision Engine (role-based alerts · risk-aware routing · what-if)
        ↓
Mine Dashboard (React + Leaflet)   ← the backend serves THIS
```

Backend = the **middleman**: it receives requests from the frontend, calls the
risk/explanation/trend/decision/routing services, and returns JSON exactly per
`docs/05_API_SPEC.md`.

## Backend component layout (mirror this in `backend/app/`)

```text
FastAPI
 ├── Zone API          (list zones, zone detail)
 ├── Risk API          (predict risk per zone)
 ├── Explanation API   (SHAP contributions)
 ├── Trend API         (escalation / risk history)
 ├── Decision API      (role-specific actions)
 ├── Route API         (risk-aware path)
 └── Simulation API    (what-if recompute)
```

## Sequence for a risk assessment (what your code should do per request)

```text
Frontend → FastAPI → Risk Engine (predict) → SHAP (explain) → Decision Engine (decide)
     ↑                                                                      │
     └────────────────── JSON back to frontend ←────────────────────────────┘
```

i.e. one zone risk request internally = predict + explain + decide, then merge.

## Tech stack (use these)

| Layer | Choice |
|---|---|
| Backend | Python, **FastAPI** |
| ML | scikit-learn (Random Forest), SHAP |
| Calibration | `CalibratedClassifierCV` (Platt / isotonic) |
| Routing | **NetworkX** (Dijkstra) on risk-weighted graph |
| Data | **SQLite** default; PostgreSQL + PostGIS optional |

## Prototype constraints

- All components run **locally**; no live external services during demo.
- SQLite default; PostGIS only if GIS work demands it.
- Parallel development seam: frontend uses mocked JSON, backend uses stub data,
  ML uses the dataset — **the API spec is the contract between them.**
- Mermaid source for all diagrams: `assets/diagrams/*.mmd`
  (01_system_architecture, 02_components, 03_sequence_risk_assessment, 04_deployment).