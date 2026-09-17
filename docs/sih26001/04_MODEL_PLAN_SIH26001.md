# TALUS Model Plan — SIH26001

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Status:** Built — Phase-1 complete frozen 2025-11-15 · **Trace to:** `03_DATA_PLAN_SIH26001.md`, `05_FEATURE_SCHEMA_SIH26001.md` · **Source:** `docs/SIH26001_RESEARCH.md` §7.4–§7.5, §9

---

## 1. Target definition

- **Primary:** landslide susceptibility — binary event / no-event per spatial unit + time window (season-window proxy tagged `approximate` when undated, 2936 rows 1468+1468 seed 42).
- **Secondary:** 5-band severity (very low / low / moderate / high / very high) mapped from the calibrated score via `model_service.band_for_score` (edges frozen post-calibration, not before; scaffold 89/78/66/52).
- **Not predicted:** exact location/time of individual landslides. We predict susceptibility, not specific events. (Say this to judges before they ask.) Field rate ~1% view is `confidence_real_1pct` (Bayes 0.5→0.01), score stays frozen from raw proba.

## 2. Model family selection

Published NER evidence (research §7.5, §10.1):

| Model | Published NER AUC | Role in v2 (actual 2025-11-14) |
|---|---|---|
| XGBoost | 0.95–0.96 (Dibang, Chamoli) | Primary — OOF 0.9418 `metrics.md:9` |
| LightGBM | 0.96 (Dibang) | Candidate third family — 0.9406 |
| Random Forest (500 trees) | 0.83–0.90 | Primary (v1 carryover, interpretable) — **OOF 0.9338** beats LR, drives live scoring `sih26001_model.py:score_row` |
| Ensemble (RF+XGB+LGBM) | 0.95+ (NEHU Meghalaya) | Deferred (best single XGB 0.9418 shipped) |
| Logistic Regression | 0.85–0.89 | Baseline only — **0.8914** |
| CNN (1D) | 0.88 | Deferred |

