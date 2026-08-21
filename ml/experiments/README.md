# ML Campaign Experiments (archived as-run)

Historical record of the experiments that shaped the frozen benchmark and
architecture decisions. Ledger entries: docs/observations.md SS23.1-SS23.7.

## Contents

| File | Experiment | Key result |
|---|---|---|
| baseline.py | Naive vs seed-holdout split (5 seeds) | R2 0.998 leaked vs -0.53 honest |
| native_compare.py | Random-split inflation quantification | R2 0.998/0.984 vs -0.53 |
| experiment_AB.py | A: chronological within-seed; B: static-vs-dynamic | A: 0.66-0.94/zone; B: dynamic -1.64 |
| experiment_C.py | C: delta-targets (train-only baselines) | R2 -0.58 -> +0.13 |
| gen_seeds.py + experiment_D.py | D: world expansion 5 -> 20 seeds | d-fos 0.125 -> 0.457 |
| ann_probe.py | MLP + LSTM-14day | MLP parity 0.895; LSTM no gain (Markov) |
| transfer_probe.py | Physics-pretrained fine-tune + TrAdaBoost.R2 | 0.906 vs 0.886 @5 worlds |
| extended_study.py | 75-world corpus: regression/classification/transitions | curve flat; moderate never predicted; 6 transitions |
| diagnose_extended.py | Extended-study diagnostics | test-set composition + pinning proof |
| audit_directionality.py | Crack/blast directionality audit | confounds/lags/artifact; no generator defect |
| verify_monotonicity.py | Raw-data monotonicity verification | ZONE_B -0.26 flips +0.36 controlled |
| experiment_g_dem.py | G: DEM context (elevation, regional slope) | KILLED: all targets degrade |

## Results

Raw metric JSONs in `results/`. Benchmark results for the FROZEN protocol live
separately in `ml/benchmark/results/`.

## Reproduction notes

Scripts are archived byte-exact as run; hardcoded paths point at the original
scratch location (`%LOCALAPPDATA%\Temp\opencode\talus_ml_probe`) and the
committed corpus at `data/processed/generator_v1/ml_handoff/`. To re-run:
adjust the path constants at top of each script, or regenerate intermediate
corpora with `gen_seeds.py` (seeds 42-61) / `extended_study.py`
(seeds 42-116, ~18 MB, deterministic from frozen generator v1.4.0).

Trained production artifact: `ml/models/talus_rf_v1.joblib` (compressed;
regenerated automatically by `backend/app/model_service.py` if deleted).
