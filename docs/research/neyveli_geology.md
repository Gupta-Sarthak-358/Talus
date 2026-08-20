# Neyveli Geology & Geotechnical Parameters (Mine-II)

Research artifact for TALUS material/groundwater grounding. Scope: Neyveli Lignite Corporation India Limited (NLCIL) **Mine-II** operations, Cuddalore Group (Upper Miocene) sedimentary basin, Tamil Nadu, India.

Mine-II documented bounds: **11°27′–11°32′ N, 79°27′–79°35′ E** (= 11.45–11.53 N, 79.45–79.58 E). These EXACTLY match the TALUS grid anchor (11.50 N, 79.50 E) used for IMD/ERA5/DEM extraction. Mine-II located to the **east-southeast of Neyveli township**; Mine-I to the west-southwest.

---

## 1. Geological sequence

Establishment: **Cuddalore Group** (Cuddalore Sandstone Formation), Upper Miocene marine-to-deltaic sediments overlying the Archaean basement of the Cauvery basin-margin. All mineable units are **unconsolidated-to-semiconsolidated sediments**, not hard rock.

### 1.1 Lithological section (top → bottom)

From overburden drill data (NLC EC documentation, readkong mirror; Mine-II):

| Unit | Typical thickness | Notes | TALUS material class |
|---|---|---|---|
| Topsoil / loam | 0–2 m | Red lateritic soil cap | `lateritic_soil` |
| Argillaceous sandstone | 5–10 m | Sandy clay, part of OB | `sandstone` / `clayey_sandstone` |
| Mottled clay | 5–12 m | Plastic, colorful clays | `clay` |
| Argillaceous sandstone | 10–20 m | Main OB sand unit | `sandstone` |
| Clay | 2–5 m | Carbonaceous clay band | `carbonaceous_clay` |
| Sand (semi-confined aquifer) | 5–15 m | **Above lignite** | `aquifer_sand` |
| **Lignite** | 10–25 m (Mine-I 10–25 m, Mine-II 4–24 m typical) | **Target seam** | `lignite` |
| Clay | 2–3 m | Aquitard below seam | `clay` |
| Sand (confined aquifer) | 10–40 m | **Below lignite**, high pressure | `aquifer_sand` |

### 1.2 Key engineering dimensions (NLC EC doc)

- **Overburden thickness: 45–112 m** — must be removed to expose lignite.
- Unconsolidated sandstone mixed with clay immediately above lignite: **3–15 m** thick.
- **Lignite seam: 4–24 m** (Mine-II).
- Stripping ratio: **5.2 m³ : 1 t** (Mine-II).
- Mine-II output: 15 MTPA (planned), pit-carried an 8.5–13 km long × ~2 km wide exposure at maturity (per NCB/industrial seminars).
- Ground elevation range: **+15 to +27 m MSL** — matches the TALUS DEM plain median (~+15 m).

### 1.3 Mine-II layout (for spatial grounding)

- Mines identified: Mine-I (W-SW), Mine-II (E-SE) of Neyveli township.
- Mined-out backfilled areas and active pit to the east-southeast align with our site's slightly-tiered band (the pit rim on DEM).
- Mine-II is the active source closest to the grid anchor.

---

## 2. Material classes (TALUS mapping)

| TALUS class | Neyveli equivalent | Role in stability | Source type |
|---|---|---|---|
| `lateritic_soil` | Lateritic topsoil/loam | Upper OB cap, crest loading | mine-specific |
| `clayey_sandstone` / `sandstone` | Argillaceous sandstone | Dominant OB unit; ~50–55% clay; often needs blasting when hard | mine-specific |
| `clay` | Mottled clay | Weak OB unit, plastic (LL up to 90) | mine-specific |
| `carbonaceous_clay` | Carbonaceous clay band | Intercalations near seam | mine-specific |
| `aquifer_sand` | Semi-confined (above lignite) + confined (below lignite) sands | Water inflow, pore-pressure drive, seepage into OB benches | mine-specific |
| `lignite` | Lignite seam | Mineral; hard w/ embedded soft layers; floor of OB slopes | mine-specific |
| `overburden_mixed` | OB mix (clay + sand) | Generic backfill/dumped material | mine-specific |

Groundwater relevance: **three aquifer systems** — (i) unconfined, (ii) semi-confined above lignite, (iii) confined below lignite. Confined systems carry **upward thrust 5–8 kg/cm² (≈ 490–785 kPa)** and drive both floor **heaving/bursting** and pit-wall pore pressure. NLC pumps on the order of **8–10 m³ of water per tonne** of lignite mined.

