# Member 2 — Final Audit (Phase 20)

Status: CLOSED. All items verified. Date: 2026-08-21.

## Frozen artifacts

| Artifact | State | Reference |
|---|---|---|
| Generator v1.4.0 | FROZEN, untouched since tag | `v1.4.0-generator-complete`, `ml/data_generation/generator_v1.py` |
| 50-world corpus | Exported, committed | `data/processed/generator_v1/ml_handoff/synthetic_ml_dataset_seeds_42_91.csv` |
| Benchmark protocol v1 | FROZEN | `ml/benchmark/protocol.md` |
| ML Model v1 | FROZEN (RF, validation-selected) | `docs/ML_MODEL_CARD_V1.md` |
| Feature contract | V1 (12 features) — V2 trends archived as refuted experiment | Ledger §18 |
| Scenario Engine v1.5 | FROZEN, all gates PASS | `ml/scenario/spec.md` |

## Evidence chain

| Claim | Evidence |
|---|---|
| Random row splits invalid | R² 0.998 (leaked) vs −0.53 (honest, 5 worlds) |
| World coverage was the bottleneck | 5→20→40 worlds: δ-R² 0.13→0.46→0.85; abs −0.58→0.59→0.92 |
| Model generalizes on unseen worlds | Test seeds 87–91: R² 0.90–0.92 across 7 model families |
| Selection honesty | RF chosen by validation only; boosting test scores never used for selection |
| Physics learned for the right reasons | Permutation/SHAP: statics+groundwater dominate, scheduler noise ≈ 0 |
| Crack/blast anomalies understood | Directionality audit: confounds (a), lags (b), ML artifact (c); no generator defect (d) |
| Temporal memory unnecessary | LSTM ≈ snapshot models; persistence R² 0.998 @1-day; FoS memoryless |
| V2 trend features refuted | Experiment F/F2: V2 ≤ V1 everywhere; archived, not shipped |
| Transfer prior works at scarcity | Pretrained 0.906 vs scratch 0.886 @5 worlds; parity by 20–40 |
| Scenarios are causal composition | 6 engine gates + 6 edge cases PASS; no direct score writes |
| Acute shock ≠ accumulated damage | Single-year storms compress; 3-yr Dec-1902 replay fires open-crack branch, ΔFoS −0.761 |

## Validation gates (final state)

Engine (`validate_scenarios.py`): baseline replay exact / pre-start isolation /
dose-response monotone / determinism / no score writes / crack continuity — **ALL PASS**.

Edge cases (`summaries.py`): scale-0 == baseline / start-day-0 / window overrun
clipping / blast-surge no-op on unblasted zones / unknown kind raises /
short-template padding — **ALL PASS**.

## Known limitations (shipped honestly)

1. Dynamic-driver fidelity weak in generated data (crack/blast confounds).
2. Risk-band classification: `moderate` band never predicted; ordinal
   reformulation recommended before production classification.
3. Generator produces almost no natural regime transitions; What-If
   deterioration requires multi-year cumulative scenarios.
4. No real-mine failure dataset — synthetic-only claims.
5. Single-year What-If score deltas are compressed by design of frozen physics;
   trajectories expose groundwater/crack/FoS responses that scores mask.

## Handoff to Member 3

- Prediction path: V1 features → RF → instability_score → risk_label.
- Simulation path: Scenario → engine → trajectory CSVs + summaries.
- Integration contract: consume `run_scenario()` frames and
  `serialize_trajectory()` outputs; never route scores around the physics.
