# Talus — Risk-Aware Decision Support

**`SIH26001` — NER Landslide Risk Intelligence (MDoNER, Disaster Management, Software) — `SIH26001 @ 68c0c28`**
*Single track, single source of truth. No legacy track mentioned here.*

Talus converts scattered geospatial signals into explainable risk and actionable safety decisions.

### Core Flow

**Detect → Understand → Escalate → Decide → Act**

*(Unchanged from V1. The pattern survives; the data and physics change.)*

### What Talus Does

1. Collects multi-source NER signals: IMD rainfall, CCI soil moisture, SRTM DEM + derivatives, Sentinel-2 NDVI / WorldCover LULC, GSI lithology/lineament, OSM roads/rivers, GSI/Bhusanket + report-PDF landslide inventories.
2. Produces slope-level susceptibility `0–100` + calibrated confidence + `missing_evidence`.
3. Explains *why* (Tree SHAP + permutation) per prediction.
4. Detects monsoon escalation and road at-risk segments.
5. Generates role-specific actions (villager / district_officer / state_manager / rescue_team) + risk-aware routing (Dijkstra avoids `R2`).
6. Supports rainfall what-if (Monga/Dahal) + causal physics replay and geo-tagged field reporting (`POST /api/reports` + `PATCH review`).
7. Serves an offline-first GIS dashboard + field queue with multilingual alerts (`en/hi/ne`).

The key differentiation: from **"What is the risk?"** → **"What should we do now, and what are we missing?"**

### MVP — Built & Frozen 2026-09-04

- NGEN over 3 corridors (`S1-S4` Gangtok + `D1-D4` Darjeeling + `N1-N4` Lachung, 12 rows, per-corridor windows) — `17/17 REAL/PROXY, zero STUBs` (`feature_matrix.sample.csv:1`, `manifest.sample.json:1`)
- Inventory-scale training `2936×22` (`1468+1468` Sikkim + Darjeeling-hills `feature_matrix.training.csv:1`, `manifest.training.json:1`) — `RF OOF 0.8983 XGB 0.9029 LGBM 0.9015` `ml/sih26001/reports/metrics.md:9`, `temporal 673/73 → RF test 0.8189`, `cal Brier 0.118`, SHAP 5-pt sample
- Field reporting `POST /api/reports` (`ReportIn {zone_id/type/text/lat/lon/captured_at/photo{sha256,exif}+consent}`) + `PATCH review` `queued|flagged→verified` + `GET /queue?status` (`15 tests`, `reports.json:1`)
- FastAPI `backend` `S1-S4` + `POST /simulation/what-if` `66→74` + `GET /roads/status` `R2 at-risk` + `POST /routes/safe`
- React + Leaflet (fixtures), offline `localStorage talus_report_outbox` + `en/hi/ne` alerts (fixture)

### Important Limitation

The prototype is **not a live warning system**. It validates the decision-support architecture on **real documented Sikkim events** (`693 shp + 777 PDF → 764 deduped`, `CCI soil 0.271`, `USGS n27_e088`, `WorldCover N27E087`, `IMD 0.25° 1901–2024`) with `1991-2020` climatology / quasi-static proxies for time-varying inputs (tagged `approximate`). In-situ rain/soil sensors are **adapter-fixture only** (`02_ARCHITECTURE:5`); live feeds and cloud are post-hackathon swaps. See `docs/sih26001/08_LIMITATIONS_SIH26001.md` and `docs/sih26001/NGEN_PROVENANCE_S1.md`.

### Repository Structure

```text
talus/
├── README.md            ← you are here
├── docs/sih26001/       ← single source of truth (NER)
│   ├── 00_PROJECT_BRIEF_SIH26001.md
│   ├── 01_REQUIREMENTS_SIH26001.md
│   ├── 02_ARCHITECTURE_SIH26001.md
│   ├── 03_DATA_PLAN_SIH26001.md
│   ├── 04_MODEL_PLAN_SIH26001.md
│   ├── 05_FEATURE_SCHEMA_SIH26001.md  (17 features)
│   ├── 06_DEMO_SCENARIO_SIH26001.md
│   ├── 07_ASSUMPTIONS_SIH26001.md
│   ├── 08_LIMITATIONS_SIH26001.md
│   ├── NGEN_PROVENANCE_S1.md  ← per-feature REAL/PROXY + evidence
│   ├── ML_MODEL_CARD_V2.md    ← RF500 + XGB + LGBM + SHAP
│   ├── SCAFFOLD_CONTRACT_SEPT5.md  ← frozen S1–S4 89/78/66/52
│   └── decisions/ADR-001-sih26001-scope.md
├── data/sih26001/
│   ├── fixtures/        ← committed samples (S1–S4, roads, reports, forecast, manifests)
│   ├── evidence/        ← sikkim_join.json, sikkim_report_gangtok.csv, training sample
│   └── processed/       ← DEM/rain/soil extracts + training matrix (git-ignored except .training.sample.csv)
├── ml/sih26001/
│   ├── reports/         ← metrics.md / calibration.md / benchmarks.md (committed)
│   └── models/          ← sih26001_*_v1.joblib (git-ignored)
├── backend/             ← FastAPI (S1–S4, reports, simulation, routing)
├── frontend/            ← React + Leaflet (fixtures)
├── routing/             ← risk-aware Dijkstra
├── scripts/             ← build_training_matrix.py, train_sih26001.py, extract_*.py, check_scaffold.py
└── SIH26001_RESEARCH.md ← 966-line fact-checked strategy
```

