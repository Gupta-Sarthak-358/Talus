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

## FROZEN predictive architecture (E12 decision, E14 collapse applied)

E12 adopted a South specialist branch; E14 tested it operationally and the
pre-registered rule fired COLLAPSE (1/5 RF, 2/5 XGB, trigger-happy FAR).
Final: **one global scorer + regional calibration + regional warning policy**.
No specialists, no ensembles, no model zoo. The E12 predictive edge is preserved
in the record as protocol-sensitive evidence, not as architecture. Production
family (RF vs XGB) remains a separate later decision. Next: E15 temporal replay
on the frozen inference pipeline, then championship evaluation.

## E13 strict regional calibration (run 2026-09-17)

`scripts/e13_calibration.py`, `runs/e13.json`. Per branch, 5 seeds, 60/20/20
spatial cluster splits (train/calib/test); isotonic on out-of-sample calib
predictions; untouched test; reliability bins saved. Pool n=4590 (E1.5b+E1.5c).

Mean over seeds, south test (RF): raw Brier 0.234/0.224 (G/S) → cal 0.163/0.169;
ECE 0.249/0.227 → 0.071/0.075. North: Brier 0.184 → 0.170/0.153, ECE 0.181 → 0.147.
XGB same pattern. **Probability validity: YES** — calibration transforms
uninterpretable scores into usable probabilities on both branches.
PR-AUC dips slightly post-isotonic (step artifacts, expected); sens50 jumps
(0.40–0.53 → 0.84–0.93) because 0.5 means something different after calibration —
raw sens50 is not an operational metric, E14 sets thresholds on calibrated outputs.

**Tension recorded honestly:** under E13's 60/20/20 protocol the specialist edge
does NOT replicate — RF south raw PR global 0.8616 vs specialist 0.8586 (tie),
XGB favors global (0.8863 vs 0.8664); post-calibration all four south configs
converge (Brier 0.16–0.18, ECE 0.05–0.10). E13 trains global on less data and
tests smaller cluster sets than E12's complementary-half protocol, so this
tempers rather than overturns the freeze — but the branch advantage is
protocol-sensitive, and the freeze now rests on E12 explicitly, not on consensus
across protocols. Regional separation stands regardless: north and south need
different calibrators (never one global curve).

## E14 warning policy (run 2026-09-17 — COLLAPSE verdict)

`scripts/e14_warning_policy.py`, `runs/e14.json`. Operating thresholds transferred
from calib at recall≥0.80, applied fixed to test (5 seeds, RF500+XGB400).

Applied rule: RF wins 1/5 (need ≥4), XGB agree 2/5 (need ≥3 in direction),
road never worse. **Verdict: COLLAPSE to global + regional calibration.**
The specialist is more trigger-happy — higher recall but substantially higher FAR
at transferred operating points (e.g. seed 42 RF: S recall 0.964/FAR 0.566 vs G
0.878/0.368). Matched-recall diagnostic (min FAR at recall≥0.90): RF specialist
wins 2/5 seeds, XGB 0/5. No consistent operational edge in either family.

What survives: regional calibration (E13, independent evidence), regional warning
policy (north operates thr 0.15–0.25 vs south 0.45–0.60 — different mappings,
not different models), road-event recall parity. The E12 predictive edge did not
survive contact with calibrated operating points — recorded, not hidden.

## E14 warning policy (PRE-REGISTERED — protocol; results above)

Question: does the South specialist buy anything *operationally* after calibration?
Compare on South test: Global+South-cal vs Specialist+South-cal across candidate
policies `NORMAL→WATCH→ALERT→CRITICAL` on calibrated probability.

Protocol (`scripts/e14_warning_policy.py`, 5 seeds, frozen E1.5b+E1.5c pool):
60/20/20 spatial cluster splits per region (same construction as E13); operating
threshold = smallest threshold with calib-positive recall ≥0.80, transferred
fixed to test; plus full 0.05–0.95 sweep curves on test (diagnostic only).
Lead-time/seasonal-burden/transitions are NOT measurable cross-sectionally —
they belong to E15 (`replay_series.json`: causality/cases/ledger present).

Metrics per policy: event recall, missed count, false-alarm rate (+ per-1000-slope
burden), precision, road-event recall (dist<200m), alert-days proxy (fraction
flagged). North reported for completeness (global only, no north specialist exists).

