# Backend Beginner Workflow — Member 4

Status: reflects the repo as of 2026-08-21 · Companion to `00_START_HERE_Backend.md`
(note: that file says the backend is empty — it is not anymore; see `06_ONE_DAY_BUILD.md`).

How to use this file: work top to bottom. One step at a time.
Learn a tiny concept → apply it → test it → move on. Do not skip ahead.

---

## Part 1 — The mental model

### What is a backend?

Restaurant analogy:

```text
You (customer)        → walk in and order a dosa
Waiter                → takes your order to the kitchen, brings food back
Kitchen               → actually cooks the dosa
Storage room          → ingredients the kitchen uses
```

Mapped to Talus:

```text
React dashboard       → the customer. It shows the mine map and asks questions.
API endpoints         → the waiters. Fixed "windows" you ask questions at.
FastAPI app           → the restaurant itself. Routes each order to the right window.
Backend logic         → the kitchen. Computes risk, trends, decisions, routes.
ML risk engine        → a specialist chef (not hired yet — currently a stand-in cook).
Zone store            → the storage room. Currently in-memory mock data.
```

The frontend never talks to the ML model or the data directly.
It always goes through the API. That is the whole point of a backend.

### The request flow in Talus (real example)

When the dashboard wants Zone B's risk after heavy rain:

```text
React dashboard (frontend)
      |
      |  POST /api/risk/predict   (HTTP request with JSON body)
      v
FastAPI  (app/main.py)
      |
      |  validates the JSON against schemas.py   ← bad input rejected here (422)
      v
endpoint function predict()  (main.py)
      |
      |  calls the store / risk logic
      v
data.py  (ZoneStore + compute_risk)     ← later: ml/ Random Forest + SHAP
      |
      |  returns score, band, confidence
      v
PredictResponse schema converts it to JSON
      |
      v
React dashboard receives:
{ "zone_id": "B", "risk_score": 61, "risk_band": "Moderate", ... }
```

---

## Part 2 — Words you must know (with Talus examples)

| Term | Simple meaning | Where in Talus |
|---|---|---|
| HTTP | The language browsers/servers use to talk. Request in, response out. | Every frontend ↔ backend message |
| GET | "Give me information." Sends no body. | `GET /api/zones` — list zones |
| POST | "Here is data, do something with it." Sends a body. | `POST /api/risk/predict` — send features, get risk |
| JSON | Text format for structured data: `{"key": value}` | Every request/response body |
| Endpoint | A URL + method pair the backend responds to | `/api/zones/B/trend` with GET |
| Path parameter | A variable part of the URL | `{zone_id}` in `/api/zones/{zone_id}` |
| Request body | Data the client sends with POST | the 12 features in `/api/risk/predict` |
| Response | What the backend sends back + a status code | `200` with zone JSON, `404` unknown zone |
| Status code | Number saying how it went: 200 ok, 404 not found, 422 invalid input | spec: errors are `{"detail": "..."}` |
| Schema | A description of allowed data shape/types | `schemas.py` (`Features`, `PredictResponse`) |
| Pydantic | Library FastAPI uses to check incoming data against a schema automatically | every request body passes through it |
| Validation | Rejecting bad data before logic runs | negative rainfall → automatic 422 |
| Service / business logic | The actual thinking: formulas, rules — kept OUT of endpoint functions | `compute_risk()` in `data.py` |
| Test client | Fake browser used by tests — no server needed | `TestClient(app)` in `tests/test_api.py` |

---

## Part 3 — Audit: what already exists (do not rebuild!)

All 9 endpoints from the frozen spec are implemented with mock data:

| Endpoint | File | State |
|---|---|---|
| `GET /api/zones` | main.py | done, matches demo initial state |
| `GET /api/zones/{id}` | main.py | done, 404 handled |
| `GET /api/zones/{id}/features` | main.py | done |
| `GET /api/zones/{id}/trend` | main.py | done |
| `GET /api/zones/{id}/explanation` | main.py | done (mock SHAP-style values) |
| `GET /api/zones/{id}/decision` | main.py | done, 4 roles |
| `POST /api/risk/predict` | main.py | done, updates store history |
| `POST /api/routes/safe` | main.py | done (own Dijkstra in data.py) |
| `POST /api/simulation/what-if` | main.py | done |

Tests: `backend/tests/test_api.py` — 8 tests, all passing (`python -m pytest tests -q`).

Files you own:

```text
backend/
├── app/
│   ├── main.py      ← endpoints (the "waiters")
│   ├── schemas.py   ← request/response shapes (the frozen feature schema)
│   └── data.py      ← store + mock risk/trend/routing logic (the "kitchen")
├── tests/test_api.py
└── requirements.txt
```

Mocked today, real later (swap internals, never the API shape):

- `data.compute_risk` → `ml/` Random Forest + SHAP (Member 3)
- `data._dijkstra` → `routing/` module (Member 6)
- in-memory store → SQLite/Postgres

### Known gaps (status: 1–3 fixed 2026-08-21, 4 pending teammates)

