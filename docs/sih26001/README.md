# TALUS v2 — SIH26001 (NER Landslide Risk Intelligence)

**Branch:** `SIH26001` · **Problem statement:** AI-Based Early Warning and
Landslide Risk Monitoring System in NER · **Org:** MDoNER, Disaster Management
· **Category:** Software

This folder is the **single source of truth for the SIH26001 track**.
TALUS v1 docs (`docs/00_*`–`08_*`, mine rockfall, SIH25071) stay frozen on
`main` and are referenced — never edited — from here.

## Relationship to TALUS v1

| Layer | v1 (mine rockfall) | v2 (NER landslide) | Status |
|---|---|---|---|
| Architecture pattern (ML + physics sim, calibrated confidence, SHAP, role decisions, risk-weighted Dijkstra, missing-evidence) | mine | NER | **Survives intact** |
| Data pipeline | synthetic generator v1.4.0 | **NGEN** — real NER geospatial ETL | Rewrite |
| Physics chain | bench FoS | rainfall → infiltration → pore pressure → FoS | Rewrite |
| Features | 12 mine | **17 NER** (see `05_FEATURE_SCHEMA_SIH26001.md`) | New contract |
| Training labels | synthetic FoS | real historical landslide events | Stronger evidence |
| Roles | worker / safety officer / mine manager / rescue | villager / district officer / state manager / rescue | Remapped |
| UI | mine zone map | GIS heatmap + roads + villages | Rebuild on same pattern |

## Doc map

| Doc | Purpose | Source |
|---|---|---|
| `00_PROJECT_BRIEF_SIH26001.md` | Scope firewall — what v2 is / is not | Research §2, §11 |
| `01_REQUIREMENTS_SIH26001.md` | FR/NFR + acceptance criteria (R1–R13) | Research §2.2 |
| `02_ARCHITECTURE_SIH26001.md` | Module mapping, NGEN pipeline, deltas | Research §8 |
| `03_DATA_PLAN_SIH26001.md` | Sources, provenance, training construction | Research §6, §9.2 |
| `04_MODEL_PLAN_SIH26001.md` | Model selection, validation protocol, benchmarks | Research §7.5, §9.3–9.4 |
| `05_FEATURE_SCHEMA_SIH26001.md` | Frozen 17-feature ML contract | Research §7.3 |
| `06_DEMO_SCENARIO_SIH26001.md` | Demo narrative skeleton (to freeze later) | — |
| `07_ASSUMPTIONS_SIH26001.md` | Working assumptions, each falsifiable | Research §6–§9 |
| `08_LIMITATIONS_SIH26001.md` | Honest limits — say proactively to judges | Research §11.3–11.4 |
| `decisions/ADR-001-sih26001-scope.md` | Why migrate (not fork), why real data | Research §1, §9.1 |
| `../../SIH26001_RESEARCH.md` (in `docs/`) | Full research & strategy (966 lines, fact-checked) | — |

## Roadmap (from research §12)

- **Phase 0 (now):** data assembly — IMD rainfall, SRTM DEM, GSI Bhusanket
  inventory, ERA5 soil moisture, Sentinel-2 NDVI/LULC, OSM roads/rivers.
  Checklist in `03_DATA_PLAN_SIH26001.md`.
- **Phase 1:** core ML — NGEN pipeline → RF+XGBoost(+LGBM) → SHAP → isotonic
  calibration → benchmark validation.
- **Phase 2:** decision layer — GIS dashboard, 4-role engine, road overlay +
  routing, rainfall-threshold scenario engine.
- **Phase 3:** platform — field-reporting app, SMS/multilingual alerts,
  offline sync, IMD API integration.

## Rules (inherit from `/CONTRIBUTING.md`)

- This branch is the integration branch for the SIH26001 track. Feature work
  branches off it as `feature/sih26001/<name>`.
- Conventional commits (`feat:`, `fix:`, `docs:`, …).
- Never commit datasets or model weights — metadata only.
- If behavior changes, update the matching doc in this folder in the same PR.
- `docs/SIH26001_RESEARCH.md` is evidence; these docs are the build contract.
  If they conflict, the contract wins and the research doc gets a correction note.
