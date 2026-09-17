# Sept-5 Team Tasks — ARCHIVED (built 2026-09-04, frozen 2025-11-15)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Source of truth:** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md` + fixtures in `data/sih26001/fixtures/`. Demo was Sept 5 — all lanes built and merged to `SIH26001 @ 68c0c28`. Phase-1 model frozen 2025-11-15 (see `04_MODEL_PLAN_SIH26001.md` + `ML_MODEL_CARD_V2.md`). Frozen bands 89/78/66/52 and R2-avoidance routing unchanged.

## Lane A — Frontend (1 person) → `feature/sih26001/frontend-sept5`

* Branch off `feature/sih26001/demo-scaffold`.
* Header/footer: Mine Safety → NER Landslide, SIH26001 / MDoNER.
* Map centre → 27.3389, 88.6065. Zones → S1–S4 names from `slopes.json`.
* Decision panel renders 4 roles: villager / district_officer / state_manager / rescue_team (no logic change, strings come from API). Yellow/Red kits + villager_explain added post-Sept 5 (field-facing).
* Add 3 static panels wired to contract paths: road-status list (`GET /api/roads/status`), alert preview (`POST /api/alerts/dispatch` fixture), report form (`POST /api/reports` → appears in queue; offline `localStorage talus_report_outbox` + `public/sw.js:1` `CACHE talus-shell-v1`).
* Provenance footnote on Screen 1: IMD + SRTM + Bhusanket + CCI + Sentinel-2 + OSM + sensor-fixture (ERA5 superseded by CCI 0.271 + SWI `swi.py:14`).
* Done = `start_demo.ps1` shows S1-S4 coloured + all 6 clicks work against fixtures. Bands 89/78/66/52 frozen.

## Lane B — Backend + merge (1–2 persons) → `feature/sih26001/backend-sept5`

* Branch off `feature/sih26001/demo-scaffold`. One person is **merger** (only merger merges to `SIH26001`).
* `backend/app/main.py`: rename `DECISIONS_BY_BAND` roles to the 4 NER roles; rename zones A–D → S1–S4; load scores/bands/confidence from `slopes.json` (keep v1 API shapes). Frozen bands guarded by `check_scaffold.py:24`.
* Add 4 fixture endpoints exactly as §2: `GET /api/roads/status`, `POST+GET /api/reports*`, `POST /api/alerts/dispatch`, `GET /api/forecast/rainfall`. In-memory only, `fixture:true` flag, no live SMS/network. Live lanes added after: `GET /api/forecast/live:1154` Open-Meteo 7d (1h cache) + `GET /api/forecast/imd-live:1124` IMD-API gated, `GET /api/soil/swi:1203` SWI 3-tank L1=15 L2=60 L3=60 `swi.py:14` warning overlay (not in X), `GET /api/warning/state:1449` 6-state with `warning_thresholds.json:1`, `GET /api/isolation:1326` R4 bottleneck, `GET /api/zones/{id}/exposure:743` operational risk, `GET /api/zones/{id}/history:379` 365d, `GET /api/model/calib:1221` Bayes.
* `GET /api/simulation/templates` returns `monga-mdl` + `dahal-144` from `forecast.json`.
* Routing: `R2` ridge shortcut always closed to risk-aware (`_road_graphs_for` `main.py:496`), exposure via deterministic geometry — bands don't gate it.
* Done = validator green + `start_demo.ps1` boots + `GET /api/zones` returns S1-S4 with 89/78/66/52. Observed vs forecast always separated.

## Lane C — Data → features (rest) → `feature/sih26001/ngen-pilot` → Phase-1 inventory

* Branch off `feature/sih26001/demo-scaffold`. Pilot extent ONLY (Gangtok cluster) for Sept 5. Inventory-scale via `scripts/build_training_matrix.py:1`.
* Split: (1) rain+moisture → `rainfall_24h/7d/30d_mm`, `soil_moisture` (IMD 0.25° 1901–2024 truth + CCI v09.2 `gangtok_soil_cci.csv:1` 0.271); (2) SRTM→slope/elev/aspect/curv/TWI/SPI + OSM→`distance_to_road/river` + Sentinel-2 NDVI/LULC + seismic 3 (USGS 26 `usgs_quakes.json:1`); (3) Bhusanket filter + negatives (>300 m) → `event` + `manifest.json`. Wound 4/2936 review-queue (`wound_map.json:1`).
* Output format MUST match `feature_matrix.sample.csv` + `manifest.sample.json` (17 numeric + lulc = 22 cols, column order frozen). Full matrix git-ignored `data/sih26001/processed/`; commit ≤20-row sample only. Models `ml/models/*.joblib` git-ignored (`/.gitignore:78`); reports `ml/sih26001/reports/metrics.md:9` committed.
* Target for Sept 5: 1 real slope row with all 17 filled + manifest. Full train is bonus — if RF trains, swap at most ONE fixture score; else present matrix+manifest as "training-ready, spatial-CV next". **Frozen truth:** 2936 rows 1468+1468 Sikkim+Darjeeling (seed 42); GroupKFold-8 OOF RF 0.9338 XGB 0.9418 LGBM 0.9406 Brier isotonic 0.0971; temporal 673/73 OOF 0.8568; TreeSHAP 5 pts; `sih26001_model.py:score_row` live Bayes 0.5→0.01 `confidence_real_1pct` + SWI overlay.
* Done = sample CSV loads, every value has provenance, validator green. Demo-touch frozen at **zero swaps** (`demo_touch: none` `manifest.training.json:954`) — scaffold scores stay 89/78/66/52.

## Result (frozen 2025-11-15)

* Lane A: fixtures ready, `S1 89 S2 78 S3 66 S4 52` `slopes.json:1` + `roads.json:1` — frontend merges off `68c0c28`, R2 avoidance + Yellow/Red kits preserved
* Lane B: `backend/app/main.py:389` `POST /api/reports` + `PATCH` + `queue?status` + `15 tests` + `reports.json:1` — live on `:8000`; live scoring `sih26001_model.py:score_row` + SWI `swi.py:14` + warning 6-state `warning_thresholds.json:1` (Gangtok 385/395/410/375) + isolation R4 `main.py:1326` + exposure `GET /api/zones/{id}/exposure:743` + history 365d
* Lane C: `17 REAL + lulc` `feature_matrix.sample.csv:1` + `2936×22` training `feature_matrix.training.csv:1` **RF 0.9338 XGB 0.9418 LGBM 0.9406 Brier 0.0971 (isotonic) / temporal 673/73 0.8568** `metrics.md:9` `calibration.md:8` `metrics.md:32`; scripts `build_training_matrix.py` `train_sih26001.py` `sih26001_model.py` `swi.py`; evidence `usgs_quakes.json` `warning_thresholds.json` `roads_osm_provenance.json` `wound_map.json` `runout_exposure.json`; reports `ml/sih26001/reports/{metrics,calibration,benchmarks}.md`