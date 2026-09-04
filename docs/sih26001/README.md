# TALUS — SIH26001 (NER Landslide Risk Intelligence)

**Branch:** `SIH26001` · **Problem statement:** AI-Based Early Warning and
Landslide Risk Monitoring System in NER · **Org:** MDoNER, Disaster Management
· **Category:** Software

This folder is the **single source of truth for the SIH26001 track**.
TALUS v1 docs (`docs/00_*`–`08_*`, landslide, SIH26001) stay frozen on
`main` and are referenced — never edited — from here.

## Relationship to TALUS v1

| Layer | v1 | v2 (NER landslide) | Status |
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

## Roadmap (built — `SIH26001 @ 68c0c28` 2026-09-04)

- **Phase 0 — done:** `124` IMD files `ind*.nc` 1901–2024 + USGS `n27_e088` + `30k` GSI inventory `+777` PDF → `764` Sikkim `manifest.training.json:42`, `CCI soil 0.271`, `WorldCover N27E087` `S2B_45RXL_20241129` — `03_DATA_PLAN:154` all `[x]`.
- **Phase 1 — done:** `1528` rows `build_training_matrix.py:1` → `RF 0.921 XGB 0.9256 LGBM 0.9207` `metrics.md:9` + `Brier 0.1019` `calibration.md:8` + SHAP 5-pt `manifest.training.json:shap_sample` + temporal `35/73` `RF test 0.9264`.
- **Phase 2 — done:** GIS dashboard fixtures `S1 89 S2 78 S3 66 S4 52` `slopes.json:1`, 4-role engine, road `R2 at-risk` avoided `roads.json:1`, rainfall-threshold `monga-mdl/dahal-144` `forecast.json:1`.
- **Phase 3 — done (backend):** field reporting `POST /api/reports` + `PATCH review` + `queue?status` `photo {sha256,exif}` + `consent` + `flagged` `15 tests` `test_reports.py:1`; SMS `en/hi/ne` fixture `alerts.json:1`, offline `localStorage talus_report_outbox` outbox `06_DEMO_SCENARIO:58`.

## Rules (inherit from `/CONTRIBUTING.md`)

- This branch is the integration branch for the SIH26001 track. Feature work
 branches off it as `feature/sih26001/<name>`.
- Conventional commits (`feat:`, `fix:`, `docs:`, …).
- Never commit datasets or model weights — metadata only.
- If behavior changes, update the matching doc in this folder in the same PR.
- `docs/SIH26001_RESEARCH.md` is evidence; these docs are the build contract.
 If they conflict, the contract wins and the research doc gets a correction note.
