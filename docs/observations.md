# Talus — Member 2 Observations Log

Running record of data-grounding and rainfall-model findings. Append as we go.

---

## 1. Data source (locked)

- **Dataset:** IMD 0.25° × 0.25° daily gridded rainfall (mm/day), NetCDF (`ind<year>_rfp25.nc`).
- **File structure (verified):** variable `RAINFALL`, dims `(TIME, LATITUDE, LONGITUDE)`, `float32`, mm/day.
  - `TIME` datetime64, 365/366 days.
  - `LATITUDE` 6.5 → 38.5°N (129 pts, step 0.25).
  - `LONGITUDE` 66.5 → 100.0°E (135 pts, step 0.25).
  - Expected sizes (integrity check): non-leap 25,431,832 B; leap 25,501,500 B.
- **Spatial anchor:** Neyveli Mine-II → grid point exactly **11.50°N, 79.50°E** = `RAINFALL[:, 20, 52]`, lies inside the documented mine bounds. No interpolation needed.
- **Provenance:** IMD NetCDF → 11.50°N,79.50°E → daily obs → rolling accumulation.

## 2. Data integrity notes

- 2000–2024 extraction: 9,132 obs, 0 missing, 0 duplicates, 0 negatives, confirming free of download damage after repairs.
- Downloader skips existing files without re-checking size → corrupt partials (32 KB–19 MB) persist. Rule: **verify size vs leap/non-leap before trusting a file.** Repaired/deleted so far: 2004 (re-downloaded), 1968, 1990, 1999 (deleted for re-run). 2024 differs by 32 B but is benign (opens cleanly).

## 3. Contemporary analysis (2000–2024)

- Annual mean ≈ **1,360 mm/yr** (total 34,001 mm), consistent with documented Neyveli ~1,200–1,500 mm.
- **Zero-rain days: 71.96%**; wet days 28.04% (2,561).
- All-days: P90 9.1, P95 21.1, P99 62.8, P99.5 92.3, P99.9 195.4, max 327.3 mm.
- Wet-days: P50 4.7, P90 34.0, P95 52.4, P99 118.7, P99.5 152.7, P99.9 225.9, max 327.3 mm.
- Rolling: 3-day max 536.7 mm (P99 166.3); **7-day max 772.9 mm (P99 323.5)**.
- **Seasonality dominates:** Oct–Dec = 64% of total (21,769 / 34,001 mm). November peak: mean 14.8 mm/day, wet freq 61%. Jun–Sep moderate (SW monsoon); Jan–Mar dry.
- Extreme days concentrate in Oct–Dec (17 of top 20; 13 in November).
- Interannual spread huge: **min 277 mm (2002), max 2,387 mm (2021)**, std 522. 2011/2012 anomaly: 221/212 wet days yet ~1,300–1,470 mm (many weak La Niña drizzle days).
- Scripts: `ml/data_generation/inspect_imd.py`, `extract_neyveli_rainfall.py`, `analyze_neyveli_rainfall.py` (supports `--start/--end`).
- Outputs: `data/processed/imd/analysis/` — `summary_2000_2024.json`, `annual_stats_2000_2024.csv`, `monthly_stats_2000_2024.csv`, `extremes_2000_2024.csv`, `plots/`.

## 4. Prototype v0 (baseline sampler) — VERDICT: validated as baseline, not final

- **Architecture:** monthly empirical wet-day pools + monthly wet/dry two-state Markov chain + empirical intensity resampling (with replacement) + rolling accumulation.
- **Gets right (matches historical):** zero-rain freq (71.96 → ~71.6%), daily P90/P95/P99, wet-day intensity curve, monthly totals, monthly wet frequency, seasonal structure.
- **Fails (known limitations):**
  - **L1 — multi-day accumulation:** 7-day P99 233.3 vs 323.5; 7-day max ~517 vs 772.9. Independent intensity draws break storm persistence. Real storms are sequences like 120/210/150/80; sampler can emit 120/5/60/3.
  - **L2 — interannual variability:** synthetic annual range ~857–2,336 vs historical 277–2,387. A stationary model collapses to "average year"; real climate has genuine wet/dry years.
  - **L3 — no extrapolation:** empirical resampling reproduces observed support exactly (including 327.3) but never exceeds the historical max. Feature of the method, not skill.
- **Do not modify v0.** It is the frozen baseline (seeds 42–46).
- Script: `ml/data_generation/prototype_rainfall_sampler.py`. Outputs: `data/processed/imd/prototype_v0/`.

## 5. Phase 2 direction (not yet built)

- Next: verify extreme events against raw NetCDF → then full 1901–2024 analysis → compare (zero %, seasonality, tail P99–max, annual range). If annual spread persists over 124 yr → year-scale conditioning is a real requirement. Storm persistence handled separately (storm/event templates, e.g. Nov 2008).
- Question answered by the long record: does 2000–2024 represent the rainfall regime (esp. tail) we want to reproduce?

## 6. Extreme events (VERIFIED against raw NetCDF)

Provenance confirmed: derived CSV values match raw NetCDF `RAINFALL[:, 20, 52]` exactly.

- **2015-11-10:** 1d 327.30, 3d 466.42, 7d 525.88 mm — confirmed in `ind2015_rfp25.nc`.
  - Storm context: … 124.1 (11-09) → **327.3** → 0/0/0 → 19.4/81.1/76.1. Middle of an active NE-monsoon period (Chennai-region Nov 2015 flooding event).
- **2008-11-28:** 1d 209.42, 3d 536.71, 7d 772.89 mm — confirmed in `ind2008_rfp25.nc`.
  - Storm context: sustained multi-day episode — 22–28 Nov daily: 51.5 / 22.3 / 92.3 / 70.0 / 215.7 / 111.6 / 209.4 mm. Six of seven days ≥ 70 mm (two ≥ 209 mm). This is the true "storm persistence" template.
- Both are prime stress-event templates for the Talus demo. They show two different failure modes: short sharp spike (2015) vs sustained week-long battering (2008).

## 7. Decision ledger (structured)

Format: Observation → Evidence → Interpretation → Decision → Version affected.

### Entry 1 — Two-process rainfall
- **Observation:** 71.96% of days are zero-rain; 28.04% wet.
- **Evidence:** 2000–2024 IMD series, 9,132 obs.
- **Interpretation:** Rainfall is a dry/wet mixture; a single distribution over all days is wrong.
- **Decision:** Two-stage model: occurrence (dry/wet) then intensity (wet days only).
- **Version:** foundational → prototype_v0.

### Entry 2 — Seasonality is dominant
- **Observation:** Oct–Dec = 64% of total rainfall; Nov mean daily 14.8 mm, wet freq 61%.
- **Evidence:** monthly_stats_2000_2024.csv.
- **Interpretation:** Global (annual) sampling erases the regime; per-month conditioning is required.
- **Decision:** Monthly occurrence model + monthly intensity pools.
- **Version:** prototype_v0.

### Entry 3 — v0 limitation L1 (storm persistence)
- **Observation:** synthetic 7-day P99 ≈ 233 mm / max ≈ 517 mm vs historical 324 / 773 mm.
- **Evidence:** prototype_v0 summary vs summary_2000_2024.json; verified 2008-11-28 sustained-storm sequence (6 of 7 days ≥ 70 mm).
- **Interpretation:** v0 reproduces the marginal wet-day distribution but not the correlation of high intensity across consecutive wet days. Independent intensity draws break storms apart.
- **Decision:** Investigate event-conditioned / storm persistence (wet-spell intensity correlation, event templates).
- **Version:** prototype_v0 → informs prototype_v1.

### Entry 4 — v0 limitation L2 (interannual variability)
- **Observation:** synthetic annual range ≈ 857–2,336 mm vs historical 277–2,387 mm.
- **Evidence:** prototype_v0 seeds 42–46 vs annual_stats_2000_2024.csv.
- **Interpretation:** Stationary per-month Markov collapses to "average year"; real climate has distinct wet and dry years.
- **Decision:** Candidate year-scale / climate-conditioning component (CONFIRM NEED only after 1901–2024 comparison).
- **Version:** prototype_v0 → informs prototype_v1.

### Entry 5 — v0 limitation L3 (no extrapolation)
- **Observation:** synthetic max can equal historical max (327.3) but never exceeds it.
- **Evidence:** empirical resampling construction of v0.
- **Interpretation:** Empirical sampling preserves observed support; it is not extrapolative. This is a property of the method, not prediction skill. Honest labeling required when discussing "risk."
- **Decision:** Document as method property; consider tail-modeling separately if extrapolation is desired.
- **Version:** all empirical variants.

