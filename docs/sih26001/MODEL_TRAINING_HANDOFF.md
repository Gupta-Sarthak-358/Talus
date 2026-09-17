# MODEL TRAINING HANDOFF — Inventory-Scale Susceptibility (SIH26001) — Frozen 2025-11-14

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**For:** the agent/teammate taking or auditing the training lane
**Date:** 2025-11-14 (Phase-1 frozen) · **Branches:** base `SIH26001` (pre-freeze `fc181f0`, lane `feature/sih26001/model-training` → `SIH26001`)
**Contracts:** `SCAFFOLD_CONTRACT_SEPT5.md` §1 (S1–S4 frozen) + `05_FEATURE_SCHEMA_SIH26001.md:16` (22-col: 17 numeric + lulc + keys) + `04_MODEL_PLAN_SIH26001.md` (validation law) + `ML_MODEL_CARD_V2.md`
**Frozen bands:** `89/78/66/52` (scaffold, `data.py:308` `live_scores` honest fallback) · **R2 avoidance:** ridge shortcut `R2` at-risk always closed to risk-aware routing (`main.py:496` `_road_graphs_for`), not slope band

Paste-ready prompt is at the bottom. The rest is the frozen spec.

---

## 0. Current state — Phase-1 complete (not "feasible now")

Sept 5 pilot (`feature_matrix.sample.csv:1` 4-row single-class) was fabrication-blocked. **Now built 2025-11-14:**

