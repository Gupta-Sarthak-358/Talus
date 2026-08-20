# TALUS Generator v1

**Status:** Research Freeze — implementation ready · Trace to: `docs/03_DATA_PLAN.md`, `docs/04_MODEL_PLAN.md`, `docs/05_FEATURE_SCHEMA.md`, `docs/05_API_SPEC.md`

Bridge between the completed research tracks and the generator implementation (Member 2).

---

## 1. Purpose

Produce a **physics-informed synthetic daily state per mine zone** that is internally consistent with the five grounded tracks (RAIN, TERRAIN, GEOLOGY, BLAST, CRACKS) and exports the frozen ML-facing feature schema (`docs/05_FEATURE_SCHEMA.md`). The output feeds the risk target (FoS) and eventually the Random Forest. It is **not** a calibrated failure simulator (see §12).

## 2. Design principles

1. **Grounded, not arbitrary** — every constant comes from a frozen constants file (`data/processed/{geotech,blasting,cracks}/*.csv`) or the IMD/DEM analysis outputs. Tag `source_type ∈ {mine_specific, regional_geological, literature, derived}` + `confidence` per row.
2. **Physics in the generator, not the model** — the model only maps the exported features to the risk target.
3. **Interface discipline** — internal fields are rich and evolving; ML-facing names are frozen.
4. **Do not overfit to invented precision** — where Neyveli data is absent (e.g. blast frequency), use wide, clearly-labelled `derived` priors.
5. **Validation gates before any training** (§10).
6. **Reproducible** — fixed seed handling (§9), versioned config, provenance logs.

## 3. Data sources

### Rainfall
- **IMD** 0.25° daily gridded, grid cell **11.50°N, 79.50°E** (= Neyveli Mine-II), 1901–2024, NetCDF verified (45,291 obs).
- Grounded model: seasonal (monthly wet/dry + intensity pools) + year conditioning (124-yr annual distribution) + storm-persistence templates (Dec 1902, Apr 1931, May 1943, Dec 1996, 2008-11-28, 2015-11-10).
- Outputs: `rainfall_24h_mm`, `rainfall_7d_mm`.
- Reference: `docs/observations.md` §3–11, §10; analysis CSVs in `data/processed/imd/analysis/`.

### Terrain
- **Copernicus GLO-30** DEM (tile `Copernicus_DSM_GLO30_N11_E079`), regional pit to −97 m, macro slope ≤ 31.3°.
- **Mine-engineering bench layer** (fixed inputs, NOT DEM): OB benches 25 m ×4 + 18 m; mineral bench 6 m @ 75°; overall 45°; backfill 26–28°.
- Outputs: `slope_angle_deg`, `slope_height_m` (combined, tagged by `slope_height_layer`).
- Reference: `docs/observations.md` §9, Entries 7 & 10; `data/processed/terrain/terrain_summary.json`.

### Geology
- **Neyveli lithological section** (Cuddalore Group): 9 material classes in `data/processed/geotech/neyveli_geotech_parameters.csv`; parameter regime `total_undrained`.
- Aquifers: 3 systems; confined thrust 490–785 kPa; pumping 8–10 m³/t.
- Outputs: `rock_type` (internal: `material_type` + c, φ, γ, k, UCS).
- Reference: `docs/research/neyveli_geology.md`, `docs/observations.md` §11.

### Blast
- **Locked PPV:** `PPV = 858.90·(D/√W)^(−1.58)`, r=0.86, freq 5–27 Hz (left-skewed, P(<8 Hz)≈0.45).
- Operational: 30% OB blasted, every OB bench, 200 mm holes, 15–22 m benches, charge-per-delay 100–600 kg (mode 300), ~14–28 blasts/wk (derived prior).
- Outputs: `blast_frequency_per_week`, `blast_vibration_ppv_mms` (observed PPV at nearest exposed structure). DGMS 7/1997 thresholds = regulatory overlay only.
- Reference: `docs/research/neyveli_blasting.md`, `data/processed/blasting/neyveli_blast_constants.csv`.

