# E-ladder: data-honesty experiments (run 2026-09-17, mnemo venv)

**Question:** is the model learning landslide conditions, or dataset construction?
**Method:** RF200 screening, spatial GroupKFold(8) on KMeans-8 coords (trainer protocol
`scripts/train_sih26001.py:147`, fewer trees — relative deltas are the claim, not absolutes).
FULL reproduces prod (RF200 0.9339 vs prod RF500 0.9345 `ml/sih26001/reports/metrics.md:10`).
**Artifacts:** `scripts/exp_e_ladder.py` (runnable) + `runs/exp_e_ladder.json` (numbers).
Prior run: region specialists lose to global (`scripts/exp_region_specialist.py`,
`runs/region_specialist.json`) — this ladder investigates *why* before adding intelligence.

## Verdict

1. **Leaderboard, not one headline number.** The hard-negative figure below is a
   stress test under one sampling policy (`elev<2500m & road<1km`), not a universal
   baseline and not the deployment distribution either:
   `Easy-background spatial OOF 0.9339 | Hard-negative stress 0.7804 | Temporal 0.8578`.
   Hard negatives (n=381) drop AUC to **0.7804**; easy negatives score 0.9877 —
   ~15 pts of headline AUC are high-Himalaya/far-from-road inflation (BG elev
   3394m vs pos ~1094–1424m; BG road-dist 4947m vs pos 294–394m).
2. **Shortcuts quantified, not fatal.** −elevation −0.005, −road −0.009, −both −0.030
   (0.9036). Model degrades gracefully — real signal remains.
3. **Dynamics > statics.** DYN_ONLY (rain+soil, 0.9169) beats TERRAIN_ONLY (0.8501).
   Memory (7d/30d/soil) +0.018, seismic +0.014, wound +0.000 → **drop
   `recent_disturbance`** (4/2936 nonzero, perm drop 0.0).
4. **Geography:** leave-DARJ-out 0.7117 (train Sikkim-only); within Sikkim,
   EASTSK (demo corridor!) 0.8877 is weakest vs WESTSK 0.9687 / S_N_SK 0.9641.
   Fix southern negatives before any Darjeeling deployment claim.
5. **Time:** temporal global 0.8578 (73 dated test pos, all Sikkim); temporal-north
   0.9159. All ≥2019 dated positives are Sikkim — Darjeeling has **zero** future
   test events. Spatial+temporal Darjeeling evaluation is currently impossible.
6. **Calibration works incl. per-region** (cross-fit isotonic, held-out halves):
   ECE global 0.166→0.040, NORTH 0.166→0.027, SOUTH 0.171→0.045. But SOUTH curve
   rests on ~460 eval points — widen southern data before trusting it.
7. **Thresholds stay candidates** (not validated): DARJ eff-med 527 vs SK 452,
   rain24-med 107 vs 83. Reconcile with `warning_thresholds.json`
   (Darjeeling 390–420 fires *below* the positive median — sensitive by design,
   document which population defines it).
8. **Exposure reorders decisions without touching hazard:** S1 (hazard 89, 0 homes)
   vs S2 (hazard 78, 85 homes) → exposure ranking leads S2. Track 2 confirmed.
9. **Prevalence:** balanced-train p=0.90 ≈ **0.08** field probability at 1% base rate.
   Never present raw outputs as real-world probabilities.

## E2/E6/E7 ablation table (spatial OOF, n=2936)

| Set | Dropped | AUC | PR-AUC | Brier | acc |
|---|---|---|---|---|---|
| FULL | — | 0.9339 | 0.9236 | 0.1178 | 0.830 |
| NO_ELEV | elevation | 0.9290 | 0.9249 | 0.1206 | 0.824 |
| NO_ROAD | distance_to_road | 0.9245 | 0.9194 | 0.1275 | 0.812 |
| NO_BOTH | elev+road | 0.9036 | 0.9094 | 0.1428 | 0.806 |
| TERRAIN_ONLY | dynamics+seismic+road+wound | 0.8501 | 0.7985 | 0.1475 | 0.790 |
| DYN_ONLY | all statics+seismic+wound (+lulc) | 0.9169 | 0.9243 | 0.1449 | 0.805 |
| TERRAIN_DYN | road+seismic+wound | 0.9124 | 0.9029 | 0.1308 | 0.795 |
| NO_MEMORY | rain7+rain30+soil | 0.9164 | 0.9010 | 0.1216 | 0.811 |
| NO_SEISMIC | 3 seismic cols | 0.9202 | 0.9057 | 0.1206 | 0.826 |
| NO_WOUND | recent_disturbance | 0.9332 | 0.9239 | 0.1179 | 0.824 |

