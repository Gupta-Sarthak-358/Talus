# TALUS Data Plan — SIH26001

**Status:** Built — pilot + training + live blend complete 2025-11-15 · **Trace to:** `05_FEATURE_SCHEMA_SIH26001.md`, `04_MODEL_PLAN_SIH26001.md` · **Source:** `docs/SIH26001_RESEARCH.md` §6, §9

> Grounding rule (inherited from v1, strengthened): every feature traces to a real source with a provenance tag. v2 values are **observed or derived from observations** — no synthetic draws. Where a source is a proxy (reanalysis, published-map uniform, demo topology), the proxy status is tagged, not hidden.

---

## A. Source inventory (all verified accessible Nov 2025)

### Rainfall — observed vs forecast separation

| Dataset | Access | Account | Use | Endpoint / File |
|---|---|---|---|---|
| IMD 0.25° daily gridded 1901–2024 | imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html | No | Historical truth: antecedent + triggering rain (24h/7d/30d) | `data/raw/imd/ind2024_rfp25.nc` → `gangtok_rainfall_2024.csv` (wettest 7d 2024-06-16: 14.0/327.3/712.2) |
| IMD district rainfall (data.gov.in) | api.data.gov.in | **IMD_API_KEY gated** | Live IMD district blend (East Sikkim / North Sikkim / Darjeeling) | `GET /api/forecast/imd-live:1124` (tries IMD first, falls back to Open-Meteo) |
| Open-Meteo 7-day forecast | api.open-meteo.com/v1/forecast | No | Live forecast blend (ECMWF/GFS, daily precipitation_sum/probability_max, 1h cache) | `GET /api/forecast/live:1154`, `backend/app/main.py:1104` `_LIVE_CACHE` 3600s |
| IMD forecast fixture | — | — | Demo fallback (recorded, never hides provenance) | `GET /api/forecast/rainfall` `forecast.json:1` (monga-mdl + dahal-144 templates) |

IMD grid: 135×129, 66.5°E–100°E × 6.5°N–38.5°N, 0.25°. NER bbox (88°E–98°E, 21°N–29°N) lies fully inside. Live IMD requires `IMD_API_KEY`; absent key → Open-Meteo blend + fixture fallback (honest, never 500).

### Soil moisture — CCI v09.2 is truth

| Dataset | Access | Account | Use |
|---|---|---|---|
| ESA CCI COMBINED TCDR v202505 (DOI 10.24381/cds.d7782f18) | CDS (cds.climate.copernicus.eu) | Free CDS account (system py311 xarray) | **Observed** volumetric soil moisture (stronger pedigree than ERA5 reanalysis; ERA5 request path never needed — `manifest.sample.json:22` notes) |
| SWI 3-tank (JMA Okada 1992) | Local `backend/app/swi.py:14` | None | Warning-layer saturation from rainfall series + forecast: L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01, `tanh(SWI/100)` |

Raw CCI: 7 daily global NC files (LOCAL ONLY), reliability-killer flag bits 4|8|16|32 masked (7/7 valid, flags=[0]), nearest 0.25° cell (27.375,88.625) per slope per day, window-mean 0.271 all slopes (same-cell consequence, stated, `manifest.sample.json:22`).

### Terrain (DEM + derivatives)

| Dataset | Access | Use |
|---|---|---|
| SRTM 30m USGS SRTMGL1.003 v3 tile n27_e088 | USGS EarthExplorer / NASA Earthdata | Elevation base `n27_e088_1arc_v3.tif` 3601×3601 int16 EPSG:4326 88–89E/27–28N |
| Derived: slope, aspect, curvature, TWI, SPI, drain density | Computed in NGEN `terrain/` `usgs_s234.json:1` | Structural + hydrological features (Horn-1981, D8 priority-flood TWI=ln(a/tanB), SPI=a·tanB on 7.7×5.9km crop, 90 voids 0.17% neighbour-mean filled) |

