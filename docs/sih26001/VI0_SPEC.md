# VI-0 Training Spec (FROZEN 2026-09-18) — temporal tabular baseline

## Task

`P(landslide within 7 days after prediction timestamp | state at timestamp)`.
7-day horizon chosen to match the M0/M1 imminence construct exactly, so VI-0 is
directly comparable to M0/M1 on the frozen held-out 10. Not tuned: it is the only
horizon that preserves comparability.

## Samples

- Positives: DEV championship events only (13 events, held-out 10 sealed and
  asserted absent). Snapshots with event-in-7d: T-7/T-3/T-1/T = 1 (52 rows).
- N2 same-site temporal negatives: same DEV events' T-30/T-14 = 0 (26 rows).
- N3 weather-matched: monsoon background windows in DEV event years
  (2015/19/20/21/22/24, July +31d, seed-42 30S+30N picks), daily rows y=0.
- N0/N4: off-season background (same years Nov–Feb, seed-43 windows), daily rows y=0.
- N5 chronic-site: automatic (29-Mile DEV rows' T-30/T-14 at the chronic site).
- N1 spatial-hard: NOT in VI-0 (deferred to VI-1 if VI-0 warrants it; stated limit).

## Features (21 numeric + lulc; new encoder — new lane, recorded)

M0's 18 + `rain_3d_mm` (V-B) + `soil_change_7d` + `rain_accel_7d` (= r7(d) − r7(d−7)).
Statics ride nearest-training-row analogue (logged distance, E15 precedent);
seismic from committed USGS catalog < row date; soil v09.2 single-version with
fallback chain + provenance column (not a feature).

## Leakage rules (asserted in build)

1. Every dynamic value timestamp ≤ row date. 2. Background rows: no championship
   event within 7 d after row date at <2 km (asserted). 3. Held-out 10 slide_nos
   absent (asserted). 4. Soil v09.2 only. 5. No post-event imagery anywhere in
   pipeline (satellite not a VI-0 input at all).

## Calibration & evaluation (model fit = next step, not this step)

Isotonic on dev GroupKFold-by-episode OOF (fixes M0's same-OOF optimism).
Evaluate on frozen held-out 10 with M0's exact metrics + burden + OOD + ledger.