## E1 negatives (FULL OOF sliced)

| Pool | AUC | n | pos_rate |
|---|---|---|---|
| Hard (BG elev<2500 & road<1km, 381) vs all pos | **0.7804** | 1849 | 0.794 |
| Easy (remaining BG, 1087) vs all pos | 0.9877 | 2555 | 0.575 |

Action: region-balanced + hard-negative resampling (Sikkim/Darjeeling comparable
counts, positives matched on elev/slope/road-dist, ≥300m separation), then re-run.

## E3 leave-district-out (BG → nearest positive group, 1-NN haversine)

| Held out | n_test / pos | AUC | Brier |
|---|---|---|---|
| DARJ (704 pos) | 916 / 704 | 0.7117 | 0.3516 |
| EASTSK (224) | 443 / 224 | 0.8877 | 0.1401 |
| WESTSK (224) | 481 / 224 | 0.9687 | 0.0844 |
| S_N_SK (316) | 1096 / 316 | 0.9641 | 0.0764 |

## E4 temporal + leakage audit

- Temporal global (≤2018 train → ≥2019 test, seeded BG split): AUC 0.8578, PR-AUC
  0.2531 (9% prevalence — report PR alongside ROC), Brier 0.0962.
- Temporal north-only: AUC 0.9159 (same 73 Sikkim test positives; north-trained
  beats global-trained here — noisy n=73, hypothesis not conclusion).
- `darj_dated_ge2019_pos = 0` — no Darjeeling future test exists.
- Tag vocab clean: rain 1468 background-peak / 740 event-peak / 724 climatology /
  4 exact-date; soil 1426 / 729 / 777 fallback / 4 exact-date.
- Known limitation: year-peak rows use that-year JJAS peak (may include post-event
  days for early-season slides); month-anchored tier TODO (manifest). Builder must
  fail on `feature_timestamp > event_timestamp` (E11).

## E5 rainfall sources

No local IMERG/CHIRPS/ERA5-Land rasters — multi-source comparison pending download.
Slice-by-source skipped honestly: `rain_source` perfectly separates label by
construction (background-peak ⟺ negative, event-peak/climatology ⟺ positive) and
must never enter X.

## E8 wound

4/2936 nonzero; road-event subset (368 pos <200m) OOF AUC 0.9467. No measurable
wound signal — drop from X; rebuild as disturbance *score* and re-test on
road-event recall (not global AUC).

## E9 exposure ranking (hazard, buildings)

- By hazard: S1(89,0) → S2(78,85) → S3(66,1) → S4(52,18)
- By exposure: S2(78,85) → S4(52,18) → S3(66,1) → S1(89,0)
- `rank_changed=true`. Method: screening runout (`runout_exposure.json`), not a
  debris-flow simulator; dense-town undercount stated.

## E10 calibration (cross-fit isotonic, even-fit/odd-eval)

| Scope | raw Brier/ECE | cal Brier/ECE | n_eval |
|---|---|---|---|
| Global | 0.1509/0.1661 | 0.1126/0.0397 | 1468 |
| NORTH | 0.1361/0.1664 | 0.0826/0.0267 | 1008 |
| SOUTH | 0.1856/0.1711 | 0.1606/0.0445 | 460 |

Protocol going forward: train → held-out geo/temporal calibration set →
untouched test; never fit isotonic on training OOF and declare victory
(trainer same-OOF caveat already logged).

## E11 championship (protocol + pre-fix baseline to beat AFTER E1 fix)

Train global + validated features, balanced. Test: later events + held-out areas +
representative negatives. Report ROC/PR-AUC, Brier, calibration, critical recall,
lead time, false alarms, misses, homes/roads captured. Pre-fix baseline:
spatial AUC 0.9339, temporal 0.8578, hard-neg 0.7804.

## E1.5a negative difficulty ladder (frozen FULL OOF, `scripts/exp_e15_ladder.py`)

Same model, increasingly honest negatives — the shortcut curve:

