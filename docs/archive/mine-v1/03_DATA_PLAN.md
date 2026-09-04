> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Data Plan

**Status:** Updated for Research Freeze · Trace to: `docs/GENERATOR_V1_SPEC.md`, `docs/05_FEATURE_SCHEMA.md`, `docs/08_LIMITATIONS.md`

Research grounding is **COMPLETE** for all five tracks (RAIN, TERRAIN, GEOLOGY, BLAST, CRACKS). This document replaces the pre-grounding assumptions with the grounded methodology.

> **Explicit grounding statement:** synthetic data are generated from **grounded distributions and physical relationships, not arbitrary random ranges.** Every feature and constant traces to a real source (artifact + constants file) and carries a provenance tag (`source_type` + `confidence`).

---

## A. Grounding summary (by track)

Each track produced (a) a research artifact in `docs/research/`, (b) a constants file in `data/processed/`, and (c) ledger decisions in `docs/observations.md`.

### RAIN — seasonal + year-conditioned + storm persistence

- **Real source:** IMD 0.25°×0.25° daily gridded rainfall, grid cell **11.50°N, 79.50°E** (= Neyveli Mine-II anchor). NetCDF verified 1901–2024.
- **Grounding:** 1901–2024 (45,291 obs) + 2000–2024 (9,132 obs). Zero-rain 73.2%; Oct–Dec ~63% of annual; 7-day P99.9 heavy tail.
- **Model components (prototype_v1+):**
  1. **Seasonality** — per-month wet/dry + wet-day intensity (monthly pools).
  2. **Year conditioning** — sampled from the **124-year annual distribution** (P05 700, median 1282, mean 1315, std 409), not a stationary "average year."
  3. **Storm persistence** — historical multi-day storm templates (Dec 1902, Apr 1931, May 1943, Dec 1996, 2008-11-28, 2015-11-10) layered onto seasonal sampling.
- **Extracts:** `rainfall_24h_mm`, `rainfall_7d_mm`.
- See `docs/observations.md` §1–11.

### TERRAIN — DEM regional context + mine-engineering bench geometry

- **Real source:** Copernicus GLO-30 (ESA) DEM, tile `Copernicus_DSM_GLO30_N11_E079`, AWS open-data, 30 m.
- **Regional terrain:** pit depression to **−97 m**; macro slope mean 1.5°, **max 31.3°**; context area 11.30–11.70 N, 79.35–79.70 E.
- **Bench layer (separate, mine-design):** OB benches 25 m ×4 + 18 m; mineral bench 6 m @ 75°; overall pit slope 45°; backfilled dumps 26–28°.
- **Rule (Entry 7/10):** `slope_angle_deg` / `slope_height_m` combine BOTH layers, tagged by source_type — the 30 m DEM cannot resolve benches (6–25 m, 45–75°).

### GEOLOGY — Neyveli lithological/material classes

- Neyveli is **Cuddalore Group (Upper Miocene) sedimentary** material — NOT a generic hard-rock 4-class lookup.
- **Material classes:** `lateritic_soil`, `clayey_sandstone` / `sandstone`, `clay` (LL ≤ 90), `variegated_sandy_clay`, `carbonaceous_clay`, `aquifer_sand`, `lignite`, `overburden_mixed`.
- Cohesion / friction / UCS / density / permeability from **NLC-documented measured ranges**; `parameter_regime = total_undrained` flagged per row; SI conversion only at the consumption interface.
- Aquifer architecture: 3 systems; confined upward thrust 490–785 kPa; pumping 8–10 m³ water per tonne lignite.
- **Artifact:** `docs/research/neyveli_geology.md` · **Constants:** `data/processed/geotech/neyveli_geotech_parameters.csv`.

### BLAST — Neyveli attenuation model, not random PPV

- **Locked model:** `PPV = 858.90 · (D/√W)^(−1.58)` (NIRM 2005), r = 0.86, freq **5–27 Hz** (left-skewed, P(<8 Hz) ≈ 0.45).
- Blast events derived from production, not sampled as a scalar: charge-per-delay 100–600 kg (mode 300), distance from synthetic geometry, ~14–28 blasts/wk (derived, broad prior), 30% of OB blasted into 15–22 m benches.
- DGMS (Tech)(S&T) 7/1997 thresholds are a **regulatory overlay, NOT the risk label**.
- **Artifact:** `docs/research/neyveli_blasting.md` · **Constants:** `data/processed/blasting/neyveli_blast_constants.csv`.

### CRACKS — stateful spatial + temporal crack model

- **5 mechanisms:** tension/crest (Rankine `z_c = (2c/γ)·tan(45°+φ/2)`, bench-bounded to 6–12 m), desiccation (LL≤90 clays, 4-stage cycle), blast-induced (PPV-damage criteria), seepage (OB bench water → wall failure), floor heave (confined thrust).
- **Spatial:** crack families anchor to the **mine-engineering geometry layer** (crest lines, bench faces, pit floor), never the raw DEM.
- **Severity:** NORMAL → MINOR → MODERATE → SEVERE → CRITICAL from a ranked decision surface on measurable props — **severity ≠ width alone**.
- **Temporal:** exports `crack_growth_rate_mm_day`; >20 mm/day sustained → failure in 6–12 days.
- **Artifact:** `docs/research/neyveli_cracks.md` · **Constants:** `data/processed/cracks/neyveli_crack_constants.csv`.

---

## B. Feature Provenance Table

Every ML-facing feature maps to a grounding (see `docs/05_FEATURE_SCHEMA.md` for the authoritative contract).

| Feature | Grounding | Source type | Real/Synthetic |
|---|---|---|---|
| `rainfall_24h_mm`, `rainfall_7d_mm` | IMD 11.50N 79.50E, 1901–2024 (seasonal + year + storm templates) | Observed-historical | Synthetic draw from real distribution |
| `slope_angle_deg`, `slope_height_m` | Copernicus GLO-30 DEM + Neyveli bench design | Geo + mine-engineering | Real-derived + fixed input |
| `rock_type` | Neyveli lithological section (Cuddalore Group) | Neyveli-documented | Sample from lithology |
| `crack_density`, `crack_severity` | CRACKS mechanisms + severity decision surface | Literature + NLC analogs | Synthetic/stateful |
| `blast_frequency_per_week` | NLC/Coal Age production-derived (14–28/wk prior) | Production-derived | Synthetic latent |
| `blast_vibration_ppv_mms` | NIRM 2005 attenuation + DGMS overlay | Mine-specific | Synthetic from physics |
| `days_since_inspection`, `prior_incident` | Prototype scenario design | Scenario | Synthetic |
| `groundwater_proxy` | RAIN + time-since-last-rain derived | Derived (confirmed Entry 13) | Synthetic proxy |

---

## C. Generator Specification

The generation contract, internal state, physical constraints, randomness, and validation gates live in **`docs/GENERATOR_V1_SPEC.md`**. The interface boundary (internal generator fields vs ML-facing fields) is defined in **`docs/05_FEATURE_SCHEMA.md`**. This data plan no longer duplicates that logic.

Pipeline: RESEARCH (complete) → GENERATOR v1 (skeleton → environment → operations → instability → validation) → physics-validated synthetic state → risk target → Random Forest.

---

## D. Physics-Informed Labels (FoS)

Labels are produced by a simplified infinite-slope stability model **fed by the generator's physical state** (not by arbitrary draws):

```text
FoS ≈ (c + (γ·h·cos²θ − u)·tanφ) / (γ·h·sinθ·cosθ)
```

- c, φ: material parameters from GEOLOGY constants (degraded by crack density, per CRACKS).
- u: pore pressure (rainfall + groundwater proxy, amplified by water-filled cracks).
- θ, h: slope angle / height from the TERRAIN bench layer.
- Blast disturbance and crack severity modulate the stochastic disturbance term.

Lower FoS → higher risk. This is the **risk target**, kept separate from the ML-facing features (see `docs/05_FEATURE_SCHEMA.md`).

---

## E. Noise, Missingness, Versioning, Sanity

- Gaussian label noise + randomly nulled features (e.g. missing vibration reading) → justifies confidence + missing-evidence reporting.
- **Sanity gates before training** (if they fail, the generator has a bug, not the model):
  - Rainfall correlates positively with risk.
  - Steep slope + high crack density dominates high-risk zones.
  - Physical distributions (PPV attenuation, FoS bounds, crack growth) stay inside grounded ranges.
- Every record tagged `synthetic: true`; generation seed, config version, and formula version logged in `metadata.json`; constants files frozen (never re-fit, re-draw only stochastic drivers).

---

## F. Validation / Cross-check Sources

| Purpose | Source | Use |
|---|---|---|
| Rainfall→risk patterns | NASA COOLR / Global Landslide Catalog | Validate synthetic correlation against real geolocated events |
| Feature distributions | ScienceDirect 7,360-slope-unit susceptibility benchmark | Sanity-check distributions and model behaviour |
| Crack mechanism | Ultralytics Crack-Seg | Train detection; NOT a mine severity claim (domain gap) |
| PPV | NIRM 2005 vs 1994 study | Cross-era consistency (SD 14.6 m/√kg → 12.4 ≈ 12.5 mm/s) |
| Stability physics | USACE EM 1110-2-1902; Lu 2022; Michalowski 2013 | FoS reduction bounds at crack presence |

---

*Kaggle rockfall/landslide datasets are small, uncurated, community uploads — inspiration only, not a primary source. State this if asked.*