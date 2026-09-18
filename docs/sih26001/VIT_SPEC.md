# VI-T Temporal Dataset + Baseline — Frozen Spec v1 (2026-09-18)

## Objective

Learn **risk escalation** (susceptible → deteriorating), not susceptibility.
Successor metric to M0 imminence: sustained ALERT-level escalation with lead
time at acceptable monsoon burden.

## Population (frozen split championship_split_v1)

- Development laboratory: 13 dev events. Held-out 10: NEVER touched (no rows,
  no calibration, no threshold, no feature decision).
- Canonical resolution: **daily rows T-60..T** (61 rows/event). Coarser
  aggregations may be derived later; daily is canonical.
- Regions: `bg` = T-60..T-31 (baseline), `pre` = T-30..T-1 (dense), `T` = event
  day (stored, `train_exclude=1`, audit only).

## Targets (frozen)

- PRIMARY: `y14(d) = 1` iff eligible event in `(d, d+14d]`, info ≤ d only.
- SECONDARY: `y7(d)` same with 7d. One model trained for 14d; 7d behavior
  reported from the same frozen model. No separate 7d tuning.
- T row: y14=y7=1, excluded from training.

## Per-row features (ALL timestamp-gated ≤ d; nothing post-d)

| group | features |
|---|---|
| rain (IMD local, REAL) | r24, r3, r7, r30 ending d; d_r24_1d, d_r7_3d, accel=(r7d-r7d_prev7)/7, dryspell (consec days r24<2.5) |
| soil (v09.2 single-version) | trailing-7d mean ending d; d_soil_3d, d_soil_7d; `soil_missing` flag; missing → NaN + MISSING provenance, never FILL |
| physics (Iverson+infinite-slope, frozen params) | fos_med(d), d_fos_7d; ABSTAIN-flat rule carried over |
| seismic (committed USGS JSON) | date-gated counts < d (n50, maxmag50, years-since) |
| static (per site, frozen) | D8 terrain (V-B values), lulc/ndvi/dist analogue (V-B), susceptibility = frozen global-RF RAW prob (deterministic per site) |
| satellite | EXCLUDED from VI-T0 (revisit in VI-T2 only) |

## Negatives (staged, controlled strata, documented counts)

- N0 same-site quiet (mandatory): same site, other-year same-season windows.
- N1 wet-but-safe (mandatory): same site, high-forcing periods, no event.
- N2 spatial hard: nearby susceptible non-event slopes.
- N3 weather-matched: similar rain/soil/season, no event.
- Clean rule: negative row valid iff NO eligible event in `(d, d+14d]`.
- Controlled volumes; separate realistic-prevalence eval population later.

## Training/eval rules

- Grouped by event/trajectory. CV: leave-events-out within dev.
- Calibration: dev only. Model choice/thresholds: dev only.
- VI-D: single frozen run on 10 held-out, compared to M0 scorecard.