* **Matrix:** `data/sih26001/processed/feature_matrix.training.csv` **2936 rows 1468+1468** (Sikkim + Darjeeling-hills, seed 42, >300m background buffer, dedupe 50 m) via `scripts/build_training_matrix.py:1` → sample `feature_matrix.training.sample.csv` 20 rows committed. Shape `2936×22` (`manifest.training.json:42` + `manifest.sample.json`).
* **Features in X — 17 numeric + lulc:** `slope_angle elevation aspect curvature twi spi_log rainfall_24h/7d/30d soil_moisture ndvi distance_to_road/river drain_density seismic_dist_km/n50_rate/years_since` + `lulc` one-hot drop_first (`usgs_s234.json:1` D8, `swi.py:14`, `sih26001_model.py:score_row`). **Omitted from X:** `lithology/lineament` uniform PROXY (`lingtse_granite_gneiss` 0.8, `bhukosh_vector_attempt.json:1` timeout) + `previous_landslide` leakage (positives ARE inventory slides). `wound` 4/2936 review-queue rare kept (`wound_as_feature.json:1`).
* **Validation (frozen):** GroupKFold 8 OOF (KMeans-8 coords seed 42, `train_sih26001.py:129`) — **RF 0.9338 / XGB 0.9418 / LGBM 0.9406 / LR 0.8914**, Brier raw 0.118 → **isotonic 0.0971 ECE 0.0** (`calibration.md:8`, same-OOF optimism disclosed); **temporal 673/73 OOF 0.8568** Brier 0.0978 ECE10 0.0986 n=807 (`metrics.md:32`, `manifest.training.json:144`); TreeSHAP 5-pt sample (`sih26001_model.py:explain_row`, `manifest.training.json:shap_sample`).
* **Live scoring:** `backend/app/sih26001_model.py:1` `Sih26001Live` — encoder → RF → isotonic → Bayes `p_real= p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` (`pi_train 0.5→pi_real 0.01`) exposed as `confidence_real_1pct` (`main.py:1221` `GET /api/model/calib`), `score=round(p*100)`. Weights absent → `None` → scaffold 89/78/66/52 retained, never crash.
* **Operational overlays (NOT in X, scoring frozen):** SWI JMA 3-tank `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 → `tanh(SWI/100)` via `GET /api/soil/swi:1203` `swi_for_zone(rain7,rain30,forecast3)` threshold 0.40 `main.py:1423`; warning 6-state `main.py:1449` NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE with local `warning_thresholds.json:1` Gangtok 385/395/410/375 (effective `r7+0.3*r30`, quake-conditioned `*0.75` for 26 USGS events `usgs_quakes.json:1` 59y); isolation R4 bottleneck (`main.py:1326` `_isolation_for_location` R4 blocked ⇒ S1/S2/S3 isolated, predictive `may_isolate`); exposure operational risk `GET /api/zones/{id}/exposure:743` `score*(1+0.18*log1p(buildings)/3+0.12 wound+0.20 isolated)`; history 365d `GET /api/zones/{id}/history:379`; Yellow/Red kits + observed vs forecast separation.
* Demo protection: `TEAM_TASKS_SEPT5:24` Lane C — training was upside, not a demo blocker. Done banner: `demo_touch: none` `manifest.training.json:954` (zero swaps; frozen bands untouched).

## 1. Workflow (every time — repro)

```bash
git clone https://github.com/Gupta-Sarthak-358/Talus.git && cd Talus
git fetch origin && git checkout SIH26001 && git pull
git checkout -b feature/sih26001/model-training  # or audit branch
python scripts/check_scaffold.py          # must stay green (bands 89/78/66/52)
python scripts/validate_ngen_sample.py    # must stay green
python -m unittest discover -s tests -p "test_*.py" -v
# Repro: python scripts/build_training_matrix.py → 2936×22 (git-ignored)
#        python scripts/train_sih26001.py → ml/sih26001/reports/{metrics,calibration,benchmarks}.md + ml/models/*.joblib
```

1. Fetch/build → commit SMALL extracts/samples + script + sha256 to `manifest.training.json` / `manifest.sample.json`; full matrix git-ignored `data/sih26001/processed/` `/.gitignore:46`.
2. Train → `ml/sih26001/` reports committed, **models `ml/models/*.joblib` git-ignored** `/.gitignore:78` (sha256 in manifest, sklearn 1.9 pickle compat shim in `sih26001_model.py`); `data/sih26001/evidence/*.json` committed.
3. PR into `SIH26001` with gate outputs + method note. Never touch `slopes.json`/`roads.json`/`forecast.json`/bands/R2 graph/roles/fronted pages.

## 2. What was built (inventory-scale)

### Positives
Deduped GSI 30,842 `GSI_Landslide_Inventory.shp.zip` + 693 Sikkim `sikkim_join.json:6` + 7 Gangtok report `sikkim_report_gangtok.csv:1` by haversine <50 m → 2286 deduped → 1468 in study area 88.06–88.96/27.0–27.999 (inside `n27_e088`, 3 corridors `locations.json:1`). Season-window proxy JJAS tagged `approximate`; dated 673/73 for temporal split `manifest.training.json:144`.

### Negatives
Seeded random points >300 m from any positive (`03_DATA_PLAN:135`, `07_ASSUMPTIONS:6`), 1:1 ratio, same tile bbox. Logged buffer + seed 42 + 50/50 timeless background for temporal.

### Features per point (17 numeric + lulc + keys = 22 cols)
* DEM 6: `extract_usgs.py:1` pattern — bilinear elev + Horn slope/aspect + Laplacian curvature + D8 `twi/spi` + `drain_density` on committed `n27_e088_1arc_v3.tif`.
* Rain: IMD 0.25° `ind2024_rfp25.nc` 1901–2024 (observed truth, per-row source in `training_sidecar.csv` `rain_source`); year-known → that-year JJAS peak, exact-date → trailing windows, else 1991–2020 climatology; live `GET /api/forecast/live:1154` Open-Meteo 7d + gated `GET /api/forecast/imd-live:1124`.
* Soil: CCI COMBINED TCDR v202505/v09.2 `gangtok_soil_cci.csv:1` 0.271 (7/7 valid, window-mean June 10–16 per row-year, `extract_soil_cci.py:1`); SWI 3-tank warning overlay only.
* NDVI: pinned `S2B_45RXL_20241129` + WorldCover `s234_lulc.json:1` 10 m mode; LULC one-hot.
* OSM distances: Geofabrik Sikkim extract locally (not Overpass ×2k) → per-point haversine → `roads_osm_provenance.json:1` Gangtok 1014 / Lachung 226 / Darjeeling 504; `distance_to_river` DEM fallback EDT if needed.
* Seismic 3: USGS 26 events `usgs_quakes.json:1` `_seismic_lookup` 59y window → `seismic_dist_km/n50_rate/years_since`.
* Omitted: lithology/lineament uniform logged `manifest.training.json:263`, previous_landslide leakage.

### Train + validate (`04_MODEL_PLAN:37-50`)
RF 500 trees (primary, live) → XGB (best OOF 0.9418) → LGBM → LR baseline. Mandatory: spatial GroupKFold-8, isotonic Brier/ECE (`model_service.py:38` pattern), temporal `≤2018/≥2019` with `≥30 dated/side` rule, threshold screen vs Monga `E=-11.10+0.62D` + Dahal 144 mm (`metrics.md:39`). Reports `ml/sih26001/reports/{metrics,calibration,benchmarks}.md` committed; model card `docs/sih26001/ML_MODEL_CARD_V2.md` frozen.

## 3. Deliverables & gates

* **Definition of done:** beats LR on spatial-held-out + calibration reported (Brier/ECE), temporal 0.8568, not a magic AUC. Dibang 0.96 / Meghalaya >90% → honestly gap 0.9418 / 82–84%.
* **Artifacts committed:** `feature_matrix.training.sample.csv` 20 rows + `manifest.training.json` + `roads_osm_provenance.json` + `bhukosh_vector_attempt.json` + `usgs_quakes.json` + `warning_thresholds.json` + `runout_exposure.json` + `wound_map.json` + `ml/sih26001/reports/*` + `ML_MODEL_CARD_V2.md`.
* **Artifacts git-ignored:** `data/sih26001/processed/feature_matrix.training.parquet|.csv` + `data/raw/imd/*.nc` + `ml/models/*.joblib` (`RF_BLOB`/`ISO_BLOB` `talus_rf_v1.joblib` whitelist exception only).
* **Allowed demo touch:** `Lane C` — at most one `slopes.json` score swap + model card, only if clean. Frozen run: **zero swaps** (`demo_touch: none`).
* **Never:** fabricate dates for 24h windows, train on `n=4`, commit datasets/weights/`.env`/`PILOT_BRIEFING.md`, or write `FILL`.
* **Gates before PR:** `check_scaffold.py` + `validate_ngen_sample.py` + `unittest` all green, paste outputs, bands 89/78/66/52 + R2 avoidance unchanged.

## 4. Risks & mitigations (archived — handled 2025-11-14)

* Overpass ×2k → local Geofabrik extract + bulk out-center nearest; Darjeeling 429/504 backoff logged.
* COG reads ×1k → single pinned scene `S2B_45RXL_20241129`.
* Tile bounds → frozen to n27_e088 88–89E/27–28N (`manifest.training.json:5`), expanded via `88.06–88.96/27.08–27.999` inset for Darjeeling-hills.
* Single-class pilot trap → builder asserts both `event` classes before training.
* Dropout risk: warnings now delivered via produced `reports.json:1` queue, so downed instruments degrade to delayed queues, not silent loss.

## 5. Questions for the requester (resolved defaults)

1. **Target:** season-window proxy `approximate` (chosen — matches `07_ASSUMPTIONS:5`) vs strict dated-event (near-zero positives, not viable) → dated 673/73 kept for temporal validation only.
2. **Study area:** tile-bounded n27_e088 (chosen, no n28 fetch) with inset 88.06–88.96 for Darjeeling-hills coverage.
3. **Ambition for 2025-11-14:** Phase-1 + model card frozen, zero swaps (chosen). No further training without ADR.

---

## Paste-ready prompt for a new agent

```
You are the model-training auditor for TALUS SIH26001 (NER landslide, Phase-1 frozen 2025-11-15).
Setup: git clone https://github.com/Gupta-Sarthak-358/Talus.git && cd Talus && git fetch origin && git checkout SIH26001 && git pull && git checkout -b audit/sih26001-train-verify
Then read docs/sih26001/MODEL_TRAINING_HANDOFF.md — it is your complete spec: data locations, dedupe/negative rules (50m/300m, seed 42, 2936 rows 1468+1468 Sikkim+Darjeeling), per-point feature reuse (USGS SRTM, IMD 0.25° exact-year/climatology tagging, CCI soil 0.271, pinned S2 20241129 + WorldCover, local OSM 1014/226/504, USGS 26 quakes 59y), validation protocol from docs/sih26001/04_MODEL_PLAN_SIH26001.md (GroupKFold-8 mandatory OOF RF 0.9338 XGB0.9418 LGBM0.9406 Brier isotonic 0.0971, temporal 673/73 OOF 0.8568 Brier 0.0978), deliverables, and gates.
Hard rules: never train on data/sih26001/fixtures/feature_matrix.sample.csv (12-row demo); train matrix is git-ignored data/sih26001/processed/ (commit ≤20-row sample only), models ml/models/*.joblib git-ignored, reports ml/sih26001/reports/ committed; live scoring is backend/app/sih26001_model.py (Bayes 0.5→0.01 confidence_real_1pct) + backend/app/swi.py L1=15 L2=60 L3=60 JMA 3-tank warning overlay (not in X) + warning 6-state with warning_thresholds.json S1 385 etc + isolation R4 bottleneck; max demo touch is 1 slopes.json swap + model card only if clean (frozen run did zero swaps, bands stay 89/78/66/52, R2 avoidance fixed); never commit datasets/weights/.env/docs/PILOT_BRIEFING.md and never use FILL; gates before PR: python scripts/check_scaffold.py && python scripts/validate_ngen_sample.py && python -m unittest discover -s tests -p "test_*.py" -v all green — paste outputs in PR body into SIH26001.
Key scripts: scripts/build_training_matrix.py, scripts/train_sih26001.py, backend/app/sih26001_model.py, backend/app/swi.py, backend/app/main.py (warning_thresholds + _isolation_for_location + exposure + history 365d + Yellow/Red kits + observed vs forecast).
Artifacts to verify: ml/models/sih26001_*v1.joblib (absent on fresh clone → fixture fallback), ml/sih26001/reports/metrics.md:9 metrics, calibration.md:8 Brier 0.0971, benchmarks.md, data/sih26001/evidence/{warning_thresholds,usgs_quakes,roads_osm_provenance,wound_map,runout_exposure}.json.
```