---

## 3. Geotechnical parameters

### 3.1 Source table (NLCIL, "Neyveli Lignite Corporation: Problems and Needs", Indo-U.S. Working Group / fossil.energy.gov archival; also NLC geotech engineering literature)

Original (field/test) units retained; SI conversion provided. **CAUTION:** these are almost certainly **undrained/total-stress (or field) parameters** — the cohesion/liquidity values are far too high for effective-stress (c′) soil behavior. They are appropriate for READILY DEFORMABLE mass-scale stability screening (factor against shear on pre-existing weak layers), NOT for drained effective-stress design without re-interpretation. Flag `parameter_regime = total/undrained` in consumption code.

| Material | Density (t/m³) | Cohesion (kg/cm²) | φ (deg) | UCS (kg/cm²) | k (cm/s) |
|---|---:|---:|---:|---:|---:|
| Lateritic soil | 1.98–2.10 | 6–9 | 18–30 | 12–18 | 1E-4 – 1E-5 |
| Variegated sandy clay | 1.90–2.30 | 2.5–10 | 15–35 | 5–20 | 1E-5 – 1E-7 |
| Clay (mottled) | 2.00–2.30 | 2.0–9.0 | n.r. | 4–20 | n.r. |
| Sandstone (argillaceous) | 2.00–2.40 | 0.3–1.6 (OCR-garbled; NLC alt. source 0.55) | 25–40 | 6–32 | 1E-4 – 1E-6 |
| **Lignite** | ~1.30–1.45 (lit.) | n.r. | n.r. | ~0.5–2 (unconfined, soft) | low (lit.) |

* Densities for clays/sand come with S.G. ~2.5–2.65 for granular fraction.
* Swell factors (dry/wet): lateritic 1.5/2.0; var. sandy clay 1.4–1.6/2.0–2.2; clay 1.5–1.6/2.2–2.4; sandstone 1.3–1.5/1.7–2.1. (Useful for backfill/bulking in settlement & hauling.)

### 3.2 Normalized tables

Files: `data/processed/geotech/neyveli_geotech_parameters.csv`.

Primary SI conversions (1 kg/cm² = 98.0665 kPa; 1 t/m³ = 1000 kg/m³; 1 cm/s = 1E-2 m/s):

| Material | ρ (kg/m³) | c (kPa) | φ (deg) | UCS (kPa) | k (m/s) |
|---|---:|---:|---:|---:|---:|
| Lateritic soil | 1980–2100 | 588–883 | 18–30 | 1177–1765 | 1E-6 – 1E-7 |
| Variegated sandy clay | 1900–2300 | 245–981 | 15–35 | 490–1961 | 1E-7 – 1E-9 |
| Clay (mottled) | 2000–2300 | 196–883 | n.r. | 392–1961 | n.r. |
| Sandstone (argillaceous) | 2000–2400 | 29–157 (alt: ~54) | 25–40 | 588–3138 | 1E-6 – 1E-8 |
| Lignite | 1300–1450 | n.r. | n.r. | 49–196 | low (lit.) |

### 3.3 Bench & slope geometry (mine engineering — separate from DEM macro-slope)

From Coal Age / NLC mining systems (BWE operations), and the 2022 Approved Mining Plan (EC-Portal PDF; user-provided; I could not fetch this PDF directly — **grep-level verification pending**):

| Parameter | Value | Source | Confidence |
|---|---|---|---|
| OB bench height (top 4 benches) | 25 m each | Coal Age / NLC | High |
| Lowest OB bench height | 18 m | Coal Age / NLC | High |
| Lignite mining bench height | 18 m | Coal Age / NLC | High |
| **Mineral (lignite) bench height** | **6 m** | 2022 Approved Mining Plan | Medium (user-provided) |
| **Mineral bench width** | **6 m** | 2022 Approved Mining Plan | Medium (user-provided) |
| **Mineral bench slope angle** | **75°** | 2022 Approved Mining Plan | Medium (user-provided) |
| **Overall pit slope angle** | **45°** | 2022 Approved Mining Plan | Medium (user-provided) |
| Backfilled dump overall slope | 26–28° (angle of repose) | NLC mining seminar (Scribd mirror) | Medium |
| DEM-resolved macro slope (pit focus) | ~31° max | Copernicus GLO-30 | High (different scale) |

