# Neyveli Cracking: Mechanisms, Geometry, Spatial Model, Severity, Temporal Growth & Interactions

Research artifact for TALUS CRACKS track. Purpose: replace the placeholder slope-instability concept with a physically grounded crack-state model — the remaining state variable connecting the physical environment (rain, geology, blasting, groundwater) to slope instability. Scope: NLC Mine-II sedimentary lignite pits, Cuddalore Group (Upper Miocene) unconsolidated-to-semiconsolidated sediments.

**Grounding rule (user-directed):** cracks are NOT synthesized from one magic dataset. They are built bottom-up from evidence layers (Mechanisms → Geometry → Spatial → Severity → Temporal → Interactions), each tagged with provenance. The crack-state latent is the missing link between the RAIN / TERRAIN / GEOLOGY / BLAST tracks and the slope-failure signal.

---

## 1. CRACK-01: Mechanisms relevant to Neyveli

### 1.1 Tension / crest cracks (stress relief + steep geometry) — PRIMARY

- Rankine active-tension crack depth (USACE EM 1110-2-1902):

  ```
  z_c = (2·c/γ)·tan(45° + φ/2)
  ```

- **Neyveli-relevant computation:** clay c = 196–883 kPa, γ ≈ 20 kN/m³, φ = 0–35°.
  - φ = 0 → `z_c = 2c/γ ≈ 20–88 m`.
  - **Capped by bench scale:** OB benches 18–25 m, mineral bench 6 m → practical crack depth **6–12 m = ⅓–½ bench**.
- Optimal crack depth ≤ **⅓ slope height** (Lu et al. 2022); hard maximum ≤ **½ slope height** (Terzaghi) — beyond this the crack interacts with the toe and the analysis loses meaning.
- Typical crest crack reduces FoS by **~10%**; deeper/steep cases more (Lu et al. 2022).
- Open vertical cracks can reduce critical height by up to **~50%** for a 60° slope (Michalowski & Park, CGJ 2013).
- Tension zone extends **0.3–0.8 × slope height** behind the crest; Teal-pit (gold) case: stress-relief cracks up to **90 m** behind the crest (Gibson 2009).
- **Comparable lignite mines (Greece, sedimentary/lignite analog):**
  - **Tomeas 6 (1994/95):** cracks behind slopes + 0.6 m heaving on the production bench, from stress relief/rebound at 120–165 m depth, 11.5–19.5° coal inclination.
  - **Mavropigi (2010):** tension cracks at the crest from steep convex geometry + low-residual-strength clay + tectonic faults.
  - Movement-rate criterion: **>20 mm/day → failure in 6–12 days** (Leonardos & Terezopoulos 2002).

### 1.2 Desiccation cracks (shrink-swell of high-plasticity clays) — PRIMARY for clay benches

- Neyveli mottled clay has **liquid limit up to 90**, high plasticity — shrink-swell prone.
- Field behavior on SLOPES (BIONICS, Newcastle): cracks are **linearly discrete, not polygonal** (polygonal networks occur on flat ground; slopes develop line-parallel cracks).
- **4-stage cycle:** initiation → expansion → contraction → closure.
- Crack **depth dominates dynamic response** (a shallow wide crack is far less threatening than a deep narrow one).
- Depth ~0.05–0.3 m; spacing ~1–3 m (Hydrology 2023, semiarid field study).
- Cracks **wet/seal under rain, redevelop on drying** → strong seasonal coupling to the RAIN track.

### 1.3 Blast-induced cracking — SECONDARY but Neyveli-specific

- ~30% of overburden blasted (BLAST track); NLC now blasts each OB bench before stripping; 15–22 m benches.
- Blast-induced damage to rock/soil mass **lowers slope stability** — PPV-based damage criteria exist and are scaled by rock-mass strength and slope angle (Savely 1986 mine slopes; GB 6722-2014 China; Xiaowan hydropower field tests).
- Neyveli PPV is the **highest of all mines studied** (NIRM 2005), low-frequency (5–27 Hz, <10 Hz usual) → vibration-driven cracking is plausible near active blast fronts.
- Tag: crack propagation likelihood scales with `PPV / material damage threshold` and blasting proximity.

### 1.4 Seepage / groundwater-induced cracking — PRIMARY at Neyveli