### Entry 6 — Verified stress events
- **Observation:** 2015-11-10 (327.3 mm 1d, spike) and 2008-11-28 (772.9 mm 7d, persistent storm) reproduce exactly from raw NetCDF.
- **Evidence:** verify_extreme_events.py read from ind2015/ind2008 directly; matches derived CSV.
- **Interpretation:** Full provenance chain confirmed; both are usable historical stress templates (different failure modes).
- **Decision:** Keep both as candidate demo templates; not asserted as generic Neyveli behavior.
- **Version:** prototype_v1 stress-event module candidate.

## 8. Current checkpoint (frozen)

- **Locked:** data source, 11.50N 79.50E anchor, 2000–2024 series, prototype_v0 baseline + L1/L2/L3, verified events, extraction/analysis parameterized by year range.
- **In progress:** 1901–1954 (and re-verify repaired 1955–1999) download. Status: 1955–2024 present/valid as of last check; 1955 was re-downloading.
- **Do NOT modify** prototype_v0 while the historical comparison is pending.
- **Next experiment (once files complete):**
  1. `python ml/data_generation/extract_neyveli_rainfall.py --start 1901 --end 2024`
  2. `python ml/data_generation/analyze_neyveli_rainfall.py --input data/processed/imd/neyveli_rainfall_1901_2024.csv --start 1901 --end 2024`
  3. Compare four dimensions: zero %, seasonality (Oct–Dec/Nov dominance), tail (daily & 7-day P99/P99.9/max), interannual spread (incl. annual quantile distribution P05..P95, mean/std/min/max, and year counts below/above thresholds).

## 9. Terrain / DEM (Copernicus GLO-30, 30 m)

- **Source:** Copernicus GLO-30 DEM (ESA; 30 m, EPSG:4326), tile `Copernicus_DSM_COG_10_N11_00_E079_00_DEM.tif` (39.2 MB) from AWS open data s3 (public, no auth). Download repaired once (resume handled truncation). File: `data/raw/dem/Copernicus_DSM_GLO30_N11_E079.tif`, bounds 79.0–80.0°E, 11.0–12.0°N.
- **Tools:** `rasterio` (gef...) — script `ml/data_generation/compute_neyveli_terrain.py`; outputs `data/processed/terrain/` (clipped GeoTIFFs, maps, `terrain_summary.json`).

### Context area (11.30–11.70°N, 79.35–79.70°E; ~40×35 km)
- Elevation −97.4 → +172.0 m; mean 34.7, median 25.2 m.
- Slope mean 1.41°, median 0.86°, P90 3.0°, P95 4.2°, P99 9.3°, max 37.4°; only 3.4% of area >5°, 0.9% >10°.
- Flat coastal plain with a distinct pit depression and a low western ridge.

### Mine focus (documented bounds 11.45–11.53°N, 79.45–79.58°E)
- Elevation **−97.4 → +46.7 m**; mean 11.7, median 15.4 m.
- Slope mean 1.54°, median 0.54°, P90 3.5°, P95 6.5°, **P99 16.6°, P99.9 25.0°, max 31.3°**; 6.7% >5°, 2.8% >10°, 0.5% >20°, none >45°.
- **Pit detected:** 8.2% of focus (≈10.5 km²) below sea level; floor ≈ −97 m. The negative-elevation depression is the open-pit excavation — the DEM resolves the pit, not the benches.
- Local relief (3×3 cell, ≈90 m window): mean 2.3 m, P95 9.4 m.

### Entry 7 — Regional terrain ≠ mine bench geometry (CONFIRMED)
- **Observation:** DEM max slope in the mine focus is ~31° (P99.9 25°); essentially no area above 45°.
- **Evidence:** Copernicus GLO-30 statistics above.
- **Interpretation:** 30 m regional DEM resolves the pit depression (to −97 m) but NOT bench-scale geometry (10–30 m benches, 45–70° faces). Our original 45–70° bench assumptions must NOT be sourced from the DEM.
- **Decision:** Split terrain grounding: DEM → regional terrain context (mostly ≤10°, pit walls to ~30°); mine-design/geotechnical literature → bench geometry (45–70° faces, bench heights). Synthetic `slope_angle_deg`/`slope_height_m` should combine both, tagged by provenance.
- **Version:** terrain generator (informs prototype_v1).

## 10. Full-record comparison (1901–2024 vs 2000–2024) — COMPLETE

- Extraction 1901–2024: **45,291 obs** (31 leap + 93 common years), 0 missing, 0 duplicates. All 124 files validated (only benign 32-byte size variants: 1901, 2024).
- Analysis: `summary_1901_2024.json`, `annual_stats_1901_2024.csv`, `monthly_stats_1901_2024.csv`, `extremes_1901_2024.csv`, plots. Comparison: `compare_periods.py`, `compare_seasonality.py`.

### Dimension 1 — zero inflation (REPRESENTATIVE)
- 2000–24: 71.96% dry | 1901–24: **73.18%** dry. Contemporary ~1.2 pp wetter; essentially representative.

### Dimension 2 — seasonality (REPRESENTATIVE, one subtle shift)
- Oct–Dec share: 64.0% (25y) vs **63.0%** (124y). November dominance confirmed over 124 yr (Nov = 29% of annual total; mean 12.7 mm/d; wet freq 53.8%).
- Subtle shift: recent Nov wet-freq 61% vs 54% long-term (mean 14.8 vs 12.7) → recent decades concentrate rainfall more in Nov/Dec; long-term September wetter (3.84 vs 2.91).

### Dimension 3 — tail (daily REPRESENTATIVE; multi-day NOT)
- Daily P99 62.8 vs **64.8**; P99.5 92.3 vs 90.4; wet-day P99 118.7 vs 116.3 — all essentially equal.
- Daily max 327.3 (2015) vs **332.9 (1931-04-14 — April, pre-monsoon)**; also 1943-05-18 314.5 (May).
- **7-day max 772.9 (2008) vs 937.9 (1902-12)**; 3-day max 536.7 vs 616.3. Contemporary UNDERESTIMATES the extreme multi-day tail.
- New stress templates from the record: **Dec 1902 (7d 937.9; 3d 616.3; daily 297.6)**, **Apr 1931 (1d 332.9)**, **May 1943 (1d 314.5)**, **Dec 1996 (7d 700.7)**, plus 1908-10-23 (1d 284), 1941-12-03 (1d 276).

### Dimension 4 — interannual (REAL over 124 yr; contemporary MORE variable)
- 124-yr annual min **276.9 (2002)** and max **2386.6 (2021)** — BOTH inside 2000–24. The 25-yr window already contains the driest and wettest year of the century+.
- But full-record annual distribution is tighter: std **409** vs 522; P05 **700** vs 317; P10 838 vs 427; median 1282 vs 1419; mean 1315 vs 1360.
- Severe-drought (<750 mm) years: **7.3%** over 124 yr vs **16%** over 25 yr → the 2001–03+2016 cluster makes the contemporary window unusually drought-prone.

### Entry 8 — Contemporary representativeness (ANSWERED)
- **Observation:** 2000–24 and 1901–24 agree on wet/dry frequency, seasonality (Oct–Dec ~63–64%), and daily percentiles through P99.5, but diverge on the extreme multi-day tail (7-day max 773 vs 938) and annual spread (std 522 vs 409).
- **Evidence:** summary JSONs both periods (see above).
- **Interpretation:** 2000–24 is representative of NORMAL Neyveli behavior and daily-tail up to ~P99.5, but (a) it misses the largest historical multi-day events (Dec 1902 938 mm/7d) and (b) it over-weights severe drought years.
- **Decision:** prototype_v1 components: (1) year-scale conditioning calibrated to the **124-yr annual distribution** (P05 700, P25 1055, median 1282, P75 1584, mean 1315, std 409), not the 25-yr one; (2) extreme-tail treatment using **historical event templates** (1902, 1931, 1943, 2008, 2015) layered onto seasonal empirical sampling; (3) keep 2000–24 as the contemporary "normal" reference.
- **Version:** prototype_v1 design input.

## 12. Blasting grounding (Mine-II) - COMPLETE

- Research artifact: `docs/research/neyveli_blasting.md`; constants: `data/processed/blasting/neyveli_blast_constants.csv` (52 rows / 6 domains).

### BLAST status
- **BLAST-01 Operational grounding (DONE, mostly):** 30% OB blasted (Surface+Top benches, hard Cuddalore sandstone); NLC now blasts EVERY bench before stripping; ~7,300 mtpy site-mixed emulsion; 200 mm holes, 15-22 m benches, electronic+NONEL, bulk delivery. Blast frequency NOT directly documented -> DERIVED 14-28 blasts/wk (broad prior). Powder factor DERIVED ~0.31 kg/m3 (=7300 t / (0.30 x 78 M m3)) - matches NIRM 'low specific charge' mechanism.
- **BLAST-02 PPV model (LOCKED):** PPV = 858.90 x (D/sqrt(W))^(-1.58), r=0.86, 22 blasts/68 obs (84 sets Mine I+II regression), freq 5-27 Hz (<10 Hz usually). Highest PPV of all sites studied (low specific charge + wet ground). Purpose: loosen for BWE, no fragmentation. Cross-era validation: at 1994-recommended SD=14.6 m/sqrt(kg) the model gives 12.4 mm/s = the 12.5 mm/s 1994 safe level.
- **BLAST-03 Frequency model (PARTLY):** left-skewed 5-27 Hz, P(<8Hz)~0.45; bins <8/8-25/>25 Hz (45/50/5%); residential natural freq 4-24 Hz resonance overlap.
- **BLAST-04 DGMS 7/1997 (LOCKED, stored separately):** full 2-category x 3-type x 3-band table; 5/10/15 domestic, 10/20/25 industrial, 2/5/10 sensitive (Cat A); 10/15/25 and 15/25/50 (Cat B). NOT used as risk label.
- **BLAST-05 Generator (designed, waits for GENERATOR):** latent event model (blast_occurs, charge_per_delay, distance, frequency, ppv_raw, ppv_observed, blast_disturbance) -> exports schema-preserving blast_frequency_per_week + blast_vibration_ppv_mms. Disturbance = f(ppv, freq, distance, receiver zone) not merely ppv threshold.

### Entry 11 - PPV is a physical model now
- **Observation:** Neyveli has a published, site-fitted attenuation relationship (NIRM 2005) instead of a generic 2-20 mm/s uniform draw.
- **Evidence:** NIRM MT/134/02 Table 2.1 + Fig 2.8/2.9; cross-validated by 1994 NIRM/NLC Master Plan study (12.5 mm/s safe level, SD recommendations 14.6/25 m/sqrt(kg)).
- **Interpretation:** PPV must be DRAWN from scratch per blast event from (charge-per-delay, distance), THEN scattered along the NIRM residual structure (r=0.86).
- **Decision:** Lock K=858.90, b=1.58, freq 5-27 Hz in constants file; generator samples W ~100-600 kg (mode 300), D from synthetic geometry; export observed PPV at nearest exposed structure.
- **Version:** prototype_v1 design input.

### Entry 12 - Blast frequency is a production-derived latent, not NIRM's 22 blasts
- **Observation:** 22 blasts / 68 observations (NIRM 2005) and 84 regression sets are MONITORING samples, not an operational schedule.
- **Evidence:** NLC/Coal Age production data (OB 78 M m3/yr, 30% blasted, 7,300 mtpy).
- **Interpretation:** weekly blast count must be derived from production throughput + charge-per-blast, with a wide prior (14-28/wk), NOT calibrated to NIRM's sample counts.
- **Decision:** Weekly Poisson rate latent with broad prior; treat as tunable in generator.
- **Version:** prototype_v1 design input.

## 11. Geology / geotechnical grounding (Mine-II) - COMPLETE

- Research artifact: `docs/research/neyveli_geology.md`; normalized parameter table: `data/processed/geotech/neyveli_geotech_parameters.csv` (9 rows, provenance + confidence per row).

### Verified (multi-source)
- **Mine-II bounds 11�16�»27'�16'33.1" N, 79�16�»27'�16'33.1" E (11.45-11.53 N, 79.45-79.58 E) EXACTLY match our grid anchor** 11.50 N, 79.50 E.
- **Cuddalore Group (Upper Miocene) sediments** - unconsolidated-to-semiconsolidated; NOT hard rock. Five mineable units: lateritic soil, argillaceous sandstone (dominant), mottled/carbonaceous clay, aquifers, lignite.
- **Overburden 45-112 m**; seam 4-24 m (Mine-II); stripping ratio 5.2:1; Mine-II 15 MTPA; ground +15 to +27 m MSL (matches DEM plain).
- **Geotech table (NLC "Problems and Needs", Indo-US WG):** laterite c 6-9 kg/cm2, phi 18-30, UCS 12-18, k 1E-4-1E-5; var. sandy clay 2.5-10, phi 15-35, UCS 5-20, k 1E-5-1E-7; clay 2-9; sandstone 0.3-1.6 (OCR-garbled; alt 0.55), phi 25-40, UCS 6-32. Repeated across independent mirrors - HIGH confidence.
- **Aquifer:** 3 systems; confined upward thrust **5-8 kg/cm2 (490-785 kPa)** drives floor heaving/bursting; NLC pumps ~8-10 m3 water per tonne lignite.
- **Bench geometry (mine design):** OB benches 25 m x4 + 18 m, lignite 18 m (Coal Age/NLC). 2022 Approved Mining Plan: mineral bench 6 m/75 deg, overall pit slope 45 deg - MEDIUM confidence (source PDF user-provided; direct fetch failed).
- **Backfilled dump slopes 26-28 deg** (angle of repose) - NLC seminar.
- **Rainfall at mine: 860-2070 mm, avg ~1200 mm** - cross-checks our 1315 mm grid mean (use case notes).
- Blast grounding for BLAST track: ~30% of OB blasted (Surface/Top benches, hard Cuddalore sandstone); ~7,300 mtpy explosives, site-mixed emulsion; DGMS (Tech)(S&T) Circular 7 of 1997 on blast vibration.

### Entry 9 - Four-rock table is dead
- **Observation:** Neyveli is Cuddalore Group sediments (lateritic soil, argillaceous sandstone, mottled clay, carbonaceous clay, aquifer sands, lignite) - not a hard-rock 4-class lithology.
- **Evidence:** NLC Mine-II lithological section, geotech soil tables (see above).
- **Interpretation:** Material classes must be sedimentologic (8 classes in the CSV), each with provenance and parameter regime.
- **Decision:** Generator samples material class from the lithological proportions; parameter regime **total/undrained** flagged per row; SI conversion only at consumption, never cross-regime silently.
- **Version:** prototype_v1 design input.

### Entry 10 - Bench geometry is mine-design, not DEM
- **Observation:** DEM max slope ~31 deg in focus; mine-design benches are 6-25 m tall at 45-75 deg faces. DEM cannot resolve benches.
- **Evidence:** GLO-30 stats (Entry 7) vs Coal Age/NLC bench table + Approved Mining Plan.
- **Interpretation:** slope_angle_deg/slope_height_m must be built from TWO provenance layers: DEM regional context + mine-design bench layer (fixed Neyveli inputs), tagged by source_type.
- **Decision:** Keep the pit-macro slope from DEM; inject bench-scale geometry as a fixed engineering-parameter layer for the mine focus.
- **Version:** prototype_v1 design input.

## 13. Cracking / slope-instability state (Neyveli) - COMPLETE

- Research artifact: `docs/research/neyveli_cracks.md`; constants: `data/processed/cracks/neyveli_crack_constants.csv` (bucket constants for geometry, formulas, temporal, severity, mechanism flags, Neyveli inputs).
- The crack-state is the missing integrator: it converts the 4 environment tracks (RAIN, TERRAIN, GEOLOGY, BLAST) into a single time-varying slope-instability state variable the RF/risk model consumes.

