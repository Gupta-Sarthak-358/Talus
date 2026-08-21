# TALUS PROJECT HANDBOOK

**The single document every team member reads before facing the panel.**
Status: 2026-08-21 · Covers the complete system as built · If any other doc conflicts with this one, this one wins on current-state claims (original plans remain as historical record).

---

## 1. What TALUS Is (30-second version)

TALUS is a **risk-aware decision-support system for open-pit mine safety**, built for SIH 2026 (Team Sangyan, theme: Disaster Management). It converts fragmented mine signals — rainfall, terrain, geology, blasting, cracks — into a zone-level risk score (0–100) with **calibrated confidence**, explains *why* via **real SHAP**, tracks escalation, recommends **role-specific actions** (worker / safety officer / manager / rescue), computes **risk-aware routes**, and runs two distinct kinds of **what-if analysis**.

**Differentiation (memorize this):** SIH25071 ("AI-Based Rockfall Prediction and Alert System", Ministry of Mines) covers *Detect → Alert*. TALUS covers **Detect → Understand → Escalate → Decide → Act**. We are not a better predictor; we are the decision layer around prediction. Say SIH25071 ourselves before a judge finds it.

**One-line philosophy:** *"ML predicts the observed present. Physics simulation answers what happens if causes change."*

---

## 2. The Two Paths (the most important architectural fact)

```text
PREDICTION PATH (answers "what is the risk now?")
  observed state → 12 frozen V1 features
    → frozen Random Forest Model v1
    → instability_score (0–100)
    → isotonic calibration → P(score ≥ 75) = confidence
    → FoS-derived risk band
    → real Tree SHAP explanation

SIMULATION PATH (answers "what happens if conditions change?")
  scenario causes (rain realization / blast schedule / historical storm)
    → Scenario Engine v1.5 modifies CAUSES only
    → FROZEN generator v1.4.0 physics chain propagates them
    → day-by-day FoS / score / label trajectory
    → Evidence Timeline (state changes + physical causes)
```