DECISION RULE (locked before running): keep the South specialist branch iff, at
calib-transferred R80 operating points on South test, its false-alarm rate is
lower than Global+South-cal by ≥0.02 absolute in ≥4/5 seeds (RF500 primary; XGB400
must agree in direction), with no worse road-event recall. Otherwise collapse to
global + regional calibration. No post-hoc metric shopping.

## E15 frozen-system replay + incident interrogation (run 2026-09-17)

`scripts/e15_replay_audit.py` (`runs/e15.json`) + `scripts/e15_incident_replay.py`
(`runs/e15_incidents.json`). Required rebuild first: the committed replay was
scored with Sept-15 weights, current prod weights are the Sept-17 retrain —
replaying stale scores would test a dead system. Rebuilt with current weights
(plus wound-schema fix: `recent_disturbance=0` const, E8).

Ledger, independently recomputed (5/5 match committed):

| Case | first High (lead) | first Critical | burden (hot/31d) |
|---|---|---|---|
| mangan-jun2024 | Jun-10 (3d) | Jun-11 | 4/31 |
| dipudara-aug2024 | Jul-21 (30d) | — | 19/31, 1 early episode (precursor slides = life-saving evacuation, not false) |
| lumsay-jun2022 | Jun-03 (27d) | Jun-08 | 28/31, month-fuzzy date |
| sichey-jun2021 | Jun-01 (7d) | — | 6/31, date-fuzzy ±days |
| nh10-oct2022 | Sep-13 (26d) | Sep-14 | 27/31 |

Leakage audit: rain 3/3 exact vs IMD archive, trailing-only ✓; NDVI all 5 scenes
pre-event ✓; soil daily ✓ for 2024 cases but **anachronistic quasi-static
(2024 window) for 2021/22 cases** — impact bounded (soil perm ~0.0001), fix is
backfilling v09.2 dailies; **analogues 5/5 were training positives (two at 0m)**
→ lead times are optimistic upper bounds, not generalisation evidence;
**seismic ref-after-event 1/5** (sichey T0110 ref 2025 > 2021 event).
Exposure join: 2/5 covered (sichey→S2 runout, 85 homes at 185m — the E9 story
live; lumsay→S3, 1 home) — runout spans Gangtok demo slopes only; 3/5 replay
sites have no exposure coverage yet.
Burden warning: lumsay 28/31 and nh10 27/31 hot days is the enthusiastic-widget
failure mode in miniature — monsoon-season susceptibility stays hot, so only the
exposure/decision layer (E9/E14) can prevent warning fatigue. Off-season burden
unmeasured (all windows are pre-event).

Verdict: the frozen system moves before events (5/5 flagged, multi-day leads,
ledger verified, rain exact) but E15 does NOT validate deployment. Championship
needs: held-out analogues, backfilled soil, off-season burden windows, dated
Darjeeling events. Replay machinery itself is now verified and current-weight.

### E15 incident tiers (frozen pipeline: prod RF + regional iso + regime-matched policy)

- Tier-1 (5 dated cases, daily T−30..T, inputs ≤T): first ALERT mangan 3d /
  dipudara 30d / lumsay 27d / sichey 7d / nh10 26d before events; trajectories +
  cards in `runs/e15_incidents.json`. Matches audit ledger exactly.
- Tier-2 (746 dated positives, event-year points, IN-SAMPLE): recall WATCH 0.916 /
  ALERT 0.787 / CRITICAL 0.685; south ALERT 0.836 vs north 0.566; road-event
  recall recorded per region. Ceiling metric, not generalisation.
- Tier-B (60 background × 31 monsoon days): 28/60 windows any-alert, mean 5.8
  hot-days — the measured false-warning burden both E14 and the dashboard must
  carry openly.

KEY FINDING — regime mismatch: policy cutoffs derived on peak-anchored pool rows
collapse on daily-trailing rows (ALERT 0.9/0.95, Tier-1 nearly silent), because
the training target (season-peak proxy) and the operating regime (daily trailing)
live on different score scales. Thresholds do not transfer across regimes:
E14 policy governs matrix-regime decisions; daily replay keeps the band system
until a daily-resolved calibration exists. Recorded as a constraint, not a bugfix.

## E15 historical incident replay (PRE-REGISTERED — not yet run)

Frozen pipeline under interrogation (no training, no threshold tuning here):
prod RF weights (`sih26001_rf_v1.joblib`) + E13-protocol regional isotonic refit
(deterministic seed 42, corrected-pool calib partitions) + policy cutoffs derived
once on calib: WATCH = calib recall≥0.95, ALERT = R80 operating point,
CRITICAL = calib precision≥0.80 (fallback 0.80 if unachievable — recorded).