| Tier | Negatives | n_bg | AUC | bg elev_med | bg road_med |
|---|---|---|---|---|---|
| N0 random | all BG | 1468 | 0.9339 | 3640m | 2403m |
| N1 low-elev | elev<2500 | 532 | 0.8212 | 1456m | 558m |
| N2 near-road | road<1km | 491 | 0.8268 | 1489m | 428m |
| N3 elev+road | both | 381 | 0.7804 | 1311m | 400m |
| N4 +slope | +slope in pos p10–p90 | 286 | 0.7811 | 1324m | 417m |
| N5 region-matched | N4 within region, pooled | 286 | 0.7811 | — | — |
| N5 SOUTH (704 pos / 117 bg) | — | 117 | 0.7176 | — | — |
| N5 NORTH (764 pos / 169 bg) | — | 169 | 0.8376 | — | — |

Slope adds nothing beyond elev+road (N3≈N4) — match on elev+road+region, keep slope
as a check. Separation audit: BG min 300.9m from positives, 100% ≥300m (Gate A
construction holds). N4 LULC is 280/286 FOREST vs positives ~85% FOREST — LULC
matching deferred to extraction (prefer similar class where available).

Match-feasibility (nearest BG in standardized elev/slope/road space):
SOUTH 753 pos / 216 BG → greedy 1:1 coverage **0.287**, nn_med 0.333;
NORTH 715 / 1252 → coverage **1.0**, nn_med 0.310.
Verdict: NORTH matchable from pool; SOUTH needs ~500+ new negatives.

## E1.5b sampler (done) → extraction (next)

`scripts/sample_e15_negatives.py` (system python, rasterio) wrote **1600 southern
candidates** (`runs/e15_candidates.json/csv`): bbox lat 27.00–27.20 / lon
88.06–88.90, all ≥300m from positives (median sep 851m, Gate-A asserted in-script),
elev 800–2500m (med 1478 vs DARJ-pos med 1094), slope 5–60°.
Pending at extraction (reuse map): road<1km filter + distances via
`scripts/extract_s1_osm.py` Overpass-bulk path; rain/soil via
`event_rain_upgrade.py` / `event_soil_upgrade.py` year-peak design;
TWI/SPI/drain via `extract_usgs.py` + `extract_catchment.py`;
NDVI/LULC via `extract_s1_sentinel2.py` / `extract_s234_lulc.py` vsicurl paths;
seismic via `event_seismic_upgrade.py` + `usgs_quakes.json`; labels=0 with the
≥300m guarantee carried in the candidate file.
Then: region-balanced splits (Sikkim N/N, Darjeeling N/N), disjoint train/eval
negatives, Gate B (global vs specialists, same corrected splits) + Gate C
(above-chance on matched negatives, ablation without elev/road dominance).

## E1.5b extraction + Gates B/C (run 2026-09-17)

`scripts/extract_e15_negatives.py` (system python) extracted **1598** candidates with
all 10 rules asserted in code (re-separation ≥300m min 300.2m, schema-identical incl.
seismic cols, `recent_disturbance`=0 const, no source tags in X, prod files untouched).
Stage log: 2 edge pixels dropped (Horn margin, logged); DEM void-fill; 18 hydro blocks;
OSM from committed bulk cache (8087 roads); optical 1407×45RXL + 191×45RXK, 76 NDVI
imputed (73 outside-scene + 3 cloud, median+logged); rain 36 year-pools (seed 4215
stream, tier-2 method); soil fallback chain cell 0 / spatial 760 / global 74.
Road<1km filter → **1114 survivors** (`data/sih26001/processed/e15_negatives.csv` +
`e15_sidecar.csv`; corrected pool n=4050, pos 1468).

Corrected-pool results (`scripts/gates_e15.py`, `runs/gates_e15.json`):

| Check | Result |
|---|---|
| B global pooled | AUC 0.8950, PR 0.8446, Brier 0.1359 |
| B ensemble pooled | 0.8674 — fragmentation still loses pooled |
| B SOUTH specialist / global-sliced | **0.7972 / 0.7719** (+0.025 specialist) |
| B NORTH specialist / global-sliced | 0.9133 / **0.9601** (−0.047 specialist) |
| C matched pooled (1468 pairs) | 0.8478, PR 0.8635 |
| C SOUTH matched (704 pairs, SMD road −0.018→0.046, elev −0.541→−0.298) | 0.7561 |
| C NORTH matched (764 pairs, SMD elev −1.439→−0.572, road −0.961→−0.657) | 0.9212 |
| C NO_BOTH / NO_MEMORY / NO_SEISMIC | 0.8661 / 0.8627 / 0.8658 (each ≈−0.03) |
| Temporal corrected (73 dated, 5.4% prev) | AUC 0.8092, PR 0.1489, sens50 0.23 |
| sens50 SOUTH / NORTH (corrected global) | 0.365 / 0.709 — southern recall demands regional thresholds |