**Interpretation for TALUS:** DEM (30 m) resolves the pit depression and the wall macro-slope (~31°) but cannot resolve bench faces (45–75° at 6–25 m height). The generator must treat bench geometry as a **separate, mine-engineering parameter layer** keyed to the pit focus — not burst from DEM slope.

### 3.4 Groundwater model input

- Aquifer architecture: 3 systems (unconfined / semi-confined above lignite / confined below lignite).
- Confined upward thrust: **5–8 kg/cm² ≈ 490–785 kPa** (source of heaving/bursting of pit floor).
- Pumping ratio: **8–10 m³ water per tonne lignite**.
- Slope instability is driven by **semi-confined aquifer seepage into OB benches**, reducing effective stress on pit walls.

---

## 4. Modeling decision

> TALUS represents Neyveli geology using material classes derived from Mine-II geological documentation. Geotechnical parameters are sampled from **documented Neyveli-specific measured ranges** where available; where Neyveli-specific measurements are unavailable, **literature values are used and tagged as such** (source_type column). All parameters retain their **original units in provenance** and are converted to SI only at the consumption interface; no parameter is silently converted between stress regimes (drained vs undrained) without a provenance flag.

### 4.1 Decision rules consumed by generator (prototype_v1+)

1. `rock_type` / material classes sampled from the lithological section (Section 1), not an arbitrary 4-row rock table.
2. Each synthetic material row carries `source_type ∈ {mine_specific, literature, regional_geology}` and `confidence`.
3. Density/cohesion/φ/UCS sampled within documented Neyveli ranges (Section 3.2).
4. **parameter_regime flag** = `total_undrained` for the NLC soil-property table; effective-stress conversions ONLY via documented relationships (e.g., Mohr–Coulomb via measured c′/φ′ when available); never c = UCS/2 blindly.
5. Bench/slope geometry and aquifer architecture supplied as Neyveli-fixed engineering inputs from Section 3.3–3.4, **not** inferred from DEM.
6. Lignite and aquifer-sand rows carry `source_type=literature` with explicit confidence=low/medium until mine-confirmed values are retrieved.

---

## 5. Cross-checks & consistency

- Mine-II bounds (11°27′–11°32′ N, 79°27′–79°35′ E) match the TALUS grid anchor (11.50 N, 79.50 E). ✅
- Ground elevation +15–27 m MSL matches DEM plain median (~+15 m). ✅
- Rainfall at mine: 860–2070 mm/yr, avg ≈ 1200 mm — cross-checks our grid-point mean (1315 mm, 1901–2024). ✅
- **Blasting** (feeds future BLAST track): ~30% of overburden requires blasting (Surface/Top benches, hard Cuddalore sandstone); ~7,300 mtpy explosives, predominantly **site-mixed emulsion**; DGMS (Tech)(S&T) Circular 7 of 1997 cited for blast-vibration limits. PPV grounding is the next task.

---

## Sources

- NLCIL Environment Clearance, Mine-II / readkong mirror: `readkong` — "NLC India Limited Mine-Ii" (lithological section, OB 45–112 m, aquifer design, +15 to +27 m MSL).
- NLC India Ltd. — Environmental Clearance (readkong 6900370): Mine-II/Mine-I details, stripping ratio, lignite seam.
- NLCIL "Problems and Needs" — Indo-U.S. Working Group, fossil.energy.gov archival (`cwg_june07_anandan.pdf` via yumpu): **geotech parameter table** (Section 3.1), swell factors, S.G.
- Coal Age / "Modern Mining" — BWE systems, bench heights (25 m ×4 + 18 m), lignite 18 m bench.
- Periyasamy, N. (2019) — *Groundwater hydrology and slope stability at Neyveli*, JGSI/IWSM (via Scribd/studylib mirrors): three aquifer systems, 5–8 kg/cm² thrust, water:lignite pumping ratio.
- 2022 Approved Mining Plan (EC-Portal PDF, user-provided): mineral bench 6 m / 75°, overall slope 45° — **PDF not directly retrieved; marked Medium confidence, to re-verify**.
- Neyveli mining seminar (Scribd mirror): backfilled dump slopes 26–28°.
- Blacksmith Institute (2012) Neyveli lignite case study: rainfall 860–2070 mm (avg 1200), cyclonic belt, water table ~aquifer depth, GOI court-monitored rendering.