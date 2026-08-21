# TALUS ML Model Card — v1 (frozen)

Status: FROZEN. Selected via seed-aware validation only; test touched once.
Baseline: Experiment F protocol (`ml/benchmark/experiment_f.py`), generator v1.4.0.

## Model

| Field | Value |
|---|---|
| Estimator | RandomForestRegressor (validation-selected primary) |
| Config | n_estimators=500, max_depth=12, min_samples_leaf=1, random_state=0 |
| Preprocessing | StandardScaler(numeric) + OneHot(rock_type, crack_severity, zone_id) |
| Target | `instability_score` (primary); δ-instability / δ-FoS (secondary) |
| Feature set | **ML_FEATURE_SCHEMA_V1** — the frozen 12 features + zone_id |

## Data

| Split | Seeds | Rows |
|---|---|---|
| Training | 42–81 (40 worlds) | 58,400 |
| Validation | 82–86 (5 worlds) | 7,300 |
| Test (touched once) | 87–91 (5 worlds) | 7,300 |

Corpus: `data/processed/generator_v1/ml_handoff/synthetic_ml_dataset_seeds_42_91.csv`
(generator v1.4.0, schema 1.0, synthetic).

## Metrics (test seeds 87–91)

| Target | R² | MAE | RMSE |
|---|---|---|---|
| abs_instability | 0.897 | 8.51 | 13.52 |
| delta_instability | 0.823 | 8.28 | 13.50 |
| delta_fos | 0.821 | 0.166 | 0.272 |

Context: Dummy floor R² ≈ −0.07; Ridge 0.898; XGB/LightGBM/HistGB 0.90/0.84;
MLP 0.895. Seven model families converge within ~0.02.

## Selection rationale

Random Forest was the validation winner on all three targets
(val R² 0.899/0.901/0.901). Boosting models retained as independent
comparative baselines; their (higher) test scores were NOT used for selection.

## Known limitations

1. Static structure (slope_angle, rock_type) dominates the target; dynamic
   drivers carry weak signal (within-zone correlations mostly < 0.1).
2. Crack-density and blast-PPV directional responses are confounded/lagged
   (audit: classes a/b/c — no generator defect; see directionality audit).
3. `moderate` risk band is never predicted by classifiers (narrow band +
   zone pinning); ordinal formulation recommended for classification work.
4. Generator produces almost no safe→dangerous regime transitions
   (6 strict events in 109,500 zone-days) — early-warning claims are NOT
   validated by this corpus.
5. Temporal trend features (V2) do NOT improve nowcasting or ≤7-day
   forecasting (Experiment F/F2): FoS is memoryless given current state and
   persistence is near-optimal at short horizons (R² 0.998 @ 1-day).

## Reproducibility

random_state=0 throughout; splits seed-intact; no random row splits.
Generator, constants, thresholds, targets and test seeds are frozen.
