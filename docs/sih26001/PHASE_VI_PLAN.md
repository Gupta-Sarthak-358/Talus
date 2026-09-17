# TALUS Phase VI Plan — Task-Correct Forecasting (FROZEN 2026-09-18)

Status: NOT STARTED. Phase V evaluation chain stays closed and untouched.

## Diagnosis inherited (measured, not hypothesized)

- Training target was season-window susceptibility ("WHERE"), M0 asked forecasting ("WHEN").
- Dynamics carry ~zero permutation signal (rain24h = 0.0); train-serve range skew
  (training 24h min 10.9 mm vs replay 0–5 mm); isotonic never saw time.
- M1-A rejected: S1 amplitude-change adds nothing (sat-only AUC 0.500).

## Architecture: static susceptibility + dynamic forecast (not RF + modalities)

```text
STATIC SUSCEPTIBILITY (terrain/geology/landcover/roads, Task A, existing RF lineage)
DYNAMIC FORECAST (trajectories: rain/soil/seismic/satellite, Task B, NEW LANE)
        \--------------\--------------/
                         v
                   HAZARD STATE -> calibration -> WARNING -> RUNOUT/EXPOSURE -> DECISION
```

Exposure stays downstream. OOD semantics frozen. No geography model zoo.

## VI-0 first (before any sequence model or fusion)

Freeze before building: forecast horizon (one: 24h/72h/7d), temporal sample
construction (location+time -> event-in-horizon), negative ladder (N0 random /
N1 spatial-hard / N2 same-site-temporal / N3 weather-matched / N4 susceptibility-matched
/ N5 chronic-site), leakage rules (feature_timestamp <= prediction time, no post-event
imagery, missing-sat stays missing, OOD never safe, exposure never an input).
Then: temporal engineered features -> RF/XGB baseline -> calibration.
Question: does correct temporal data alone fix M0?

## Ladder (each stage faces held-out warning + lead + burden + calibration + OOD; stop on fail)

- VI-0: temporal tabular baseline. VI-1: sequence model (GRU/TCN/small Transformer).
- VI-2: + SAR coherence/deformation (NOT amplitude — M1-A closed that).
- VI-3: + clear-scene optical. VI-4: full multimodal temporal fusion.
- VI-5: regime-aware routing, only if evidence demands it.

## Data governance

Large temporal training population built separately; 23-event championship stays the
gold anchor; 10 held-out events NEVER used for development (features, thresholds,
selection). 50/50 training balance allowed with weighting; calibration/evaluation
reflect deployment prevalence. PS mapping: rainfall->forcing, soil->state,
satellite->independent evidence, terrain->susceptibility, history->targets+prior,
GIS/roads/alerts/offline->downstream product layers.