### Running Locally

```text
# Validators (must stay green)
python scripts/check_scaffold.py        # SCAFFOLD OK: S1-S4 89/78/66/52, roles, R2-avoidance
python scripts/validate_ngen_sample.py  # NGEN SAMPLE OK: 22 cols, no STUBs

# Backend (reporting + simulation + routing live on :8000, fixtures S1–S4)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # http://127.0.0.1:8000  GET /api/zones → S1 89 S2 78 S3 66 S4 52
python -m pytest backend/tests/test_reports.py -v  # 15 passed (geo-tagged reports)

# Frontend (fixtures)
cd frontend
npm install
npm run dev                               # http://localhost:5173  (VITE_USE_LIVE_API=true → :8000)

# One-command demo (backend + frontend, offline)
powershell -ExecutionPolicy Bypass -File ./start_demo.ps1  # http://localhost:3000 + :8000/docs

# Training (inventory-scale, other terminal — mnemo venv has xgb/lgbm/shap)
C:\Users\satvi\AppData\Local\Programs\Python\Python311\python.exe scripts/build_training_matrix.py
C:\Users\satvi\Desktop\mnemo\.venv\Scripts\python.exe scripts/train_sih26001.py  # RF 0.8983 XGB 0.9029 → ml/sih26001/reports/
```

### Related Docs

- [Project Brief](docs/sih26001/00_PROJECT_BRIEF_SIH26001.md) — scope firewall (Gangtok pilot, 2936-row training, reporting LIVE)
- [Requirements](docs/sih26001/01_REQUIREMENTS_SIH26001.md) — `R1–R13 → FR-01–13` built + acceptance `✅`
- [Architecture](docs/sih26001/02_ARCHITECTURE_SIH26001.md) — sensor adapter `§5`, report capture/queue
- [Data Plan](docs/sih26001/03_DATA_PLAN_SIH26001.md) — Phase 0 all `[x]` Gangtok
- [Model Plan](docs/sih26001/04_MODEL_PLAN_SIH26001.md) — Phase-1 complete `RF/XGB/LGBM` `temporal 673/73`
- [Feature Schema](docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md) — frozen `17 + 2 keys` slope-point
- [Demo Scenario](docs/sih26001/06_DEMO_SCENARIO_SIH26001.md) — live Screens 1–6 (`S1 89 → High`, `66→74`, `R2 avoided`, report queue)
- [Assumptions](docs/sih26001/07_ASSUMPTIONS_SIH26001.md) — validated `5: 16` rescue, `673/73` temporal
- [Limitations](docs/sih26001/08_LIMITATIONS_SIH26001.md) — `CCI quasi-static`, `672/764 undated`, `center-approx` OSM
- [Provenance S1](docs/sih26001/NGEN_PROVENANCE_S1.md) — `16/17 REAL/PROXY` per-feature evidence
- [Model Card](docs/sih26001/ML_MODEL_CARD_V2.md) — `RF500 + XGB + LGBM + SHAP` `clean:true`
- [Research & Strategy](docs/SIH26001_RESEARCH.md) — PS decomposition, gap analysis, data inventory (updated 2026-09-04)
- [Scaffold Contract](docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md) — frozen `S1-S4` + API shapes + merge rules

**New to the project?** Start with `docs/sih26001/00_PROJECT_BRIEF_SIH26001.md` and `01_REQUIREMENTS_SIH26001.md`. For the full NER strategy, read `docs/SIH26001_RESEARCH.md`.

## Navigating the Repository

This repo is the **single source of truth**. If two people disagree, the repo decides.

**Onboarding (read these three first, ~10 min):**
1. `README.md` — this page (V2)
2. `docs/sih26001/00_PROJECT_BRIEF_SIH26001.md`
3. `docs/sih26001/01_REQUIREMENTS_SIH26001.md`

> If it's not in the Brief / Requirements, **don't build it**. Propose it, update the ADR, then build.

**Then, by area:** `02_ARCHITECTURE` + `06_DEMO_SCENARIO` (everyone), `03_DATA_PLAN` + `04_MODEL_PLAN` (data/ML), `05_FEATURE_SCHEMA` (ML contract), `CONTRIBUTING.md` (branch rules).

**Git in one line:** `SIH26001` is the integration branch — `feature/sih26001/<name>` off it, conventional commits, `python scripts/check_scaffold.py` + `validate_ngen_sample.py` green before merge, never push to `main`, keep datasets/weights out of git.

---

*Team Sangyan — SIH 2026 — SIH26001 (MDoNER) — NER Landslide Risk Intelligence — `SIH26001 @ 68c0c28` — Phase-1 built, 15 report tests green.*
