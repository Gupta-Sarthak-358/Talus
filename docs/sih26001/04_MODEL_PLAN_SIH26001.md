# TALUS Model Plan — SIH26001

**Status:** Built — Phase-1 complete 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · **Trace to:** `03_DATA_PLAN_SIH26001.md`,
`05_FEATURE_SCHEMA_SIH26001.md` · **Source:** `docs/SIH26001_RESEARCH.md`
§7.4–§7.5, §9

---

## 1. Target definition

- **Primary:** landslide susceptibility — binary event / no-event per spatial
 unit + time window.
- **Secondary:** 5-band severity (very low / low / moderate / high / very high)
 mapped from the calibrated score. Band edges freeze after calibration, not
 before.
- **Not predicted:** exact location/time of individual landslides. We predict
 susceptibility, not specific events. (Say this to judges before they ask.)

## 2. Model family selection

Published NER evidence (research §7.5, §10.1):

| Model | Published NER AUC | Role in v2 |
|---|---|---|
| XGBoost | 0.95–0.96 (Dibang, Chamoli) | Primary |
| LightGBM | 0.96 (Dibang) | Candidate third family |
| Random Forest | 0.83–0.90 | Primary (v1 carryover, interpretable) |
| Ensemble (RF+XGB+LGBM) | 0.95+ (NEHU Meghalaya) | Candidate final |
| Logistic Regression | 0.85–0.89 | Baseline only |
| CNN (1D) | 0.88 | Deferred |

**Plan:** start RF + XGBoost (mirrors v1's multi-family convergence habit),
add LightGBM as third family, ensemble only if it beats the best single on
spatial-held-out data. Logistic regression is the mandatory dumb baseline —
no model ships without beating it.

## 3. Validation protocol (built — verified 2026-09-04)

1. **Spatial cross-validation:** `KMeans-8` on coords → `GroupKFold(8)` OOF `train_sih26001.py:129` — `RF 0.921 XGB 0.9256 LGBM 0.9207` `metrics.md:9`, per-cluster `cluster_6 n/a` single-class logged `metrics.md:25`. Random splits banned (v1 leakage proof).
2. **Temporal validation:** `≤2018 vs ≥2019` with `≥30 dated/side` rule `train_sih26001.py:54` — rescued year `16` clusters `build_training_matrix.py:294` → `35/73 dated` `done:true` `RF test AUC 0.9264 Brier 0.0867` `manifest.training.json:144`.
3. **Calibration:** isotonic on `RF` OOF `Brier 0.1019 ECE 0.0` vs `naive 0.25` `calibration.md:8` (same-OOF optimism caveat stated, clean check is temporal above).
4. **Published benchmarks:** `benchmarks.md:5` — Dibang `0.96` → `best 0.9256` below (honest), Meghalaya `>90%` → `84.95%` below, `threshold screen` consistency only.
5. **Threshold consistency:** scenario-engine `Monga E=-11.10+0.62D` `Dahal >144mm` screen `metrics.md:39` — `frac_pos_ge_144 0.1047` (climatology, not event-intensity).

## 4. Scenario / physics engine

- Rainfall-threshold scenarios: Monga 2026 MDL curve + Dahal–Hasegawa
 intensity-duration + monsoon 13 mm/day separator (research §3.3).
- NER physics chain: rainfall (antecedent + triggering) → infiltration /
 wetting state → pore pressure → shear-strength reduction → FoS → score
 (Iverson 2000 infiltration theory; infinite-slope model).
- **Labeling rule (from v1, enforced):** ML counterfactuals are labeled
 counterfactual, never causal. Causal claims go through the scenario engine.

## 5. Benchmarks to beat

| Published result | Our target |
|---|---|
| Dibang XGBoost AUC 0.96 | Match or exceed on spatial-held-out |
| Meghalaya ensemble >90% accuracy | Match or exceed |
| Monga threshold E = −11.10 + 0.62×D | Scenario engine consistent |
| GSI RLFS CSI >70% | Exceed (more data sources than thresholds alone) |
| NASA LHASA 2.0 over NER | NER-specific model outperforms global model |

LHASA doubles as fallback prior for sparse-data pixels (blend, don't hide).

## 6. Explainability + honesty gates (ship-blockers)

- Tree SHAP per prediction; base value + top contributions logged.
- Confidence = calibrated P(elevated susceptibility) under the prototype
 target — never "probability a landslide will occur here tomorrow."
- Off-manifold caveat (v1 lesson): single-feature overrides that break
 realistic feature correlations get a warning, not a silent number.
- Missing-evidence list on every score (proxy tags, undated-inventory tags,
 OSM-QA tags flow through).

## 7. Artifacts (built — committed 2026-09-04)

```text
ngen outputs: data/sih26001/processed/feature_matrix.training.csv (1528×22, 764+764, git-ignored) + data/sih26001/evidence/feature_matrix.training.sample.csv (20 rows, committed) + data/sih26001/manifest.training.json (committed)
models: ml/models/sih26001_{rf,xgb,lgb,lr,iso}_v1.joblib (git-ignored, sha256 in manifest)
reports: ml/sih26001/reports/{metrics,calibration,benchmarks}.md (committed) — RF OOF 0.921 XGB 0.9256 LGBM 0.9207, cal Brier 0.1019, temporal test AUC 0.9264 (35/73 dated)
model card: docs/sih26001/ML_MODEL_CARD_V2.md (committed draft, clean=true)
```

Built: `scripts/build_training_matrix.py:1` 1528 rows + `scripts/train_sih26001.py:1` RF500/XGB/LGBM + SHAP 5-pt `manifest.training.json:shap_sample` on `mnemo` venv (`xgb 3.2/lgbm 4.7/shap 0.51`).
