# Backend Team — Start Here

## Where you are

The `backend/` folder is **empty** (just `.gitkeep` stubs). You are building the
FastAPI application from scratch. The design docs are finished — your job is to
turn them into working code.

## The one sentence

> Talus is a FastAPI backend that takes mine-zone data (12 features), returns a
> risk score with confidence, explains it (SHAP), tracks the trend, produces
> role-based decisions, computes safe routes, and simulates what-if changes —
> all over JSON for the React dashboard.

## Reading order (backend member only)

| Order | File | Why you need it |
|---|---|---|
| 1 | `docs/05_API_SPEC.md` | **Your contract.** Every endpoint, request, response, and error. Frozen. |
| 2 | `helpful/01_API_SPEC_summary.md` | Cheat-sheet version of the above |
| 3 | `docs/05_FEATURE_SCHEMA.md` | The 12 feature names/types you must accept and pass through unchanged |
| 4 | `docs/06_DEMO_SCENARIO.md` | The known expected outputs you will test your API against |
| 5 | `docs/01_REQUIREMENTS.md` | The "why" behind the endpoints (FR-01 to FR-10) |
| 6 | `docs/02_ARCHITECTURE.md` | How the backend component is laid out and how it talks to ML/routing |

**Skip for now:** `docs/03`, `docs/04`, `docs/07`, `docs/08`, `docs/source/`,
`research/`, `ml/` internals, `cv/`.

## What you need to build

The 8 endpoints from `docs/05_API_SPEC.md`:

```
GET    /api/zones
GET    /api/zones/{id}
GET    /api/zones/{id}/features
GET    /api/zones/{id}/trend
GET    /api/zones/{id}/explanation
GET    /api/zones/{id}/decision
POST   /api/risk/predict
POST   /api/routes/safe
POST   /api/simulation/what-if
```

Base path `/api`, JSON only, errors as `{"detail": "..."}`.

## Dependencies you can expect to use

| Purpose | Library |
|---|---|
| Web framework | FastAPI + uvicorn |
| ML model calls | scikit-learn (Random Forest), SHAP — *consumed from `ml/`* |
| Routing | NetworkX (risk-weighted Dijkstra), *consumed from `routing/`* |
| Data storage | SQLite (default), PostgreSQL + PostGIS optional |

## How the team works (from CONTRIBUTING.md)

- Branch off `dev` as `feature/<name>` (e.g. `feature/backend`). Never push to `main`.
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- If you change the API, update `docs/05_API_SPEC.md` in the same PR.
- Large datasets and trained models never go in git.

## The golden rules

1. **The API spec is frozen** — build exactly what it says. No extra fields, no renaming.
2. **Feature names must match `docs/05_FEATURE_SCHEMA.md` exactly** (the 12 fields). The generator, ML, backend, and frontend all share these names.
3. **The demo scenario is your test** — Zone B must reach ~85+ Critical with a reproducible story (see `helpful/05_Demo_Scenario_summary.md`).
