# VI-2 Justification: SAR deformation/coherence evidence (FROZEN 2026-09-18)

## Hypothesis H2

Pre-event SAR interferometric deformation and coherence trajectories contain
information about impending slope failure absent from rainfall, soil, terrain,
seismic, and S1 amplitude-change features (the last closed by M1-A rejection).

## Evidence discipline (blocking)

- Pre-T pairs ONLY: secondary acquisition date ≤ T−1. No post-event pairs, no
  windows extending beyond T. Date-gating asserted in extraction code.
- Source: published LiCSAR products over 4 frozen frames (012A_06241,
  048D_06252, 114A_06191, 114A_06391). No self-processing, no portal requests.
- Same extraction contract for dev and held-out; background contrast from same frames.

## Feature families (small, fixed — no landfill)

1. LOS deformation: recent displacement, cumulative pre-T displacement, trend.
2. Coherence: recent value, change, temporal trend (coherence-as-feature; low
   coherence ≠ deformation — monsoon decorrelation is the null, not the signal).
3. Temporal consistency: usable pre-T pair count, span, acquisition density
   (distinguishes "no evidence" from "insufficient observations"; S1B-gap flagged).
4. Spatial aggregation: patch statistics at 1 km box (coordinate uncertainty),
   footprint class (resolvable Mantam-class vs sub-pixel point), coverage flags.

## Model contract

Frozen M0/VI-1 baseline + narrow SAR branch (compact fusion, same class as M1-A
machinery, retrained under identical protocol). No new architecture, no image
encoder, no regime routing. OOD semantics frozen (SAR never clears OOD).

## Evaluation (identical to M0/VI-0/VI-1)

Frozen held-out 10. WATCH/ALERT/CRITICAL recall, imminence AUC, Brier/ECE, novel
ALERT, burden, OOD. Gate: discrimination AND calibration must improve; recall-only
gains repeat the VI-1 failure and do not pass. M1-A's rejection stands — this tests
a different observable, not the same hypothesis twice.