### Cracks
- 5 mechanisms (tension/crest, desiccation, blast-induced, seepage, floor heave); geometry ranges; bench-bounded depth (⅓–½ slope height, practical 6–12 m); severity decision surface (≠ width); temporal growth (>20 mm/day → failure in 6–12 days).
- Constants: `data/processed/cracks/neyveli_crack_constants.csv`.
- Reference: `docs/research/neyveli_cracks.md`.

## 4. Dependency graph

```text
time / seed
   ↓
RAIN (daily weather state: intensity, wet/dry, storm template, year-condition)
   ↓
TERRAIN (zone geometry: slope_angle_deg, slope_height_m, bench layer tag)
   ↓
GEOLOGY (material_type, c, φ, γ, k, groundwater state per zone)
   ↓                  │
   ├── BLAST (weekly Poisson blasts → per-event charge/distance/freq → PPV)
   ↓                  │
GROUNDWATER proxy (rain + time-since-rain + aquifer state)
   ↓                  │
CRACKS (families per zone ← geometry + rain + blast + geology; growth & severity)
   ↓
INSTABILITY (FoS via infinite-slope, crack/blast/rain modifiers) → risk target
   ↓
FEATURE EXPORT (frozen ML-facing schema) → train/val/test CSVs
```

Order: RAIN → TERRAIN → GEOLOGY → (BLAST ∥ groundwater) → CRACKS → INSTABILITY → EXPORT.

## 5. Internal state schema

Daily per-zone internal state (evolving):

```text
zone_id, date, seed_component
rainfall_24h, rainfall_7d, wet_or_dry, storm_template_id, year_condition
slope_angle_deg, slope_height_m, slope_height_layer
material_type, cohesion_kpa, friction_phi_deg, density_kg_m3, perm_m_s, parameter_regime
groundwater_proxy, pore_pressure_kpa, groundwater_thrust_kpa
blast_event?: charge_per_delay_kg, blast_distance_m, dominant_frequency_hz, ppv_raw_mms
crack_*: family, depth_m, width_mm, length_m, segment_spacing_m, water_filled,
         growth_rate_mm_day, severity
fos, risk_score, risk_band, confidence_seed, provenance_tags
```

Every field carries `source_type` + `confidence` (provenance). See `docs/05_FEATURE_SCHEMA.md` §3.

## 6. ML-facing output schema

Exactly the 12 frozen fields (FROZEN):

```text
rainfall_24h_mm, rainfall_7d_mm, slope_angle_deg, slope_height_m, rock_type,
crack_density, crack_severity, blast_frequency_per_week, blast_vibration_ppv_mms,
days_since_inspection, prior_incident, groundwater_proxy
```

Names and semantics per `docs/05_FEATURE_SCHEMA.md` §2. Output records also carry `zone_id`, `date`, `synthetic: true`, and provenance tags. Missingness is emitted separately (`missing_features`) per `docs/05_API_SPEC.md`.

## 7. Generation order (implementation phases)

```text
Phase 1A  Skeleton     schema · configuration · seed handling · zone inventory · output plumbing
Phase 1B  Environment  RAIN → TERRAIN → GEOLOGY
Phase 1C  Operations   BLAST (weekly events, PPV) → GROUNDWATER
Phase 1D  Instability  CRACKS (cross-track damage process with memory)
Phase 1E  Validation   INSTABILITY score (FoS-based) + risk labels · physics · provenance gates (see §10)
```

No physics in 1A — get the skeleton and plumbing working first.

### 7.1 Phase 1A placeholder policy (EXPLICIT AUTHORIZATION)

The spec **explicitly permits** Phase 1A to emit provisional placeholder values:

- **Physics-derived columns are NA in 1A** (rainfall, DEM terrain, sampled materials, groundwater, blast, cracks, instability). Their schema names/types/enums are still present so the CSV header is final; values fill in from Phase 1B onward.
- **Risk fields are provisional in 1A** (`slope_condition`, `instability_score`, `risk_label`) — present as NA, never used for validation. They are NOT labels yet; they only become meaningful after Phase 1D.
- **Scenario fields that are seed-scoped are permitted in 1A**: `days_since_inspection` is derived deterministically from the seed + zone (inspection-schedule scheduler; no physics). `prior_incident` = 0 in 1A.
- `synthetic = True` on every row.
- Schema validation is enforced by `ml/data_generation/validate_generator_v1.py` (fail loudly on missing/renamed/wrong-typed/enum-violating columns) — this runs in 1A on the header + nullable types, and after 1D on populated values.
- No rainfall, terrain, geology sampling, blasting, crack dynamics, or risk logic may be implemented in 1A. Those are 1B–1D.