- Neyveli-specific instability drivers (Periyasamy 2019, JGSI):
  - **Water oozing/seeping from OB benches → bench wall failure → slope stability problem** (the documented failure chain).
  - Alluvial clay chocks BWE buckets in wet seasons.
  - Sporadic boulders / hard ferruginous bands damage BWE teeth.
  - Confined aquifer below lignite: **5–8 kg/cm² (490–785 kPa) upward thrust → floor heaving/bursting → flooding**.
- Semi-confined aquifer seepage reduces effective stress on pit walls (GEOLOGY track §3.4) → wet seams + soft zones where cracks nucleate.
- M74 motorway slope (ECSMGE 2019, Jennings): a **tension crack along the crest was the first measurable onset of slope failure**; toe berm was the mitigation — cracks are the early-warning observable, not the final event.

### 1.5 Floor-heave / upward-thrust cracks — pit-floor specific

- Confined aquifer upward thrust (490–785 kPa) on the pit floor → **heave cracks + bottom bulging** (Periyasamy 2019; Tomeas 6 analog: 0.6 m heaving).
- Distinct from crest cracks: located on the **pit floor / lowest benches**, orientation roughly parallel to pit axis, driven by unloading rebound + hydraulic pressure.

---

## 2. CRACK-02: Geometry & ranges

| Attribute | Tension (crest) | Desiccation (clay surface) | Source | Confidence |
|---|---|---|---|---|
| Width | **10–100 mm** | **1–20 mm** | Lit. field studies | Medium |
| Depth | **⅓–½ bench** → Neyveli practical **6–12 m** | **0.05–0.3 m** | USACE; Lu; Hydrology 2023 | High (frac) / Medium (Neyveli cap) |
| Length along crest | **20–200 m** | (surface mesh) | Lit. | Low |
| Segment spacing along crest | **10–50 m** | 1–3 m | Lit. | Low |
| Distance from crest | **0–30 m** (zone 0.3–0.8 × slope height; Teal up to 90 m) | everywhere exposed | Lit.; Gibson 2009 | Medium |
| Orientation | Parallel to crest | Slope-parallel linear | BIONICS | High |

**Interaction constraints (MUST be enforced in generator):**
1. `crack_depth ≤ ⅓–½ slope height` — always check against the bench the crack sits on (18–25 m OB, 6 m mineral).
2. Crack opening ≠ water storage in the simple sense: during rain the crack is **assumed to fill with water** → the water column exerts **hydrostatic pressure on the crack wall** (USACE EM 1110-2-1902). This is the single largest crack–rain coupling term.
3. Severity is a function of the crack's **physical context** (slope angle, material strength, water, blast exposure), not its opening alone.

---

## 3. CRACK-03: Spatial model (attach to mine-engineering geometry layer)

Cracks attach to the **mine-engineering geometry layer** (bench planes, crest lines, pit floor from GEOLOGY §3.3 / TERRAIN Entry 7), never to the raw 30 m DEM slope.

| Crack family | Anchoring layer | Spatial rule | Density driver |
|---|---|---|---|
| Tension (crest) | **Crest lines** of bench geometry (OB 18–25 m benches, mineral 6 m bench) | Segments of length 20–200 m, spaced 10–50 m, **offset 0–30 m from crest, parallel to it** | Slope height & face angle, material weakness (clay > sandstone), steep overall geometry |
| Desiccation | Exposed **clay surfaces** (bench faces, berms, dormant slopes) | Surface mesh of linear cracks, depth 0.05–0.3 m, spacing 1–3 m | LL/plasticity (Neyveli clay LL ≤ 90), sun exposure, drying days since last wetting |
| Blast-induced | **Advancing blast front** on blasted OB benches (15–22 m, 200 mm holes, ~30% of OB) | Within a band behind the active blast front; propagation ∝ PPV/receiver distance | Blasting cadence (`blast_frequency_per_week`), charge per delay, distance |
| Seepage / wet-seam | Semi-confined aquifer contact zones in OB benches | Along seepage faces/soft seams | Rainfall (pore-pressure), pumping drawdown dynamics |
| Floor heave | **Pit floor** and lowest benches | Broad bulging + axial-parallel cracks | Confined aquifer thrust (490–785 kPa), residual overburden load |

