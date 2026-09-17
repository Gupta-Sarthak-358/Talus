# VI-2P-B Justification: analytical Iverson physics branch (FROZEN 2026-09-18)

## Hypothesis H3

Rainfall → pore-pressure → stability trajectories computed from linearized
infiltration physics contain event-relevant information absent from the ML
features, WITHOUT any training, weights, piezometers, or FEM.

## Method (Iverson 2000 linearized response, documented simplifications)

Response function R(t*) = sqrt(t*/π)·exp(−1/t*) − erfc(1/sqrt(t*)), t* = t·D0/H².
Transient head at depth H: convolution of trailing-30d daily IMD pulses
ψ(H,t) = Σᵢ (Iᵢ/Kz)·H·[R(t₁*) − R(t₀*)] over each pulse interval, plus steady
background (30d-mean intensity × 0.5·H), capped ψ ∈ [0, H].
Infinite-slope FoS = [c' + (γH − ψγw)·cos²β·tanφ'] / [γH·sinβ·cosβ].
Simplifications (not hidden): daily pulses (not storm hyetographs), 1D vertical,
homogeneous H, no evapotranspiration, steady term is a 0.5-factor heuristic.

## Ensemble = sensitivity, NOT calibration (blocking rule)

- D0 (m²/s): {1e-6, 1e-5, 1e-4, 1e-3} — clay-colluvium to sandy.
- H (m): {1.0, 2.0, 3.0} — shallow-slide range per inventories.
- Kz (m/s): {1e-6, 1e-5, 1e-4}.
- c' (kPa): {0, 2, 5}; φ' (deg): {25, 30, 35}; γ = 18 kN/m³.
- 324 combos per snapshot. Outputs per snapshot: fos_median, fos_min (worst case),
  fos_frac_below_1, fos_drop_7d (median T-7→T). NEVER tuned against held-out;
  ranges are literature-anchored priors, frozen here.

## Leakage & scope

Rain pulses timestamped ≤ snapshot grid-end (V-B convention); T-day excluded.
Slope β from frozen V-B terrain. No fitting, no thresholds, no scores in this step:
features + audit only. Fusion/model is a separate gated experiment.