### 7.2 Versioning convention

```text
Phase 1A   → generator_version 1.0.0   (schema_version 1.0 frozen)
Phase 1B   → 1.1.0
Phase 1C   → 1.2.0
Phase 1D   → 1.3.0    (1.3.1 = pre-freeze audit: material-direction fix + acute-window policy)
Phase 1E (final) → 1.0.0-final metadata (bump stays explicit in generator_summary.json)
```

`schema_version` (the 12 ML-facing fields, `docs/05_FEATURE_SCHEMA.md`) remains **1.0** throughout; any change to it requires the schema-change-rule path in `docs/05_FEATURE_SCHEMA.md` §4.

### 7.3 Phase 1C operations policy (BLAST + GROUNDWATER)

Phase 1C populates the operation track. BLAST and GROUNDWATER are **not** independent random columns — they are physically coupled to the mine environment:

- **GROUNDWATER**: zone-static aquifer thrust sampled once per zone from grounded ranges (ZONE_D = confined aquifer below lignite, 490–785 kPa; OB benches semi-confined seepage). The time response is an exponential wetting memory of the mine-wide daily rainfall series (τ≈12 d), added to the zone thrust to produce `pore_pressure_kpa`, `groundwater_thrust_kpa`, `groundwater_state`, and the ML-facing `groundwater_proxy` (wetting memory in mm). **Semantic contract:** `groundwater_thrust_kpa` is the baseline component of `pore_pressure_kpa` (the confined aquifer presses upward on the pit floor with 490–785 kPa regardless of weather — geology §3.4); the wetting transient modifies that baseline upward. Consequently ZONE_D is legitimately high/critical even in dry weather (documented floor-heave condition, not a bug). Same seed ⇒ identical output; pore pressure must be far more persistent than same-day rain (lag-1 auto-correlation) and must track multi-day accumulation.
- **BLAST**: the 14–28/wk derived rate is **mine-wide** (Interpretation A, decided pre-1D) and is allocated across the represented blasting zones — ZONE_A + ZONE_B sum to 14–28/wk, so every generated event is a real blast affecting the modelled system (no operational rate hidden on unrepresented benches). Only OB benches (A/B) blast — lignite bench and pit floor never. Per event: charge per delay W ~ triangular(100, 600, 300 kg); receiver distance D zone-static from the synthetic layout; dominant frequency from the 5–27 Hz 3-bin model (P(<8 Hz) ≈ 0.45); PPV = K·(D/√W)^(−b) with K=858.90, b=1.58 (LOCKED NIRM constants, loaded from `neyveli_blast_constants.csv`, never re-fit) plus lognormal scatter tuned toward r≈0.86. Non-blast days expose PPV = 0 mm/s (no disturbance), so the ML projection has no NaN.
- **Regulatory boundary**: DGMS (Tech)(S&T) Circular 7/1997 PPV limits are stored in the constants CSV as **reference only**. They are never exported as columns and never become the risk label; risk is unaffected by statutory compliance limits (that is the crank/instability track).
- No crack dynamics or risk logic may be implemented in 1C. Those are 1D/1E.

### 7.4 Phase 1D instability policy (CRACKS)

Phase 1D populates the crack track as a **time-evolving damage process with memory**, not a random column. Physics:

