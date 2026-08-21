# TALUS — Current System (single source of truth)

Status: 2026-08-21. This document reflects what IS; older docs that describe
superseded plans are listed at the bottom. If a doc conflicts with this one,
this one wins.

## Live architecture

```text
PREDICTION PATH
  observed state (12 V1 features + zone)
    -> frozen RF Model v1 (ml/models/talus_rf_v1.joblib)
    -> instability_score 0-100
    -> isotonic calibration (ml/models/talus_calibration_v1.joblib)
       = P(score >= 75), "calibrated probability of elevated synthetic risk"
    -> FoS-derived risk band
    -> real Tree SHAP explanation

SIMULATION PATH
  Scenario causes (rain realization / blast schedule / historical template)
    -> Scenario Engine v1.5 (ml/scenario/, composes FROZEN generator v1.4.0)
    -> day-by-day FoS/score/label trajectory
    -> Evidence Timeline (state changes + physical causes, NOT SHAP)

API (backend/, FastAPI -- 25/25 tests)
  GET  /api/zones[/id][/features|/trend|/explanation|/decision]
  POST /api/risk/predict                 (prediction path)
  POST /api/simulation/what-if           (ML counterfactual -- labeled as such)
  POST /api/simulation/causal-what-if    (causal physics -- Scenario Engine)
  GET  /api/simulation/templates         (IMD-provenance historical storms)
  POST /api/routes/safe                  (risk-weighted Dijkstra)
```

## Frozen artifacts

| Artifact | Location |
|---|---|
| Generator v1.4.0 | `ml/data_generation/generator_v1.py` (tag `v1.4.0-generator-complete`) |
| Corpus v2 (50 worlds) | `data/processed/generator_v1/ml_handoff/synthetic_ml_dataset_seeds_42_91.csv` |
| Model v1 (RF) | `ml/models/talus_rf_v1.joblib` |
| Calibration v1 (isotonic) | `ml/models/talus_calibration_v1.joblib` |
| Benchmark protocol | `ml/benchmark/protocol.md` |
| Scenario contract | `ml/scenario/spec.md` |
| Model card | `docs/ML_MODEL_CARD_V1.md` |
| Member-2 audit | `docs/MEMBER2_AUDIT.md` |

## Key results (real numbers)

- Unseen-world regression: R2 0.90-0.92 abs (7 model families converge); MAE ~8.5.
- Leakage proof: random split R2 0.998 vs seed-holdout -0.53 -> seed-intact splits mandatory.
- Calibration: Brier 0.081 vs 0.116 naive; ECE 0.095 vs 0.157 (validation seeds).
- Transfer: physics-pretrained 0.906 vs scratch 0.886 @5 worlds; parity by 20-40.
- Scenario: multi-year Dec-1902 replay fires open-crack branch; FoS divergence -0.761 over 51 days.

## Superseded / historical documents (do NOT implement from these)

| Doc | Status |
|---|---|
| docs/source/Talus_Data_Training_Plan.md | HISTORICAL plan; superseded by protocol.md + this doc (calibration now implemented; CV/COOLR/benchmark checks deferred -- see below) |
| docs/source/Talus_Deep_Research_Report.md | HISTORICAL research; architecture evolved past it |
| docs/source/Complete_Context.md | Presentation history only |
| docs/03_DATA_PLAN.md, 04_MODEL_PLAN.md, 05_API_SPEC.md, 05_FEATURE_SCHEMA.md | Original MVP plans; V1 feature contract and API shapes still authoritative where they match code -- otherwise code wins |
| docs/06_DEMO_SCENARIO.md | v2 (re-frozen against real model) |

## Explicitly deferred (decided, not forgotten)

- YOLO/CV crack detection (Tier 3; dataset never downloaded).
- Missingness/noise retraining (Model v1 stays frozen; missing evidence is
  reported from provenance instead).
- COOLR external pattern validation; susceptibility-benchmark sanity check.
- DGMS incident reconstruction.
- New geological features or generator physics changes.

## Known limitations

See docs/ML_MODEL_CARD_V1.md and docs/MEMBER2_AUDIT.md. Headlines: weak
dynamic-driver fidelity; `moderate` band unlearnable as direct multiclass;
no natural regime transitions in passive generation; synthetic-only evidence.