- Tier-1 (daily T−30..T): 5 dated cases (2 fuzzy-flagged). Full trajectories +
  incident cards. Inputs strictly ≤T (trailing IMD, same/prior-day soil, pre-event
  S2, static analogue; 2021/22 soil anachronism carried from audit).
- Tier-2 (all 746 dated positives, 638 Darjeeling): event-year point replay,
  IN-SAMPLE labeled (training rows). Recall-at-state only, never generalisation.
- Tier-B (background burden): 60 BG windows (30 S incl. new negatives, 30 N) ×
  31 monsoon days, same pipeline. False-warning burden + hot-day fractions.

Stratify: N/S, road<200m, monsoon/non-monsoon. Outputs: per-incident trajectories,
first WATCH/ALERT/CRITICAL + leads, misses, burden, exposure-at-warning,
`runs/e15_incidents.json` (+ calibrator arrays for dashboard).
E15 carries no architecture gate — verdict is the ledger. Verdict criteria:
system survives iff Tier-1 exact-date cases all reach ≥ALERT before T with
documented leads AND Tier-B burden stays discussable (hot-day frac reported,
not hidden); else the failure mode (misses vs burden) names the next work.

## E16 daily-regime calibration + held-out census (PRE-REGISTERED — not yet run)

Census (`runs/e16_census.json`): 818 held-out positives, ALL West Bengal plains
(Darjeeling 509 + Jalpaiguri 309, lat 26.69–27.0), 734 dated 1965–2016, zero in
DEM tile, all IMD years present. Different geomorphic regime (Terai/plains) —
usable only as flagged out-of-regime test, never as hills validation.

Protocol (`scripts/e16_daily_calibration.py`): daily population = exact-date event
days (label 1, n reported, fuzzy excluded from fit) + Tier-B background days
(label 0); fit isotonic AND Platt (logistic — pre-registered as the stable
candidate at tiny-n); leave-one-event-out comparison; Tier-1 redo with cleaned
inputs (soil backfill via v09.2 dailies where files exist, seismic ref=event year);
Tier-B redo; E16c pilot = 10 northernmost held-out events, per-feature pedigree
flags (REAL/PROXY/imputed), event-year-point replay, regime flag.
E16 carries no architecture gate. Success = daily-calibrated Tier-1 reaches
≥ALERT with sane (non-degenerate) thresholds + burden re-measured + held-out
pilot runs with pedigree recorded.

## E16 daily-regime calibration + held-out census (run 2026-09-17)

Census (`runs/e16_census.json`): 818 held-out positives, ALL West Bengal plains
(Darjeeling 509 + Jalpaiguri 309), 734 dated 1965–2016, zero in DEM tile —
different regime, flagged out-of-regime test only.

Daily population: 4 exact-date event days + 1860 background days.
LOO-event: iso Brier 0.0002 vs raw 0.0765 — vacuous at n=4 (predict-zero nearly
wins at 0.2% prevalence); Platt collapses flat (max 0.008). **Daily-regime
calibration is DATA-blocked, not method-blocked**: iso overfits to steps
(Tier-1 event days 1.0/1.0/0.03/0.0/0.03 — misses 3/5 incl. exact nh10),
Platt to base rate. Tier-B redo under daily-iso (0/60) is over-conservatism,
not good news. Required: exact-date mining to ~30–50 positives; until then NO
daily-calibrated policy — daily replay keeps bands, E14 matrix policy stands.
Methodology itself works (soil backfill via v09.2 dailies, seismic ref=event-year
fix, LOO machinery ready). Raw Tier-1 peaks 0.69–0.91 confirm ranking survives;
only the probability mapping is missing.

E16c pilot (`runs/e16c.json`): 10 northernmost held-out events, dynamic-only
(IMD/soil/seismic local; terrain/optical/OSM queued with tile spec): eff median
725.7 vs DARJ 527, 10/10 above — plausibility signal with coarse-cell caveat
(neighbors share 0.25° cells: ~5 independent cell-years).

### E16c full held-out MODEL replay — terrain the model never trained on (run 2026-09-17)