- **Daily growth** is the sum of six physically-coupled terms: **tension** (slope steepness × material susceptibility × wetting factor × activity), **hydraulic** (wetting memory, amplified by material susceptibility and moisture-bearing clays), **blast-induced** (only on OB benches A/B, active above the locked 8 mm/s damage threshold, scaled by PPV), **seepage** (ZONE_B under high wetting), **desiccation** (clay-rich zones after prolonged dry spells), and **heave** (ZONE_D confined aquifer thrust, `thrust/490 − 1`). Growth is **never negative** — cracks do not shrink. **Material coupling direction is contractual:** every material-scaled term passes through `susceptibility(weakness)` and is MONOTONE NON-DECREASING in weakness (weakness up → crack growth up; cracks research "cracks concentrate in the weakest materials"). The 1D audit asserts this direction (audit item 2).
- **Hydraulic rainfall chain (explicit dependency):** `rainfall → rainfall_7d → groundwater wetting memory (τ≈12 d) → pore pressure → hydraulic crack growth`. 1C already collapses rainfall into the groundwater memory variable; 1D's hydraulic term consumes **groundwater_proxy** (the wetting memory) — it does NOT re-read `rainfall_7d` directly (which is used only for the `water_filled` boolean). So `rainfall_7d` participates in the chain via groundwater, exactly as the causal arrow dictates, rather than as an independent second rainfall input.
- **Memory / ratcheting:** `crack_depth_m` and `crack_width_mm` are cumulative state; each day's growth is added and never retracted (CRACK-01/02). Width cap 150 mm general, 60 mm on ZONE_D (floor panel); depth cap = ⅓–½ bench height on benches, 0.6–1.5 m on the floor panel (CRACK-02/03). ZONE_D (pit floor above confined aquifer) is *always* the `floor_heave` family — the documented confined-aquifer condition.
- **Family** is the dominant-driver of the day among the six terms (`tension_crest`, `blast_induced`, `seepage`, `desiccation`, `floor_heave`; `none` before damage). Under Interpretation A, ZONE_B (150 m, high PPV) fires nearly daily ⇒ dominated by `blast_induced`.
- **Severity (CRACK-04/05):** `crack_severity` is **cumulative state only** — crack depth as a fraction of the reserved bench layer (0.10/0.20/0.33/0.49 → normal/minor/moderate/severe/critical), so the rating rats with the crack and never downgrades. The transient **6–12 day failure-window signal** (>20 mm/day sustained growth, Leonardos & Terezopoulos 2002) is NOT folded into the rating; it is exposed as the ML feature `crack_growth_rate_mm_day` (long-run 7-day trend). Width (`crack_width_mm`) remains an independent ML feature.
- **Failure-window coverage policy (audited):** the baseline coupling has a structural growth ceiling of ~10 mm/day (max PPV + peak wetting simultaneously), so a routine-operations synthetic year **does not** produce >20 mm/day pre-failure-window states (0/60 audit seeds, max ~10). This is by design — such losses mark the 6–12 day run-up to failure and are the domain of the 1E/1F stress-event layer, not the routine baseline. The 1D audit asserts the baseline *stays below* the window; acute states must be generated deliberately as stress events, never fabricated by the routine sampler.
- No slope-stability score or risk label may be implemented in 1D (`slope_condition`, `instability_score`, `risk_label` stay NaN) — those are Phase 1E.

### 7.5 Phase 1E instability & risk contract (FoS-based)

Phase 1E converts the physical state built in 1B–1D into slope stability and risk. **It may not invent an independent random risk score.** The chain is strictly bottom-up:

```text
physical parameters (c, φ, γ, θ, h)
      ↓
factor of safety (infinite-slope, driven below by the 1B–1D state)
      ↓
stability interpretation (slope_condition)
      ↓
instability score (monotone in FoS)
      ↓
risk label (bands)
```

The generator outputs `fos`, `instability_score`, `risk_label`, and `slope_condition`; `risk_label` is the target for the ML model (kept separate from the 12 frozen ML-facing *features*).

**FoS model (simplified infinite-slope, `docs/03_DATA_PLAN.md` §D, `docs/04_MODEL_PLAN.md` §2):**

```text
FoS ≈ (c_eff + (γ·h·cos²θ − u)·tanφ) / (γ·h·sinθ·cosθ)
```

- `c`, `φ`, `γ`: GEOLOGY material parameters consumed **unchanged from 1B** (never re-drawn in 1E).
- `c_eff` = cohesion **degraded by crack density** (cracked mass loses effective cohesion; CRACKS research: "cracked mass = lower effective cohesion", so `c_eff = c·(1 − k·crack_density)` with the crack −10% FoS line forming the budget, Lu 2022).
- `u` = pore-water pressure from 1C (`pore_pressure_kpa`) **amplified by water-filled cracks** (`water_filled`, CRACKS): a rain-filled crack adds hydrostatic wall pressure on top of aquifer pore pressure (USACE assumption).
- `θ`, `h`: TERRAIN bench layer from 1B (bench face angle / height; `slope_angle_deg`, `slope_height_m`).
- **Blast disturbance** modulates via the crack-state path (blast-induced crack growth lowers `c_eff`, is not an independent additive terror term).