### Satellite (vegetation / land use)

| Dataset | Access | Use |
|---|---|---|
| Sentinel-2 L2A S2B_45RXL_20241129 (cloud 0.02, STAC earth-search AWS) | ESA Copernicus (no account) | NDVI via B04/B08+SCL: S1 0.718 veg, S2 0.139 bare road-cut, S3 0.817 veg, S4 0.468 veg `s234_ndvi.json:1` |
| ESA WorldCover 2021 v200 10m tile N27E087 | AWS Open Data (no sign-in) | LULC via 3×3 mode centre-agreement 9/9: 10→FOREST / 50→BUILT (S1 FOREST S2 BUILT S3 FOREST S4 BUILT) `s234_lulc.json:1` 76.7% overall accuracy |

### Geology / tectonics

| Dataset | Access | Use | Evidence |
|---|---|---|---|
| GSI Bhukosh lithology WFS/WMS | bhukosh.gsi.gov.in/Bhukosh/Public | Material strength class | **PROXY-published-map uniform** `lingtse_granite_gneiss` (`manifest.sample.json:93`) — **timeout 15s both WFS/WMS 2025-11-14 live probe logged** `evidence/bhukosh_vector_attempt.json:1` grade PROXY-published-map (not STUB). Prior fallback: DRAP Fig25 + NESAC Bhuvan SK_LN50K_0506 verified WMS. Re-run `extract_lithology.py --wfs` when vector reachable. |
| Lineament density | GSI + DEM derived | Tectonic weakness | Uniform 0.8 km/km² (published-map PROXY, omitted from X when uniform) |
| Seismic conditioning | USGS FDSN M5+ 26.5–28.5N/87.5–89.5E 1965–2024 | Post-quake 25% threshold drop 6 mo | `evidence/usgs_quakes.json:1` n=26, per-zone `seismic_dist_km / n50_rate / years_since` via `sih26001_model.py:_seismic_lookup` 59-year window, warning-conditioned `main.py:1525` `quake_factor 0.75` |

### Landslide inventories (labels — 2936 rows 1468+1468)

| Source | NER coverage | Access |
|---|---|---|
| GSI Bhusanket | 30,842+ all-India points | user-supplied `GSI_Landslide_Inventory.shp.zip` + `evidence/sikkim_gangtok_sample.csv:1` 6 rows + `sikkim_join.json:6` 693 Sikkim haversine join |
| GSI Gangtok report PDF | 7 Gangtok events | `sikkim_report_gangtok.csv:1` |
| USGS quakes as conditioning | 26 events 1965–2024 | `usgs_quakes.json:1` |
| ILSM (Sharma et al. 2024) | 154,329 pan-India 100m | Zenodo (open) |
| Monga & Ganguli 2026 | 490 NEH events + rainfall 2006–2019 | Published paper |
| Mihu et al. 2026 (Dibang) | 537 points | Published paper |
| NEHU/Agrawal (Meghalaya) | 1,330+ points | Published paper |
| NASA COOLR export | Crowdsourced | Viewer download (REST 404 stale, viewer CSV used) |

Dedupe <50m, season-window proxy target tagged `approximate` / `dated-only-negative`, evidence_quality per row.

### Infrastructure / exposure

