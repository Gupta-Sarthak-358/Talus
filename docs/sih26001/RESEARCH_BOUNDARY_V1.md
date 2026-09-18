# TALUS Research Boundary v1 (FROZEN 2026-09-18)

Further model/modality expansion is suspended unless new evidence demonstrates a
specific information gap unaddressable within the validated architecture.

## Proven (production-usable)

1. Susceptibility: global RF + regional calibration + warning policy + OOD guard.
2. Environmental reconstruction: 138 snapshots, provenance/leakage-controlled.
3. Physics state: Iverson FoS ensemble as stability context (never a trigger).
4. Hazard/exposure separation. 5. Trust layer (missing/proxy/OOD/abstention explicit).

## Rejected (closed, with evidence)

Regional specialists (E12) · S1 amplitude fusion (M1-A, sat-AUC 0.500) ·
S1 coherence/phase summaries (VI-2, AUC 0.481, Brier 0.368) · temporal tabular
(VI-0) · GRU sequence (VI-1) · borrowed PINN (VI-2P) · FoS-as-trigger (always).

## Unresolved (stated, not hidden)

Reliable event timing from public data. Not claimed anywhere in the product.

## Frozen evaluation conclusions (939db79 + train/serve audit)

A. Spatial susceptibility discrimination: strong (OOF 0.93). B. Regional structure
(calibration/policy/OOD): defensible. C. Persistent pre-event WATCH 9/23, median
lead 13d. D. WATCH ≥14d: 4/23. E. Persistent ALERT: 3/23, all lead ≤2d; ALERT ≥7d:
0/23 — the binding constraint. F. Monsoon background any-alert 46.7% (WATCH alone
is susceptibility-plus-season, not escalation). G. 7-day imminence unsolved
(AUC 0.53, Brier 0.317). H. Training dynamics unrepresentative of operational
daily weather (rain24h 39.9% below training min; soil semantic mismatch).
Named next target: sustained ALERT-level escalation with lead time at acceptable
monsoon burden. No retraining M0 to chase these numbers.

## Open gates (only these)

VI-2 SAR stays parked (resume probe). Env+Physics fusion ONLY on concrete
product/research need. Everything else requires a new justification document.
