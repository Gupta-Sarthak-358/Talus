# backend

FastAPI backend for Talus.

## Run it

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open:

- API: http://127.0.0.1:8000
- Interactive docs (Swagger): http://127.0.0.1:8000/docs

## Run the tests

```bash
cd backend
python -m pytest tests -q
```

## Run the demo scenario

The API ships with deterministic mock data that reproduces the "Zone B
Escalation" demo from `docs/06_DEMO_SCENARIO.md`:

1. `GET /api/zones` → initial state A22 / B48 / C35 / D28 (all stable).
2. `POST /api/risk/predict` with `rainfall_24h_mm: 55` → B ≈ 58–63 (Event 1).
3. `POST /api/risk/predict` with higher `crack_density` → B ≈ 68–74 (Event 2).
4. `GET /api/zones/B/trend` → `rapid_increase: true` (Event 3).
5. `GET /api/zones/B/decision` → 4 role messages.
6. `POST /api/routes/safe` → risk-aware route avoids Zone B.
7. `POST /api/simulation/what-if` with `rainfall_24h_mm: 80` → B ≥ 80 Critical.

## Structure

- `app/main.py` — the FastAPI app with all 9 endpoints.
- `app/schemas.py` — Pydantic models (the 12 frozen features + responses).
- `app/data.py` — zone store, mock risk formula, trend detection, Dijkstra routing.
- `tests/test_api.py` — demo-scenario smoke tests.
- `tests/fixtures/` — mock JSON for the frontend.

## What is mocked vs real

Everything is mock data right now so the demo works offline. When the ML and
routing modules are ready, swap these:

- `data.compute_risk(...)` → trained Random Forest + SHAP.
- `data.detect_trend(...)` → real escalation logic from `ml/`.
- `data._dijkstra(...)` → `routing/` risk-weighted Dijkstra.
- The in-memory `ZoneStore` → SQLite/Postgres.

See `docs/05_API_SPEC.md` (frozen contract) and `../helpful/` (summaries).