`scripts/e16c_extract.py` + `scripts/e16c_score.py`, `runs/e16c_features.csv` +
`runs/e16c_full.json`. All 10 got REAL full rows: Copernicus GLO-30 (N26E088+N26E089)
elev/slope + grafted repo-hydro TWI/SPI/drain, IMD event-year peaks, v09.2 soil
windows, WC LULC, per-point Overpass geometry distances (10/10, cached+recorded),
seismic ref=event year, NDVI median-impute + flag. Result: **0/10 band≥High, 1/10
E14-op** vs Tier-2 south 0.836 — mechanism diagnosed: raw probs 0.49–0.83 (median
~0.64) vs train-pos 0.97, i.e. the model discounts plains terrain below its
experience (several points 226–382m vs train-pos p10=447; 4/10 road distances below
train-pos p1); the south isotonic then crushes mid-raw to ~0 because raw 0.5–0.8
is negative territory in its calibration population — calibrated outputs are
overconfident-LOW out-of-regime. Boundary drawn: hills model does not cover
Terai/plains physics; OOD inputs need an OOD flag or calibration floor, not silent
zeros. The 818-event census stands as the population for that future work.

## E16 wrap: Track A audit + regime-tagged warnings (run 2026-09-17)

Track A (`runs/trackA_date_audit.json`): 2181 year-or-undated + 57 month-year PDF
+ 36 year-only + 12 undated + 4 exact news-anchored. Gap to 30 exact: 26 events
needing news/Govt/DHM cross-ref. Inclusion filter locked: exact date + supported
geography + feature coverage + pre-event daily inputs; fuzzy stays replay-only.
818-event census reframed: out-of-regime geographic transfer population (WB plains),
never hills validation.

E16c full replay stands as the first out-of-regime transfer test (0/10 with
diagnosed mechanism, not a silent miss).

Trust feature shipped: `GET /api/warning/state` states now carry `confidence`,
`probability_status: calibrated`, `probability_regime: matrix`, `scoring`
(live-rf/fixture) and a `regime_note` stating daily-trailing scores are
ranking-only pending exact-date events (`backend/app/main.py:warning_state`,
19 tests green). The system now declares which numbers are probabilities.

Hierarchy going forward: E1–E10 data/leakage → E1.5 sampling correction → E12
branch test → E13 regional calibration → E14 policy collapse → E15 replay
machinery → E16 daily-calibration feasibility + transfer test → championship
(exact-date mining → held-out analogues → off-season burden → dated Darjeeling).
No new model architectures: RF/XGB/ensembles/neural would be procrastination.

## E16d OOD boundary + shipped guardrail (run 2026-09-17)

`scripts/e16d_ood_boundary.py`, `runs/e16d.json`,
`data/sih26001/evidence/feature_support.json`, `backend/app/support.py`,
`backend/tests/test_ood.py` (8 tests). Distances vs p_raw: kNN5 Spearman −0.61,
Mahalanobis −0.64 — farther from support scores lower, measured.
Rule process: pre-registered ≥2-any-feature FAILED validation (Tier-1 analogues
flagged 0.40 — monsoon rain extremes must never trigger abstention) and was
rejected in favor of terrain-only OOB≥1: heldout 0.60 / tier1 0.00 / trainpos
0.07. All 6 OOD-driven silent-low held-out rows fire; remaining 4 are in-support
model misses (honest false negatives, same class as any other).
Shipped invariant: any terrain-OOB row gets `ood:true` + `probability_status:
uncalibrated-ood` + reasons (`score_row`, warning states); warnings never
suppressed, values never invented, S1-style extremes get a truthful caveat.

System invariant: **calibration must never silently convert OOD outputs into
confident low-risk probabilities.** Dashboard contract: `RISK: low calibrated
probability` only in-support; else `MODEL SUPPORT: outside validated regime /
CONFIDENCE: limited / REASON: <features>` — "I don't know" is a valid output.
818 WB-plains census formalized as the **out-of-regime transfer benchmark**
(population, not validation). Championship claims split: (1) in-domain detection,
(2) daily calibration NOT supported (n=4), (3) geographic transfer FAILS on
tested plains (mechanism: terrain discount + calibrator burial, both recorded).

## Phase IV: championship tracks (opened 2026-09-17)

Shipped this run: Trust Ledger v2 (`GET /api/trust/ledger`, 6 rows incl. OOD
contrast row; `TrustLedgerCard` renders Warning|Lead|Exposure|Support|Result with
legacy fallback; backend test `test_trust_ledger.py`), Sichey incident bundle
(`incident_sichey.json`: trajectory + 85-home exposure + decision), OOD badge in
`WarningStateCard` (frontend build green), Track-A tracker (81 rows: 78 month-hint
+ 3 mined-exact — 2015-07-01 Darjeeling disaster, 2015-07-09 NH10, 2021-10-20 NH10;
exact-date pool now 7). Mining pilot proved feasible (convergent multi-source dates).
Track-A target: 30 exact (gap 23). Note: mined events may sit near training points
geographically — their contribution is new exact DATES, which is what daily
calibration lacks.