1. ~~**what-if overrides are unvalidated**~~ — FIXED. Overrides now merge with the
   zone's current features and pass through the `Features` schema; bad values → 422.
2. ~~**Route points missing `zone_id`**~~ — FIXED. Request points require `zone_id`;
   response path points stay `{lat, lng}` (separate `PathPoint` model).
3. ~~**CORS hardcoded to `*`**~~ — FIXED. Reads `CORS_ORIGINS` env var
   (comma-separated), falls back to `*` when unset.
4. Later: swap mocks for real `ml/` + `routing/` when ready (still not ready as of
   2026-08-21 — those folders contain no code yet).

---

## Part 4 — Learning roadmap (only what this repo needs)

### LEVEL 0 — Backend basics
- [ ] What a backend is (Part 1 above)
- [ ] HTTP: request → response
- [ ] GET vs POST
- [ ] JSON shape
- [ ] Status codes 200 / 404 / 422

### LEVEL 1 — FastAPI basics
- [ ] Run the server (`uvicorn`)
- [ ] Open `/docs` (auto-generated interactive docs)
- [ ] Read ONE endpoint end-to-end (`GET /api/zones/{id}`)
- [ ] `@app.get(...)` decorator = "when a GET arrives at this path, run the function below"
- [ ] Path parameters (`{zone_id}`)
- [ ] Request bodies (`PredictRequest`)

### LEVEL 2 — Validation
- [ ] Pydantic models in `schemas.py`
- [ ] Field constraints (`ge=0`, `le=1`, `Literal[...]` enums)
- [ ] Trigger a 422 on purpose and read the error

### LEVEL 3 — Talus backend structure
- [ ] Trace one full flow: request → schema → endpoint → data.py → response
- [ ] Understand why logic lives in `data.py`, not in endpoints
- [ ] Know the mock-vs-real swap points

### LEVEL 4 — Implementation (your real contributions)
- [ ] Fix gap #1: validated what-if overrides
- [ ] Fix gap #2: add `zone_id` to route points
- [ ] Fix gap #3: read CORS origins from env
- [ ] Integrate `ml/` and `routing/` when ready

### LEVEL 5 — Testing
- [ ] Read the 8 existing tests, understand what each checks
- [ ] Add tests for your fixes (invalid override → 422, etc.)

Not needed for this project: Docker, auth, WebSockets, Redis, Celery, microservices. Ignore tutorials about them for now.

---

## Part 5 — Baby-step plan

Each step = one small session. Check the box when you can explain it out loud.

- [ ] **Step 1.** Start the server, open `http://127.0.0.1:8000/docs`, click through `GET /api/zones`.
- [ ] **Step 2.** Same call from PowerShell with `Invoke-RestMethod`. See raw JSON.
- [ ] **Step 3.** Read `GET /api/zones/{zone_id}` in main.py line by line. Find the 404.
- [ ] **Step 4.** Call `GET /api/zones/ZZZ`. See the 404. Why?
- [ ] **Step 5.** Read `Features` in schemas.py. Match all 12 fields to `docs/05_FEATURE_SCHEMA.md`.
- [ ] **Step 6.** POST bad input to `/api/risk/predict` (e.g. rainfall `-5`). Read the 422 error.
- [ ] **Step 7.** Read `compute_risk` in data.py. Explain the mock formula in one sentence.
- [ ] **Step 8.** Run the test suite. Read `test_predict_event1_target_58_to_63` until it makes sense.
- [ ] **Step 9.** Fix gap #1 (validated overrides) with tests.
- [ ] **Step 10.** Fix gap #2 (route point `zone_id`) with tests.
- [ ] **Step 11.** Fix gap #3 (CORS from env).
- [ ] **Step 12.** Walk the whole demo scenario via `/docs` using `helpful/05_Demo_Scenario_summary.md`.

---

## Part 6 — Your FIRST tiny task (do this now, ~10 minutes)

Goal: see the backend alive. Change nothing yet.

```powershell
cd E:\TALUS\backend
python -m uvicorn app.main:app --reload
```

What that command means:

- `python -m uvicorn` — start the program that serves FastAPI apps
- `app.main:app` — inside folder `app`, file `main.py`, find the object named `app`
- `--reload` — restart automatically when you edit code (dev convenience only)

Then open in a browser:

1. `http://127.0.0.1:8000/docs` — interactive API documentation, generated free by FastAPI
2. Click `GET /api/zones` → "Try it out" → "Execute"
3. Look at the response: `{"zones": [...]}` with A22 / B48 / C35 / D28

Stop the server with `Ctrl+C`.

Done when: you can answer "what did the browser send, and what came back?"

---

## Part 7 — Rules we never break

1. `docs/05_API_SPEC.md` is frozen. Build exactly what it says. If code and spec disagree, stop and discuss — do not silently change either.
2. Feature names come from `docs/05_FEATURE_SCHEMA.md` exactly (12 fields).
3. Git: branch off `dev` as `feature/backend`, never push to `main`, conventional commits (`feat(api): ...`).
4. No secrets in code. `.env` is git-ignored; `.env.example` shows the keys.
5. Tests before claiming done: `cd backend; python -m pytest tests -q`.