| Dataset | Access | Use | Honesty |
|---|---|---|---|
| Roads, rivers, settlements | OSM Overpass API (`[out:json][timeout:30];(way["highway"](bbox););out geom;`) 0.16° bbox per corridor | Road graph, distances, exposure, restriction catalogue | **Counts proven, geometry demo topology**: Gangtok 1014 / Lachung 226 / Darjeeling 504 `evidence/roads_osm_provenance.json:1` example way 47416074 NH310A trunk; **R1–R4 fixture geometry is centroid-aligned deterministic** (not OSM trace) to keep R2-avoidance pedagogical, stated explicitly. Full OSM traces available on demand. |
| Villages / population | Census / DRAP `Gangtok_Disaster_Resilience_Action_Plan.pdf:31` / OSM | Priority + exposure |
| Panchayat tiling (100 tiles, WILL→PARTIAL) | Panchayat-scale tiling 10x10 26.95-28.05/88.05-89.0 | `panchayat_tiles.json` 100 tiles GET /api/panchayat/tiles (frozen 12 untouched) | WILL→PARTIAL |
| Copernicus COP30 vs SRTM | Copernicus DEM GLO-30 10m/30m TanDEM-X | `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4 GET /api/terrain/copernicus (BigGIS proxy) | WILL→PARTIAL |
| Dense AWS 10-min | AWS/ARG gauges MQTT | `backend/app/aws_ingest.py` 12 gauges GET /api/aws/gauges QA flagged spike | WILL→PARTIAL |
| Wound / runout screening | Sentinel-2 pair pre/post monsoon + SRTM steepest descent | `evidence/wound_map.json:1` 4 candidates review-queue (S1/S3 near R2/R3, roadside NDVI loss ≥0.3 ≤150m road, SCL-gated) + `runout_exposure.json:1` screening approx buildings downstream (fetch capped 400/zone), not debris-flow simulator |

### Benchmarks (not training data)

| Source | Use |
|---|---|
| NASA LHASA 2.0 (github.com/nasa/LHASA) | Beat-the-global-model benchmark over NER |
| ML-CASCADE / ILSM (IIT Delhi, Zenodo) | Closest published pipeline precedent; fallback prior for sparse pixels |

### Sensor feeds (PS-required, adapter-ready)

The PS Expected Solution explicitly lists sensor data alongside IMD and satellite feeds. Prototype position: no physical deployment, but a **Sensor Ingestion Adapter** is part of NGEN `fetch/` from day one:

| Feed | Format | Maps to | Prototype status |
|---|---|---|---|
| AWS/ARG rain gauges | IMD/NEDRP feed format | `rainfall_24h_mm`, `rainfall_7d_mm` + SWI `swi_for_zone` | Recorded fixture + `live_feed.sample.json` → `GET /api/live/feed:1248` (simulator wins, sample fallback) |
| Soil-moisture probes | Probe telemetry → 0–1 volumetric | `soil_moisture` (overrides CCI where present, SWI recomputed) | Recorded fixture |

Adapter contract: timestamped, geo-tagged observations → same feature names as `05_FEATURE_SCHEMA_SIH26001.md`, tagged `source=sensor`. When live feeds exist, swap fixture for connector — no schema/model change. Sensor gaps fall back to CCI/rain-derived SWI and are listed in `missing_evidence`. Live tick simulator `scripts/local_sensor_sim.py` → `runs/live_feed.json` + `runs/sim_audit.jsonl` (`GET /api/live/audit:1308`). See `02_ARCHITECTURE_SIH26001.md` §5.1.

---

## B. Feature provenance table

Authoritative contract: `05_FEATURE_SCHEMA_SIH26001.md`. Summary (22 cols = 17 numeric + lulc + 4 keys/target):

| Feature | Grounding | Source type | Per-zone evidence |
|---|---|---|---|
| `slope_angle`, `elevation`, `aspect`, `curvature`, `twi`, `spi` (+ `spi_log`) | SRTM n27_e088 derivatives | Observed-derived | `usgs_s234.json:1` per-slope bilinear/Horn/D8 |
| `rainfall_24h_mm`, `rainfall_7d_mm`, `rainfall_30d_mm` | IMD 0.25° historical truth (observed) | Observed | `ind2024_rfp25.nc` 14.0/327.3/712.2 `2024-06-16` + `manifest.training.json:30` climatology |
| live rainfall | Open-Meteo 7-day + IMD_API_KEY district | Live forecast (separated, never silent) | `GET /api/forecast/live:1154` `GET /api/forecast/imd-live:1124` `_LIVE_CACHE` 1h, provenance header |
| `soil_moisture` | CCI v09.2 COMBINED TCDR | Satellite-observed (stronger than ERA5) | `gangtok_soil_cci.csv:1` 0.271 |
| `swi` (warning overlay) | JMA 3-tank from rainfall series + forecast | Physics overlay (scoring frozen) | `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12, `GET /api/soil/swi:1203` |
| `ndvi` | Sentinel-2 S2B_45RXL | Observed | `s234_ndvi.json:1` S1 0.718 S2 0.139 S3 0.817 S4 0.468, scene 2024-11-29 quasi-static |
| `lulc` | ESA WorldCover 2021 v200 10m N27E087 | Observed | `s234_lulc.json:1` S1 FOREST S2 BUILT S3 FOREST S4 BUILT, accuracy 76.7% |
| `lithology` | GSI Bhukosh PROXY-published-map | Survey-mapped PROXY uniform | `lingtse_granite_gneiss` uniform, omitted from X `manifest.training.json:263`, `bhukosh_vector_attempt.json:1` timeout |
| `distance_to_road` | OSM | Observed (crowd-maintained — counts proven 1014/226/504, topology demo) | `s1_osm_nearest.json:1` center-approx, `osm-qa-unverified` kept, `roads_osm_provenance.json:1` |
| `distance_to_river` | DEM-derived network | Derived | `catchment_s234.json:1` |
| `lineament_density`, `drain_density` | GSI + DEM | Derived PROXY uniform | `0.8` uniform, spillover honest |
| `previous_landslide` | Inventories above | Observed (incomplete — tagged, leakage-guarded omitted from X) | `sikkim_join.json:6` S2 hit 286.7m SK/ESK/78A11/2019/02, `prev_rate` training sidecar |
| `seismic_dist_km`, `seismic_n50_rate`, `seismic_years_since` | USGS 26 quakes 1965–2024 | Observed conditioning | `usgs_quakes.json:1` → `sih26001_model.py:_seismic_lookup` 59-year window, 3 feats |
| `wound` | Sentinel-2 pair NDVI loss review-queue | Screening (not confirmed cut) | `wound_map.json:1` 4/2936 positive, `GET /api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` |
| `isolation`, `warning_state` | Road graph + SWI + thresholds | Operational overlay (not in X) | `_isolation_for_location:1326` R4 bottleneck + `GET /api/warning/state:1449` 6 states |

