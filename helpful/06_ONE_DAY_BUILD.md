# One-Day Prototype — What You Built

Date: 2026-08-20 · Status: **demo-ready, all mock data**

## What exists now

A working FastAPI backend in `backend/` with all **9 endpoints** from the frozen
API spec, reproducing the "Zone B Escalation" demo scenario exactly.

| Endpoint | Verified against demo |
|---|---|
| `GET /api/zones` | A22 / B48 / C35 / D28, all `stable` ✓ |
| `GET /api/zones/{id}` | detail + geometry, 404 works ✓ |
| `GET /api/zones/{id}/features` | 12 features + `missing_features` ✓ |
| `GET /api/zones/{id}/trend` | `rapid_increase: true` after events ✓ |
| `GET /api/zones/{id}/explanation` | SHAP-style contributions ✓ |
| `GET /api/zones/{id}/decision` | 4 roles returned ✓ |
| `POST /api/risk/predict` | Event1→61, Event2→70 ✓ |
| `POST /api/routes/safe` | risk-aware avoids B ✓ |
| `POST /api/simulation/what-if` | 80mm→80 Critical ✓ |

All demo targets hit: **58–63 → 68–74 → ≥80**, rapid increase, avoided zones.

## How to show it

```bash
cd backend
python -m uvicorn app.main:app --reload
```

1. Show Swagger docs at `http://127.0.0.1:8000/docs` (instant "wow").
2. `GET /api/zones` → initial table.
3. Walk Events 1–3 by calling `POST /api/risk/predict` with stronger features.
4. Finish with `/simulation/what-if` rain=80 → Critical.

## Files you own

```
backend/
├── app/
│   ├── main.py      ← the API (all routes live here)
│   ├── schemas.py   ← Pydantic models = the frozen feature schema
│   └── data.py      ← zone store + mock risk/trend/routing logic
├── tests/
│   ├── test_api.py  ← 8 passing demo-scenario tests
│   └── fixtures/    ← mock JSON for the frontend team
└── requirements.txt
```

## What's mock (swap later, don't panic)

- `data.compute_risk` → real Random Forest + SHAP when `ml/` is ready.
- `data.detect_trend` → real escalation logic.
- `data._dijkstra` → the `routing/` module.
- In-memory store → SQLite/Postgres.

The API shape never changes — only the internals — because the spec is frozen.

## What to learn next (if you get time today)

1. FastAPI basics: `@app.get("/path")` + a function returning a dict.
2. Pydantic: how `schemas.py` validates incoming JSON (invalid feature → 422).
3. Read `main.py` top to bottom once — it's ~180 lines and you wrote it.

## One-line summary for the team

> Backend is done for the prototype: all 9 spec endpoints work with
> demo-matching mock data, 8/8 tests green, ready to connect to the frontend.