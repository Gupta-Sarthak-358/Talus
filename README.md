# Talus

## Risk-Aware Decision Support for Open-Pit Mine Safety

Talus converts scattered mine data into explainable risk and actionable safety decisions.

### Core Flow

**Detect → Understand → Escalate → Decide → Act**

### What Talus Does

1. Collects environmental, geological, operational and visual signals.
2. Produces zone-level rockfall risk scores.
3. Provides confidence and explainability (SHAP).
4. Detects rapidly increasing risk (trend / escalation).
5. Generates role-specific actions (worker, safety officer, manager, rescue team).
6. Recommends risk-aware routes between points on the mine map.
7. Supports what-if simulation of changed conditions.

The key differentiation: from **"What is the risk?"** → **"What should we do now?"**

### MVP

- Random Forest risk engine
- SHAP explainability
- Confidence + missing-evidence reporting
- Risk trend / escalation detection
- Role-based decisions
- Risk-aware Dijkstra routing
- React + Leaflet dashboard
- FastAPI backend
- Synthetic training data (physics-informed FoS labels)

### Important Limitation

The prototype does **not** have real Indian mine sensor telemetry. Unavailable mine-specific data is simulated using a documented, physics-informed synthetic generation process. See [docs/07_ASSUMPTIONS.md](docs/07_ASSUMPTIONS.md) and [docs/08_LIMITATIONS.md](docs/08_LIMITATIONS.md).

### Repository Structure

```text
talus/
│
├── README.md            ← you are here
├── CONTRIBUTING.md      ← branch/commit rules for the team
├── LICENSE              ← MIT
├── .gitignore
├── .env.example
│
├── docs/                ← single source of truth (spec)
│   ├── 00_PROJECT_BRIEF.md   → product scope firewall
│   ├── 01_REQUIREMENTS.md    → what the software must do
│   ├── 02_ARCHITECTURE.md    → how it is built
│   ├── 03_DATA_PLAN.md       → data + provenance table
│   ├── 04_MODEL_PLAN.md      → training & evaluation
│   ├── 05_FEATURE_SCHEMA.md  → frozen ML-facing schema + internal vs ML boundary
│   ├── 05_API_SPEC.md        → frozen API contract
│   ├── 06_DEMO_SCENARIO.md   → known expected outputs
│   ├── 07_ASSUMPTIONS.md
│   ├── 08_LIMITATIONS.md
│   ├── GENERATOR_V1_SPEC.md  → research→implementation bridge (Member 2)
│   ├── observations.md       → research decision ledger (why we chose X)
│   ├── research/             → grounded track artifacts:
│   │                           neyveli_geology.md, neyveli_blasting.md, neyveli_cracks.md
│   ├── decisions/            → ADR-001 MVP scope, ADR-002 Neyveli reference mine
│   └── source/               → original research/plan documents:
│                               Talus_Master_Project_Document.md
│                               Talus_Data_Training_Plan.md
│                               Talus_Deep_Research_Report.md
│                               Complete_Context.md (full project history)
│
├── research/            ← references & data sources index
│   ├── references.md
│   ├── sources.md
│   └── papers/          ← citation-only policy (no copyright PDFs)
│
├── data/                ← git-ignored datasets (small samples only)
│   ├── raw/             → IMD rainfall, DEM, Crack-Seg
│   ├── processed/       → engineered features
│   └── synthetic/       → generated training data (v1/…)
│
├── ml/                  ← data_generation / training / evaluation / models
├── backend/             ← FastAPI app + tests
├── frontend/            ← React + Leaflet dashboard
├── routing/             ← risk-aware Dijkstra
├── cv/                  ← crack detection / feature extraction
├── scripts/             ← one-off utilities
├── tests/               ← cross-module tests
└── assets/              ← diagrams / ppt / demo
```

### Running Locally

Coming with the first code commit. Planned:

```text
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://127.0.0.1:8000

# Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

### Team

| Area | Owner |
|---|---|
| Architecture / Integration | Member 1 |
| Data / Synthetic Generator | Member 2 |
| ML / Risk Engine | Member 3 |
| Backend / API | Member 4 |
| Frontend / GIS | Member 5 |
| Routing / CV / QA | Member 6 |

Owner ≠ "only person allowed to touch it." Owner = **if something breaks in this area, this person is responsible for understanding it.**

### Related Docs

- [Project Brief](docs/00_PROJECT_BRIEF.md) — what Talus is
- [Requirements](docs/01_REQUIREMENTS.md) — functional/non-functional requirements
- [Architecture](docs/02_ARCHITECTURE.md) — diagrams
- [Data Plan](docs/03_DATA_PLAN.md)
- [Model Plan](docs/04_MODEL_PLAN.md)
- [Feature Schema (ML-facing contract)](docs/05_FEATURE_SCHEMA.md)
- [API Spec](docs/05_API_SPEC.md)
- [Generator v1 Spec](docs/GENERATOR_V1_SPEC.md)
- [Demo Scenario](docs/06_DEMO_SCENARIO.md)
- [Assumptions](docs/07_ASSUMPTIONS.md)
- [Limitations](docs/08_LIMITATIONS.md)
- [ADR-001: MVP Scope](docs/decisions/ADR-001-mvp-scope.md)
- [ADR-002: Neyveli Reference Mine](docs/decisions/ADR-002-neyveli-reference-mine.md)
- [Data Grounding Manifest](data/grounding_manifest.md) — what grounds the synthetic data
- [Contributing](CONTRIBUTING.md) — branch & commit rules
- [Complete Project Context](docs/source/Complete_Context.md) — full project history
- [Master Project Document](docs/source/Talus_Master_Project_Document.md) — research/original spec
- [Data & Training Plan](docs/source/Talus_Data_Training_Plan.md) — research source
- [Deep Research Report](docs/source/Talus_Deep_Research_Report.md) — research source

**New to the project?** Start with the [Project Brief](docs/00_PROJECT_BRIEF.md) and [Requirements](docs/01_REQUIREMENTS.md). For the full project history and narrative (deck decisions, data honesty rules, differentiation story), read [Complete Project Context](docs/source/Complete_Context.md).

## Navigating the Repository

This repo is the **single source of truth**. If two people disagree about something, the repo decides.

**Onboarding order (read these three first, ~10 min total):**

1. `README.md` — what Talus is, who owns what (this page)
2. `docs/00_PROJECT_BRIEF.md` — the scope firewall (what is / is not in the MVP)
3. `docs/01_REQUIREMENTS.md` — what the software must actually do

> If it's not in the Brief / Requirements, **don't build it**. Propose it, update the ADR, then build.

**Then, by area:**

| Your area | Read next |
|---|---|
| Everyone | `docs/02_ARCHITECTURE.md`, `docs/06_DEMO_SCENARIO.md` |
| Data / ML | `docs/03_DATA_PLAN.md`, `docs/04_MODEL_PLAN.md` |
| Backend / Frontend | `docs/05_API_SPEC.md` ← frozen contract, develop against it |
| Everything | `CONTRIBUTING.md` ← branch & commit rules |

**Full background (optional, for the story):** `docs/source/Complete_Context.md` (project history), `docs/source/Talus_Master_Project_Document.md`, `docs/source/Talus_Data_Training_Plan.md`, `docs/source/Talus_Deep_Research_Report.md`.

**Git in one line:** branch off `dev` as `feature/<your-area>`, never push to `main`, conventional commits (`feat:` / `fix:` / `docs:` / `refactor:`), keep large datasets and trained models out of git.

---

*Team Sangyan — College Internal Hackathon for SIH 2026.*