Known incompleteness (see `08_LIMITATIONS_SIH26001.md`): lithology/lineament uniform (Bhukosh vector unreachable), OSM geometry demo topology, IMD live requires key, 12 demo slopes not Gram Panchayat scale.

## C. Training-data construction

```text
Positive samples (event, tagged approximate when undated → season-window JJAS proxy):
 inventory location + dated or undated season window + antecedent rainfall (7d, 30d) + triggering (24h)
 + CCI soil 0.271 + SWI-derived effective rain + static terrain/geology/LULC/proximity + seismic 3

Negative samples (no-event):
 random locations >300m from any known landslide + same temporal conditioning + same static features

Wound: roadside NDVI loss review-queue appended as feature 4/2936 (positive rare, not leaked)

Training matrix: 2936 rows 1468+1468 (seed 42), 17 numeric (+spi_log) + lulc one-hot drop_first → encoder → RF500/XGB/LGBM
 Isotonic on RF OOF, Bayes 0.5→0.01 field view; lithology/lineament/previous_landslide omitted when uniform/leakage
```

Sampling ratio, buffer distance, and date-window rules frozen in `04_MODEL_PLAN_SIH26001.md` before training. Spatial-cluster CV (KMeans-8, GroupKFold, not random split) is mandatory — spatial autocorrelation makes random splits lie (lesson carried from v1's seed-leakage proof).

## D. NGEN versioning + data rules

- Every NGEN run writes a manifest: source versions, download dates, seeds, CRS/grid, checksums → committed alongside code (`manifest.sample.json:1` + `manifest.training.json` + `warning_thresholds.json:1` + `roads_osm_provenance.json:1` + `bhukosh_vector_attempt.json:1` + `usgs_quakes.json:1`).
- Raw downloads + feature matrices live outside git (Drive / HF / LFS, `LOCAL ONLY` per `.gitignore`); small samples only in-repo (22-col `feature_matrix.sample.csv:1` 12 rows, `feature_matrix.training.sample.csv` 20 rows, committed). Same `.gitignore` policy as v1.
- `previous_landslide` and any season-window positives carry an `evidence_quality` tag consumed by missing-evidence reporting and are omitted from X when leakage/uniformity dictates.

## E. Phase-0 download checklist (built — 3 corridors frozen 2025-11-15)

```text
[x] IMD daily gridded 0.25° — 124 files 1901–2024 data/raw/imd/ind*.nc + data/processed/imd/gangtok_rainfall_2024.csv (wettest 7d 2024-06-16: 14.0/327.3/712.2) + Open-Meteo live 7-day GET /api/forecast/live:1154 + IMD_API_KEY gated GET /api/forecast/imd-live:1124 + 30-yr climatology manifest.training.json:30
[x] SRTM DEM 30m — USGS n27_e088_1arc_v3.tif → usgs_s234.json (6 derivatives, TWI/SPI via D8, 90 voids 0.17% filled)
[x] GSI Bhusanket — 30,842 points GSI_Landslide_Inventory.shp.zip + 777 PDF rows p659-676 → 764 deduped Sikkim manifest.training.json:42 + 693 Sikkim join sikkim_join.json:6 (S2 hit 286.7m)
[x] Soil — CCI C3S-SOILMOISTURE TCDR v202505 7-day gangtok_soil_cci.csv 0.271 7/7 valid flags=[0] + SWI swi.py:14 L1=15 L2=60 L3=60 a1=0.10 b1=0.12
[x] Sentinel-2 / WorldCover — S2B_45RXL_20241129 + N27E087 → s234_ndvi.json (0.718/0.139/0.817/0.468) + s234_lulc.json (FOREST/BUILT 9/9) 10m 76.7%
[x] GSI Bhukosh lithology — PROXY-published-map lingtse_granite_gneiss uniform, WFS/WMS timeout 15s bhukosh_vector_attempt.json:1, NESAC Bhuvan SK_LN50K_0506 verified WMS prior
[x] OSM roads + rivers — Overpass bbox 0.16° → gangtok 1014 / lachung 226 / darjeeling 504 roads_osm_provenance.json:1 example 47416074 NH310A trunk + warning_thresholds.json:1 per-zone 385/395/410/375 + fixture demo topology R1–R4 deterministic
[x] USGS quakes — 26 events M5+ 1965–2024 26.5–28.5N/87.5–89.5E usgs_quakes.json:1 → seismic_dist_km / n50_rate / years_since per zone (59y)
[x] Published inventories — Dibang/Mizoram/ILSM via shapefile + PDF above → 2936 rows 1468+1468
[x] Wound + runout screening — wound_map.json:1 4 candidates review-queue + runout_exposure.json:1 steepest descent buildings capped 400/zone
[x] Terrain derivatives — slope/aspect/curvature/TWI/SPI/drain usgs_s234.json + catchment_s234.json
[x] Census village/population — Gangtok wards via DRAP Gangtok_Disaster_Resilience_Action_Plan.pdf:31 + per-corridor shelters/phones in warning kits
```

Pinned pilot: Gangtok cluster 27.3389/88.6065 27.315–27.345N/88.595–88.612E + Lachung Valley 27.69/88.74 + Darjeeling hills 27.041/88.263 (locations.json:1) — Sikkim per research §3.2, best-dated + best tile coverage, 12 demo slopes (Gram Panchayat gap stated in §8).

---

**2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched):**

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT
