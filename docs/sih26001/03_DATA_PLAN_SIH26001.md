# TALUS v2 Data Plan — SIH26001

**Status:** Draft · **Trace to:** `05_FEATURE_SCHEMA_SIH26001.md`,
`04_MODEL_PLAN_SIH26001.md` · **Source:** `docs/SIH26001_RESEARCH.md` §6, §9

> Grounding rule (inherited from v1, strengthened): every feature traces to a
> real source with a provenance tag. v2 values are **observed or derived from
> observations** — no synthetic draws. Where a source is a proxy (e.g.
> reanalysis soil moisture for in-situ), the proxy status is tagged, not hidden.

---

## A. Source inventory (all verified accessible Aug 2026)

### Rainfall

| Dataset | Access | Account | Use |
|---|---|---|---|
| IMD 0.25° daily gridded (1901–2024) | imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html | No | Antecedent + triggering rain (24h / 7d / 30d) |
| `imdlib` (Python) | `pip install imdlib` | No | Same, scripted fetch |
| `imddata` (CLI) | `pip install imddata` | No | Same, CLI fetch |
| IMD forecast API | IMD weather API | Check ToS | Demo fixture (recorded, not live) |

IMD grid: 135×129, 66.5°E–100°E × 6.5°N–38.5°N, 0.25°. NER bbox
(88°E–98°E, 21°N–29°N) lies fully inside.

### Soil moisture

| Dataset | Access | Account | Use |
|---|---|---|---|
| ERA5 volumetric soil water | CDS API (cds.climate.copernicus.eu) | Free CDS account | Pore-pressure proxy |
| SMAP (via LHASA inputs) | NASA Earthdata | Free account | Cross-check / fallback |

Tag as proxy: reanalysis ≠ in-situ. (Marino et al. 2020 shows in-situ
improves LEWS; we state the resolution limit openly.)

### Terrain (DEM + derivatives)

| Dataset | Access | Use |
|---|---|---|
| SRTM 30m | USGS EarthExplorer / NASA Earthdata | Elevation base |
| Derived: slope, aspect, curvature, TWI, SPI, drain density | Computed in NGEN `terrain/` | Structural + hydrological features |

### Satellite (vegetation / land use)

| Dataset | Access | Use |
|---|---|---|
| Sentinel-2 L1C/L2A | ESA Copernicus Open Access Hub | NDVI, LULC |

### Geology / tectonics

| Dataset | Access | Use |
|---|---|---|
| GSI Bhukosh lithology | bhukosh.gsi.gov.in/Bhukosh/Public | Material strength class |
| Lineament density | Derived from DEM + geological maps | Tectonic weakness |
| Seismic zone | GSI / NDMA maps | Context (Zone V) |

### Landslide inventories (labels)

| Source | NER coverage | Access |
|---|---|---|
| GSI Bhusanket | 37,903+ NER points + year | bhusanket.gsi.gov.in |
| NASA GLC | 11,000+ global since 2007, point + date | landslides.nasa.gov/viewer |
| NASA COOLR | Crowdsourced, point + date | Same viewer + REST FeatureServer |
| ISRO Landslide Atlas | 80,000+ nationwide | nrsc.gov.in |
| Monga & Ganguli 2026 | 490 NEH events + rainfall (2006–2019) | Published paper |
| Mihu et al. 2026 (Dibang) | 537 points | Published paper |
| NEHU/Agrawal (Meghalaya) | 1,330+ points | Published paper |
| Sarma 2026 (Mizoram) | 19 events 2016–2025 | Zenodo (open) |
| ILSM (Sharma et al. 2024) | 154,329 pan-India points, 100m | Zenodo (open) |
| Khan et al. 2025 | 109,504 landslides, 90m national LSM | Scientific Reports |

### Infrastructure / exposure

| Dataset | Access | Use |
|---|---|---|
| Roads, rivers, settlements | OSM Overpass API / Geofabrik extracts | Road graph, distances, exposure |
| Villages / population | Census / OSM / state GIS | Priority + exposure |
| Critical facilities | OSM / state GIS | Priority |

### Benchmarks (not training data)

| Source | Use |
|---|---|
| NASA LHASA 2.0 (github.com/nasa/LHASA) | Beat-the-global-model benchmark over NER |
| ML-CASCADE / ILSM (IIT Delhi, Zenodo) | Closest published pipeline precedent; fallback prior for sparse pixels |

