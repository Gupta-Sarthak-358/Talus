# TALUS Data Plan — SIH26001

**Status:** Built — pilot + training complete 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · **Trace to:** `05_FEATURE_SCHEMA_SIH26001.md`,
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

## E. Phase-0 download checklist (built — Gangtok pilot frozen 2026-09-04)

```text
[x] IMD daily gridded rainfall (0.25°) — 124 files 1901–2024 `data/raw/imd/ind*.nc` → `gangtok_rainfall_2024.csv` (wettest 7d 2024-06-16: 14.0/327.3/712.2) + 30-yr climatology `manifest.training.json:30`
[x] SRTM DEM 30m — USGS `n27_e088_1arc_v3.tif` → `usgs_s234.json` (6 derivatives, TWI/SPI via D8)
[x] GSI Bhusanket — `30,842` points `GSI_Landslide_Inventory.shp.zip` + `777` PDF rows `p659-676` → `764` deduped `manifest.training.json:42`
[x] Soil — CCI `C3S-SOILMOISTURE` 7-day `gangtok_soil_cci.csv` `0.271` (ERA5 path never needed — CCI stronger pedigree)
[x] Sentinel-2 / WorldCover — `S2B_45RXL_20241129` + `N27E087` → `s234_ndvi.json` / `s234_lulc.json` (FOREST/BUILT 9/9)
[x] GSI Bhukosh lithology — NESAC map `s234_lithology.json` `lingtse_granite_gneiss` PROXY-published-map
[x] OSM roads + rivers — `606` test bbox / `6698/1320` training bulk `out center` → `s*_osm_nearest.json`
[x] Published inventories — Dibang/Mizoram/ILSM via shapefile + PDF above
[x] NASA COOLR export — viewer download path logged (REST endpoint stale 404, viewer CSV/SHP used)
[x] Terrain derivatives — `slope/aspect/curvature/TWI/SPI/drain` `usgs_s234.json` + `catchment_s234.json`
[x] Census village/population — Gangtok wards via DRAP `Gangtok_Disaster_Resilience_Action_Plan.pdf:31`
```

Pilot extent frozen: Gangtok cluster `27.3389/88.6065` `27.315-27.345N/88.595-88.612E` `NGEN_PROVENANCE_S1.md:10` — Sikkim per research §3.2, best-dated + best tile coverage.