Provenance per synthetic crack row: `source_type ∈ {mine_specific, regional_geological, literature, derived}` + `confidence` (same convention as GEOLOGY/BLAST constants).

---

## 4. CRACK-04: Severity model (NORMAL → MINOR → MODERATE → SEVERE → CRITICAL)

**Explicit rule: severity ≠ width alone.** A 20 mm crack in a benign low-slope clay bench is LESS severe than a 10 mm crack on a steep critical slope under rain. Severity is a weighted combination of measurable props:

| Prop | Weight class |
|---|---|
| Depth / bench-height ratio | high |
| Growth rate (mm/day) | high |
| Width | low–medium (context-dependent) |
| Length + segment density | medium |
| Distance from crest (lower = worse) | high |
| Nearby slope angle / face angle | high |
| Material class (clay weakest, sandstone harder) | medium |
| Rainfall state (water-filled crack) | high |
| Blast exposure (PPV) | medium |
| Location (active bench vs reclaimed/dormant) | medium |

Suggested decision surfaces (derived, tunable — thresholds in constants CSV):

```
risk_crack = f( depth_ratio, growth_rate, distance_to_crest, slope_angle, water_filled, material, blast_PPV )
```

- CRITICAL: growth‑rate trend > 20 mm/day (failure in 6–12 days), OR water-filled crack on an actively-mined steep slope, OR crack reaches ½ slope height.
- SEVERE: sustained growth 10–20 mm/day, deep crack, wet, on active bench.
- MODERATE: growth 2–10 mm/day, notable depth, dry or moderate context.
- MINOR: slow growth, shallow/wide-only, benign location.
- NORMAL: stable static crack, no active driver.

The generator exports crack state per zone per day (latent), and the ML-facing fields `crack_severity` + `crack_growth_rate_mm_day` only after ranking by these surfaces.

---

## 5. CRACK-05: Temporal growth model

### 5.1 Growth phases (per crack family)

| Phase | Tension | Desiccation | Blast | Heave |
|---|---|---|---|---|
| Initiation | stress-relief + slope unloading | first drying cycle | blast event exceeds threshold | thrust exceeds resist | 
| Expansion | seasonal rain cycles, creep | continued drying | repeated low-freq PPV | sustained thrust, unloading |
| Stabilization | stress release expended | wet season closure | blast front moves away | equilibrium + dewatering |

### 5.2 Key temporal outputs

- `crack_growth_rate_mm_day` — the ML-facing temporal feature.
- **Movement-rate criterion:** >20 mm/day sustained → failure in 6–12 days (Leonardos & Terezopoulos 2002, lignite context).
- **Desiccation cyclicity:** cracks open on drying, seal on wetting → growth rate is seasonally anti-correlated with rainfall (strong RAIN linkage).
- **Rain coupling:** during rainfall a crack fills with water → hydrostatic wall pressure (USACE) → effective stress drop → transient growth spike even as the surface seals.
- **Blast coupling:** a blast event within the damage band can cause a step increase in existing cracks (propagation), not usually fresh nucleation at distance.

### 5.3 Generator sketch (deferred to GENERATOR v1)

```
CRACK STATE (per zone, per day)
 ├── crack_families_active   ← from mechanism flags + zone geometry (CRACK-01/03)
 ├── crack_geometry           ← sampled ranges (CRACK-02), depth ≤ ⅓–½ bench enforced
 ├── water_filled             ← rainfall state (RAIN track) → hydrostatic pressure term
 ├── growth_mm_day            ← base growth + rain/desiccation/blast impulse (CRACK-05)
 ├── severity                 ← ranked by decision surface (CRACK-04)
 └── export: crack_severity, crack_growth_rate_mm_day
```

---

## 6. CRACK-06: Interaction matrix