Four scorecards for the final page (not one leaderboard): (1) predictive validity
(spatial/hard/temporal AUC, Brier, ECE); (2) historical warning performance
(recall, leads, misses); (3) warning burden (false alerts, hot days, seasonal split);
(4) trust/domain validity (OOD detection, calibration coverage, support flags,
freshness). Frozen: no new architectures, no plains model to rescue 10 cases, no
threshold tuning on replay cases, Tier-2/in-sample never presented as validation,
0/10 never hidden.

## Phase IV opened (2026-09-17): evidence before intelligence

Track A (`trackA_candidates.csv`, 90 rows; `championship_events_v1.csv` DRAFT, 7 rows,
UNFROZEN until 30): 7 exact (4 seed + 3 mined: 2015-07-01
Darjeeling 36–38 dead multi-source, 2015-07-09 NH10, 2021-10-20 NH10 multi-source),
Mining pass 1 ingested (`trackA_mining1.py`): DipuDara-20240820 was ALREADY pooled
(peer-reviewed paper = corroboration, not a new sample); Mangan-20240613 episode-tagged
as ONE sample for its multi-slide cluster; Majwa-20240610 duplicate-guarded;
Meghalaya/Assam trio (2022-06-09/14/17, dual-source exact) auto-failed contam_geo and sit
in a transfer cohort, not the championship; Pubung-20190708 provisional at the domain
edge (0.01deg S of box). Eligibility computed False/True by rule: pool stays 7, honestly.
Mining pass 2 (`trackA_mining2.py`): pool 7 -> 10 eligible (+Rongey-20220628 dual,
+Yumthang-20220831 triple Army-rescue, +20Mile-20220901 triple; gap 20).
Pubung source-leg passed (6 outlets + IMD 172mm/24h) but still edge-provisional.
Jun-17-2022 HT Friday-5-dead identified as aggregate re-report of Jun-15 Lingzya/17th-Mile
deaths (Telegraph Jun 16) and duplicate-guarded; Lingzya ravine itself a road accident,
not a slide; Chungthang-20231004 rejected (GLOF cascade, trigger 5200m outside regime).
29-Mile-20210906 dual-source but point unresolved (mile-marker vs 60km-from-Rangpo conflict).
Chronic-site repeats now visible (29-Mile Sep-2021 + Oct-2021; 20-Mile Sep-2022 + Oct-2022):
distinct dates, non-overlapping T-30 windows, legitimate separate samples.
Also fixed a bool-vs-string filter bug that undercounted eligible 10 as 4.
Mining pass 2b (`trackA_mining3.py`): pool 10 -> 13 eligible (+Pubung-20190708 on Chataidhura
GPS 27.0044, edge-flagged with 0.5km margin documented, NOT silently promoted; +17Mile-20220615
quad-source; +BirikDara-20220802 dual with timed detail; gap 17). Pooled Oct-2021 event gains
peer-reviewed scar study (Das et al Curr Sci 2022: Birik Dara 10pm Oct-20-2021, same chronic site
as Aug-2022 recurrence). 29-Mile held provisional (localization search rate-limited).
event_type metadata added (fatal / non-fatal / road-block / high-exposure / multi-slide).
Mining pass 3 (`trackA_mining4.py`, 3 of 6 windows answered, 3 rate-limited): pool 13 -> 14
(+Pathing/Gaguney-20221124: PTI rescue + field GPS 27.2955,88.3924 + peer paper, chronic-slide
ONE-sample at Nov-24 evacuation pulse; gap 16). SeesaGolai-20210601 provisional (single +
subsidence-mechanism caveat); Sichey-20210609 provisional (single + internal time conflict);
BhaluKhola tunnel-face collapse REJECTED (construction accident, with Lingzya precedent).
Jul-2020 / May-2020-North / Sep-2021-Gangtok windows deferred on 429s, not closed.
Mining pass 4 (`trackA_mining5.py`, NER-wide search, support-constrained classification):
championship UNCHANGED at 14; transfer-eligible 3 -> 6 (+Tigdo-20200710 +ModiRijo-20200710,
same Itanagar Friday episode two points 9h apart; +Tupul-20220630 with GSI three-phase
ONE-sample guard). 4 provisional-transfer (Sood/Hollongi/Itanagar-NH415/NH29-Kohima).
Nagaland Jul-Aug-2018 statewide toll noted-not-added (month-long aggregate, no exact
date/point — phantom class). Mizoram/Tripura/Meghalaya-2023 windows deferred on 429s.
Regime honesty shipped (Phase IV system track): `/api/warning/state` now carries
`model_support` (validated-regime vs outside-validated-regime), `prediction_status`
(calibrated-validity vs operational-inference-unvalidated) and `feature_provenance`
(REAL/PROXY/MISSING — verified: lithology + lineament 0.8 uniform PROXY everywhere,
drain_density REAL in G/L/D but 1.2-constant PROXY in AR/AS/MN/ML/MZ; digitized
geology MISSING). Header selector shows Validated/Outside-validated-regime badge in
5 languages; CorridorComparison covers all 8 corridors with per-corridor regime tags
(stale NGEN-pending footer removed). 62 passed 2 skipped, build green. No new model.
Mining pass 5 (`trackA_mining6.py`): 29-Mile LOCALIZED (Teesta-Rambi via 3 outlets +
mile-marker math; 60km-from-Rangpo outweighed as reporter error) -> pool 14 -> 16
(+29Mile-20210711 quad, +29Mile-20210906 dual; 4th hit Sep-23-2020 provisional).
Transfer 6 -> 9 (+Tripura May-18 pair, +Nongstoin-20230617 quad-source).
Provisional-transfer +5 (Tripura May-20 pair, Lumshong, Pynthor, Rngain-road-cut).
Skipped with reason: Mawsynram truck gorge (accident), Guwahati guard-wall (structural).
Mizoram + Jul-2020-Sikkim deferred on 429s. Gap 14.
Mining pass 6 (`trackA_mining7.py`): pool 16 -> 17 (+29Mile-20200923 now 5 outlets;
29-Mile series complete at 4 dated hits). SeesaGolai HELD (follow-ups same-outlet,
mechanism caveat stands); Sichey HELD (Telegraph dead page; InSAR chronic-slope
context added, event still single-source). Transfer 9 -> 10 (+Hlimen-20240528 Remal
houses point); Hunthar-NH6 provisional-transfer; Melthum quarry REJECTED (excavation
site, BhaluKhola precedent); other Remal village tolls stay aggregate context.
Mirik/Kurseong deferred on 429. Gap 13.
78 month-hint with priority (A/B/C), source tiers, precision statuses
(EXACT_VERIFIED/MULTI_SOURCE, MONTH_CONFIRMED, YEAR_ONLY, UNDATED, REJECTED) and
automated contamination checks (`trackA_v2.py`: geo/DEM/rain + train proximity;
mined rows pass). Gap to 30 exact: 23. Mining pilot proved feasible — convergent
multi-source dates, no lonely-webpage assertions.
Trust Ledger v2 live (`GET /api/trust/ledger`, 6 rows incl. OOD contrast;
`TrustLedgerCard` renders Warning|Lead|Exposure|Support|Result). Sichey bundle
(`incident_sichey.json`) + OOD badge in `WarningStateCard` (build green).
Off-season burden (`runs/burden_offseason.json`): 0/60 windows any-hot, mean 0.0
hot-days vs monsoon 28/60 and 5.8 — seasonal separation measured, not assumed.
0/10 framing (locked): out-of-regime transfer test with diagnosed mechanism
(terrain-support mismatch + calibrator extrapolation) and shipped OOD guard —
failure analysis, never a headline metric.
Four scorecards for the final page: predictive validity / warning performance /
warning burden / trust-domain. E17 frozen until championship evidence demands a
specific regime-aware-routing question. No new architectures, no plains model to
rescue 10 cases, no replay-tuned thresholds, Tier-2 never as validation.

## Implementation order (frozen)

1. E1.5 matched negatives + gates A/B/C → 2. re-run ladder+specialists on corrected
   splits → 3. global calibration → 4. regional calibration test → 5. candidate bands →
6. replay on calibrated output. No new features until 2 clears.
   Gates: **A** data integrity (no future/label/source-proxy leakage) ·
   **B** generalisation (global vs specialists on same corrected splits) ·
   **C** useful signal (above chance on matched negatives, not elev/road-driven).
