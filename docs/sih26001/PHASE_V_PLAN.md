# TALUS Phase V Plan — Championship → Replay → Multimodal (FROZEN 2026-09-18)

## Where Phase IV left us

- Championship pool: **22 eligible exact-date events / 17 episodes** (`championship_events_v1.csv`), audit 22/17/0, all dual+ convergence.
- Readiness: **20 ready + 2 conditional (Dipudara same-episode pair) + 0 blocked** (`runs/calibration_readiness.json`).
- Transfer cohort: 10 eligible + provisionals, strictly separate. Post-championship study: Mirik-2025 etc.
- Frozen: NGEN box, contamination rules, exclusion case-law (`CHAMPIONSHIP_RULE_v1.md`), onset schema, same-episode split law, global RF + regional calibration + warning policy, OOD guard.
- Live: regime badges + REAL/PROXY/MISSING provenance on all 8 corridors.
- Target: 30 events **or documented evidence ceiling** — quality over quota. Freeze at whichever comes first.

## Phase V-A: Championship freeze (no modeling)

1. Final admin-lead sweep only (Tsong-type DDMA/SSDMA/GSI leads). No press trawling.
2. Freeze `championship_events_v1` (whether 22, 30, or ceiling number N).
3. Integrity audit + readiness audit re-run; record composition limits (2022-heavy, Gangtok concentration, monsoon-heavy).
4. Development / held-out split, fixed **before any held-out scoring**:
   - same-episode rows same side (Dipudara law);
   - temporal realism (not "5 most recent");
   - chronic-site repeats distributed, not stacked.
5. Split manifest frozen and committed. Held-out becomes untouchable.

## Phase V-B: Daily reconstruction (no modeling)

For every championship event, build T-30/T-14/T-7/T-3/T-1/T histories:

- rainfall (IMD, timestamp ≤ T), soil (CCI v09.2, ≤ T), seismic (USGS history ≤ T),
- satellite state (S2/L8 era-checked, cloud-flagged), NDVI/LULC (note WorldCover anachronism pre-2020),
- terrain/static, disturbance state. REAL/PROXY/MISSING per feature per timestamp.
- No post-event contamination (assertion-checked at build).

## Phase V-C: Baseline replay M0 (frozen system only)

Run frozen global RF + regional calibration + warning policy over all event histories.
Measure: detection, lead time, misses, false-alert burden (monsoon vs off-season),
calibration (Brier/ECE), OOD behavior, regional/novel-vs-recurrent splits.
**M0 is the baseline every later architecture must beat. No retraining, no threshold touch.**

## Phase V-D: Multimodal evidence (only if M0 exists)

- **M1 (evidence fusion):** `[p_base + sat change features + physical features] → compact fusion (XGB/small MLP) → calibration`. Question: does satellite change add value beyond tabular?
- **M2 (image encoder):** only if M1 wins. CNN embedding + tabular fusion. No from-scratch ViT on this data volume.
- **M3 (temporal multimodal):** only if M2 wins. T-30→T trajectories answering "is this slope entering an abnormal state?"
- Exposure stays **downstream** of hazard (never an input to probability).
- Stop rule: if M(N) doesn't improve held-out warning + burden + calibration metrics, don't build M(N+1).

## Phase V-E: Regime-aware routing E17 (only after championship scorecards)

- E17-A: feature-space regime discovery (no labels in routing).
- E17-B: test whether regimes have different conditional risk relationships.
- E17-C: specialists only for well-supported regimes; prefer M4 (global backbone + specialist-as-exception).
- E17-D: hard vs soft gating. E17-E: per-regime calibration. E17-F: held-out geography/time. E17-G: burden.
- Governance: regimes proposed automatically, promoted to operational experts only with data + validation + calibration + explicit deployment decision. No ML hydra.

## Final scorecards (four)

1. Predictive validity (ROC/PR, hard-negative, temporal). 2. Warning performance (recall, lead time, misses).
3. Burden (false-alert windows, hot days, monsoon vs off-season). 4. Trust/domain (calibration, OOD, provenance, unsupported geography). Plus exposure/decision analysis on top.

## Standing prohibitions

No E17 before final Phase-IV scorecards. No multimodal production before M0 baseline. No threshold/model/feature change during held-out. No geography-specific model zoo. No silent PROXY→REAL upgrades.

## Architecture freeze (8193101, 2026-09-18)

Roles locked: susceptibility=where, environment=forcing, physics=state (FoS never a
threshold), SAR=response-pending, exposure downstream, OOD/provenance as trust layer.
No new branches (no PINN, no second physics, no new modalities). Open gates only:
VI-2 SAR extraction (route cracked via browser chain; batch in flight, pilot validated) then one tiny fusion experiment (env vs
env+physics vs env+physics+SAR). After that: build product, not machinery.
