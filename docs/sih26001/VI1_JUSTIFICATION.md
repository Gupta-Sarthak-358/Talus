# VI-1 Justification: explicit sequence representation (FROZEN 2026-09-18)

VI-0 negative does not justify adding model complexity merely because the baseline
failed. It specifically rules out the hypothesis that temporal target correction,
time-matched negatives, and low-dimensional trajectory derivatives are sufficient
when represented as independent tabular snapshots. VI-1 therefore tests a narrower
representation hypothesis: whether preserving ordered state history improves
imminence discrimination and calibration.

VI-1 is not approved on the expectation that a sequence model will perform better.
It is approved as the next falsifiable representation experiment.

## Frozen (inherited from VI-0/M0, unchanged)

Population (3798 rows), 7-day horizon, y7d labels, leakage rules, held-out 10 sealed,
metrics/burden/OOD/ledger protocol, decision rules (FROZEN_BANDS on model output,
dev-Youden operating point), no satellite, no threshold tuning on held-out.

## Changed (one thing only)

Row independence -> ordered sequences: dev events as 6-step trajectories,
background windows as 31-step daily trajectories. Minimal architecture:
Linear(D->16) + 1-layer GRU(16) + per-timestep head, BCE with pos_weight,
fixed budget (300 epochs, Adam 1e-3, seed 42). Isotonic on episode-grouped OOF,
refit, freeze, single held-out run.

## Stop rule

If VI-1 does not beat VI-0/M0 on held-out warning + calibration, it is rejected
and the evidence points to richer temporal evidence (SAR coherence/deformation),
not to a more expressive network. No architecture escalation on failure.
