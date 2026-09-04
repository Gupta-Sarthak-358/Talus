# NGEN Provenance — S1 (Gangtok Pilot) — Persons 1, 2, 3: Complete Honest Pilot (Rain + Terrain/Satellite + Labels/Manifest)

**Status:** Honest training-ready fixture (STUB/demo) — all 3 roles covered · **Pilot:** Gangtok cluster, Sikkim ONLY · **Branch:** `feature/sih26001/ngen-pilot` · **Date:** 2026-09-04
**Roles:** Person 1 = rainfall_24h/7d/30d + soil_moisture · Person 2 = terrain/satellite/spatial (10 features) · Person 3 = labels/manifest/provenance
**Trace to:** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:1`, `docs/sih26001/TEAM_TASKS_SEPT5.md:24`, `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md:16`, `docs/sih26001/03_DATA_PLAN_SIH26001.md:1`
**Related files:** `data/sih26001/fixtures/feature_matrix.sample.csv:1`, `data/sih26001/fixtures/manifest.sample.json:1` · **Validator:** `python scripts/check_scaffold.py:1`

---

## 1. Pilot location (frozen for demo)

*   **Cluster:** Gangtok cluster, Sikkim — `SCAFFOLD_CONTRACT_SEPT5.md:4` Centre `27.3389, 88.6065`, CRS `EPSG:4326` (demo, reprojection deferred)
*   **Frozen zones:** `SCAFFOLD_CONTRACT_SEPT5.md:14`
    *   S1 Tathangchen (upper) `27.3450, 88.6000` — Critical 89
    *   S2 Chandmari (road-cut) `27.3380, 88.6120` — High 78
    *   S3 Tadong (mid) `27.3250, 88.6065` — Moderate 66
    *   S4 Ranipool (valley) `27.3150, 88.5950` — Low 52
*   Scope is **pilot only**. No 8-state implementation on this branch (`TEAM_TASKS_SEPT5.md:24`).

> Coordinates, IDs, scores, bands, and CSV schema are frozen by contract and were not changed here.

---

## 2. S1 row status — 3 rainfall features REAL (2026-09-04), rest STUB/demo

The S1 rainfall columns are now **REAL direct extractions** from the committed
IMD archive (see evidence below). All other science features remain STUB/demo.

**CSV row (verbatim, `feature_matrix.sample.csv:2`):**
```
S1,2024-06-16,34.5,1650,180,0.02,8.1,12.4,14.0,327.3,712.2,0.42,0.35,BUILT,schist,45,210,1.8,2.1,1,1,dated
```
Extraction: `scripts/extract_gangtok_rainfall.py` (xarray nearest grid
27.25N 88.50E to S1 27.3450N 88.6000E, ~13 km — 0.25° representativeness limit
applies) over `data/raw/imd/ind2024_rfp25.nc` → daily series committed as
`data/processed/imd/gangtok_rainfall_2024.csv` (366 rows, 0 missing,
sha256 in manifest). Window rule: wettest trailing-7d spell of 2024 at the
pilot cell → end date 2024-06-16 (24h trailing = 14.0, 7d = 327.3,
30d = 712.2; verified against raw daily slice June 1–20 in extraction log).
Antecedent-driven saturation framing matches the v2 physics chain
(`04_MODEL_PLAN_SIH26001.md` §4): June 10–16 delivered 327 mm after a
712 mm/30 d buildup. No ERA5 fetch exists, so `soil_moisture` stays STUB;
no Bhusanket Sikkim join exists, so `previous_landslide`/`event` stay STUB
(the `dated` tag now covers the REAL rainfall window, not a proven slide).

**Why STUB:** STUB = temporary placeholder. REAL = directly verified from an actual source file committed or checksumed in repo. PROXY = indirect substitute (e.g. ERA5 reanalysis). None of the Gangtok values meet REAL/PROXY yet, so they stay STUB.

**Per-feature status — all 17 features + 2 keys + 2 labels (external to CSV because schema is frozen — adding a column would break `scripts/check_scaffold.py:24`). Classified per honesty rules: REAL=verified file, PROXY=indirect substitute (ERA5), CONSTANT=fixed demo value, STUB=temporary placeholder, UNKNOWN=not verified:**

| # | Feature | S1 value | Status | Why this label | Evidence that would upgrade it |
|---|---|---|---|---|---|
| — | `zone_id` | S1 | REAL (ID) | Frozen ID from contract `SCAFFOLD_CONTRACT_SEPT5.md:14` | — already frozen |
| — | `time_window` | 2024-06-16 | REAL (rainfall window) | Wettest trailing-7d spell end, IMD 2024 extraction (above) | Event-occurrence at S1 still unproven — see rows 18–19 |
| 1 | `slope_angle` | 34.5 | STUB/demo | No SRTM tile for Gangtok proves it | SRTM 30m tile (e.g. `N27E088`) + GDAL slope calc + committed `.sample.tif` checksum |
| 2 | `elevation` | 1650 | STUB/demo | No DEM extraction log | SRTM elevation at 27.3450,88.6000 + tile name + date |
| 3 | `aspect` | 180 | STUB/demo | Derived from DEM, DEM missing | Same SRTM tile + aspect derivative |
| 4 | `curvature` | 0.02 | STUB/demo | Derived from DEM | Same SRTM tile |
| 5 | `twi` | 8.1 | STUB/demo | Derived from DEM | Same SRTM tile + TWI calc |
| 6 | `spi` | 12.4 | STUB/demo | Derived from DEM | Same SRTM tile + SPI calc |
| 7 | `rainfall_24h_mm` | 14.0 | REAL | IMD NetCDF `ind2024_rfp25.nc` → `gangtok_rainfall_2024.csv`, trailing 24h to 2024-06-16 | — verified (raw slice June 1–20 sums check) |
| 8 | `rainfall_7d_mm` | 327.3 | REAL | Same extraction, trailing 7d (June 10–16 daily: 41.3+50.5+35.2+76.7+73.4+36.3+14.0) | — verified |
| 9 | `rainfall_30d_mm` | 712.2 | REAL | Same extraction, trailing 30d to 2024-06-16 | — verified |
| 10 | `soil_moisture` | 0.42 | STUB/demo | Would be PROXY if from ERA5, but no ERA5 fetch proves it | ERA5 volumetric soil water CDS API request log + date/version, tagged `reanalysis-proxy` |
| 11 | `ndvi` | 0.35 | STUB/demo (constant) | No Sentinel-2 composite proves it (`TEAM_TASKS_SEPT5.md:27` allows constant if tagged, tagged here) | Sentinel-2 L2A composite for pilot bbox + date + NDVI calc |
| 12 | `lulc` | BUILT | STUB/demo (constant) | No codebook extraction | Sentinel-2 LULC classification + codebook frozen with schema |
| 13 | `lithology` | schist | STUB/demo | No GSI Bhukosh extract proves it | GSI Bhukosh lithology export for pilot bbox + codebook |
| 14 | `distance_to_road` | 45 | STUB/demo | No OSM extract proves it | OSM Overpass/Geofabrik sikkim extract + date + QA note + distance calc |
| 15 | `distance_to_river` | 210 | STUB/demo | DEM-derived network missing because DEM missing | SRTM-derived river network + distance |
| 16 | `lineament_density` | 1.8 | STUB/demo | Derived from geology+DEM | GSI lineaments + DEM |
| 17 | `drain_density` | 2.1 | STUB/demo | Derived from DEM | DEM drain density calc |
| 18 | `previous_landslide` | 1 | STUB/demo | No Bhusanket ID proves prior event at S1 | GSI Bhusanket NER export + NER filter + S1 spatial join |
| 19 | `event` | 1 | STUB/demo | No dated inventory event proves landslide at S1 in this window | Same Bhusanket inventory + date window; else `evidence_quality=season-window` + `missing_evidence` tag |
| 20 | `evidence_quality` | dated | PARTIAL (rainfall window dated-real; occurrence unproven) | Date 2024-06-16 is a real IMD window end; no Bhusanket ID proves a slide at S1 | Bhusanket Sikkim join, or retag occurrence claim |

**3 of 17 science features are REAL (rainfall 24h/7d/30d); `time_window` is a REAL rainfall-window date. All other Gangtok features remain STUB/demo.** Grid representativeness (~13 km nearest-cell) is disclosed in the manifest and stays a stated limit.

---

## 3. Gangtok source evidence in this repository (2026-09-04)

*   ✅ IMD rainfall: `data/raw/imd/ind2024_rfp25.nc` (national 0.25° grid, covers NER) → extraction `scripts/extract_gangtok_rainfall.py` → `data/processed/imd/gangtok_rainfall_2024.csv` (366 rows, sha256 in manifest). Grid cell 27.25N 88.50E, nearest to S1.
*   No `data/raw/dem/*.tif` or SRTM tile for Gangtok (tiles for Neyveli in `data/processed/terrain/` only)
*   No ERA5 CDS request for Sikkim, no `soil_moisture` provenance
*   No Sentinel-2 L2A composite for Gangtok, no NDVI/LULC raster
*   No GSI Bhukosh lithology export for Sikkim
*   No OSM extract file or Overpass query log for Sikkim
*   No GSI Bhusanket Sikkim-filtered CSV + export date
*   Phase-0 checklist `03_DATA_PLAN_SIH26001.md:154` all `[ ]` (unchecked)

Validator `scripts/check_scaffold.py:1` confirms **schema and frozen scores only** — it does not verify scientific provenance. Passing the validator does not mean the numbers are real.

See honest manifest `data/sih26001/fixtures/manifest.sample.json:1` — IMD entry is `status: available` with file/script/grid/window/checksum; all other sources stay `status: not_available`, `date: null`, `tiles: []` until fetched honestly.

---

## 4. Neyveli data is unrelated — do not use as Gangtok evidence

*   `data/grounding_manifest.md:1`, `data/processed/terrain/*`, `ml/data_generation/*`, and the `neyveli_*` files under `data/processed/imd/` describe **Neyveli Mine-II** (≈11.5°N, 79.5°E, lignite mine) — the legacy v1 track. Exception: `data/processed/imd/gangtok_rainfall_2024.csv` is the Gangtok-pilot extraction (§2) and IS citable for S1 rainfall.
*   That terrain (Copernicus GLO-30 tile `N11E079`), rainfall (Neyveli 1901–2024), geotech, and blast constants **must not** be cited as evidence for Gangtok slopes.
*   Confusing the two locations would be fabrication. This document explicitly separates them.

---

## 5. What is required to upgrade each feature to REAL or PROXY

Per `03_DATA_PLAN_SIH26001.md:1` and `05_FEATURE_SCHEMA_SIH26001.md:1`:

*   **SRTM terrain (slope/elevation/aspect/curvature/twi/spi):** Download SRTM 30m tile covering 27.3–27.4°N, 88.5–88.7°E via USGS EarthExplorer / NASA Earthdata → commit small `*.sample.tif` + record tile name, version, date, CRS, checksum in `manifest.json`. Derive with `rasterio/GDAL` and log formula.
*   **IMD rainfall (24h/7d/30d):** ✅ DONE for S1 (2026-09-04) — `ind2024_rfp25.nc` → `extract_gangtok_rainfall.py` → `gangtok_rainfall_2024.csv`, window 2024-06-16. Method stands for S2–S4 (same script, same grid).
*   **Soil moisture:** Fetch ERA5 volumetric soil water via CDS API for pilot period → store request JSON + version/date. Tag everywhere as `reanalysis-proxy` (`05_FEATURE_SCHEMA_SIH26001.md:50`).
*   **NDVI/LULC:** Fetch Sentinel-2 L2A cloud-free composite for pilot bbox via Copernicus Open Access Hub → log product ID, date, NDVI calc. Constants allowed only if tagged as STUB (done here).
*   **Lithology:** Export GSI Bhukosh lithology for pilot bbox → log export date + codebook. Map to `05_FEATURE_SCHEMA_SIH26001.md:34`.
*   **Roads/rivers:** Pull OSM roads/rivers via Overpass or Geofabrik sikkim extract → commit extract date + Overpass query + QA tag `osm-qa-unverified` until checked. Compute distances in metres (EPSG:4326 → projected re-measurement noted).
*   **Lineament/drain density:** Derive from GSI + DEM as above → log method.
*   **previous_landslide / event:** Filter GSI Bhusanket NER inventory (37,903+ points) for Gangtok bbox + ISRO Atlas / NASA COOLR → commit filtered CSV sample (≤20 rows) + export date. Negative samples: `>300 m` buffer (`03_DATA_PLAN_SIH26001.md:135`) + `evidence_quality` tag. Spatial-cluster CV required later (`04_MODEL_PLAN_SIH26001.md`).
*   **Every run:** Write `manifest.json` with source versions, download dates, seeds `[42]`, CRS/grid, sha256 — committed alongside code (`03_DATA_PLAN_SIH26001.md:145`). Full matrix stays git-ignored (`data/processed/*` ignored), only `*.sample.csv` in repo.

---

## 6. Limitations and next steps

**Current limitations (honest):**
*   3 of 17 Gangtok values are REAL (S1 rainfall); the other 14 + soil moisture + labels are STUB/demo — not usable for model training beyond shape-checking.
*   IMD grid representativeness (~13 km nearest-cell) disclosed; Bhusanket IDs, tile names (DEM), and ERA5 requests still missing — verifiable from repo history.
*   No `ngen/` pipeline exists yet (`Test-Path ngen` = False) — NGEN is documentation-only on this branch.
*   CSV cannot carry per-feature tags without breaking frozen schema (`05_FEATURE_SCHEMA_SIH26001.md:59` boundary rule + `check_scaffold.py:24` header check). Tags live here until schema ADR adds a provenance sidecar.

**Next steps (no invention, no huge download):**
1.  Person 1 (rain — REAL for S1 today): extend the same script to S2–S4 cells (same grid, same 2024 window rule) → one row each; ERA5 soil moisture still needs a CDS fetch — stays STUB until then.
2.  Person 2 (terrain+satellite — STUB/CONSTANT today): fetch single SRTM 30m tile for 27.3-27.4°N,88.5-88.7°E via USGS EarthExplorer → `rasterio`/`GDAL` derive slope/elevation for S1 only → replace STUB with REAL-derived value + commit `.sample.tif` checksum; Sentinel-2/GSi stays CONSTANT until product fetched.
3.  Person 3 (labels/manifest — honest now): IMD manifest entry is filled; keep `null`/`[]`/`status:not_available` convention for the rest; once Person 2 delivers one REAL value, update this doc `STUB → REAL/PROXY` for it with computed values (never invented).
4.  Do not claim production readiness — prototype honesty rules `docs/sih26001/08_LIMITATIONS_SIH26001.md:1` apply. Scores remain susceptibility bands, not P(landslide tomorrow).

**Validation:** `python scripts/check_scaffold.py` passes, CSV has 22 cols and ≤20 rows with S1 present, manifest parses as JSON with no `FILL` strings. See `manifest.sample.json:1` for `status: not_available` convention used to remove misleading placeholders.

---

*This fixture is training-ready in shape, with S1 rainfall REAL-verified. It honestly documents what is missing so judges and teammates can verify progress without hidden fabrication.*
