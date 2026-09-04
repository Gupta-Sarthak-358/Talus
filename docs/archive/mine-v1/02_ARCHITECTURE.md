> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Architecture

**Status:** Frozen for MVP · Trace to: `docs/01_REQUIREMENTS.md`, `docs/05_API_SPEC.md`

All diagrams for the system live here.

---

## 1. System Architecture (data flow)

```text
Data
 ↓
Feature Processing
 ↓
Risk Engine
 ↓
Explainability + Trend
 ↓
Decision Engine
 ↓
Alerts + Routing + What-if
 ↓
Dashboard
```

Detailed pipeline:

```text
Data Sources
  Environmental (rainfall, groundwater proxy)
  Geological (slope angle, height, rock type)
  Operational (blast frequency, vibration)
  Visual (crack imagery → features)
  Historical (prior incidents, global patterns)
        ↓
Feature Processing
  (unified feature vectors per zone, with missingness)
        ↓
TALUS RISK ENGINE
  Random Forest → calibrated probability → risk score 0–100 + confidence
        ↓
  Explainability (SHAP)        Trend / escalation detection
        ↓
Decision Engine
  Role-based alerts · Risk-aware routing · What-if simulation
        ↓
Mine Dashboard (React + Leaflet)
```

## 2. Component Diagram

### Frontend (React)

```text
React
 ├── MineMap        (Leaflet zone polygons, risk colors)
 ├── RiskPanel      (selected zone score + confidence)
 ├── SHAPPanel      (feature contributions)
 ├── TrendChart     (risk over time)
 ├── AlertPanel     (role-based alerts)
 ├── RouteView      (shortest vs risk-aware route)
 └── WhatIfPanel    (sliders: rainfall, blasting, crack density)
```

### Backend (FastAPI)

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

### ML / Data

```text
ml/
 ├── data_generation   (synthetic generator, FoS labels)
 ├── training          (Random Forest + calibration)
 ├── evaluation        (metrics, reliability, ablation)
 └── models            (trained artifacts, git-ignored)
```

## 3. Sequence Diagram — Risk Assessment

```text
User/Dashboard        FastAPI           Risk Engine      SHAP      Decision Engine
      │                  │                  │               │              │
      │ GET zone risk    │                  │               │              │
      │─────────────────▶│                  │               │              │
      │                  │ predict(features)│               │              │
      │                  │─────────────────▶│               │              │
      │                  │  score, confidence                │              │
      │                  │◀─────────────────│               │              │
      │                  │ explain(zone)    │               │              │
      │                  │──────────────────────────────────▶│              │
      │                  │  SHAP contributions                │              │
      │                  │◀──────────────────────────────────│              │
      │                  │ decide(score, trend)               │              │
      │                  │─────────────────────────────────────────────────▶│
      │                  │  role-specific actions              │              │
      │                  │◀─────────────────────────────────────────────────│
      │ risk + confidence + explanation + actions              │              │
      │◀─────────────────│                  │               │              │
      │                  │                  │               │              │
```

## 4. Deployment Diagram (prototype)

```text
Browser
   │
   ▼
React Frontend (localhost:5173)
   │  REST / JSON
   ▼
FastAPI (localhost:8000)
   │
   ├── Risk Model (Random Forest)
   ├── SHAP
   ├── Trend
   ├── Decision
   └── Routing (risk-weighted Dijkstra)
   │
   ▼
Local Data / PostgreSQL (PostGIS optional)
```

Prototype constraints:

- All components run locally; no dependency on live external services during demo.
- SQLite is the default for the prototype; PostgreSQL + PostGIS is available for GIS-heavy work.
- Frontend can develop against mocked JSON; backend against stub data; ML against the dataset — the API contract in `docs/05_API_SPEC.md` is the seam.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React, Leaflet (react-leaflet) |
| Backend | Python, FastAPI |
| ML | Scikit-learn (Random Forest), SHAP |
| Calibration | scikit-learn `CalibratedClassifierCV` (Platt / isotonic) |
| Routing | NetworkX (Dijkstra) on a risk-weighted graph |
| CV (Tier 2+) | Ultralytics YOLO-seg on Crack-Seg dataset → structured features |
| Data | SQLite default; PostgreSQL + PostGIS optional |

## Diagram Files

Mermaid (`.mmd`) source for each diagram above lives in `assets/diagrams/`:

| Diagram | File |
|---|---|
| System architecture (data flow) | `assets/diagrams/01_system_architecture.mmd` |
| Component diagram | `assets/diagrams/02_components.mmd` |
| Sequence (risk assessment) | `assets/diagrams/03_sequence_risk_assessment.mmd` |
| Deployment (prototype) | `assets/diagrams/04_deployment.mmd` |