### CRACK status
- **CRACK-01 Mechanisms (LOCKED):** (1) tension/crest cracks - Rankine zc=(2c/gamma)tan(45+phi/2); phi=0 clay gives 20-88 m but bench-bounded -> practical 6-12 m (1/3-1/2 bench); FoS -10% typical (Lu 2022), open-crack critical-height -50% on 60 deg (Michalowski); tension zone 0.3-0.8x slope height (Teal up to 90 m); (2) desiccation - Neyveli clay LL<=90, linearly discrete (not polygonal) on slopes, 4 stages (initiation/expansion/contraction/closure), depth dominates response, 0.05-0.3 m deep, 1-3 m spacing, seals on rain/redevelops on dry; (3) blast-induced - 30% OB blasted, PPV-damage criteria (Savely 1986, GB 6722-2014, Xiaowan); (4) seepage - water oozing from OB benches -> bench wall failure (Periyasamy 2019); (5) floor heave - confined thrust 490-785 kPa. Greece lignite analogs: Tomeas 6 (stress-release cracks + 0.6 m heave), Mavropigi 2010 (crest cracks); >20 mm/day -> failure in 6-12 days.
- **CRACK-02 Geometry (LOCKED):** tension width 10-100 mm, length 20-200 m, segment spacing 10-50 m, offset 0-30 m behind crest; desiccation width 1-20 mm, depth 0.05-0.3 m, spacing 1-3 m. Constraints enforced: crack_depth <= 1/3-1/2 slope height; rain fills crack -> hydrostatic wall pressure (USACE).
- **CRACK-03 Spatial (LOCKED):** cracks attach to the mine-engineering geometry layer (crest lines, bench planes, pit floor), NOT the raw DEM. Per-family anchoring + density drivers (tension at crest lines; desiccation on exposed clay; blast at advancing bench front; seepage at aquifer contact seams; heave on pit floor). Provenance + confidence per row.
- **CRACK-04 Severity (LOCKED):** NORMAL->MINOR->MODERATE->SEVERE->CRITICAL from ranked decision surface over measurable props (depth ratio, growth rate, distance to crest, slope angle, water-filled, material, blast PPV). **Rule: severity != width alone.**
- **CRACK-05 Temporal (LOCKED):** per-family growth phases; exports crack_growth_rate_mm_day; >20 mm/day sustained -> failure in 6-12 days; desiccation anti-correlated with rain; rain fills cracks (transient growth spike); blast causes step-growth, not fresh distant nucleation.
- **CRACK-06 Interactions (LOCKED):** rain (waters/seals + hydrostatic fill), blast (step-growth), geology (clays desiccate/sandstones blast-crack/wet seams seep), groundwater (heave + seep), terrain (steep crest hosts tension cracks). Crack state = environment integrator.

### Entry 13 - Cracks are the integrator state variable
- **Observation:** The four completed tracks (RAIN, TERRAIN, GEOLOGY, BLAST) produced environment fields but no single slope-instability state the ML/risk model could consume.
- **Evidence:** Periyasamy 2019 (bench seepage -> wall failure), USACE tension-crack + water-fill physics, Lu 2022/Michalowski FoS-coupling studies, Greece lignite analogs, BIONICS desiccation behavior.
- **Interpretation:** Crack state (families x geometry x severity x growth) is the physical link -> slope instability. No single dataset captures it reliably; build it from evidence layers.
- **Decision:** CRACKS track: crack families anchored to mine-engineering geometry layer; severity ranked on measurable props (NOT width alone); exports crack_severity + crack_growth_rate_mm_day; depth capped at 1/3-1/2 bench; rain fills -> hydrostatic crack pressure; >20 mm/day -> failure window.
- **Version:** prototype_v1 design input.

### Entry 14 - Crack depth is bench-bounded, not rankine-infinite
- **Observation:** Rankine zc for phi=0 Neyveli clay gives 20-88 m, far exceeding any bench height.
- **Evidence:** Geotech clay c=196-883 kPa, gamma~20 kN/m3 (GEOLOGY); OB benches 18-25 m, mineral 6 m.
- **Interpretation:** Cracks physically cannot exceed the bench they sit on; free-field zc is theoretical upper bound only.
- **Decision:** Enforce crack_depth <= 1/3-1/2 * bench height; practical Neyveli depth range 6-12 m.
- **Version:** prototype_v1 design input.

## 14. Generator v1 Phase 1A (skeleton) - COMPLETE

- Code: `ml/data_generation/generator_v1.py` + `generator_schema.py` + `validate_generator_v1.py`.
- Outputs: `data/processed/generator_v1/` - synthetic_mine_states.csv (43 cols), generator_summary.json, validation/schema_validation.json, plots/.
- 4 synthetic zones (mine-engineering layer, NOT DEM): ZONE_A upper OB bench (25 m, 60 deg), ZONE_B middle OB bench (18 m, 55 deg), ZONE_C mineral/lignite bench (6 m, 75 deg - medium confidence), ZONE_D pit floor (low slope).
- Generator versioning (GENERATOR_V1_SPEC.md 7.2): 1A=1.0.0, 1B=1.1.0, 1C=1.2.0, 1D=1.3.0, final=1.0.0-final. schema_version 1.0 frozen.
- Phase 1A placeholder policy (GENERATOR_V1_SPEC.md 7.1): 36 physics fields NaN; ONLY time/zone/bench geometry + inspection scheduler + prior_incident=0 + synthetic=True populated. NO rainfall/terrain/geology/blast/crack/risk logic - that is 1B-1D.
- Row = 1 zone x 1 day. seed 42, 2024-01-01, 365 days -> 1,460 rows. 10-year run -> 14,600 rows (smoke test).

### GEN-1A Status
- **Determinism (PASS):** same seed across separate process invocations -> byte-identical CSV (SHA-256 equal). Different seed -> different CSV. seed 42 -> A == B, seed 43 -> not equal.
- **Schema (PASS, 60 checks):** exact internal column set (43), ML-facing projection (12 frozen fields from docs/05_FEATURE_SCHEMA.md) present via ML_PROJECTION map, timestamps valid datetime, zone_id in {A,B,C,D} never missing, categoricals within allowed enums, synthetic==True everywhere, row count == days x zones, physics fields NaN in 1A.
- Validator exit code 0/1 (fail loudly). Generator bf4b64: fixed rng seeding (SeedSequence[seed, zone_idx]); fixed bool physics fields to nullable boolean dtype so they can be NaN in 1A.

### Entry 15 - Generator v1 Phase 1A skeleton shipped
- **Observation:** Before any physics, we needed proof the pipeline can deterministically emit a correctly structured synthetic mine state.
- **Evidence:** same-seed byte-identical CSV across processes; 60 schema checks all PASS; 1,460-row canonical output.
- **Interpretation:** The output contract (internal schema + 12-field ML projection) is now mechanically enforced, not just doc'd. Fail-loud validator means Member 3 gets a stable contract.
- **Decision:** Freeze Phase 1A; proceed to Phase 1B (RAIN + TERRAIN + GEOLOGY) when team has pulled. 1B bumps generator_version to 1.1.0.
- **Version:** generator 1.0.0 / schema 1.0.

## 15. Generator v1 Phase 1B (RAIN + TERRAIN + GEOLOGY) - COMPLETE

- Code: `ml/data_generation/` modular — `rainfall/sampler.py`, `terrain/sampler.py`, `geology/sampler.py` under `generator_v1.py` orchestrator + `make_generator_plots.py`. Validator upgraded to Phase 1B (`validate_generator_v1.py`).
- Outputs: `data/processed/generator_v1/` — `synthetic_mine_states.csv` (43 cols), `generator_summary.json`, `validation/schema_validation.json`, `plots/` (3 PNGs now that physics exist).
- Version bump per GENERATOR_V1_SPEC.md 7.2: **1.0.0 → 1.1.0** (schema 1.0 frozen); `phases_completed: ["1A", "1B"]`.

### RAIN (mine-wide daily weather, shared across zones)
- **Architecture:** ported validated prototype_v0 core — monthly wet/dry Markov chain + monthly empirical intensity pools (`rainfall/sampler.py`), seeded stream `[seed, 1000]` so it never collides with per-zone rngs. Rainfall is ONE series for the whole mine: all 4 zones on the same grid cell receive identical daily rain (validator asserts `rainfall shared across zones per day`).
- **Populated fields:** `rainfall_mm`, `rainfall_3d_mm`, `rainfall_7d_mm` (partial-window rolling, no NaN), `wet_day = rainfall > 0`, `rainfall_regime` (IMD boundaries: dry 0 / normal ≤35.5 / wet ≤64.5 / storm >64.5).
- **Single-year stats vs grounding:** zero-rain 73.7% vs 71.96%; wet-day P99 150.7 vs 118.7; 7d P99 222.8 vs 323.5; Nov > Feb seasonality kept. Bands in validator are single-year-tuned (organic: empirical tail of a 1-yr draw is noisier than the 25-yr reference).
- **NOT in 1B (deliberate):** year-scale conditioning (124-yr annual distribution) and storm-persistence templates (1902/1931/1935... templates) — the empirical core only; extreme-event machinery stays for the phase that layers it on.

### TERRAIN (two provenance layers, static per zone)
- **DEM layer (Copernicus GLO-30):** `elevation_m` drawn once per zone from bench-located ranges anchored to `terrain_summary.json` (ZONE_A near ground +10..+27 m → ZONE_D pit floor to −97 m); `regional_slope_deg` from the flat coastal-plain band 0.3–6°.
- **Mine-engineering layer (NOT the DEM):** `slope_angle_deg` + `slope_height_m` drawn once per zone from the ZONES bench config (`face_angle_range_deg`, `bench_height_range_m`): A 25 m/45–75°, B 18 m/45–75°, C 6 m/75°, D 0–10°.
- **Rule preserved:** regional terrain (≤6°) ≠ bench geometry (45–75°); validator asserts `regional_slope < bench slope` per bench zone and constant-over-time for all static fields. The 60°-from-DEM idea stays dead.

