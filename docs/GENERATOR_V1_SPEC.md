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
Phase 1D  Instability  CRACKS → cross-track interactions → INSTABILITY score (FoS-based)
Phase 1E  Validation   physics · distribution · provenance checks (gates; see §10)
```

No physics in 1A — get the skeleton and plumbing working first.

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