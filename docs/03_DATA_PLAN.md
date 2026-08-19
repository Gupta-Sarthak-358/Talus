# Talus Data Plan

**Status:** Frozen for MVP · Trace to: `docs/01_REQUIREMENTS.md`, `docs/08_LIMITATIONS.md`

This document distills the research source document ([`Talus_Data_Training_Plan.md`](source/Talus_Data_Training_Plan.md)) into the working data plan. Full research detail lives in the source document and in [`research/`](../research/).

---

## A. Data Categories

### Environmental

- **Rainfall** — real source: IMD gridded rainfall, 0.25°×0.25°, daily, 1901–2024 (imdpune.gov.in). Used to ground the synthetic rainfall distribution for a real mining region's grid cell.
- **Groundwater / pore pressure** — no public mine feed. Represented by a **derived proxy** from rainfall + time-since-last-rain.

### Geological / Topographic

- **Slope angle** — derived from DEM (ISRO Bhuvan CartoDEM 1–3 arc-sec or NASA/USGS SRTM 30–90 m).
- **Slope height** — derived from DEM / bench geometry.
- **Terrain** — DEM-derived.
- **Rock type** — literature lookup (cohesion, friction angle by rock class); no public mine-specific dataset.

### Operational

- **Blast frequency** — literature-derived parameter (synthetic).
- **Blast vibration** — literature-derived PPV ranges (synthetic).

### Visual / Structural

- **Crack imagery** — Ultralytics Crack-Seg dataset (4,029 annotated images). Trains the *mechanism* of crack detection. **Domain gap:** roads/walls, not mine rock faces.
- **Crack features** — length, density, orientation (CV output) feed the risk engine.

### Historical

- **Prior incidents** — no public Indian mine incident dataset. Synthetic event flags.
- **Global landslide/rockfall patterns** — NASA COOLR / Global Landslide Catalog (real, geolocated events) used to validate rainfall→risk correlation.

---

## B. Data Provenance Table

*Gold during judging. Every feature maps to a source.*

| Feature | Source | Type | Real/Synthetic | Status |
|---|---|---|---|---|
| Rainfall | IMD | Historical | Real | Planned |
| Elevation | Bhuvan / SRTM | Geospatial | Real | Planned |
| Slope | Derived from DEM | Computed | Real-derived | Planned |
| Rock type | Literature | Lookup | Literature-derived | Planned |
| Cohesion | Literature | Lookup | Literature-derived | Planned |
| Friction angle | Literature | Lookup | Literature-derived | Planned |
| Blast frequency | Literature | Parameter | Synthetic | Planned |
| Blast vibration | Literature | Parameter | Synthetic | Planned |
| Groundwater | Derived | Proxy | Synthetic | Planned |
| Crack images | Crack-Seg | Image | Real, non-mine | Planned |
| Crack features | CV (YOLO-seg) | Computed | Model-derived | Planned |
| Mine incidents | None public | Event | Synthetic | Synthetic |
| Global events (validation) | NASA COOLR/GLC | Event | Real | Planned |

---

## C. Synthetic Dataset Generation

Goals: physically grounded, reproducible, and honest.

**Step 1 — Feature schema (per zone).**
Rainfall (mm, last 24h/7d), slope angle (°), slope height (m), rock type (categorical), crack density, crack severity (derived), blast frequency (events/week), blast vibration (PPV, mm/s), days since last inspection, prior incident flag (0/1), groundwater proxy (derived).

**Step 2 — Realistic sampling.**
- Rainfall: sample from the actual IMD historical distribution for a real mining-region grid cell.
- Slope angle/height: from real geometry ranges (bench angles 45–70°, overall slopes 30–45°) or derived from a real CartoDEM/SRTM tile of a mine area.
- Rock type: small categorical set tied to literature cohesion/friction-angle ranges.
- Blasting/vibration: literature-reported PPV and blast-frequency ranges — labeled literature-derived, not measured.

**Step 3 — Physics-informed labels (FoS).**
Approximate Factor of Safety via a simplified infinite-slope stability model:

```text
FoS ≈ (c + (γ·h·cos²θ − u)·tanφ) / (γ·h·sinθ·cosθ)
```

- c = cohesion (from rock type)
- φ = friction angle (from rock type, degraded by crack density)
- θ = slope angle
- h = slope height
- γ = unit weight of rock
- u = pore pressure (from rainfall/groundwater proxy)

Add a stochastic disturbance term scaled by blast vibration (blast-induced destabilization). Map FoS to the 5-band risk scheme (Very Low → Critical). Lower FoS → higher risk.

**Step 4 — Noise and missingness.**
Add Gaussian label noise (real geotechnical risk isn't deterministic). Randomly null features (e.g. missing vibration reading) to justify confidence + missing-evidence reporting.

**Step 5 — Sanity checks before training.**
- Rainfall correlates positively with risk.
- Steep slope + high crack density dominates high-risk zones.
If these don't hold, the generator has a bug, not the model.

**Step 6 — Document and version.**
Log generation seed, feature ranges, formula version. Tag every record `synthetic: true`. See [`data/README.md`](../data/README.md) and the `metadata.json` convention in `data/synthetic/v1/`.

---

## D. Validation / Cross-check Sources

| Purpose | Source | Use |
|---|---|---|
| Rainfall→risk patterns | NASA COOLR / GLC | Validate synthetic correlation against real events |
| Feature distributions | ScienceDirect 7,360-slope-unit susceptibility benchmark | Sanity-check distributions and model behavior |
| CV mechanism | Ultralytics Crack-Seg | Train crack detection; NOT a severity claim |

---

*Kaggle rockfall/landslide datasets are small, uncurated, community uploads — inspiration only, not a primary source. State this if asked.*