### GEOLOGY (grounded table, static per zone)
- Material drawn once per zone from grounded candidates (`geology/sampler.py` reads `neyveli_geotech_parameters.csv`); c/φ/γ sampled from the row min/max; `parameter_regime` taken verbatim from the row — total_undrained never silently mixed with effective_stress.
- Seed-42 mapping: A clayey_sandstone (c 45 kPa, φ 27°), B clayey_sandstone (c 110, φ 32°), C clayey_sandstone (c 102, φ 38°), D variegated_sandy_clay (c 701, φ 23°).
- **Lignite deliberately excluded in 1B:** its grounding row has no cohesion/friction and its regime label ("literature") is outside the frozen schema enum; ZONE_C (mineral bench) samples the dominant seam-host sediment until a grounded lignite geotech row exists. Documented here so it is a known gap, not a silent substitution.

### GEN-1B Validation (all pass)
- **Schema:** 43-col exact set, 12-field ML projection, all 14 Phase-1B fields populated (no NaN), the remaining 21 physics fields (groundwater/blast/crack/risk) still NaN (1C/1D), enums/types valid, row count 1,460.
- **Distribution (rain):** zero-day %, wet-day P99, 7d>3d>daily accumulation structure, 7d P99 band, regime↔wet_day consistency, Nov>Feb seasonality — all pass vs grounding.
- **Terrain:** engineering ranges, static-over-time, DEM≠bench separation (per bench zone), pit floor ≤10°.
- **Geology:** material static per zone, c/φ within matched row range, regime == row regime (no mixing), enum-valid.
- **Determinism:** same seed → byte-identical CSV (SHA-256); seed+1 → different. Validator exit code 0/1.

### Entry 16 - Phase 1B: environment physics are live and zone-stable
- **Observation:** 1A emitted a correct skeleton with 36 NaN physics fields. 1B needed to populate the RAIN/TERRAIN/GEOLOGY environment without violating the frozen 43-col schema, the phase boundary, or the no-silent-mixing rule.
- **Evidence:** generator v1.1.0; 74 validation checks ALL PASS; plots `rainfall_wet_intensity_1B.png`, `rainfall_monthly_1B.png`, `zone_structure_1B.png`.
- **Interpretation:** The modular sampler split works — `generator_v1.py` orchestrates `rainfall/`, `terrain/`, `geology/` and stayed a thin 190-line coordinator. Rainfall varies in time (shared mine-wide weather); terrain and geology are static per zone (the mine does not respawn its geology every morning). Grounding survived zone-level generation.
- **Decision:** Freeze Phase 1B; proceed to Phase 1C (GROUNDWATER + BLAST) when team has pulled. GENERATOR_VERSION 1.1.0. Known gap tracked: lignite geotech row incomplete → ZONE_C currently seam-host sediment, to be revisited when a grounded lignite table exists (or in 1D review).
- **Version:** generator 1.1.0 / schema 1.0.

### Entry 17 - Phase 1B rainfall validation scope (RECORDED)
- **Observation:** 1B plots show structural seasonality (Oct rises strongly, Nov dominant, Dec high, dry-season months low) but seed-42 January/June sit above the 25-yr climatological means while November sits below; the synthetic wet-intensity curve carries ~1 yr of wet observations vs 2,561 historical.
- **Evidence:** `plots/rainfall_monthly_1B.png`, `plots/rainfall_wet_intensity_1B.png`; single-year wet-day P99 150.7 vs 118.7, 7d P99 222.8 vs 323.5.
- **Interpretation:** Phase 1B rainfall is validated as a **single-year stochastic realization, not yet a long-horizon climatological generator**. The empirical/Markov core reproduces seasonal structure and daily intensity behavior but NOT yet the 124-yr annual distribution or historical multi-day storm persistence. Do NOT "fix" January on a single seed; the multi-year ensemble test belongs to later rainfall refinement / stress-event layering. Daily intensity already produces strong events; temporal persistence remains the unresolved rainfall problem (v0 limitation L1, expected).
- **Decision:** Accept 1B as-is; keep year-scale conditioning and storm-persistence templates as deliberately deferred mechanisms for the rainfall-refinement phase, not 1B defects. Track as a known limitation.
- **Version:** generator 1.1.0 / schema 1.0.

### Entry 18 - Phase 1C: groundwater and blast are live
- **Observation:** 1B left groundwater/blast NaN by design. 1C needed to populate GROUNDWATER + BLAST from the frozen research without treating them as independent random columns: groundwater must *respond to* the mine-wide rainfall with lag/persistence, and blast PPV must come from the locked NIRM attenuation law, not `random.uniform(2, 20)`.
- **Evidence:** generator v1.2.0; 122 validation checks ALL PASS; plots `groundwater_1C.png`, `blast_1C.png`.
- **GROUNDWATER** (`groundwater/sampler.py`): zone-static aquifer thrust sampled once per zone from grounded ranges (ZONE_D confined below lignite 490–785 kPa — the floor-heave driver; A/B semi-confined seepage; C near-seam intermediate). The transient is an exponential *wetting memory* of the daily rainfall series (τ≈12 d) added on top of the zone thrust → pore pressure and groundwater_state. Same seed ⇒ identical output; pore pressure is far more persistent than daily rain (lag-1 AC 0.995 vs 0.049) and tracks 7-d accumulation (within-zone corr 0.82). `groundwater_proxy` = wetting memory (mm) for the ML projection.
- **BLAST** (`blast/sampler.py`): latent weekly rate 14–28/wk (derived, §1.2) partitioned across the 5 stripping benches; only OB benches A/B blast (lignite/floor never). Per event: W ~ triangular(100,600,300 kg), D zone-static from the synthetic layout (A 300 m village, B 150 m boundary hutments), frequency from the 5–27 Hz 3-bin model (P<8 Hz ≈ 45%), PPV = **858.90·(D/√W)^−1.58** × lognormal scatter (σ=0.40, toward r≈0.86). Non-blast days carry PPV 0. DGMS Circular 7/1997 thresholds remain regulatory **reference only** — never exported as columns, never used as the risk label.
- **Data fix:** `neyveli_blast_constants.csv` row `n_regression` had an unquoted comma in its note; quoted so pandas parses all 8 fields.
- **Decision:** Freeze Phase 1C; GENERATOR_VERSION 1.2.0, PHASES_COMPLETED 1A+1B+1C. Remaining NaN set is the crack/slope/risk track (crack fields, slope_condition, instability_score, risk_label) → Phase 1D/1E.
- **Version:** generator 1.2.0 / schema 1.0.

### Entry 19 - Pre-1D corrections: groundwater semantics + blast rate interpretation (CORRECTED)
- **Observation:** An independent review of the uploaded 1C samplers flagged two issues to settle before 1D inherits them. (1) `groundwater_thrust_kpa` and `pore_pressure_kpa` played unclear roles — ZONE_D starts at 490–785 kPa before any rainfall, and its state bands (>500 → critical) meant the floor sat critical even in dry weather. (2) The blast weekly rate 14–28/wk (derived, §1.2) was partitioned across 5 stripping benches while only 2 benches are represented as blast zones, so the generated A+B total was ~5.6–11.2/wk — the model silently threw away most of the operational rate.
- **GROUNDWATER — resolved as the documented semantic contract, physics unchanged:** the research (neyveli_geology.md §3.4) itself says the confined aquifer's upward thrust (490–785 kPa) drives floor heaving AND pit-wall pore pressure. So `groundwater_thrust_kpa` IS the baseline component of `pore_pressure_kpa`, and the wetting-memory transient modifies it. ZONE_D being permanently high/critical is the genuine, grounded floor-heave condition — not a bug. This is now written into `groundwater/sampler.py` as a semantic contract + a validator check (`ZONE_D permanently high/critical; still rises with rain`).
- **BLAST — resolved per Interpretation A:** the 14–28/wk is a **mine-wide** operational rate; it is drawn once on a dedicated stream and allocated across the represented blasting zones so ZONE_A + ZONE_B = 14–28/wk (validator now asserts the sum is conserved, `A+B = 25.3/wk` on seed 42). Every generated event is a real blast affecting the modelled system; none are hidden on unrepresented benches. Explicitly documented in `blast/sampler.py` and spec §7.3.
- **Evidence:** validator now 161 checks ALL PASS (added semantic locks for both fixes); plots unchanged.
- **Decision:** 1C is ready for 1D consumption — groundwater/blast states now have unambiguous, documented meaning and honest rate accounting. Proceed to 1D (CRACKS) consuming rainfall/7d, pore pressure, material c/φ, bench geometry, blast PPV/frequency, and temporal crack state; risk labelling stays in 1E.
- **Version:** generator 1.2.0 / schema 1.0.