These are **never mixed**. The ML never simulates; the simulator never writes scores directly (enforced by validation gate). If asked "why not feed 500 mm rain into the RF?" → because the RF interpolates learned states; it does not propagate causal consequences. Live proof: single-feature overrides move inputs off-manifold (raising groundwater *lowered* Zone C's predicted score 66→58 despite positive physics correlation) while the Scenario Engine responds correctly.

---

## 3. Data Provenance Taxonomy (know what is REAL)

| Class | Items | Source |
|---|---|---|
| **Real / observed** | IMD gridded daily rainfall 1901–2024 (45,291 obs, cell 11.50°N 79.50°E = Neyveli Mine-II); Copernicus GLO-30 DEM (pit to −97 m, macro slope ≤31.3°) | IMD Pune; ESA Copernicus |
| **Mine-engineering (documented)** | Bench geometry: OB 25 m×4 + 18 m; mineral bench 6 m @75°; overall 45°; aquifer thrust 490–785 kPa; NLC geotech ranges (cohesion 29–981 kPa etc.) | Neyveli lignite documentation / NLC tables |
| **Literature-derived** | PPV attenuation `PPV = 858.90·(D/√W)^−1.58` (NIRM 2005, r=0.86); blast freq prior 14–28/wk; charge 100–600 kg mode 300; crack mechanisms (tension/desiccation/blast/seepage/heave); DGMS thresholds (regulatory overlay only, NOT labels) | Research artifacts in `docs/research/` |
| **Derived-physical** | groundwater_proxy (wetting-memory transient), crack_density/severity/growth, pore pressure ratio r_u, effective cohesion c_eff | Computed by frozen generator chain |
| **Synthetic/scenario** | days_since_inspection cadence, prior_incident flag, zone layout A–D, road graph | Scenario design |

**Never claim:** real Indian mine telemetry exists; generic crack imagery predicts mine severity; bands are calibrated safety standards. The data disclaimer stays in every deck: *"No public Indian mine sensor/incident dataset was identified. Prototype validation uses public, historical and synthetic data."*

---

## 4. The Physics Chain (undergraduate-intuition level)

Per simulated day, per zone:

```text
rainfall_24h/7d ──► wetting memory (groundwater_proxy, mm; saturates at 180 mm)
                       │
                       ▼
        pore-pressure ratio r_u = 0.35·min(proxy/180,1) [+0.15 if cracks water-filled]
                       │                                          (capped at 0.55)
crack_density ──► retention = 1 − 0.10·min(density,1)   ← costs at most ~10% cohesion
                       │           (DISCRETE −50% branch ONLY if critical AND
                       │            water-filled AND face ≥ 60°)
                       ▼
   FoS = (c·retention + γ·h·cos²θ·(1−r_u)·tanφ) / (γ·h·sinθ·cosθ)     [bench zones]
   FoS_D = 490 kPa / pore_pressure                                     [ZONE_D floor-heave]
                       │  (capped at 2.5, floor 0.5)
                       ▼
   instability_score = 100·(2.5 − FoS)/2.0      (monotone decreasing in FoS)
                       ▼
   risk_label: <0.8 Critical · <1.0 High · <1.2 Moderate · <1.5 Low · else Very Low
```

Key facts to remember:
- **FoS is memoryless** — a pure function of current state (proven empirically three times: LSTM no-gain, V2-trend refutation, persistence R²=0.998).
- **Zone D has no slope** — it fails by floor uplift, not sliding.
- **Severity ≠ continuous driver**: cohesion only drops discretely via the open-crack branch.
- Zones are structurally pinned: A/B/D chronically critical, C chronically stable (this is physically honest, from frozen geometry+strength draws).

---

## 5. The Generator & Worlds

- **Generator v1.4.0** (frozen, git tag `v1.4.0-generator-complete`): phases 1A skeleton → 1B RAIN/TERRAIN/GEOLOGY → 1C GROUNDWATER/BLAST → 1D CRACKS → 1E FoS/labels. Every constant carries `source_type` + `confidence` provenance.
- One **seed** = one stochastic world = 365 days × 4 zones (A upper-OB, B middle-OB, C mineral seam, D pit floor) = 1,460 rows.
- Corpora: v1 handoff (5 seeds, 7,300 rows), **v2 official (50 seeds, 73,000 rows, committed)**, extended study (75 seeds, regenerable).
- Deterministic: same seed ⇒ identical output. Every row tagged `synthetic: true`.

## 6. The 12 Frozen V1 Features (ML-facing contract)

| # | Feature | Unit/Type | Origin |
|---|---|---|---|
| 1 | rainfall_24h_mm | mm | IMD-grounded sampler |
| 2 | rainfall_7d_mm | mm | rolling 7-day sum |
| 3 | slope_angle_deg | degrees | bench layer (mine-engineering) |
| 4 | slope_height_m | metres | bench layer |
| 5 | rock_type | categorical (4 in corpus) | geology draw (c/φ/γ behind it) |
| 6 | crack_density | 0–2.5 | crack accumulator state |
| 7 | crack_severity | normal→critical (ordinal) | depth-ratio decision surface |
| 8 | blast_frequency_per_week | events/wk | production-derived latent |
| 9 | blast_vibration_ppv_mms | mm/s | NIRM attenuation on blast days |
| 10 | days_since_inspection | days | inspection scheduler |
| 11 | prior_incident | 0/1 | scenario flag (False in baseline year) |
| 12 | groundwater_proxy | mm | wetting-memory transient |

Plus `zone_id` as grouping/categorical. **Targets:** `fos` (physics), `instability_score` (primary regression target), `risk_label` (derived bands).

---

## 7. The Experimental Story (tell it chronologically — it's the strongest slide)

| # | Question asked | Result | Lesson |
|---|---|---|---|
| 1 | Naive random split? | **R²=0.998** | Leakage — near-duplicate days across train/test. Banned forever. |
| 2 | Honest unseen-seed split (5 worlds)? | **R²=−0.53** | Worse than guessing the mean. Each world pinned to its own risk band. |
| 3 | Can dynamics be learned within one world? (time-ordered) | R² 0.66–0.94/zone | Yes — signal exists. |
| 4 | Static vs dynamic features cross-world? | −0.55 vs −1.64 | Statics dominate; dynamics don't transfer. |
| 5 | δ-targets (deviation from intact baseline)? | −0.58 → **+0.13** | First positive transfer. |
| 6 | More worlds? 5→20→40→50 | 0.13→0.46→**0.90–0.92** | Coverage was THE bottleneck. |
| 7 | Which model? | 7 families converge ±0.02 | RF selected by VALIDATION (won all targets); boosting test scores never used for selection. |
| 8 | Temporal trend features (V2)? | Worse than V1; persistence R²=0.998@1d | REFUTED — FoS is memoryless. |
| 9 | ANN (MLP/LSTM)? | MLP parity 0.895; LSTM no gain | Architecture isn't the bottleneck; Markov confirmed again. |
| 10 | Transfer learning? | Pretrained **0.906 vs scratch 0.886 @5 worlds**; zero-shot −0.97; parity by 20–40 | Prior = data-efficiency, not replacement. TrAdaBoost 0.775. |
| 11 | DEM context features (G)? | All targets ↓ (−0.04…−0.15) | KILLED. Refused to invent coordinates. |
| 12 | Classification at scale? | macro-F1 0.47; `moderate` never predicted | Direct multiclass is wrong formulation; regression→bands wins. |
| 13 | Natural regime transitions? | **6 in 109,500 zone-days** | Passive generation can't demo early-warning → motivated Scenario Engine. |

**Calibration (FR-03):** isotonic P(score≥75) fit on out-of-fold train-seed predictions; evaluated on validation seeds only. Brier **0.081** vs 0.116 naive; ECE **0.095** vs 0.157. High-risk bins honest (pred 0.93 → obs 0.98). Confidence means: *"calibrated probability of elevated SYNTHETIC risk under the prototype target definition"* — never "probability of rockfall."

## 8. Audits (we tried to break it ourselves)

- **Directionality audit:** physics verified monotone counterfactually; model inversions classified — (a) wetting confound (ZONE_B −0.26 flips to +0.36 controlling rain/GW), (b) lag/state-memory (PPV→growth 0.55 same-day; persists 7d), (c) ML artifact. **Zero generator defects.**
- **Scenario Engine gates:** exact baseline replay, pre-start isolation, monotone dose-response, determinism, no direct score writes, crack continuity — ALL PASS (+6 edge cases).
- Backend suite: **25/25 tests** (model consistency, monotone deterioration, calibration artifact, timeline causality, determinism).

## 9. Scenario Engine v1.5 & Historical Templates

Kinds: `rainfall_storm`, `prolonged_rain`, `blast_surge` (A/B zones only — invariant enforced), `combined`, `historical_rain`. Templates from real IMD record: **Dec-1902 (1,088 mm/month, max day 297.6 mm)**, Apr-1931, Nov-2015, Dec-1996.

**Flagship result:** a single extreme storm barely moves scores (r_u saturates; cohesion-dominated benches are water-immune). But a **3-year Dec-1902 replay accumulates crack damage until the discrete open-crack branch fires naturally: FoS diverges −0.761 from baseline across 51 days.** Acute shock ≠ accumulated deterioration — the system knows the difference.

## 10. API (FastAPI, backend/, 25/25 tests)

| Endpoint | Path | Notes |
|---|---|---|
| Zones | GET `/api/zones[/{id}][/features|/trend|/explanation|/decision]` | live scores 89/100/66/99 (A/B/C/D) |
| Predict | POST `/api/risk/predict` | score + calibrated confidence + derived missing-evidence |
| Explanation | GET `.../explanation` | **real Tree SHAP** + base value |
| ML what-if | POST `/api/simulation/what-if` | **ML counterfactual** — labeled as such |
| Causal what-if | POST `/api/simulation/causal-what-if` | **causal physics** trajectory + Evidence Timeline + divergence metrics |
| Templates | GET `/api/simulation/templates` | IMD-provenance storms |
| Routing | POST `/api/routes/safe` | avoids high-risk zones (`avoided_zones`) |

Live predictions reproduce generator structure independently: A=89 Critical, B=100 Critical, C=66 Moderate, D=99 Critical.

## 11. Demo Script (rehearsed, deterministic — see docs/06_DEMO_SCENARIO.md v2)

1. **Map:** A 89 Critical · B 100 Critical · C 66 Moderate · D 99 Critical.
2. **Click C → SHAP:** base 53.92; crack_severity_critical +19.71, slope_angle −15.68, rock_type +11.47, slope_height −8.40.
3. **ML what-if** (rain ↑ on C): barely moves — say the off-manifold caveat out loud.
4. **Causal what-if:** Dec-1902 replay, 3-year horizon → gw proxy 840.8 mm → branch fires → **ΔFoS −0.761 over 51 days**, Evidence Timeline shows physical causes per event.
5. **Routing:** safe route avoids B.
6. Close with methodology slide: leakage caught (0.998→−0.53), coverage fixed (−0.58→0.92), two feature families killed honestly, calibration measured.

## 12. Frontend Dashboard — Running & Navigating

### One-command launch (demo laptop)

```powershell
powershell -ExecutionPolicy Bypass -File .\start_demo.ps1
```

Starts FastAPI on :8000, health-checks it, prints live zone predictions, then starts Vite on **http://localhost:3000** (live-API mode via `frontend/.env.local`, gitignored). Close the two spawned windows to stop.

Manual alternative: terminal 1 → `cd backend` + uvicorn; terminal 2 → `cd frontend` + `npm run dev`. Frontend runs in mock mode unless `VITE_USE_LIVE_API=true`.

### Screen map (what you're looking at)

| Region | Component | Content |
|---|---|---|
| Top bar | QuickStatsBar | rainfall chip, zones monitored, model status |
| KPI row | RiskSummaryCards | Escalated / Surveillance / Nominal counts + Evidence Quality (mean calibrated confidence, provenance gaps) — all derived live |
| Left | MineMap (Leaflet) | zone polygons centered on Neyveli Mine-II (11.54N 79.49E); red glow = high/critical; click to select |
| Right | ZoneIntelligencePanel | risk gauge, RoleActionCard (FR-06), ShapChart (real Tree SHAP), RiskTrendChart (365-day deterministic series), MissingEvidenceCard |

### The two What-If modes (WhatIfDrawer toggle)

- **ML COUNTERFACTUAL** — overrides observed features, re-predicts with frozen RF. Columns: *Current State* vs *What-If State*, badge reads "Risk change: ±N pts". Caveat shown in-UI: single-feature overrides can move off-manifold.
- **CAUSAL PHYSICS** — Scenario Engine v1.5. Pick kind/template (Dec-1902 etc.), horizon; returns trajectory summary (FoS divergence, open-crack branch flag), IMD provenance, and Evidence Timeline (state changes → causes). **This is the escalation demo**: Dec-1902 replay, 3-year horizon, Zone C/B.

Zone D is **blocked for ML counterfactual** (422): its uplift failure mode is aquifer-driven and cannot be represented by surface-feature overrides — use causal scenarios.

### Reading the numbers

- Confidence = isotonic-calibrated P(score ≥ 75) — elevated synthetic risk, not rockfall probability.
- Bands from FoS: <50 Very Low · <65 Low · <75 Moderate · <85 High · ≥85 Critical.
- Trend chart draws the zone's deterministic 365-day series from the frozen corpus (world seed 91); threshold lines at 75/85.

### Troubleshooting

| Symptom | Meaning / fix |
|---|---|
| ErrorBoundary panel appears | read the message; Retry re-renders — report persistent ones |
| Zone D what-if returns 422 | by design (see above) |
| Page shows placeholder scores | live mode off — check `frontend/.env.local` |
| Backend slow first response (~10 s) | SHAP import + artifact load; launcher waits for it |

---

## 13. Known Limitations (say these BEFORE judges find them)

1. Synthetic-only evidence — no real mine telemetry; architecture validated, not field-calibrated.
2. Dynamic-driver fidelity weak (crack/blast partially masked/confounded in generated data).
3. `moderate` band unlearnable as direct multiclass (narrow band + pinning) — use regression→bands.
4. No natural regime transitions passively; deterioration demos require multi-year scenarios.
5. Bands/thresholds are prototype operational values, not safety standards.
6. SHAP explains the MODEL, not the physical slope.
7. Routing graph and zone geometry are schematic.
8. Final decisions remain with qualified personnel — TALUS recommends, never commands.

## 14. Panel Q&A Prep (hard questions, ready answers)

**"Is your data real?"** → "No public Indian mine sensor/incident dataset exists. Rainfall and terrain are real (IMD 124-year record, Copernicus DEM); geotech parameters are documented Neyveli ranges; the rest is physics-generated and tagged `synthetic: true`. The prototype validates the architecture; deployment requires a mining-partner data feed."

**"Where does the risk score come from mathematically?"** → "12 observable features feed a Random Forest regressor trained on 58,400 physics-generated states. The score is a monotone transform of an infinite-slope Factor of Safety. Bands are FoS thresholds. Confidence is isotonic-calibrated P(score≥75), fit without touching test worlds."

**"How do you know the model works?"** → "It generalizes to entirely unseen stochastic worlds: R²≈0.90 after we proved random splitting leaked (0.998) and that 5 worlds were insufficient (−0.53). Seven model families converge within 0.02. And we tried to break it — temporal features, DEM features, sequence models — and kept the negative results in the ledger."

**"Why not just give 500 mm to the model?"** → "That's an off-manifold counterfactual — the RF would interpolate unrealistically correlated states. Changing rainfall causally requires propagating through wetting memory, pore pressure, crack growth and strength degradation. That's our Scenario Engine, which never writes scores directly."

**"Is the confidence a probability of failure?"** → "No — and we say so precisely. It is the calibrated probability of elevated synthetic risk under our prototype target definition. Real failure calibration needs incident data we don't have."

**"What did you get wrong along the way?"** → "Plenty, deliberately: we shipped the leakage discovery, the 5-world collapse, the refuted temporal features, the killed DEM experiment, and the classification formulation failure in our own ledger. Negative results changed the architecture — that's why the surviving claims hold."

**"Why Random Forest and not deep learning?"** → "Seven families converge within 0.02 — the ceiling is feature information, not architecture. Trees are explainable, fast, and tabular-appropriate. Our LSTM experiment confirmed history adds nothing when current state is fully observed."

**"What would production require?"** → "A mining-partner sensor/incident feed, site-specific recalibration, CV fine-tuning on real rock-face imagery, and certified thresholds under DGMS oversight."

## 15. Repository Map

```text
ml/data_generation/   frozen generator v1.4.0 + validators + export
ml/benchmark/         frozen protocol, baselines/tuning/explain, results/
ml/features/          V2 temporal builder + causality selftest (archived experiment)
ml/scenario/          Scenario Engine spec/engine/validation/summaries
ml/models/            talus_rf_v1.joblib + talus_calibration_v1.joblib
ml/experiments/       archived campaign scripts + raw result JSONs
backend/              FastAPI app (model_service, scenario_service, tests 25/25)
data/processed/       grounded constants + ml_handoff corpora
docs/                 this handbook, CURRENT_SYSTEM.md, observations.md (SS1-SS24),
                      GENERATOR_V1_SPEC, ML_MODEL_CARD_V1, MEMBER2_AUDIT,
                      06_DEMO_SCENARIO v2, source/ (historical plans)
frontend/             React+Leaflet dashboard (integration seam)
```

---

*Final reminder: every number in this handbook is reproducible from committed code and deterministic seeds. If you can't reproduce it, treat it as wrong and check.*