### Sensor feeds (PS-required, adapter-ready)

The PS Expected Solution explicitly lists sensor data alongside IMD and
satellite feeds. Prototype position: no physical deployment, but a
**Sensor Ingestion Adapter** is part of NGEN `fetch/` from day one:

| Feed | Format | Maps to | Prototype status |
|---|---|---|---|
| AWS/ARG rain gauges | IMD/NEDRP feed format | `rainfall_24h_mm`, `rainfall_7d_mm` | Recorded fixture |
| Soil-moisture probes | Probe telemetry → 0–1 volumetric | `soil_moisture` (overrides reanalysis where present) | Recorded fixture |

Adapter contract: timestamped, geo-tagged observations → the same feature
names as `05_FEATURE_SCHEMA_SIH26001.md`, tagged `source=sensor`. When live feeds exist, swap
the fixture for a connector — no schema or model change. Sensor gaps fall
back to gridded/reanalysis values and are listed in `missing_evidence`.
See `02_ARCHITECTURE_SIH26001.md` §5.1.

---

## B. Feature provenance table

Authoritative contract: `05_FEATURE_SCHEMA_SIH26001.md`. Summary:

| Feature | Grounding | Source type |
|---|---|---|
| `slope_angle`, `elevation`, `aspect`, `curvature`, `twi`, `spi` | SRTM DEM derivatives | Observed-derived |
| `rainfall_24h_mm`, `rainfall_7d_mm`, `rainfall_30d_mm` | IMD gridded (+GPM cross-check) | Observed |
| `soil_moisture` | ERA5/SMAP | Reanalysis proxy (tagged) |
| `ndvi`, `lulc` | Sentinel-2 | Observed |
| `lithology` | GSI Bhukosh | Survey-mapped |
| `distance_to_road` | OSM | Observed (crowd-maintained — QA note) |
| `distance_to_river` | DEM-derived network | Derived |
| `lineament_density`, `drain_density` | GSI + DEM | Derived |
| `previous_landslide` | Inventories above | Observed (incomplete — tagged) |

Known incompleteness (see `08_LIMITATIONS_SIH26001.md`): inventories lack
precise dates for many events (Sikkim/Nagaland best-dated); OSM rural
coverage varies; reanalysis moisture is coarse vs slope scale.

## C. Training-data construction

```text
Positive samples (event):
  inventory location + event date (where dated; else season-window with tag)
  + antecedent rainfall (7d, 30d) + triggering rainfall (24h)
  + soil moisture at event time + static terrain/geology/LULC/proximity

Negative samples (no-event):
  random locations >300 m from any known landslide
  + same temporal conditioning + same static features
```

Sampling ratio, buffer distance, and date-window rules freeze in
`04_MODEL_PLAN_SIH26001.md` before training. Spatial-cluster CV (not random
split) is mandatory — spatial autocorrelation makes random splits lie
(lesson carried from v1's seed-leakage proof).

## D. NGEN versioning + data rules

- Every NGEN run writes a manifest: source versions, download dates,
  seeds, CRS/grid, checksums → committed alongside code.
- Raw downloads + feature matrices live outside git (Drive / HF / LFS);
  small samples only in-repo. Same `.gitignore` policy as v1.
- `previous_landslide` and any season-window positives carry an
  `evidence_quality` tag consumed by missing-evidence reporting.

## E. Phase-0 download checklist

```text
[ ] IMD daily gridded rainfall (0.25°) for NER bbox — pilot period first, then full 1901–present record
[ ] SRTM DEM 30m for pilot extent (then 8 states)
[ ] GSI Bhusanket NER landslide inventory (filter + export)
[ ] ERA5 soil moisture for NER (pilot period first)
[ ] Sentinel-2 cloud-free composite → NDVI + LULC (pilot extent)
[ ] GSI Bhukosh lithology for pilot extent
[ ] OSM roads + rivers + settlements (Overpass / Geofabrik)
[ ] Published inventories (Zenodo: Mizoram, Dibang, ILSM points)
[ ] NASA COOLR export for NER bbox
[ ] Compute terrain derivatives (slope/aspect/curvature/TWI/SPI/drain density)
[ ] Census village/population for pilot extent
```

Pilot extent freezes in ADR before Phase-0 completion (candidate: district
cluster with best-dated inventory — Sikkim or Nagaland per research §3.2).