**CRACK-DENSITY CONTRACT (LOCKED):**

```text
crack_density is normalized to [0, 1].

The 1E baseline crack-cohesion degradation is bounded so that ORDINARY crack
presence cannot exceed the ~10% FoS budget derived from Lu (2022):

    c_eff = c · (1 − k_crack · min(crack_density / D_REF, 1))     k_crack ≈ 0.10

so even crack_density → 1 degrades c by at most ~10% on the ordinary path.

The ~50% reduction is RESERVED for the explicitly identified steep engineered
open-crack worst case (Michalowski 2013) and must NOT emerge merely because
crack_density approaches 1. The −50% branch requires BOTH:
    · an open crack state (critical severity + water_filled), AND
    · a steep engineered slope (bench-layer face angle ≥ 60°).
It is a distinct, auditable branch, not a continuous function of density.
```

**COUNTERFACTUAL FoS-ORDERING GATE (LOCKED):** for any fixed zone, the validator constructs four states that differ ONLY in the physical drivers and asserts, within tolerance:

```text
FoS(dry + intact + no blast)  ≥  FoS(wet + intact)  ≥  FoS(wet + cracked)  ≥  FoS(wet + cracked + blast damage)
```

This makes the causal contract `dry intact > wet > cracked > blast-damaged` mechanically enforceable (same physics as §10's sanity gate, now a deterministic counterfactual rather than a correlation).

**Cap contract (spec §8, CRACKS):** FoS is bounded and physical. Crack presence is budgeted at ~−10% from dry-intact FoS (Lu 2022); the open-crack worst case is −50% and applies **only** on steep engineered slopes (Michalowski 2013), never as a global default. FoS is capped above at ~2.5 so the intact dry bench reads "Very Low" rather than unbounded; local spikes from benign dry geometry must not dominate.

**Bands (prototype thresholds, `docs/08_LIMITATIONS.md` §7 — FoS is NEVER a safety certification, only an operational band):**

```text
FoS < 0.80                    → critical   (risk_label / risk_band)
0.80 ≤ FoS < 1.00             → high
1.00 ≤ FoS < 1.20             → moderate
1.20 ≤ FoS < 1.50             → low
FoS ≥ 1.50 (≤ ~2.5 cap)       → very_low
```

- `slope_condition` (stable/marginal/unstable/failed) mirrors FoS: ≥1.20 stable, 1.00–1.20 marginal, 0.80–1.00 unstable, <0.80 failed. It deliberately has **4 physical states**, while `risk_label` has **5 operational bands** (a "stable" slope can still be "low" operational risk — not a contradiction).
- `instability_score`: 0–100, **monotone decreasing in FoS** (lower FoS → higher score), continuous for regression; mapped to the same bands for classification. **FoS is its only source** — no random noise, no feature-weight soup. Two states with the same FoS get the same score regardless of which driver (rain/groundwater/cracks/geometry) produced it.
- `confidence_seed`, `provenance_tags` record that the label came from the FoS physics path, not a random draw.

**Gates before training (§10):** FoS bounded (≤ ~2.5, ≥ 0); the **counterfactual FoS-ordering gate** (`dry intact ≥ wet ≥ cracked ≥ cracked+blast`) holds per zone; rainfall correlates positively with risk; steep + highly cracked zones dominate High/Critical; the 1E audit checks `risk_label` never downgrades relative to a stricter physical state and that an extreme synthetic zone (steep + heavy rain + deep crack + blast) lands in Critical.

**Label-pinning provenance (expected, not a defect):** Per-zone risk-label pinning is expected where frozen geometry and strength anchors place a zone inside a single FoS band. In seed 42, ZONE_A's critical pinning is primarily a consequence of the low-cohesion clayey_sandstone draw (c=45 kPa within the grounded 29–157 kPa range), while ZONE_C remains very_low because its short 6 m bench and c/φ draw produce FoS above the upper band. This is not considered a generator defect. The continuous instability_score retains within-band variation and is the preferred regression signal; multi-seed generation should be used for classification studies.

## 8. Physical constraints (must hold, validated in 1E)

| Constraint | Rule | Source |
|---|---|---|
| Crack depth | ≤ ⅓–½ of the bench/slope height the crack sits on; never > slope height | CRACKS (USACE/Terzaghi/Lu) |
| Practical crack depth (Neyveli) | 6–12 m band on 18–25 m OB benches | CRACKS |
| PPV | must follow the NIRM attenuation law with lognormal scatter (r≈0.86); never exceed the law's unreachable tail | BLAST |
| Dominant frequency | 5–27 Hz support, P(<8 Hz) ≈ 0.45 | BLAST |
| Blast frequency | weekly Poisson ≈ 14–28/wk (broad prior); **not** NIRM's 22-blast sampling | BLAST |
| Rainfall accumulations | reproduce seasonal structure, 7-day P99/P99.9 tail, and storm-templates when used | RAIN |
| FoS | bounded, physical (FoS ≤ ~2.5 for activate-critical mapping; crack presence −10% line; open-crack worst case −50% only on steep engineered slopes) | CRACKS |
| Crack growth rate | **baseline stays below the 20 mm/day failure window** (routine year never fabricates pre-failure states; acute window is stress-event/1F only) | CRACKS |
| Material coupling | all material-scaled growth MONOTONE NON-DECREASING in `MATERIAL_WEAKNESS` (susceptibility contract) | CRACKS |
| Slope angle | bench-layer values from fixed engineering inputs (45–75° faces, 6–25 m); DEM layer ≤ ~31° | TERRAIN |
| Material regime | never silently convert drained ↔ undrained (regime = `total_undrained` for NLC table) | GEOLOGY |

## 9. Randomness / seeds

- Global `SYNTHETIC_SEED` default 42 → per-track sub-seeds (rain, terrain, geology, blast, cracks) derived via a deterministic scheme.
- Zone inventory seeded so the same config reproduces the same zones/states.
- All stochastic draws use `numpy.random.default_rng(seed)`-style generators; log sub-seeds in `metadata.json`.
- Prototype runs seeds 42–46 for the v0 baseline lineage.

## 10. Validation gates

**Phase 1E gates — all must pass before training:**

1. **Physics checks** — every §8 constraint sampled over a validation run (e.g. 5 seeds, full year each); hard-fail on violation; log rates.
2. **Distribution checks** — synthetic rainfall percentiles (daily, 7d), zero-rain %, seasonality vs historical; PPV vs attenuation; slope/bench-layer ranges.
3. **Provenance checks** — every output row carries `source_type` + `confidence`; constants files never re-fit, only re-drawn.
4. **Sanity checks** — rainfall correlates positively with risk; steep + cracked zones dominate high-risk; blast disturbance visible but not dominant everywhere.

## 11. Known uncertainties

| Item | State | Handling |
|---|---|---|
| Blast frequency / charge-per-delay | Derived, low confidence (wide prior 14–28/wk; MCD 100–600 kg) | Tagged `derived`; log as tunable latent |
| Mineral bench 6 m / overall 45° | User-provided PDF; direct fetch failed | Medium confidence; re-verify when possible |
| PPV K, b, freq | NIRM 2005 measured; high confidence | Frozen |
| Rock cohesion (sandstone) | OCR-garbled source; alt value | Range retained + flag |
| Desiccation crack geometry | Field studies (not Neyveli-specific) | Tagged literature |
| DEM bench resolution | 30 m cannot see benches | Bench layer injected from engineering inputs |

## 12. What Generator v1 does NOT claim

> Generator v1 produces **physics-informed synthetic training data for prototype development**. It does not constitute a calibrated mine-slope failure simulator or a validated probability-of-failure model. It is not certified, not validated against real mine-incident data, and its risk bands are prototype thresholds, not safety standards. Real deployment requires a mine-partner telemetry/incident-data agreement and site-specific calibration.

See `docs/07_ASSUMPTIONS.md` and `docs/08_LIMITATIONS.md`.