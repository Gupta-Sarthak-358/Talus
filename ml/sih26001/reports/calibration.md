# SIH26001 Phase-1 calibration (2026-09-04)

Isotonic fit on RF spatial-OOF predictions (CalibratedClassifierCV-style prefit on OOF; optimism caveat: fit and evaluation share the same OOF — clean check is the temporal holdout, currently skipped for lack of dated positives).

| predictor | Brier | ECE10 |
|---|---|---|
| RF raw OOF | 0.1111 | 0.0688 |
| RF isotonic OOF | 0.1019 | 0.0 |
| naive prevalence | 0.25 | 0.0 |

Confidence = calibrated P(elevated susceptibility) under the prototype season-window target — never 'probability a landslide will occur here tomorrow'.
