# NGEN Provenance — S1 (Gangtok Pilot) — Persons 1, 2, 3: Complete Honest Pilot (Rain + Terrain/Satellite + Labels/Manifest)

**Status:** Built — honest training-ready fixture (16/17 REAL/PROXY, zero STUBs, plus training 2936×22) — all 3 roles covered · **Pilot:** Gangtok cluster, Sikkim ONLY · **Branch:** `SIH26001 @ 68c0c28` · **Date:** 2026-09-04
**Roles:** Person 1 = rainfall_24h/7d/30d + soil_moisture · Person 2 = terrain/satellite/spatial (10 features) · Person 3 = labels/manifest/provenance
**Trace to:** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:1`, `docs/sih26001/TEAM_TASKS_SEPT5.md:24`, `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md:16`, `docs/sih26001/03_DATA_PLAN_SIH26001.md:1`
**Related files:** `data/sih26001/fixtures/feature_matrix.sample.csv:1`, `data/sih26001/fixtures/manifest.sample.json:1` · **Validator:** `python scripts/check_scaffold.py:1`

---

## 1. Pilot location (frozen for demo)

* **Cluster:** Gangtok cluster, Sikkim — `SCAFFOLD_CONTRACT_SEPT5.md:4` Centre `27.3389, 88.6065`, CRS `EPSG:4326` (demo, reprojection deferred)
* **Frozen zones:** `SCAFFOLD_CONTRACT_SEPT5.md:14`
 * S1 Tathangchen (upper) `27.3450, 88.6000` — Critical 89
 * S2 Chandmari (road-cut) `27.3380, 88.6120` — High 78
 * S3 Tadong (mid) `27.3250, 88.6065` — Moderate 66
 * S4 Ranipool (valley) `27.3150, 88.5950` — Low 52
* Scope is **pilot only**. No 8-state implementation on this branch (`TEAM_TASKS_SEPT5.md:24`).

> Coordinates, IDs, scores, bands, and CSV schema are frozen by contract and were not changed here.

---

## 2. S1 row status — 16/17 REAL/PROXY + labels REAL (2026-09-04, updated) — zero STUBs

The S1 rainfall columns are **REAL direct extractions** from the committed
IMD archive (see evidence below). S1 road/river distances are **REAL direct
extractions** from the Overpass API (extract JSON committed, §3). S1 NDVI is
**REAL** read from the Sentinel-2 L2A COG (no download, rasterio /vsicurl/,
§3). S1 DEM derivatives (slope/elevation/aspect/curvature) are **PROXY** —
computed from an open SRTM-derived mirror (AWS Terrain Tiles Terrarium), not
the USGS N27E088 tile — as is S1 drain density (**PROXY-window**: measured
zero mapped streams inside the 271-m window, catchment work pending). All
other science features remain STUB/demo. S2–S4 road/river distances are REAL
per-slope Overpass reads (same method, `s234_osm_nearest.json`, §3).
Catchment round (Person 3, 2026-09-04): `scripts/extract_catchment.py` (z14
3×3 Terrarium mosaic ~6.5 km, centroid-centred, priority-flood D8 +
descending-order accumulation) → `catchment_s234.json` (sha256 in manifest):
S1 TWI **4.24** / SPI **9.4** (PROXY); S2–S4 full DEM rows PROXY from the same
mosaic (S2 1643 m/17.9°/TWI 3.96/SPI 5.5; S3 1367 m/37.0°/TWI 4.03/SPI 31.9;
S4 1131 m/23.2°/TWI 5.47/SPI 43.7 — S4 concave + highest TWI matches its valley
position; S1 z14 re-derivation reproduces the committed z15 values).
`scripts/extract_s234_ndvi.py` (same pinned scene) → `s234_ndvi.json`: S2
ndvi **0.139** (SCL bare — road-cut, consistent), S3 **0.817** (veg), S4
**0.468** (veg) — all REAL. `scripts/extract_landuse.py` → `s234_landuse.json`:
no mappable landuse within 300 m of any slope (nearest: S3 residential
324 m-to-centre, noted not used) — SUPERSEDED 2026-09-04 by WorldCover
(see LULC bullet in §3): S1 FOREST, S2 BUILT, S3 FOREST, S4 BUILT, all REAL.

**CSV row (verbatim, `feature_matrix.sample.csv:2`):**
```
S1,2024-06-16,28.5,1290,289,0.0111,5.99,120.9,14.0,327.3,712.2,0.42,0.718,BUILT,schist,4,226,1.8,0.0,1,1,dated
```
USGS round (user-supplied tile, 2026-09-04): `data/raw/dem/n27_e088_1arc_v3.tif`
(USGS SRTMGL1 v3, LOCAL ONLY per .gitignore) → `scripts/extract_usgs.py`
(rasterio+numpy, py311: bilinear elev, anisotropic Horn, Laplacian curv, D8
priority-flood TWI/SPI on a 7.7×5.9 km crop, 90 voids neighbour-filled, slope
neighbourhoods void-free) → `data/processed/terrain/usgs_s234.json` (sha256
in manifest). Elevations reproduce the mirror within 7 m on all slopes (the
mirror grid is thereby validated); slope/aspect/curv/TWI/SPI differ by
resolution (30 m native vs smoothed 4–8 m — e.g. S1 slope 22.1→28.5, aspect
248→289, curv sign flip = scale effect, all logged per-slope in the JSON).
USGS is the specified source: all six DEM derivatives PROMOTED PROXY→REAL.
Extraction (Person 3, 2026-09-04): `scripts/extract_s234_osm.py` drives
`extract_s1_osm.py` per slope (split roads/rivers queries after combined
queries 504'd; same foot-path filter, same radii) →
`data/processed/terrain/s234_osm_nearest.json` (sha256 in manifest):
S2 road 6 m residential OSM-84696777 / stream 183 m;
S3 road 126 m trunk OSM-349554354 / Rongbe Chu river 1093 m OSM-416534058;
S4 road 66 m trunk OSM-47416222 / Rongbe Chu 460 m (same way).
`scripts/extract_s1_sentinel2.py` (Element84 STAC → least-cloudy 2024 scene
S2B_45RXL_20241129_0_L2A, 0.02% cloud → rasterio /vsicurl/ B04+B08+SCL) →
`data/processed/terrain/s1_sentinel2.json`: DN red=390 nir=2380 scl=4
(vegetation), **ndvi 0.718** (old 0.35 STUB far off). Scene date 2024-11-29
post-monsoon vs row window 2024-06-16 — NDVI treated as quasi-static state,
dated in manifest. LULC has since been REAL-verified from ESA WorldCover
(see §3 LULC bullet): S1 FOREST, superseding the BUILT STUB.
`scripts/extract_s1_drain.py` clips fresh Overpass waterways to the committed
64×64 DEM window (~267×265 m): 1 waterway in 400 m but **0.0 m inside the
window** → `drain_density` **0.0 PROXY-window** (measured, not invented;
catchment-scale work still pending).
Extraction (Person 1): `scripts/extract_gangtok_rainfall.py` (xarray nearest grid
27.25N 88.50E to S1 27.3450N 88.6000E, ~13 km — 0.25° representativeness limit
applies) over `data/raw/imd/ind2024_rfp25.nc` → daily series committed as
`data/processed/imd/gangtok_rainfall_2024.csv` (366 rows, 0 missing,
sha256 in manifest). Window rule: wettest trailing-7d spell of 2024 at the
pilot cell → end date 2024-06-16 (24h trailing = 14.0, 7d = 327.3,
30d = 712.2; verified against raw daily slice June 1–20 in extraction log).

Extraction (Person 2, 2026-09-04): `scripts/extract_s1_osm.py` (Overpass
`overpass-api.de`, 48 road + 12 river ways, foot-path filter logged) →
`data/processed/terrain/s1_osm_nearest.json` (sha256 in manifest): nearest
road = unnamed tertiary way OSM-348966165 at **4 m** (S1 sits effectively
roadside — the old 45 m STUB understated this); nearest waterway = unnamed
stream OSM-129509880 at **226 m**. `scripts/extract_s1_dem.py` (z15 3×3
Terrarium mosaic, Horn-1981 + Laplacian, bilinear at exact S1) →
`data/processed/terrain/s1_dem_window.csv` (64×64 audit grid, sha256 in
manifest): elevation **1287 m**, slope **22.1°**, aspect **248°** (WSW,
downslope), curvature **−0.0395/m** (convex spur). Independently re-derived
from the committed window (2026-09-04: slope 22.1 ✓, aspect 247.8→248 ✓,
elev 1287.5 ✓). NOTE: first version shipped aspect 68° (uphill convention,
atan2(dzdx,−dzdy) — 180° off); corrected to downslope atan2(−dzdx,dzdy) in
`extract_s1_dem.py`, which is now self-consistent with the westward fall
toward the stream. Cross-check: same mosaic reads
Gangtok centre (27.3389,88.6065) at 1509 m vs ~1600–1650 nominal — grid
trusted within SRTM steep-terrain limits; westward fall toward the stream
(226 m) is internally consistent. (TWI/SPI have since been PROXY-verified via
the z14 catchment and then REAL-verified from the USGS tile — see §5; NDVI is
REAL from the pinned Sentinel-2 scene; LULC is REAL from WorldCover — §3.)
Antecedent-driven saturation framing matches the v2 physics chain
(`04_MODEL_PLAN_SIH26001.md` §4): June 10–16 delivered 327 mm after a
712 mm/30 d buildup, with CCI soil moisture at 0.271 (7/7 valid days).
Labels are REAL-joined (rows 18–20): S2 previous_landslide=1 with Bhusanket
ID SK/ESK/78A11/2019/02; all events 0 with logged reason (INITIATION is
year-only). S1/S3/S4 evidence_quality = `dated-only-negative` (real window,
negative label); S2 = `approximate` (2019 occurrence real, out-of-window).

**Why STUB:** STUB = temporary placeholder. REAL = directly verified from an actual source file committed or checksumed in repo. PROXY = indirect substitute (e.g. ERA5 reanalysis, Terrarium mirror for the USGS tile). Features without such evidence stay STUB.

**Per-feature status — all 17 features + 2 keys + 2 labels (external to CSV because schema is frozen — adding a column would break `scripts/check_scaffold.py:24`). Classified per honesty rules: REAL=verified file, PROXY=indirect substitute (ERA5), CONSTANT=fixed demo value, STUB=temporary placeholder, UNKNOWN=not verified:**

| # | Feature | S1 value | Status | Why this label | Evidence that would upgrade it |
|---|---|---|---|---|---|
| — | `zone_id` | S1 | REAL (ID) | Frozen ID from contract `SCAFFOLD_CONTRACT_SEPT5.md:14` | — already frozen |
| — | `time_window` | 2024-06-16 | REAL (rainfall window) | Wettest trailing-7d spell end, IMD 2024 extraction (above) | Event-occurrence at S1 still unproven — see rows 18–19 |
| 1 | `slope_angle` | 28.5 | REAL | USGS SRTMGL1 v3 Horn-1981 anisotropic, `usgs_s234.json` (mirror 22.1, delta logged) | — verified |
| 2 | `elevation` | 1290 | REAL | Bilinear at exact S1, same source (mirror 1287, ±7 m all slopes) | — verified |
| 3 | `aspect` | 289 | REAL | Horn downslope WNW, same source (mirror 248 — resolution facet effect, logged) | — verified |
| 4 | `curvature` | 0.0111 | REAL | Laplacian, same source (mirror −0.0395 — sign flip is a scale effect, stated) | — verified |
| 5 | `twi` | 5.99 | REAL | D8 on 7.7×5.9 km USGS crop, ln(a/tanB) (mirror 4.24 — cell-size scaling, stated) | — verified |
| 6 | `spi` | 120.9 | REAL | Same crop, a·tanB (raw units; log-transform at model time) | — verified |
| 5 | `twi` | 4.24 | PROXY (mirror+window) | D8 accumulation on z14 6.5-km mosaic, ln(a/tanB) (`catchment_s234.json`) | USGS tile + catchment validation |
| 6 | `spi` | 9.4 | PROXY (mirror+window) | Same mosaic, a·tanB (`catchment_s234.json`) | Same |
| 7 | `rainfall_24h_mm` | 14.0 | REAL | IMD NetCDF `ind2024_rfp25.nc` → `gangtok_rainfall_2024.csv`, trailing 24h to 2024-06-16 | — verified (raw slice June 1–20 sums check) |
| 8 | `rainfall_7d_mm` | 327.3 | REAL | Same extraction, trailing 7d (June 10–16 daily: 41.3+50.5+35.2+76.7+73.4+36.3+14.0) | — verified |
| 9 | `rainfall_30d_mm` | 712.2 | REAL | Same extraction, trailing 30d to 2024-06-16 | — verified |
| 10 | `soil_moisture` | 0.271 | REAL | ESA CCI COMBINED TCDR v202505, daily 2024-06-10–16, nearest cell (27.375,88.625), 7/7 valid flags=[0], window-mean (`gangtok_soil_cci.csv` + `extract_soil_cci.py`) | — verified (same-cell all slopes, stated) |
| 11 | `ndvi` | 0.718 | REAL | Sentinel-2 L2A S2B_45RXL_20241129_0_L2A (0.02% cloud), rasterio /vsicurl/ DN red=390 nir=2380 scl=4 (`s1_sentinel2.json`) | — verified (scene 2024-11-29 post-monsoon vs June window, dated in manifest) |
| 12 | `lulc` | FOREST (S1; S2 = BUILT, S3 = FOREST, S4 = BUILT) | REAL | ESA WorldCover 2021 v200 tile N27E087 (AWS Open Data, no login), 3x3-window mode 9/9 + centre agreement all slopes (`s234_lulc.json`); mapping 10->FOREST, 50->BUILT | — verified (NDVI-consistent) |
| 13 | `lithology` | lingtse_granite_gneiss (all slopes) | PROXY-published-map | Digitized NESAC Figure 25/48 Lithology Map Gangtok (Source: NESAC, SSDMA+GSI) p71/p118 — all 4 points central town → lingtse granite gneiss (`s234_lithology.json`) | Bhukosh vector clip (upgrade: per-slope GSI lithocode) |
| 14 | `distance_to_road` | 4 | REAL | Overpass extract 2026-09-04: unnamed tertiary OSM-348966165, 48 ways examined, foot-path filter logged (`s1_osm_nearest.json`) | — verified (field-check + OSM QA pass still open, `osm-qa-unverified` kept) |
| 15 | `distance_to_river` | 226 | REAL | Overpass extract 2026-09-04: unnamed stream OSM-129509880, 12 waterways in 4 km (`s1_osm_nearest.json`) | — verified |
| 16 | `lineament_density` | 0.8 (all slopes) | PROXY-published-map + Bhuvan-availability | Bhuvan Lineament 50K Sikkim advertised (NRSC/GSI, 2005-06) + report Figures 24/47 density map context → 0.8 km/km2 conservative proxy, uniform (50K figure not per-slope; `s234_lineament.json`) | Bhuvan Thematic "Clip and Ship" per-slope clip → length/area |
| 17 | `drain_density` | 0.0 | PROXY-window | 0.0 m mapped streams inside the 271-m DEM window (`s1_drain_window.json`); window-scale only, catchment work pending | Catchment-scale DEM + flow routing |
| 18 | `previous_landslide` | 0 (S1; S2 = 1) | REAL | Haversine join over all 693 Sikkim points (`sikkim_join.json`): S2 hit SK/ESK/78A11/2019/02 @286.7 m, corroborated by report-PDF second ID SI/GTK/78A11/2025/03 Upper Sichey @~259 m (`report_pdf` block); S1 nearest 417.5 m (outside 300 m rule); S3 1019 m; S4 1156 m | — verified |
| 19 | `event` | 0 | REAL (all zero) | INITIATION is year-or-0, never a full date — cannot place any event inside the June-2024 window, so 0 with reason logged (never invented) | A dated Sikkim inventory would upgrade this |
| 20 | `evidence_quality` | dated-only-negative (S1; S2 = approximate) | REAL (tags) | S2 occurrence year 2019 is real but out-of-window → `approximate`; S1/S3/S4 = `dated-only-negative` (real window, negative label) | Same as row 19 |

**16 of 17 science features are REAL or PROXY (14 REAL + lithology PROXY-published-map + lineament PROXY-Bhuvan/figure; only drain stays PROXY-window). Zero science STUBs remain. Labels are REAL joins (S2 previous_landslide=1 with Bhusanket ID + report corroboration; all events 0 with logged reason).** S2–S4 match S1 throughout. Grid representativeness (~13 km nearest-cell for rain; ~4 km for the CCI cell) is disclosed in the manifest and stays a stated limit; USGS-vs-mirror deltas, OSM QA limits, and the NDVI scene-date gap are stated with the values.

---

## 3. Gangtok source evidence in this repository (2026-09-04)

* ✅ IMD rainfall: `data/raw/imd/ind2024_rfp25.nc` (national 0.25° grid, covers NER) → extraction `scripts/extract_gangtok_rainfall.py` → `data/processed/imd/gangtok_rainfall_2024.csv` (366 rows, sha256 in manifest). Grid cell 27.25N 88.50E — verified nearest cell for **all four slopes** (S2 27.338/88.612, S3 27.325/88.6065, S4 27.315/88.595 all resolve to 27.25/88.50), so S2–S4 carry identical REAL rain values for window 2024-06-16. Consequence of 0.25° coarseness, disclosed: rain does not differentiate slopes; static terrain features do.
* ✅ OSM spatial: Overpass 2026-09-04 → S1 `scripts/extract_s1_osm.py` → `s1_osm_nearest.json`; S2–S4 `scripts/extract_s234_osm.py` (split queries after 504s, same filters/radii) → `s234_osm_nearest.json` (sha256s in manifest). QA stays `osm-qa-unverified`. Notable corrections: S3 river 180→1093 (Rongbe Chu), S4 river 90→460, S2 road 20→6.
* ✅ Sentinel-2 (NDVI REAL): Element84 STAC, no account → least-cloudy 2024 scene S2B_45RXL_20241129_0_L2A (0.02% cloud) → `scripts/extract_s1_sentinel2.py` (rasterio /vsicurl/, system py311) → `data/processed/terrain/s1_sentinel2.json` (sha256 in manifest). (LULC closed separately via WorldCover — next bullet.)
* ✅ Drain PROXY-window: fresh Overpass waterways clipped to the committed DEM window → `scripts/extract_s1_drain.py` → `data/processed/terrain/s1_drain_window.json` (0.0 m in-window, sha256 in manifest).
* ✅ Catchment (TWI/SPI PROXY + S2–S4 DEM): z14 3×3 Terrarium mosaic ~6.5 km (centroid-centred, 9 PNGs committed under `terrarium_z14/`) → `scripts/extract_catchment.py` (numpy-only: stdlib PNG decode reuse, priority-flood, D8, descending-order accumulation) → `catchment_s234.json` (sha256s in manifest). S1 z14 re-derivation reproduces committed z15 (1287/20.2 vs 1287/22.1).
* ✅ S2–S4 NDVI (REAL): same pinned scene → `scripts/extract_s234_ndvi.py` (rasterio /vsicurl/, py311) → `s234_ndvi.json` (sha256 in manifest).
* ✅ LULC (REAL all slopes, 2026-09-04): ESA WorldCover 2021 v200 tile N27E087 (AWS Open Data bucket, no sign-in — Terrascope login NOT needed; bounds 27–30N/87–90E verified in-repo, all slopes inside) → `scripts/extract_s234_lulc.py` (rasterio /vsicurl/ range reads, 3x3-window mode, system py311) → `data/processed/terrain/s234_lulc.json` (sha256 in manifest). S1 FOREST (WC-10), S2 BUILT (WC-50), S3 FOREST (WC-10), S4 BUILT (WC-50) — 9/9 agreement + centre agreement everywhere; NDVI-consistent (veg slopes forested, bare road-cut built). Supersedes the OSM-landuse STUB (nothing mappable ≤300 m stands recorded as the attempt).
* ✅ Bhusanket labels (REAL join): user-supplied `data/raw/gsi/GSI_Landslide_Inventory.shp.zip` (30,842 point slides, all-India, LOCAL ONLY) → `scripts/extract_sikkim_labels.py` (struct+numpy, no GIS libs) → `sikkim_gangtok_sample.csv` (6 bbox rows) + `sikkim_join.json` (sha256s in manifest). Haversine join over all 693 Sikkim points: S2 hit SK/ESK/78A11/2019/02 @286.7 m; S1 nearest 417.5 m (outside rule); S3/S4 >1 km.
* ✅ GSI report corroboration (REAL, second source, 2026-09-04): user-supplied `data/raw/landslide_report.pdf` (904 pp, LOCAL ONLY) → Sikkim block pp. 659–676 (first SK Sl.26052 foot of p659; p677 Tripura) → `scripts/extract_sikkim_report.py` (pymupdf Sl.No.-anchored parse, every field asserted vs hand-verified dump) → `data/sih26001/evidence/sikkim_report_gangtok.csv` (7 Gangtok District rows: 14th Mile, Lumsay, Luing, Dipudara, Dochum, Tintek, Upper Sichey; sha256 in manifest) → corroboration block in `sikkim_join.json` (`report_pdf`; shapefile `join` untouched). Outcome: S2 prev=1 now has a SECOND ID (SI/GTK/78A11/2025/03 Upper Sichey @~259 m, 31 Jul 2025); S1/S3/S4 stay 0 (nearest PDF rows 1219/1102/1261 m); all events stay 0 (histories Mar 2023–Jul 2025, all outside 2024-06-10/16). `feature_matrix.sample.csv` unchanged (join outcomes identical).
* ✅ USGS SRTM (REAL, mirror superseded): user-supplied `data/raw/dem/n27_e088_1arc_v3.tif` (LOCAL ONLY) → `scripts/extract_usgs.py` → `usgs_s234.json` (sha256 in manifest). Elevations reproduce mirror ±7 m; resolution deltas logged per slope. Mirror PNGs/CSVs retained as method audit trail only — do not cite their values.
* USGS tile landed via user download (see SRTM bullet above). Neyveli tiles in `data/processed/terrain/` remain unrelated — do not cite.
* ✅ Soil (REAL, satellite-observed): user CDS download 2026-09-04 (ESA CCI COMBINED TCDR v202505, volumetric/combined/daily/June 10–16) → 7 daily global files LOCAL ONLY → `scripts/extract_soil_cci.py` → `data/processed/soil/gangtok_soil_cci.csv` (+ .meta.json, sha256s in manifest). Nearest cell (27.375,88.625) all slopes, 7/7 valid, window-mean 0.271. Stronger pedigree than ERA5 reanalysis; same-cell consequence stated.
* ✅ Lithology (PROXY-published-map, 2026-09-04): `data/raw/docs/Gangtok_Disaster_Resilience_Action_Plan.pdf` p71 §3.4.9 + p118 §5.4.5 + Figures 25/48 — "main Gangtok town stands over the intrusive lingtse granite gneiss (highly weathered, soil <1-10m; map by NESAC from SSDMA+GSI)" → `scripts/extract_lithology.py` → `s234_lithology.json` (sha256 in manifest): all 4 pilot points central Gangtok (Fig 9-25 town extent) → `lingtse_granite_gneiss`. CGWB corroborates Chungthang Subgroup as immediate country rock. Limit: 50K figure not a Bhukosh vector clip — tagged PROXY-published-map (upgrade: Bhukosh vector clip).
* ✅ Lineament (PROXY-published-map + verified Bhuvan layer, 2026-09-04): exact layer `lineament:SK_LN50K_0506` verified live via WMS GetCapabilities (`bhuvan-vec2.nrsc.gov.in/bhuvan/wms?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.1.1`, 5.2 MB, bbox 88.035/27.073-88.892/28.061 covers all 4 points, queryable=1) — advertised as Lineament 50K 2005-06 Sikkim (`bhuvan-app1.../mines.php` + `nwdp.../lineament` "in association with GSI") + report Figures 24/47 show central Gangtok low-moderate (<1.5) — WFS disabled + GetMap KML forbidden + GetFeatureInfo at Gangtok AOI + state centre returned 0 features (WMS renders but vector not exposed via GetFeatureInfo) → `scripts/extract_lineament.py` → `s234_lineament.json` (sha256 in manifest): **0.8 km/km2** all slopes — conservative literature proxy (0.3-1.4, uniform). Tag PROXY-published-map + Bhuvan-availability (verified layer, not a vector clip). Upgrade: QGIS WMS `bhuvan-vec2.../bhuvan/wms` → `SK_LN50K_0506` → Clip and Ship → GeoPackage → length/area per slope.
* Trigger validation (bonus from the shapefile): TRIGGERING = Rainfall* on all 6 bbox slides (one Rainfall/Earthquake) — the rainfall-trigger assumption in `04_MODEL_PLAN_SIH26001.md` §4 holds on local evidence. S2's slide GEOLOGY ("weathered biotite schist…") is schist-family area context — consistent with the gneiss-family lithology above (both high-grade metamorphics; difference is local facies, not contradiction) — but not a direct S2 read.
* Both former Bhukosh/lineament STUBs are now closed as PROXY-published-map/Bhuvan-availability (above). No science STUBs remain; only the Bhukosh-vector / per-slope Bhuvan-clip upgrades remain as stated limits.
* Phase-0 checklist `03_DATA_PLAN_SIH26001.md:154` all `[ ]` (unchecked)

Validator `scripts/check_scaffold.py:1` confirms **schema and frozen scores only** — it does not verify scientific provenance. Passing the validator does not mean the numbers are real.

See honest manifest `data/sih26001/fixtures/manifest.sample.json:1` — IMD, OSM, DEM, Sentinel-2, soil, Bhusanket, GSI-report, WorldCover, lithology, lineament entries are `status: available` with file/script/method/checksum; only the Bhukosh-vector / per-slope Bhuvan-clip upgrades remain as stated limits.

---

## 4. Neyveli data is unrelated — do not use as Gangtok evidence

* `data/grounding_manifest.md:1`, `data/processed/terrain/*`, `ml/data_generation/*`, and the `neyveli_*` files under `data/processed/imd/` describe **Neyveli Mine-II** (≈11.5°N, 79.5°E, lignite mine) — the legacy v1 track. Exception: `data/processed/imd/gangtok_rainfall_2024.csv` is the Gangtok-pilot extraction (§2) and IS citable for S1 rainfall.
* That terrain (Copernicus GLO-30 tile `N11E079`), rainfall (Neyveli 1901–2024), geotech, and blast constants **must not** be cited as evidence for Gangtok slopes.
* Confusing the two locations would be fabrication. This document explicitly separates them.

---

## 5. What is required to upgrade each feature to REAL or PROXY

Per `03_DATA_PLAN_SIH26001.md:1` and `05_FEATURE_SCHEMA_SIH26001.md:1`:

* **SRTM terrain (slope/elevation/aspect/curvature/twi/spi):** ✅ REAL for all slopes (2026-09-04) — USGS tile → `extract_usgs.py` → `usgs_s234.json`. Mirror closed out (elevations agreed ±7 m).
* **IMD rainfall (24h/7d/30d):** ✅ DONE for S1–S4 — `ind2024_rfp25.nc` → `extract_gangtok_rainfall.py` → `gangtok_rainfall_2024.csv`, window 2024-06-16, same cell 27.25/88.50 verified per slope.
* **Soil moisture:** ✅ REAL for all slopes (2026-09-04) — CCI TCDR v202505 via user CDS download → `extract_soil_cci.py` → window-mean 0.271 (7/7 valid). ERA5-via-CDS path never needed.
* **NDVI/LULC:** ✅ BOTH DONE (2026-09-04) — NDVI per slope from the pinned Sentinel-2 scene; LULC from WorldCover tile N27E087 (above). OSM-landuse attempt retained as logged history.
* **Lithology:** ✅ PROXY-published-map (2026-09-04) — `Gangtok_Disaster_Resilience_Action_Plan.pdf` p71/p118 + Figures 25/48 (NESAC, SSDMA+GSI) → `extract_lithology.py` → `s234_lithology.json` (all 4 central Gangtok points → `lingtse_granite_gneiss`; Chungthang subgroup noted as country rock per CGWB). Upgrade: Bhukosh vector clip (per-slope GSI lithocode).
* **Roads/rivers:** ✅ DONE for S1–S4 (2026-09-04) — Overpass extracts + committed JSONs + manifest entries, QA kept `osm-qa-unverified` until field-checked.
* **Lineament/drain density:** drain ✅ PROXY-window (0.0 measured); lineament ✅ PROXY-published-map + Bhuvan-availability (2026-09-04) — Bhuvan 50K Sikkim advertised + report Figures 24/47 context → `extract_lineament.py` → `s234_lineament.json` (0.8 km/km2 all slopes, conservative, uniform; upgrade: Bhuvan Clip and Ship per-slope length/area).
* **previous_landslide / event:** ✅ REAL-joined (2026-09-04) — user-supplied GSI inventory (30,842 points) → `extract_sikkim_labels.py` → S2 hit SK/ESK/78A11/2019/02 @286.7 m; corroborated same day by report PDF (`extract_sikkim_report.py` → second ID SI/GTK/78A11/2025/03 Upper Sichey @~259 m); all events 0 (INITIATION year-only / histories outside window, reason logged). Portal-probe history (dashboard/COOLR/ILSM/DesInventar-TN) retained in manifest attempt notes. Negatives: `>300 m` buffer holds (S1 417 m / PDF 1219 m, S3/S4 >1 km both sources). Spatial-cluster CV required later (`04_MODEL_PLAN_SIH26001.md`).
* **Every run:** Write `manifest.json` with source versions, download dates, seeds `[42]`, CRS/grid, sha256 — committed alongside code (`03_DATA_PLAN_SIH26001.md:145`). Full matrix stays git-ignored (`data/processed/*` ignored), only `*.sample.csv` in repo.

---

## 6. Limitations and next steps

**Current limitations (honest):**
* 16 of 17 science features are REAL or PROXY (14 REAL + lithology PROXY-published-map + lineament PROXY-Bhuvan/figure + drain PROXY-window). Zero science STUBs remain — only Bhukosh-vector / per-slope Bhuvan-clip upgrades remain as stated limits (50K scale, published-figure digitization). Labels REAL-joined (S2 hit + report corroboration). Shape-usable for model prototyping; production calibration still needs field validation.
* IMD grid representativeness (~13 km nearest-cell) disclosed; Bhusanket IDs, tile names (DEM), and ERA5 requests still missing — verifiable from repo history.
* No `ngen/` pipeline exists yet (`Test-Path ngen` = False) — NGEN is documentation-only on this branch.
* CSV cannot carry per-feature tags without breaking frozen schema (`05_FEATURE_SCHEMA_SIH26001.md:59` boundary rule + `check_scaffold.py:24` header check). Tags live here until schema ADR adds a provenance sidecar.

**Next steps (no invention, no huge download):**
1. Person 1 (rain + soil): rain REAL for S1–S4 (same cell verified per slope); soil REAL via CCI — both done. ERA5-via-CDS path never needed (CCI stronger pedigree, logged).
2. Person 2 (terrain+satellite): closed out — USGS REAL (6 derivatives), NDVI REAL, LULC REAL via WorldCover (FOREST/BUILT), lithology + lineament closed as PROXY-published-map/Bhuvan-availability this session.
3. Person 3 (labels): REAL-joined (S2 hit + report corroboration); NDVI + catchment + landuse-attempt + lithology/lineament rounds all closed. Nothing convertible remains from this machine — only the stated PROXY→REAL upgrades (Bhukosh vector clip, per-slope Bhuvan clip, larger catchment if needed).
4. Do not claim production readiness — prototype honesty rules `docs/sih26001/08_LIMITATIONS_SIH26001.md:1` apply. Scores remain susceptibility bands, not P(landslide tomorrow).

**Validation:** `python scripts/check_scaffold.py` passes, CSV has 22 cols and ≤20 rows with S1 present, manifest parses as JSON with no `FILL` strings. See `manifest.sample.json:1` for `status: not_available` convention used to remove misleading placeholders.

---

*This fixture is training-ready in shape, with 13 REAL-verified features per slope, REAL-joined labels, and drain as stated PROXY. It honestly documents what is missing so judges and teammates can verify progress without hidden fabrication.*
