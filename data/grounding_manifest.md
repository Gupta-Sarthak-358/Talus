# Talus Data Grounding Manifest

**Owner:** Member 2 (Data / Synthetic Generator) · **Trace to:** `docs/decisions/ADR-002-neyveli-reference-mine.md`, `docs/03_DATA_PLAN.md`

This manifest is the **operational record of the grounding phase** — what real sources anchor the synthetic generator, and their exact provenance. Updated as each grounding step completes. **Current state: all five tracks grounded (RAIN, TERRAIN, GEOLOGY, BLAST, CRACKS).**

---

## Anchor Mine

```
Anchor mine  : Neyveli Mine-II
Company      : NLC India Limited
Region       : Neyveli, Cuddalore district, Tamil Nadu, India
Mining method: Open-cast lignite mining (BWE / conveyor / spreader)
Scale        : ~15 MTPA, ~7,193.975 ha, 365-day three-shift operation
Stripping    : ~5.2:1
```

## Coordinates

```
Documented extent : 11°27′N–11°32′N, 79°27′E–79°35′E
Approx           : lat 11.45–11.53 N, lon 79.45–79.58 E
Anchor point     : 11.50°N, 79.50°E  (exactly matches the documented extent)
Status           : ✅ locked
```

## IMD (rainfall)

```
Dataset  : IMD 0.25° × 0.25° Daily Gridded Rainfall (imdpune.gov.in)
Period   : 1901–2024 (124 yr)
Grid cell: 11.50°N, 79.50°E = RAINFALL[:, 20, 52]  (inside mine bounds)
Format   : NetCDF (ind<year>_rfp25.nc) — integrity-verified
Purpose  : grounded rainfall distribution (rainfall_24h_mm, rainfall_7d_mm)
Model    : seasonal + year-conditioned (124-yr annual dist) + storm templates
Status   : ✅ complete → data/processed/imd/analysis/, data/processed/imd/neyveli_rainfall_*.csv
```

## DEM (terrain)

```
Provider : Copernicus GLO-30 (ESA), 30 m, tile Copernicus_DSM_GLO30_N11_E079 (AWS open data)
Coverage : 79.0–80.0°E, 11.0–12.0°N
Extents  : regional context 11.30–11.70 N, 79.35–79.70 E; mine focus 11.45–11.53 N, 79.45–79.58 E
Key stats: pit floor −97.4 m; macro slope max 31.3°; focus median 15.4 m
Note     : regional terrain ≠ mine bench geometry → benchmarked in a SEPARATE
           mine-engineering layer (OB 25 m×4+18 m, mineral 6 m @ 75°, overall 45°) 
           marked synthetic/engineering-input in provenance.
Status   : ✅ complete → data/processed/terrain/ (tifs, maps, terrain_summary.json)
```

## Geology (rock parameters)

```
Context  : Neyveli lignite field overburden — Cuddalore Group (Upper Miocene) SEDIMENTARY units
Classes  : 9 material classes incl. lateritic_soil, clayey_sandstone/sandstone, clay (LL≤90),
           variegated_sandy_clay, carbonaceous_clay, aquifer_sand, lignite, overburden_mixed
Sources  : NLCIL "Problems and Needs" (Indo-US WG / fossil.energy.gov), NLC EC Mine-II
           (readkong), Periyasamy 2019 JGSI (aquifer systems) — multiple mirrors
Parameter regime : total/undrained flagged per row; SI conversion only at consumption
Status   : ✅ complete → docs/research/neyveli_geology.md, data/processed/geotech/neyveli_geotech_parameters.csv
```

## Blasting (operational)

```
Sources  : NIRM 2005 MT/134/02 (K=858.90, b=1.58, r=0.86, 22 blasts/68 obs), NLC/LAUBAG 1995
           Master Plan, Coal Age 2015, DGMS (Tech)(S&T) 7/1997
Model    : PPV = 858.90 · (D/√W)^(−1.58); freq 5–27 Hz left-skewed
Ranges   : MCD 100–600 kg (mode 300), 14–28 blasts/wk (DERIVED, wide prior), 30% OB blasted
Status   : ✅ complete → docs/research/neyveli_blasting.md, data/processed/blasting/neyveli_blast_constants.csv
           Note: blast freq is production-derived, NOT NIRM's 22-blast monitoring sample.
```

## Cracks (state variable)

```
Model    : 5 mechanisms (tension/crest, desiccation, blast-induced, seepage, floor heave)
Sources  : USACE EM 1110-2-1902; Lu 2022 (MDPI); Michalowski 2013; BIONICS/Newcastle;
           Hydrology 2023; Periyasamy 2019; Leonardos & Terezopoulos 2002 (lignite analog)
Geometry : bench-bounded depth (≤ ⅓–½ slope height; practical 6–12 m); severity ≠ width; 
           growth rate (crack_growth_rate_mm_day; >20 mm/day → 6–12-day failure window)
Status   : ✅ complete → docs/research/neyveli_cracks.md, data/processed/cracks/neyveli_crack_constants.csv
```

---

## Grounding references

See `research/sources.md` → "Neyveli reference-mine sources" for the full list (NLC EC/NGT minutes, USGS groundwater-control study, Ministry of Coal report, IMD, Crack-Seg). Track-specific sources are listed in each `docs/research/*.md`.

## Data honesty

Neyveli defines the **operational context and spatial scenario**. The prototype validates on **public, historical and synthetic data**. Real deployment would require a mine-partner telemetry/incident-data agreement. Synthetic rows are tagged `synthetic: true` and carry provenance (see `docs/05_FEATURE_SCHEMA.md`).