**Plan executed:** RF + XGBoost stared (mirrors v1's multi-family habit), LGBM as third family, no ensemble (best single XGB 0.9418 wins). LR mandatory dumb baseline beaten (0.9338 vs 0.8914). Wound appended as rare feature 4/2936, then **REMOVED from X per E8** (no measurable signal; rebuild as disturbance score later, test on road-event recall).

## 8. Frozen predictive architecture (E12 decision + E14 collapse, 2026-09-17)

E12 found a South specialist edge (5 seeds × RF500/XGB400, ΔPR +0.041/+0.044);
E14 tested it operationally (calib-transferred R80 operating points) and the
pre-registered rule fired COLLAPSE (RF 1/5, XGB agree 2/5 — specialist higher
recall but substantially higher FAR; matched-recall diagnostic RF 2/5, XGB 0/5).
Final: **one global scorer + regional calibration + regional warning policy**
— no specialists, no ensembles. Full record: `EXPERIMENTS_E_LADDER.md`
(E12/E14) + `scripts/e12_south_confirmation.py` + `scripts/e14_warning_policy.py`.
Leaderboard: easy-background OOF 0.9339 · hard-negative stress 0.7804 · corrected
pooled 0.8950 · matched pooled 0.8478 · temporal 0.8578. Production family (RF vs
XGB) is a separate later decision. Next: E15 replay, then championship.

## 3. Validation protocol (built — verified 2025-11-14)

1. **Spatial cross-validation:** `KMeans-8` on coords (seed 42) → `GroupKFold(8)` OOF `train_sih26001.py:129` — **RF 0.9338 XGB 0.9418 LGBM 0.9406 LR 0.8914** `metrics.md:9`, per-cluster out shape `cluster_0 n/a` single-class logged `metrics.md:25`. Random splits banned (v1 leakage proof). Previous stale 0.8983 is expunged — do not cite.
2. **Temporal validation:** `≤2018 vs ≥2019` with `≥30 dated/side` rule `train_sih26001.py:54` → `673/73 dated` `done:true` `manifest.training.json:144` → **RF test AUC 0.8568 Brier 0.0978 ECE10 0.0986** `metrics.md:32` (n=807). Earlier draft 0.8189 superseded by 2025-11-14 run.
3. **Calibration:** isotonic on RF OOF `Brier 0.0971 ECE 0.0` vs raw `0.118` vs naive `0.25` `calibration.md:8` (same-OOF optimism caveat stated, clean check is temporal 0.0978 above); plus **Bayes prevalence correction** `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` for field 1% (`pi_train 0.5→pi_real 0.01`, `GET /api/model/calib:1221` + `score_row confidence_real_1pct`).
4. **Published benchmarks:** `benchmarks.md:5` — Dibang `0.96` → best 0.9418 just below (honest), Meghalaya `>90%` → 82–84% range below, threshold screen consistency only.
5. **Threshold consistency:** scenario-engine `Monga E=-11.10+0.62D` `Dahal >144mm` screen `metrics.md:39` — `frac_pos_dailymax_ge_144 0.1907` (climatology, not event-intensity).
6. **Features:** 17 numeric (spi→spi_log + seismic 3) + lulc one-hot drop_first; lithology/lineament omitted uniform PROXY (`manifest.training.json:263`), previous_landslide omitted leakage (positives ARE inventory slides), wound rare 4/2936 kept. 22-col sample `feature_matrix.sample.csv:1`.
7. **Explainability:** TreeSHAP top-4 per live row (`sih26001_model.py:explain_row`, 5-pt sample `manifest.training.json:shap_sample`).

## 4. Scenario / physics engine

- Rainfall-threshold scenarios: Monga 2026 MDL curve + Dahal–Hasegawa intensity-duration + monsoon 13 mm/day separator (research §3.3).
- NER physics chain: rainfall (antecedent + triggering + forecast 3-day) → **SWI JMA 3-tank** `swi.py:14` (L1=15 L2=60 L3=60 a1=0.10 b1=0.12) infiltration / tank storage → pore-pressure proxy → shear-strength reduction → FoS → score (Iverson 2000 infiltration theory; infinite-slope model).
- Effective rain proxy for warning: `rain7 + 0.3*rain30`, local thresholds `warning_thresholds.json:1` Gangtok 385/395/410/375, quake-conditioned −25% (USGS 26), SWI ≥0.40 `swi_for_zone`.
- **Isolation physics:** road-graph bottleneck (R4) cuts egress to plains even if upslope spur open — `may_isolate` predictive one-at-risk-left logic (`_isolation_for_location:1326`).
- **Labeling rule (from v1, enforced):** ML counterfactuals are labeled counterfactual, never causal (`POST /api/simulation/what-if:567` S3 66→74). Causal claims go through the scenario engine (`POST /api/simulation/causal-what-if:629`).

## 5. Benchmarks to beat

| Published result | Our target | Actual 2025-11-14 |
|---|---|---|
| Dibang XGBoost AUC 0.96 | Match or exceed on spatial-held-out | XGB 0.9418 — just below, honestly gap |
| Meghalaya ensemble >90% accuracy | Match or exceed | ~82–84% acc@0.5, below — honestly gap |
| Monga threshold E = −11.10 + 0.62×D | Scenario engine consistent | Screen 0.1907 (climatology) |
| GSI RLFS CSI >70% | Exceed (more data than thresholds alone) | OOF 0.9338 + Brier 0.0971 + temporal 0.0978 |
| NASA LHASA 2.0 over NER | NER-specific model outperforms global model | NER XGB 0.9418 vs global LHASA (not co-evaluated; LHASA doubles as fallback prior for sparse pixels — blend, don't hide) |

## 6. Explainability + honesty gates (ship-blockers — all passed 2025-11-14)

- TreeSHAP per live prediction; base value + top-4 contributions logged (`sih26001_model.py:explain_row`, 35/35 live tests include explainer fallback).
- Confidence = calibrated P(elevated susceptibility) under prototype season-window target — never "probability a landslide will occur here tomorrow." Field view `confidence_real_1pct` via Bayes documented separately.
- Off-manifold caveat (v1 lesson): single-feature overrides that break realistic correlations get a warning, not a silent number (`WhatIfDrawer` flagged).
- Missing-evidence list on every score (proxy tags, undated-inventory tags, OSM demo-topology tags flow through).
- Scoring frozen from raw `p*100`; calibration does not move scaffold bands 89/78/66/52.

## 7. Artifacts (built — committed 2025-11-14)

```text
ngen outputs: data/sih26001/processed/feature_matrix.training.csv (2936×22, 1468+1468, git-ignored) + data/sih26001/evidence/feature_matrix.training.sample.csv (20 rows, committed) + data/sih26001/fixtures/feature_matrix.sample.csv (12×22 demo, committed) + manifest.training.json + manifest.sample.json (committed)
models: ml/models/sih26001_{rf,xgb,lgb,lr,iso}_v1.joblib (git-ignored, sha256 in manifest, sklearn 1.9 pickle compat shim in sih26001_model.py)
reports: ml/sih26001/reports/{metrics,calibration,benchmarks,counterfactual_summary,wound_as_feature}.md — RF OOF 0.9338 XGB 0.9418 LGBM 0.9406, cal Brier 0.0971, temporal AUC 0.8568 Brier 0.0978 (673/73 dated)
evidence: data/sih26001/evidence/{usgs_quakes,roads_osm_provenance,bhukosh_vector_attempt,warning_thresholds,runout_exposure,wound_map,replay_series}.json
fixtures: data/sih26001/fixtures/{slopes,roads,forecast,alerts,feature_matrix.sample}.json + slopes.{lachung,darjeeling}.json + locations.json (12 demo slopes)
api: backend/app/{sih26001_model,swi,data,main}.py — live-rf scoring (Sih26001Live), SWI swi.py L1=15…, isolation _isolation_for_location R4, warning 6-state, Bayes calib
model card: docs/sih26001/ML_MODEL_CARD_V2.md (2025-11-14 frozen, clean Brier 0.0978, wound 4/2936 documented)
tests: backend/tests 9 suites 60 funcs, 35/35 live (env-gated live forecast needs network; fixture path always passes)
```

Built: `scripts/build_training_matrix.py:1` 2936 rows + `scripts/train_sih26001.py:1` RF500/XGB/LGBM + TreeSHAP 5-pt `manifest.training.json:shap_sample` + `scripts/build_replay_series.py` / `runout_exposure.py` / `wound_map.py` evidence generators.