| Driver (track) | Effect on cracks | Crack effect back on slope |
|---|---|---|
| **Rain (RAIN)** | Waters & seals desiccation cracks; fills tension cracks → hydrostatic crack-wall pressure (USACE assumption) | Pore pressure + fissure water → reduced FoS, faster growth (Lu ~10% FoS drop at crack presence) |
| **Blast (BLAST)** | Step-growth of existing cracks on PPV exceedance; nucleation near active blast front | Cracked mass = lower effective cohesion → stability loss consistent with BLAST's damage premise |
| **Geology (GEOLOGY)** | Clay benches desiccate (LL≤90); sandstone benches blast-crack; weak clay seams concentrate seepage cracks | Cracks concentrate in precisely the weakest materials → non-uniform stability |
| **Groundwater (GEOLOGY §3.4)** | Seepage faces nucleate wet-seam cracks; confined thrust → floor heave cracks | Both reduce effective stress and mass strength |
| **Terrain geometry (TERRAIN)** | Steep crests (bench 45–75°) host tension cracks; overall pit macro-slope (31°) sets the regional loading | Cracks at crest = early-warning onset of slope failure (M74 case) |

**The crack state is the integrator:** it converts the 4 environment tracks (RAIN, TERRAIN, GEOLOGY, BLAST) into a single time-varying slope-instability state variable that the RF/risk model can consume.

---

## 7. Verification & cross-checks

- **Tension depth vs bench:** φ=0 clay gives z_c = 2c/γ ≈ 20–88 m, but benches are 6–25 m → cracking is **bench-bounded**; practical depth 6–12 m (⅓–½ bench). Self-consistent with Terzaghi/Lu cap. ✅
- **FoS impact:** ~10% reduction for a typical crest crack (Lu 2022) is the conservative FoS-budget line; ≤50% only for steep open cracks (Michalowski) — generator keeps the conservative figure as the default coupling. ✅
- **Movement criterion:** 20 mm/day → 6–12-day failure window matches the Greece lignite analog and the M74 tension-crack-on-set-of-failure experience. ✅
- **Neyveli compatibility:** desiccation (LL≤90 clays), seepage from OB benches, floor heave from 490–785 kPa thrust, and 30%-blasted benches all have documented Neyveli or directly-comparable-lignite evidence — no mechanism is invented. ✅
- **Interface safety:** exported ML fields (severity, growth rate) derive from ranked decision surfaces on measurable props; severity ≠ width. ✅

---

## Sources

- USACE EM 1110-2-1902: Rankine tension-crack depth; crack-fills-with-water assumption (crack-water pressure boundary).
- Lu et al. (2022) — MDPI Applied Sciences 12(24):12687, https://doi.org/10.3390/app122412687 (tension cracks reduce FoS ~10%; optimal crack depth ≤ ⅓ slope height; Yunnan–Tibet highway landslide).
- Terzaghi (via USACE): crack depth ≤ ½ slope height.
- Michalowski & Park, Can. Geotech. J. (2013): open vertical cracks reduce critical height up to ~50% on 60° slopes.
- Gibson (2009): Teal-pit stress-relief cracks up to 90 m behind crest.
- BIONICS / Newcastle, https://eprints.ncl.ac.uk/273344: field desiccation-crack monitoring — linearly discrete cracks on slopes, 4 stages, crack depth dominates dynamic response.
- Hydrology (2023) 10(4):83, https://doi.org/10.3390/hydrology10040083: field desiccation-crack morphology (semiarid): depth 0.05–0.3 m, spacing 1–3 m.
- Periyasamy, N. (2019) — JGSI, https://doi.org/10.1007/s12594-019-1315-5: Neyveli-specific instability drivers (bench seepage → wall failure; alluvial chocks; ferruginous boulders; confined-aquifer heaving/bursting).
- ECSMGE (2019), Jennings: M74 tension crack = onset of slope failure; toe berm mitigation.
- Frontiers in Earth Science (2022) 10:1098630, https://doi.org/10.3389/feart.2022.1098630: blast-induced damage to slope rock masses lowers stability; PPV-based damage criteria (Savely 1986; GB 6722-2014; Xiaowan field tests).
- Leonardos & Terezopoulos (2002): Greece lignite — >20 mm/day movement → failure in 6–12 days; Tomeas 6 (deep stress-relief cracks + 0.6 m heave); Mavropigi (2010) crest tension cracks on steep convex geometry.
- Neyveli inputs consumed from GEOLOGY track (`data/processed/geotech/neyveli_geotech_parameters.csv`) and BLAST track (`data/processed/blasting/neyveli_blast_constants.csv`): clay LL≤90, c=196–883 kPa, γ≈20 kN/m³, benches 6–25 m, blast PF 30%, PPV model.