Gate verdicts: **A PASS** (assertions green). **C PASS** (0.848 matched pooled,
graceful ablations, PR reported). **B MIXED → Case C** (at the time): south specialist
marginally beats global-sliced (+0.025, ~2 SE, screening), north specialist loses
clearly (−0.047). *Superseded by E12 below, which confirmed the south branch across
5 seeds × RF500/XGB and froze the architecture.*
Specialists collapse on acc-type metrics (sens50 0.32–0.38) — prevalence-shift
miscalibration, another vote for decision-layer localisation. NORTH residual road
SMD −0.657: northern near-road negatives still wanted. 0.7176 kept as history.

## E12 South Specialist Confirmation (run 2026-09-17, DECISION)

Frozen E1.5b pool (n=4050). M0 global / M1 south / M2 cross-fit-calibrated, RF500 +
XGB400 (prod parity), 5 spatial seeds (KMeans-2 south halves), held-out hard
negatives, PR-AUC primary (`scripts/e12_south_confirmation.py`, `runs/e12.json`):

| Δ (specialist − global) | mean | median | 95% CI | all 5 seeds + |
|---|---|---|---|---|
| RF PR-AUC / ROC-AUC | +0.041 / +0.047 | +0.041 / +0.043 | ±0.023 / ±0.012 | yes / yes |
| RF hard PR-AUC / ROC-AUC | +0.035 / +0.030 | +0.036 / +0.027 | ±0.024 / ±0.012 | yes / yes |
| XGB PR-AUC / ROC-AUC | +0.044 / +0.034 | +0.042 / +0.034 | ±0.024 / ±0.010 | yes / yes |
| XGB hard PR-AUC | +0.034 | +0.031 | ±0.024 | yes |
| RF sens50 (all / hard) | +0.142 / +0.147 | — | ±0.049 / ±0.051 | yes |
| XGB sens50 (all / hard) | +0.168 / +0.173 | — | ±0.028 / ±0.027 | yes |
| XGB Brier (all / hard) | +0.018 / +0.014 | — | ±0.006 / ±0.006 | yes |
| RF Brier | −0.002 / −0.006 | CI crosses 0 | noise | no |

M2: specialist+cal beats global+cal on Brier (0.156 vs 0.177) and ECE
(0.047 vs 0.103) — the edge is predictive, not just calibration.
Audit: global drivers = elevation / seismic_n50_rate / distance_to_road (perm +
SHAP agree); south drivers = seismic_dist_km / elevation / ndvi (+seismic_years_since
in SHAP). Different relationships = model behavior, not physics proof.

**DECISION: adopt South specialist branch + global backbone** (north stays global:
0.960 vs 0.913 settled). No universal regional-model collection, no ensembles.
Next: E1.5c north top-up → calibrate surviving architecture → candidate bands →
replay. Calibration decorates nothing until then.

## E1.5c north top-up (cleanup, NOT a debate rerun)

800 north candidates → 800 extracted (all 45RXL, 0 NDVI imputes) → **540 road<1km
survivors** (`e15c_negatives.csv`, seed 4217, BG-20000+, same 10 rules).
Pool SMD north: road −0.961→−0.791, elev −1.439→−1.087. Greedy 1:1 north matching
now reaches full 764-pair coverage with matched SMDs elev −0.125 / road −0.039
(slope 0.518, diagnostic only). North matched-eval AUC **0.9219** (was 0.9212):
stable, as intended — the cleanup made the evaluation harder to fool, not prettier.
No specialists retrained here by design.

## FROZEN predictive architecture (E12 decision)

Shared global backbone (north/general) + South specialist branch (Darjeeling/south).
No north specialist, no ensembles, no model zoo. The retired hypothesis
("one global scorer + only local thresholds") is superseded by evidence:
regional specialization earned its branch across 5 seeds × 2 families.
Production family (RF vs XGB) is a separate later decision. Next: E13
calibration of the surviving architecture (regional, held-out) → E14 candidate
warning bands vs recall/false-alarms/lead-time → E15 temporal replay on the
frozen inference pipeline.

## Implementation order (frozen)

1. E1.5 matched negatives + gates A/B/C → 2. re-run ladder+specialists on corrected
   splits → 3. global calibration → 4. regional calibration test → 5. candidate bands →
6. replay on calibrated output. No new features until 2 clears.
   Gates: **A** data integrity (no future/label/source-proxy leakage) ·
   **B** generalisation (global vs specialists on same corrected splits) ·
   **C** useful signal (above chance on matched negatives, not elev/road-driven).