### Entry 20 - Phase 1D: cracks now live and ratchet with a grounded failure-window signal
- **Observation:** 1C left crack/slope/risk NaN by design. 1D needed to populate CRACKS as a *time-evolving damage process*, not a random column: it must inherit the existing RAIN/TERRAIN/GEOLOGY/GROUNDWATER/BLAST state, accumulate monotonically with memory, never self-heal, and carry a severity label that respects the CRACK-01..05 rules (crack state does not reset daily; width capped; ZONE_D confined floor-heave only; decision surface; ML severity field).
- **Evidence:** generator v1.3.0; 195 validation checks ALL PASS; plots `cracks_1D.png`; 30-seed sweep (5–34) shows no negative growth, no resets, families/caps stable.
- **CRACKS** (`cracks/sampler.py`): six physically-couple growth terms per day — **tension** (slope: steepness × wetting factor × activity), **hydraulic** (rainfall wetting memory, amplified by moisture-bearing clays), **blast-induced** (PPV above the locked 8 mm/s damage threshold, active only on OB benches A/B), **seepage** (B when wetting is high), **desiccation** (clay-rich zones after prolonged dry stretches), and **heave** (ZONE_D confined aquifer thrust /490 − 1). Growth is always ≥ 0. **Depth and width ratchet with memory** (accumulated; caps: depth = 1/3–1/2 bench height for benches, 0.6–1.5 m for the floor panel; width ≤ 150 mm general / 60 mm on D). Family is chosen by *dominant driver of the day* (tension_crest / blast_induced / seepage / desiccation / floor_heave), so B — the 150 m high-PPV zone firing ~daily under Interpretation A — is dominated by blast_induced; D is always floor_heave (the grounded confined-aquifer condition).
- **Severity semantics:** `crack_severity` is **cumulative state only** (depth penetration fraction of the reserved bench layer), so it rats with the crack and never downgrades — matching "crack state does not reset daily". The transient, >20 mm/day **6–12 day failure-window signal** (Leonardos & Terezopoulos) is *not* conflated into the rating; it lives as its own ML feature `crack_growth_rate_mm_day` (7-day trend above 20 → the operator's acute-alarm signal). Width and growth rate remain independent ML features.
- **Data fix:** validator used `bench_height_m` as the depth cap for ZONE_D which has no bench; fixed to the floor panel's own 0.6–1.5 m generation cap.
- **Decision:** Freeze Phase 1D; GENERATOR_VERSION 1.3.0, PHASES_COMPLETED 1A+1B+1C+1D. Remaining NaN set is the slope-stability/risk track (`slope_condition`, `instability_score`, `risk_label`) → Phase 1E.
- **Version:** generator 1.3.0 / schema 1.0.

### Entry 21 - Pre-1D-freeze audit: material coupling was backwards; acute-window policy formalized (CORRECTED)
- **Observation:** an audit review before freezing 1D (audit_cracks_1D.py, 30-seed ensemble) left 1D architecturally PASS but flagged two hard items. (1) `MATERIAL_WEAKNESS` is documented as "higher = more prone to cracking", yet tension used `(1 − weak·0.5)` and hydraulic `(1 − weak·0.35)`, so increasing weakness *reduced* growth — the most crack-prone materials got the least growth, directly contradicting the monotone direction the research states ("material weakness (clay > sandstone)", "cracks concentrate in the weakest materials"). (2) The research-defined acute signal (crack growth > 20 mm/day ⇒ predicted failure in ~6–12 days) was never observed in the baseline, and needed an explicit decision, not an accident.
- **FIX (material direction):** `cracks/material.py` now exposes `susceptibility(weakness) = 0.5 + 0.5·weakness` — a documented DIRECTION CONTRACT (monotone non-decreasing in weakness). All material-scaled growth terms (tension, hydraulic) and density base are multiplied by it. Audit: monotonicity OK for tension/hydraulic/density (weak 0.30→1.00 : 0.094→0.144, 0.390→0.600, 0.287→0.375). Validator now carries a permanent check (196 total) so the direction can never silently regress.
- **FINDING (B time-to-cap):** B (18 m bench, cap ⅓–½ ⇒ 6–9 m) reaches its depth cap in **0% of 30 audit seeds** (P50 final depth/cap 0.79, P90 0.89). The hard cap holds and the "smooth march to the cap" concern is not realized: B progresses strongly (blast-dominated, as the research expects for the 150 m high-PPV boundary zone) but does not systematically saturate. Gate PASS. The smooth plot shape reflects steady cumulative damage, which is the intended memory behaviour, not a cap-pinning artifact.
- **FINDING (acute >20 mm/day):** across 30 audit seeds (and 60-seed tail probe, PPV at its 100 mm/s cap) the baseline peak growth ceiling is ~10 mm/day; **0 days exceed 20 mm/day**. This is structurally real, not a tuning miss. The >20 mm/day rate is the 6–12 day **pre-failure window** — the run-up to an imminent collapse — which a routine-operations synthetic year must NOT routinely inhabit. Decision: the baseline deliberately does not fabricate acute-window states; that crisis window is the domain of the 1E/1F stress-event layer (deliberate scenario injection), and the audit now asserts the baseline *stays below* it (gate PASS). Documented in spec §7.4.
- **Chain documentation (item 3):** the hydraulic term consumes `groundwater_proxy` (the τ≈12 d wetting memory), not `rainfall_7d` directly; `rainfall_7d` remains only for the `water_filled` boolean. The causal chain is now explicit in spec §7.4: `rainfall → rainfall_7d → groundwater wetting memory → pore pressure → hydraulic crack growth`.
- **Evidence:** generator v1.3.1; 196 validation checks ALL PASS; audit gates PASS (B cap rate 0%, baseline < 20 mm/day, material monotone); family matrix zone-separated (A tension+blast, B blast-dominant, C tension-only, D floor-heave) consistent; 30-seed stability hold.
- **Decision:** 1D is audited and freezes at GENERATOR_VERSION 1.3.1 with the material direction corrected and the acute-window boundary policy locked. Proceed to Phase 1E (slope stability / FoS + risk labels) when team has pulled.
- **Version:** generator 1.3.1 / schema 1.0.

## 16. Generator v1 Phase 1E (FoS / risk labels) - COMPLETE

- Code: `ml/data_generation/instability/sampler.py` (deterministic FoS chain), wired into `generator_v1.py`, validator upgraded to Phase 1E (`validate_generator_v1.py`). Diagnostic audit: `ml/data_generation/audit_phase1e_calibration.py`.
- Outputs: `data/processed/generator_v1/` — `synthetic_mine_states.csv` (44 cols, includes `fos`), `generator_summary.json` (includes `phase_1e_pinning_provenance` note), `validation/schema_validation.json`.
- Version bump per GENERATOR_V1_SPEC.md 7.2: **1.3.1 → 1.4.0** (schema 1.0 frozen); `phases_completed: ["1A", "1B", "1C", "1D", "1E"]`.

### INSTABILITY (FoS chain, spec §7.5, LOCKED equation)
- **Chain:** 1B state (c/φ/γ/θ/h) → infinite-slope FoS → slope_condition → instability_score → risk_label. FoS is a pure function of state — no randomness, no feature-weight soup; same state always yields the same label.
- **Equation:** `FoS = (c_eff + (γh·cos²θ)(1−r_u)·tanφ) / (γh·sinθ·cosθ)`, capped at 2.5.
  - `c_eff` = c degraded by crack density on the ordinary path: `1 − k_crack·min(density/D_REF, 1)`, k=0.10 → at most −10% (Lu 2022). The −50% branch is **reserved** for the steep engineered open-crack worst case (critical severity + water_filled + bench face ≥ 60°, Michalowski 2013) — distinct auditable branch.
  - `u` = pore-pressure **ratio** r_u driven by the 1C wetting transient (`groundwater_proxy`) + water-filled crack boost. The confined-aquifer **thrust is deliberately not placed on a shallow bench slip plane** (plan §D defines u as rainfall + groundwater proxy; the thrust is the floor-heave driver). Raw thrust on a 6 m bench would force negative effective stress — the ratio form keeps FoS physical and bounded.
  - **ZONE_D (floor)** has no slope (h=0, θ≈0); it uses the documented **floor-uplift branch** `FoS = 490/pore_pressure` — chronically high/critical, rising with rain (the grounded confined-aquifer heave condition).
  - **Blast** acts only through the crack state (blast-induced cracks lower c_eff); no direct additive term.
- **Bands (locked):** <0.80 critical; 0.80–1.00 high; 1.00–1.20 moderate; 1.20–1.50 low; ≥1.50 very_low (cap 2.5). `slope_condition` = 4 physical states (stable/marginal/unstable/failed) mirroring FoS; `instability_score` monotone decreasing in FoS, 0–100, FoS-only.

### GEN-1E Validation (all pass)
- **Schema:** 44-col exact set, `fos` float field added, all 4 Phase-1E fields populated, band enums valid.
- **Physics gates:** FoS bounded (0–2.5); ZONE_D chronic FoS < 1 and high/critical only; risk_label ↔ FoS band mapping exact; slope_condition ↔ FoS exact; score monotone in FoS (corr −0.9998), FoS-only (same FoS ⇒ same score); **counterfactual ordering gate** (dry-intact ≥ wet ≥ wet+cracked ≥ wet+cracked+blast) holds per zone; crack-density budget (ordinary ≤10%, −50% branch gated on steep+critical+filled); rainfall→risk correlation positive (mean corr 0.67).
- **Determinism:** same seed → identical dataset; seed+1 → different.

### Entry 22 - Phase 1E: labels pinned per zone is expected from frozen anchors (CALIBRATION AUDITED, NOT A DEFECT)
- **Observation:** with frozen 1B statics, seed 42 labels are pinned: ZONE_A critical ×365 (FoS 0.39–0.62), ZONE_B high/critical ×365 (0.75–0.98), ZONE_C very_low ×365 (1.74–2.50), ZONE_D critical ×365 (0.50–0.78, chronic by design). The risk_label shows ~no within-zone daily variation.
- **Evidence:** `audit_phase1e_calibration.py` — incremental driver states (dry→wet→cracked→blast) and per-driver sensitivity: rain r_u 0→0.5 moves A 0.63→0.40 (dFoS/dr_u = −tanφ/tanθ = −0.45); the whole 10% crack budget moves A ~0.02; the −50% open-crack branch (A face 60°, C face 75° fire) moves A 0.39→0.31 and C 2.5→1.74. Cross-seed: pinning is a **draw outcome** — seed 43 (c=120) gives A 0.73–1.02; seed 44 (lateritic c=715–740) gives 2.5. B's blast step is small (0.76→0.74) because face 55°<60° excludes the −50% branch, per the signed steep-only contract.
- **Interpretation:** band anchors are set by frozen geometry+strength; dynamic drivers are correctly coupled (ordering gate + rainfall correlation PASS) but move FoS ≤ the 0.20–0.50 band pitch. The pinning is: expected from grounded geometry/material (C 6 m strong, D heave), partly c/φ regime semantics for A (field/total-undrained c=45 on a 48.6°/23 m face is genuine), NOT an implementation issue, NOT insufficient coupling.
- **Decision:** Keep physics, thresholds (0.80/1.00/1.20/1.50), constants, and coupling unchanged. Document the pinning as expected provenance (spec §7.5 + generator_summary `phase_1e_pinning_provenance`). The continuous `instability_score` is the preferred regression signal; multi-seed generation for classification. Validator records the anchor provenance diagnostically (never asserts a label distribution). Freeze Phase 1E.
- **Version:** generator 1.4.0 / schema 1.0.

## 17. ML-facing handoff export (HANDOFF STEP, not a generator phase)

- Code: `ml/data_generation/export_ml_dataset.py` — reuses the **unchanged** frozen `project_ml()` projection and appends targets. No physics, generator logic, schema, or Phase 1E behavior modified.
- Outputs: `data/processed/generator_v1/ml_handoff/`:
  - `seed_42_ml_features_targets.csv` — seed 42, 1,460 rows.
  - `synthetic_ml_dataset_seeds_42_46.csv` — seeds 42–46 combined (5 × 1,460 = 7,300 rows) with a `seed` column.
  - `README.md` — manifest (features, targets, seeds, row counts, version 1.4.0 / schema 1.0, synthetic flag, deferred-preprocessing note).
- **12 frozen features** exported as-is: rainfall_24h_mm, rainfall_7d_mm, slope_angle_deg, slope_height_m, rock_type, crack_density, crack_severity, blast_frequency_per_week, blast_vibration_ppv_mms, days_since_inspection, prior_incident, groundwater_proxy.
- **Targets included:** `fos` (continuous), `instability_score` (preferred regression target; seed 42 range 0–100, mean 68.7), `risk_label` (5-band discrete). Auxiliary id columns: `zone_id`, `seed`.
- **Categoricals preserved** — rock_type / crack_severity keep their existing values (no one-hot). `prior_incident` boolean (False in routine baseline).
- **Deliberately deferred to ML phase:** train/val/test splits, categorical handling, scaling, feature engineering, leakage review.
- Combined-label mix across seeds: very_low 2,894 (39.6%), critical 1,858 (25.5%), high 1,484, moderate 726, low 338 — multi-seed coverage spans all bands (per the Entry 22 provenance note, single seeds are band-pinned; classification studies require the multi-seed set).
- **Validation after export:** `validate_generator_v1.py --seed 42` re-run — ALL PASS (physics/ordering/schema unchanged).
- **Decision:** record as handoff/export; generator remains frozen at 1.4.0. Next phase = reverse-engineering walkthrough + ML layer (features/targets/splits/leakage/baseline).
## 18. Experiment F: temporal trend features (V2) -- hypothesis tested and REFUTED

- **Code:** ml/features/temporal_features.py (V2 builder + causality selftest), ml/benchmark/experiment_f.py, ml/benchmark/experiment_f2_forecast.py.
- **Hypothesis (roadmap Phase 2-5):** exposing temporal trends (rain accumulation, groundwater deltas, crack growth rates, blast history) improves ML prediction.
- **Causality gate:** trailing windows only; selftest_causality() verifies features at t are invariant to deleting the future (PASS, 20 randomized truncation checks).
- **Result (nowcasting, same frozen protocol 42-81/82-86/87-91):** V2 is consistently WORSE than V1. abs: 0.890 vs 0.915; d-inst: 0.812 vs 0.852; d-fos: 0.808 vs 0.853. No ablation group beats V1 beyond noise.
- **Result (forecasting t+1 / t+7):** persistence baseline dominates everything (R2 0.998 / 0.991); learned models ~0.88-0.91 regardless of feature set.
- **Diagnosis:** third independent confirmation that generator FoS is memoryless given the current state (after LSTM probe and directionality audit). Day-scale changes are tiny and driven by future stochastic weather, which no observable trend encodes. Trend features would matter only with hysteresis or longer-horizon seasonal forecasting.
- **Decision:** V1 remains the frozen ML feature contract. "Understands changing conditions" is served by the Scenario Engine (physics simulation of causes), NOT by trend features in the nowcast model. ML Model v1 frozen per docs/ML_MODEL_CARD_V1.md (RF, validation-selected).

## 19. Scenario Engine v1.5 (What-If extension layer) -- built and validated

- **Code:** ml/scenario/spec.md (Phase 10 contract), engine.py, alidate_scenarios.py.
- **Architecture:** scenarios inject modified CAUSES (rain realization, blast schedule) into the FROZEN v1.4.0 chain (rain -> groundwater -> cracks -> blast -> FoS -> score -> label). Engine never writes fos/score/label directly (gate 5 enforces). Generator untouched.
- **Scenario kinds:** rainfall_storm (triangular), prolonged_rain, blast_surge (frozen attenuation law for injected events), combined, historical_rain (IMD-provenance templates: Dec-1902 1088mm/month, Apr-1931, Nov-2015, Dec-1996).
- **Validation gates: ALL PASS.** (1) baseline replay == generator output exactly; (2) pre-start rows identical; (3) dose-response monotone; (4) deterministic re-runs; (5) no direct score writes; (6) crack damage accumulates without resets.
- **Key finding -- compressed single-year response envelope:** under frozen physics, extreme single-year storms move groundwater massively (proxy 222->805mm) but barely move FoS: r_u saturates at 0.35-0.55, cohesion-dominated benches (ZONE_C) are water-immune, critical zones already saturated. Passive-generation band pinning extends to scenarios.
- **Breakthrough -- multi-year cumulative exposure:** 3-year horizon with Dec-1902 replayed at day 550 lets crack damage accumulate until the DISCRETE open-crack branch (critical AND water-filled AND face>=60deg) fires naturally: ZONE_C reaches 796 critical-severity days, 448 critical+water-filled days, FoS diverges from baseline by **-0.761** across 51 days. A genuine regime response with ZERO physics changes.
- **Decision:** What-If v1 ships trajectory outputs (day-by-day gw/crack/FoS/score) with honest score deltas; multi-year historical-replay is the flagship scenario class. ML (RF on V1) stays the prediction path; the engine is the simulation path -- responsibilities never mixed.

## 20. Phase 19-20 close-out: summaries, edge cases, Member-2 audit

- **Code:** ml/scenario/summaries.py -- compact scenario summaries (min FoS / peak score / days High+Critical / peak crack growth / peak pore pressure / first-response day / worst day), comparison tables, trajectory serialization with metadata sidecars, template provenance (IMD window totals).
- **Edge cases: ALL PASS.** scale-0 == baseline; start-day-0; window overrun clips; blast-surge no-op on unblasted zones (ZONE_C/D invariant enforced); unknown kind raises; short templates pad.
- **Audit:** docs/MEMBER2_AUDIT.md -- full evidence chain from leakage discovery to scenario engine; frozen artifacts list; known limitations shipped honestly.
- **Member 2 COMPLETE.** Prediction path (V1 -> RF) and simulation path (Scenario -> engine) delivered as separate responsibilities. Handoff contract documented for Member 3 integration.

## 21. Backend integration (real ML live) + Experiment G killed

- **Backend integration (PR #1 merged by team):** ackend/app/model_service.py bridges the API to frozen ML Model v1 -- RF trained on seeds 42-81 per protocol, real Tree SHAP explanations, confidence from tree-spread, FoS-derived band thresholds replace mock cutoffs (80/60/40/15 -> 50/65/75/85). ZoneStore bootstraps from REAL corpus states (last day of held-out seed 91); hardcoded INITIAL_RISK constants removed; schema bounds matched to generator scales (crack_density<=2.5, groundwater_proxy<=1000mm). Tests rewritten from mock-score assertions to model properties (consistency, monotone deterioration): 15/15 PASS. Live predictions match known generator structure: A=89 Critical, B=100 Critical, C=66 Moderate, D=99 Critical.
- **Experiment G (DEM spatial context): KILLED.** Zones have no geo-coordinates, so curvature/aspect/flow-accumulation would require inventing locations (rejected as Tier-3). Only REAL DEM-derived fields already internal to the generator were tested: elevation_m + regional_slope_deg added to V1. Result: abs R2 0.917->0.806 (-0.111), d_inst 0.849->0.806 (-0.043), d_fos 0.848->0.700 (-0.148). DEM context actively degrades prediction: fields are near-constant per zone (redundant with zone_id/rock_type but noisier) and the frozen FoS never consumes them. V1 contract stands unchanged.
- **Architecture note:** the API's /api/simulation/what-if remains an ML counterfactual (feature overrides re-predicted). True causal What-If stays in the Scenario Engine (ml/scenario/), per the prediction-vs-simulation separation. Wiring the engine into the API is future integration work.

## 22. Causal Scenario Engine wired into the API -- Member 2 fully closed

- **New endpoints (backend):** GET /api/simulation/templates (IMD-provenance for Dec-1902/Apr-1931/Nov-2015/Dec-1996); POST /api/simulation/causal-what-if (Scenario Engine v1.5: modifies causes, frozen v1.4.0 chain propagates, returns day-by-day FoS/score/label trajectory + summary incl. open-crack-branch flag). Existing /api/simulation/what-if explicitly documented as ML counterfactual in its API description.
- **Tests:** 8 new causal tests (determinism via identical summaries, template provenance, blast no-op on unblasted zones visible through the API, multi-year branch firing at 1095-day horizon, kind/zone validation) -- full suite 23/23 PASS.
- **Member 2 COMPLETE.** Prediction path and causal simulation path are both live behind the API with the distinction made explicit.

## 23. BACKFILL: ML campaign experiment log (recorded post-hoc, chronological)

Entries for work performed between SS17 and SS18 that lived in scratch reports
and docs/MEMBER2_AUDIT.md but was never given ledger states. Numbers are from
the committed result JSONs under ml/benchmark/results/ unless noted.

### SS23.1 Baseline + leakage discovery (5-seed corpus)
- Naive random row split: R2=0.998 / macro-F1 0.985 -- INVALID (within-seed near-duplicates).
- Honest unseen-seed split (train 42-45 -> test 46): R2=-0.53, worse than dummy. Cause: per-seed band pinning (test mean 38.5 vs train 56.9; seed 46 held 92% of all 'low' rows).
- Verdict: random splitting banned; seed-intact splits become protocol law.

### SS23.2 Experiments A-D (diagnostic ladder, 5-20 seeds)
- A single-seed chronological (Jan-Sep -> Dec): R2=0.66 overall; per-zone 0.75-0.94 (ZONE_C -5.0 = rare-event miss). Dynamic signal EXISTS within a world.
- B static-vs-dynamic on unseen seed: static -0.55, dynamic -1.64. Dynamics do not transfer across worlds.
- C delta-targets (train-only zone baselines): R2 -0.58 -> +0.13 (both d-inst and d-fos agree).
- D world expansion: 20 seeds -> d-fos 0.457 / abs 0.590. Coverage, not physics, was the bottleneck.
- Artifacts: experiment_AB_report.json, experiment_C_report.json, experiment_D_report.json (scratch).

### SS23.3 Formal 50-world benchmark (protocol v1 frozen)
- Corpus: seeds 42-91, 73,000 rows. Splits 42-81 / 82-86 / 87-91, test touched once.
- Default + GroupKFold-by-seed tuning (cheap-search then production refit).
- Test R2: abs -- Ridge 0.898, RF 0.897, HistGB 0.901, XGB 0.902, LightGBM 0.901; delta targets 0.82-0.85.
- Selection by VALIDATION only: RF winner on all three targets -> frozen as Model v1 (docs/ML_MODEL_CARD_V1.md). Boosting test scores recorded as comparative baselines only.
- Artifacts: ml/benchmark/{baselines,tuning}.py, results/baselines_default.json, results/tuned_*.json.

### SS23.4 Explainability + directionality audit
- Permutation/SHAP: slope_angle + rock_type dominate; groundwater correct direction; days_since_inspection ~ 0 (no scheduler crutch).
- Monotonicity sweeps: crack_density and blast PPV inverted in MODEL; raw-data check shows ZONE_B crack corr -0.26 flips to +0.36 controlling rain+GW.
- Audit classification: (a) wetting confound, (b) lag/state-memory (PPV->growth 0.55 same-day; growth->inst persists 7d), (c) ML artifact mirroring confounds. NO class-(d) generator defect. Physics retention contract verified monotone counterfactually.
- Artifact: results/explainability.json; audit script/report in scratch.

### SS23.5 ANN probe (MLP + LSTM)
- MLP R2=0.895 abs -- seventh model family inside the same band; ceiling is feature information.
- LSTM-14day no gain over snapshots -> generator FoS confirmed Markovian in current state (third independent confirmation).
- Artifact: ann_results.json (scratch).

### SS23.6 Transfer learning study
- Source domain: 120K cases from published geotech ranges through frozen FoS functions (stands in for Xu-et-al-style pretrained surrogate; no public checkpoint exists).
- Zero-shot on Neyveli: R2=-0.97. Fine-tuned at 5 worlds: 0.906 vs scratch 0.886; parity by 20-40. TrAdaBoost.R2 simplified: 0.775 @5 worlds.
- Conclusion: physics pretraining is a data-efficiency prior, not a replacement for target coverage.
- Artifacts: transfer_probe.py, transfer_results.json (scratch).

### SS23.7 Extended 75-world study (seeds 42-116)
- Regression: same-test controlled comparison 40 vs 65 train seeds -> +0.001. Curve flat; 50-world benchmark stands. R2 not comparable across different test sets.
- Classification at scale (first proper numbers): macro-F1 0.47, balanced acc 0.47, critical recall 0.87 (RF); 'moderate' band NEVER predicted -- formulation problem (ordinal recommended), not coverage.
- Transitions: 6 strict safe->dangerous events in 109,500 zone-days; zones quantitatively pinned (ZONE_D 100% critical/high). Early-warning claims impossible on passive generation -> motivated Scenario Engine.
- Artifacts: extended_study_results.json, diagnose_extended.py (scratch); corpus seeds_42_116.csv (scratch, not shipped).

### SS23.8 Backend merge
- PR #1 (devSaumitr): FastAPI scaffold accepted -- additive only, no frozen artifacts touched. Mock scoring replaced immediately after by real model integration (see SS21).
