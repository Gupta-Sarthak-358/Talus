# TALUS Assumptions — SIH26001

**Status:** Built — validated 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · Each assumption is falsifiable and owned. `5` validated via `673/73 dated` temporal `metrics.md:32` (year rescue `61` clusters), `2` via `CCI 0.271` `manifest.sample.json:22`, `3` via `USGS n27_e088` `usgs_s234.json:1`, `4` via `6698/1320 OSM` `manifest.training.json:30` — all logged. · **Source:** `docs/SIH26001_RESEARCH.md` §6–§9

## Data

1. **IMD 0.25° gridded rainfall resolves pilot triggers.** 0.25° (~27 km) is
 coarse vs slope scale; hyperlocal cloudbursts will be missed. Mitigation:
 GPM cross-check; tag spatial representativeness in provenance.
2. **ERA5 soil moisture is a usable pore-pressure proxy** at prototype scale
 despite coarse resolution. Tagged `reanalysis-proxy` everywhere it appears.
3. **SRTM 30m resolves pilot terrain features** (slope/TWI/SPI) adequately for
 susceptibility (not for site engineering).
4. **OSM roads/rivers are complete enough** in the pilot extent after a QA
 pass (rural gaps expected; `osm-qa-unverified` tag until checked).
5. **Undated inventory events can seed season-window positives** without
 corrupting the target, provided `event-date:approximate` tags flow to
 missing-evidence and a dated-only sensitivity run is reported. **Validated:** `92→108 dated` after `61`-cluster rescue `build_training_matrix.py:294`, `673/73` dated temporal `done:true` `manifest.training.json:144` `RF test AUC 0.8189`.
6. **Negative sampling at >300 m from known landslides** yields true
 negatives often enough for the prototype (buffer distance freezes in model
 plan; sensitivity on buffer reported). **Built:** `764` negatives `>300m` `seed 42` `manifest.training.json:42`, `prev_rate 0.437` `training_sidecar.csv:1`.

## Modeling

7. **RF + XGBoost transfer from v1's pattern** to NER features with published
 AUC 0.89–0.96 as a realistic bar (not a promise).
8. **Spatial-cluster CV + temporal holdout** will be sufficient validation for
 a prototype (no field deployment claim).
9. **LHASA 2.0 over NER is a fair beat-the-global benchmark** (resolution and
 target differences documented, not hidden).

## Product

10. **4 NER roles cover the PS alert chain** (villager / district officer /
 state manager / rescue). Language matrix starts at English + Hindi +
 pilot language; full NER coverage needs community co-design (deferred).
11. **PWA + SMS-adapter + recorded-fixture demo** satisfies "multilingual +
 offline" at prototype depth; real gateway integration and field testing
 are post-hackathon work.
12. **GSI RLFS complementarity** — assumption that positioning as "the AI/ML
 decision layer GSI asked for" (not a replacement) is the credible and
 cooperative stance.

## Process

13. **Pilot-first, then scale.** One district cluster fully working beats
 eight states thinly mapped. Expansion is a roadmap item, not MVP.
