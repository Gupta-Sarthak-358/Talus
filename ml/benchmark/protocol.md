# TALUS ML Benchmark Protocol — v1 (frozen)

Status: FROZEN protocol. Applies to the v2 corpus
(`data/processed/generator_v1/ml_handoff/synthetic_ml_dataset_seeds_42_91.csv`).

Ties to: `docs/GENERATOR_V1_SPEC.md` (generator frozen at v1.4.0),
`docs/05_FEATURE_SCHEMA.md` (12 frozen features), `docs/observations.md`
(Entries 22-23 provenance).

## 1. Goal (what this benchmark answers)

Does an ML model learn the *cross-world* instability relationship encoded by
the frozen physics generator, when the model never sees a test seed?
This is a **capacity + coverage** benchmark, NOT a tuning Olympics. One number
never appears as a headline unless it survived a completely-unseen-seed test.

## 2. Non-negotiable split rule (frozen)

- **NO random row splits.** Rows within a seed (4 zones x 365 days) are
  highly correlated (same world). A random split yields R2 ~= 0.998 = leakage.
- Seeds are the only unit of split. Entire seeds are assigned to train /
  validation / test. Never split a seed across partitions.
- Official partition (frozen for this round):
  - TRAIN       seeds 42..81   (40 worlds, 58,400 rows)
  - VALIDATION  seeds 82..86   (5 worlds, 7,300 rows)
  - TEST        seeds 87..91   (5 worlds, 7,300 rows)
- Tuning may use TRAIN (with GroupKFold over seeds) and VALIDATION (model
  selection only). TEST is touched exactly once, after tuning is finished,
  to report final metrics. No test re-use, no test-tuned hyperparameters.

## 3. Targets (3, frozen)

| Target           | Formula                             | Meaning                                |
| ---------------- | ----------------------------------- | -------------------------------------- |
| abs_instability  | instability_score                   | "How unstable is this zone right now?" |
| delta_instability| instability_score - baseline(zone)   | Deviation from the zone intact state   |
| delta_fos        | fos - baseline_fos(zone)            | Physical deviation from intact FoS     |

Baseline per zone and target is derived **from TRAIN rows only** and is zone-scaled:

- baseline_inst(zone) = min(instability_score) over train rows of that zone
- baseline_fos(zone)  = max(fos) over train rows of that zone (higher is safer)

Rationale: intact/dry physical state of the zone. This is a diagnostic baseline
definition, not yet the final production target; see "Deferred" ($7).

## 4. Features (frozen, 12 ML-facing + zone as categorical)

12 features from `project_ml()`: rainfall_24h_mm, rainfall_7d_mm, slope_angle_deg,
slope_height_m, rock_type, crack_density, crack_severity,
blast_frequency_per_week, blast_vibration_ppv_mms, days_since_inspection,
prior_incident, groundwater_proxy. Plus **zone_id** as an explicitly-labelled
categorical (grouping key). The model must decide whether zone_id helps or
hurts cross-seed transfer; this is measured, not assumed. No feature scaling
is meaningfully required for tree models; linear models use StandardScaler via
a dedicated ColumnTransformer (see config).

## 5. Models (frozen registry, in this order)

1. DummyRegressor(mean)        -- floor for regression
2. Ridge                       -- linear baseline
3. RandomForest                -- established baseline (Exp A-D)
4. HistGradientBoosting        -- gradient boosting reference
5. XGBoost                     -- boosting, native treatment of missing
6. LightGBM                    -- boosting, fast, categorical-native

All regression models run on ALL 3 targets. Default params first ($6a), then
tuned best-validated config ($6b) re-evaluated on TEST exactly once.

## 6. Workflow (frozen)

### 6a. Default-param baseline
Fit each model with documented default/typical params on TRAIN, evaluate on
VALIDATION (diagnostic) and TEST (headline). Report MAE, RMSE, R2 per target,
plus 95% bootstrap CI of R2 over test *seeds*.

### 6b. Tuning (TRAIN-only via GroupKFold; VALIDATION for model selection)
- Hyperparameter search space per model family (RandomizedSearchCV).
- **GroupKFold(k=5) with groups=seed** over TRAIN seeds only. NO test rows in CV.
- Select lowest validation-fold RMSE. Then refit on TRAIN+VALIDATION
  (seeds 42-86) with the winning config. Evaluate ONCE on TEST (seeds 87-91).
- Any accidental test-peek invalidates the result; re-run protocol from clean state.

### 6c. Explainability
- Permutation importance (seed-aware strategy: permute within test seeds) per
  model, per target; report changes in RMSE not raw accuracy.
- SHAP (TreeExplainer) on best validated model for delta_fos + abs_instability
  to expose physics-aligned drivers (rain-groundwater-cracks-blast vs static).
- Summary verdict: does variable ranking align with generator physics?

## 7. Deferred (explicitly NOT decided here, reviewed later with Member 3)

- Final production target choice (abs vs delta) -- data dependent.
- Baseline definition hardening (physical intact state vs observed min/max).
- Stress-event evaluation (storms, rapid crack growth) -- new eval harness.
- Future-time monitoring benchmark (past->future within a world).
- Classification (risk_label) benchmark and class-balancing.

## 8. Reproducibility (frozen)

- random_state=0 everywhere; n_jobs=-1; same sklearn/XGB/LGBM versions recorded
  in run manifest. Generator unchanged (v1.4.0). Corpus file hash recorded at
  run time. All results reproduce from `run_all.py --save` outputs.

## 9. File layout

ml/benchmark/
  protocol.md        (this file)
  config.py          (paths, features, targets, splits, model registry)
  prepare.py         (load v2 corpus, derive baselines, build partition)
  baselines.py       ($6a default-param evaluation)
  tuning.py          ($6b GroupKFold tuning + final test eval)
  explain.py         ($6c permutation + SHAP)
  run_all.py         (orchestrator that emits a single manifest)