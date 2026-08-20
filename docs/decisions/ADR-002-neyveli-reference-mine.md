# ADR-002: Neyveli Mine-II as Reference / Base Mine for Data Grounding

**Status:** Accepted · **Date:** 2026-08-20 · **Owner:** Member 2 (Data / Synthetic Generator)
**Trace to:** `docs/03_DATA_PLAN.md`, `docs/00_PROJECT_BRIEF.md`, `docs/07_ASSUMPTIONS.md`

## Context

The synthetic data generator must be **grounded before it is written** (`03_DATA_PLAN.md` Step 2: sample from *real* distributions, not invented ranges). To do that we need one anchor mine environment with enough public documentation to ground rainfall, terrain, geology, and groundwater inputs.

Two candidates were considered:

| Candidate | Open-cast? | Public grounding material |
|---|---|---|
| Hutti Gold Mines Ltd | Mostly underground (Hutti mine); open-cast subsidiaries only (Uti, Ajjanahalli) | Limited; would require choosing a subsidiary mine |
| **Neyveli Mine-II (NLC India)** | **Yes — open-cast lignite** | **Unusually good** |

## Decision

Adopt **Neyveli Mine-II, NLC India Limited** (Neyveli, Cuddalore district, Tamil Nadu) as the **reference / base mine environment for prototyping and scenario modelling**.

**It is a reference environment, not a dataset.** The official statement:

> **"Neyveli Mine-II is used as the reference/base mine environment for prototyping and scenario modelling. Prototype validation uses public, historical and synthetic data; deployment would require mine-partner telemetry and incident data."**

## Why Neyveli (reasons)

1. **Matches the target.** Neyveli is a large, long-running, mechanized **open-cast lignite mine** — directly the setting Talus is designed for.
2. **Large, complex operational context.** Mine-II is a ~**15 MTPA open-cast project over ~7,193.975 ha**, with bucket-wheel excavator/conveyor/spreader mining, large-scale overburden handling, 365-day three-shift operation and a stripping ratio of ~**5.2:1**. A mine this size makes the zone-based dashboard + risk-aware routing concept *necessary*, not decorative.
3. **Documented geographic extent.** Mine-II is documented at approximately **11°27′N–11°32′N, 79°27′E–79°35′E** — enough to pin the IMD 0.25° grid cell without guessing.
4. **Documented rainfall.** Average annual precipitation reported ~**1369 mm** (NGT rejoinder) and ~**1200 mm** (Ministry of Coal) for the Neyveli mine-industrial complex.
5. **Documented hydrogeology.** A USGS study exists on groundwater control in the Neyveli lignite field, and NLC documentation describes **groundwater depressurisation as part of safe mining**. This makes the `groundwater_proxy` and the rainfall → ground conditions → zone risk → decision chain credible rather than invented.
6. **Regulatory material as complexity evidence.** The 2021 EAC/NGT records show Mine-II operates with multiple simultaneous streams (production, groundwater, air quality, land use, rehabilitation, environmental damage assessment) — supporting evidence that Neyveli is a complex, continuously operating environment where multiple risk-related information streams matter. This is exactly the problem Talus addresses.

### Feature grounding coverage

| Talus feature | Neyveli grounding |
|---|---|
| `rainfall_24h_mm` | Excellent — IMD grid cell |
| `rainfall_7d_mm` | Excellent — derived from IMD daily series |
| `slope_angle_deg` | Good — DEM + mine geometry |
| `slope_height_m` | Good — DEM / mine documents |
| `rock_type` | Good — geological literature (to be Neyveli-relevant) |
| `groundwater_proxy` | Very good — actual Neyveli hydrogeology |
| `blast_frequency_per_week` | Literature / synthetic |
| `blast_vibration_ppv_mms` | Literature / synthetic |
| `crack_density` | Crack-Seg + synthetic |
| `prior_incident` | Synthetic / proxy |
| Rainfall–risk relationship | Good |

## Alternative rejected

**Hutti Gold Mines Limited** — its main Hutti mine is underground, and its open-cast operations are at subsidiary sites (Uti, Ajannnahalli), so we would have had to pick a sub-mine and would still have far less public documentation.

## Framing constraints (do not violate)

- ❌ Do **not** claim "TALUS was developed using Neyveli Mine-II sensor data."
- ❌ Do **not** claim "We trained our model on Neyveli's real incident history."
- ✅ Neyveli = **reference environment**; the prototype uses **public + historical + synthetic** data.
- The EAC/environmental material is **supporting evidence of operational complexity**, not the central problem. Talus is a mine-safety decision-support platform, not an environmental-compliance system.
- The central chain remains **Detect → Understand → Escalate → Decide → Act**.

## Consequences

- Provenance must **distinguish DEM-derived regional terrain** from **synthetic pit/bench geometry** — the mine geometry itself (steeper benches) is what matters, not natural regional slope alone.
- Rock/geotechnical parameters will be checked against Neyveli's actual geological context (lignite field overburden) and labelled **literature-derived** where evidence is insufficient.
- Blast/PPV remain synthetic, sourced from published mining literature, documented in provenance.
- `groundwater_proxy` is grounded in Neyveli hydrogeology.
- Crack features come from Crack-Seg with the documented **domain gap** (road/wall → mine rock).
- Neyveli sources are recorded centrally in `research/sources.md`; the grounding manifest lives in `data/grounding_manifest.md`.

## Member 2 workflow (from here)

```text
Neyveli Mine-II
  1. Fix anchor coordinates
  2. Identify IMD 0.25° grid cell
  3. Download relevant IMD rainfall data
  4. Extract Neyveli rainfall time series
  5. Analyze rainfall distribution
  6. Obtain DEM covering Neyveli
  7. Derive terrain/slope statistics
  8. Ground rock/geotechnical parameters
  9. Ground blast/PPV ranges from literature
 10. Ground crack statistics (Crack-Seg)
 11. Freeze generator constants
 12. Build synthetic generator
 13. Generate train/val/test
 14. Run sanity checks
```

## Change Log

- 2026-08-20 — ADR-002 created (Neyveli reference mine locked).