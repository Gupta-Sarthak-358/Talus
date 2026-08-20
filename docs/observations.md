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