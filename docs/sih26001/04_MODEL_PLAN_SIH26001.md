# TALUS v2 Model Plan — SIH26001

**Status:** Draft · **Trace to:** `03_DATA_PLAN_SIH26001.md`,
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

## 3. Validation protocol (mandatory, in order)

1. **Spatial cross-validation:** leave-one-cluster-out. Random splits are
   banned (spatial autocorrelation; v1's leakage proof is the precedent:
   random-split R² 0.998 vs seed-holdout −0.53).
2. **Temporal validation:** train ≤2018, test 2019+ (monsoon regime shift
   check).
3. **Calibration:** isotonic on out-of-fold predictions; report Brier + ECE
   vs naive (v1 bar: 0.081 vs 0.116; 0.095 vs 0.157 — v2 must report its own,
   not inherit these).
4. **Published benchmarks:** match-or-exceed table below (§5).
5. **Threshold consistency:** scenario-engine outputs cross-checked against
   Monga 2026 (E = −11.10 + 0.62×D) and Dahal–Hasegawa (>144 mm/day).

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

## 7. Artifacts (to be created — placeholders, not claims)

```text
ngen outputs:   data/sih26001/processed/feature_matrix.<ext> + manifest.json (git-ignored)
models:         ml/sih26001/models/<model>.joblib (git-ignored)
reports:        ml/sih26001/reports/{metrics,calibration,benchmarks}.md (committed)
model card:     docs/sih26001/ML_MODEL_CARD_V2.md (committed on freeze)
```

No artifact exists yet. Any number quoted before these reports land is a
proposal, not a result.
