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

## 2. S1 row status — STUB/demo, not verified science

The current `feature_matrix.sample.csv` S1 row is a **demonstration fixture** to prove the pipeline shape, not a verified field or scientific measurement.

**CSV row (verbatim, `feature_matrix.sample.csv:2`):**
```
S1,2026-08-15,34.5,1650,180,0.02,8.1,12.4,132,320,780,0.42,0.35,BUILT,schist,45,210,1.8,2.1,1,1,dated
```
Every value below is `STUB/demo` unless repository evidence proves otherwise. No value is labelled `REAL` or `PROXY` in this file because no Gangtok source evidence exists yet (see §3). This is intentional honesty — not missing work.

**Why STUB:** STUB = temporary placeholder. REAL = directly verified from an actual source file committed or checksumed in repo. PROXY = indirect substitute (e.g. ERA5 reanalysis). None of the Gangtok values meet REAL/PROXY yet, so they stay STUB.

**Per-feature status — all 17 features + 2 keys + 2 labels (external to CSV because schema is frozen — adding a column would break `scripts/check_scaffold.py:24`). Classified per honesty rules: REAL=verified file, PROXY=indirect substitute (ERA5), CONSTANT=fixed demo value, STUB=temporary placeholder, UNKNOWN=not verified:**

| # | Feature | S1 value | Status | Why this label | Evidence that would upgrade it |
|---|---|---|---|---|---|
| — | `zone_id` | S1 | REAL (ID) | Frozen ID from contract `SCAFFOLD_CONTRACT_SEPT5.md:14` | — already frozen |
| — | `time_window` | 2026-08-15 | STUB | Demo date, not a dated landslide event window | Bhusanket dated event + IMD day for that date |
| 1 | `slope_angle` | 34.5 | STUB/demo | No SRTM tile for Gangtok proves it | SRTM 30m tile (e.g. `N27E088`) + GDAL slope calc + committed `.sample.tif` checksum |
| 2 | `elevation` | 1650 | STUB/demo | No DEM extraction log | SRTM elevation at 27.3450,88.6000 + tile name + date |
| 3 | `aspect` | 180 | STUB/demo | Derived from DEM, DEM missing | Same SRTM tile + aspect derivative |
| 4 | `curvature` | 0.02 | STUB/demo | Derived from DEM | Same SRTM tile |
| 5 | `twi` | 8.1 | STUB/demo | Derived from DEM | Same SRTM tile + TWI calc |
| 6 | `spi` | 12.4 | STUB/demo | Derived from DEM | Same SRTM tile + SPI calc |
| 7 | `rainfall_24h_mm` | 132 | STUB/demo | No IMD NetCDF extraction | IMD 0.25° daily NetCDF for pilot bbox + `imdlib` extract log + file date/version |
| 8 | `rainfall_7d_mm` | 320 | STUB/demo | Same | Same IMD source |
| 9 | `rainfall_30d_mm` | 780 | STUB/demo | Same | Same IMD source |
| 10 | `soil_moisture` | 0.42 | STUB/demo | Would be PROXY if from ERA5, but no ERA5 fetch proves it | ERA5 volumetric soil water CDS API request log + date/version, tagged `reanalysis-proxy` |
| 11 | `ndvi` | 0.35 | STUB/demo (constant) | No Sentinel-2 composite proves it (`TEAM_TASKS_SEPT5.md:27` allows constant if tagged, tagged here) | Sentinel-2 L2A composite for pilot bbox + date + NDVI calc |
| 12 | `lulc` | BUILT | STUB/demo (constant) | No codebook extraction | Sentinel-2 LULC classification + codebook frozen with schema |
| 13 | `lithology` | schist | STUB/demo | No GSI Bhukosh extract proves it | GSI Bhukosh lithology export for pilot bbox + codebook |
| 14 | `distance_to_road` | 45 | STUB/demo | No OSM extract proves it | OSM Overpass/Geofabrik sikkim extract + date + QA note + distance calc |
| 15 | `distance_to_river` | 210 | STUB/demo | DEM-derived network missing because DEM missing | SRTM-derived river network + distance |
| 16 | `lineament_density` | 1.8 | STUB/demo | Derived from geology+DEM | GSI lineaments + DEM |
| 17 | `drain_density` | 2.1 | STUB/demo | Derived from DEM | DEM drain density calc |
| 18 | `previous_landslide` | 1 | STUB/demo | No Bhusanket ID proves prior event at S1 | GSI Bhusanket NER export + NER filter + S1 spatial join |
| 19 | `event` | 1 | STUB/demo | No dated inventory event proves landslide at S1 on 2026-08-15 | Same Bhusanket inventory + date window; else `evidence_quality=season-window` + `missing_evidence` tag |
| 20 | `evidence_quality` | dated | STUB | Claims dated, but no dated source committed | Real inventory date or retagged `approximate` |

**All 17 science features are STUB/demo today.** No Gangtok feature is REAL or PROXY yet.

---

## 3. No Gangtok source evidence exists in this repository

Checked files and git history on `feature/sih26001/ngen-pilot` (2026-09-04):

*   No `data/raw/imd/*.nc` or IMD download log for 27–28°N, 88–89°E
*   No `data/raw/dem/*.tif` or SRTM tile for Gangtok (tiles for Neyveli in `data/processed/terrain/` only)
*   No ERA5 CDS request for Sikkim, no `soil_moisture` provenance
*   No Sentinel-2 L2A composite for Gangtok, no NDVI/LULC raster
*   No GSI Bhukosh lithology export for Sikkim
*   No OSM extract file or Overpass query log for Sikkim
*   No GSI Bhusanket Sikkim-filtered CSV + export date
*   Phase-0 checklist `03_DATA_PLAN_SIH26001.md:154` all `[ ]` (unchecked)

Validator `scripts/check_scaffold.py:1` confirms **schema and frozen scores only** — it does not verify scientific provenance. Passing the validator does not mean the numbers are real.

See honest manifest `data/sih26001/fixtures/manifest.sample.json:1` — all sources now `status: not_available`, `date: null`, `tiles: []` until fetched honestly.

---

## 4. Neyveli data is unrelated — do not use as Gangtok evidence

*   `data/grounding_manifest.md:1`, `data/processed/terrain/*`, `data/processed/imd/*`, `ml/data_generation/*` describe **Neyveli Mine-II** (≈11.5°N, 79.5°E, lignite mine) — the legacy v1 track.
*   That terrain (Copernicus GLO-30 tile `N11E079`), rainfall (Neyveli 1901–2024), geotech, and blast constants **must not** be cited as evidence for Gangtok slopes.
*   Confusing the two locations would be fabrication. This document explicitly separates them.

---

## 5. What is required to upgrade each feature to REAL or PROXY

Per `03_DATA_PLAN_SIH26001.md:1` and `05_FEATURE_SCHEMA_SIH26001.md:1`:

*   **SRTM terrain (slope/elevation/aspect/curvature/twi/spi):** Download SRTM 30m tile covering 27.3–27.4°N, 88.5–88.7°E via USGS EarthExplorer / NASA Earthdata → commit small `*.sample.tif` + record tile name, version, date, CRS, checksum in `manifest.json`. Derive with `rasterio/GDAL` and log formula.
*   **IMD rainfall (24h/7d/30d):** Fetch IMD 0.25° daily gridded NetCDF for pilot bbox (pilot period first) via `imdpune.gov.in` or `imdlib` → log file name, grid indices, extraction script, date. No invention of rainfall numbers.
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
*   All 17 Gangtok values are STUB/demo — not usable for model training beyond shape-checking.
*   No source dates, tile names, checksums, or Bhusanket IDs can be verified from repo history.
*   No `ngen/` pipeline exists yet (`Test-Path ngen` = False) — NGEN is documentation-only on this branch.
*   CSV cannot carry per-feature tags without breaking frozen schema (`05_FEATURE_SCHEMA_SIH26001.md:59` boundary rule + `check_scaffold.py:24` header check). Tags live here until schema ADR adds a provenance sidecar.

**Next steps (no invention, no huge download):**
1.  Person 1 (rain — STUB today): run `imdlib` for pilot bbox **only** pilot period (`03_DATA_PLAN_SIH26001.md:154` first box) → record honest `manifest.json` with real NetCDF file name + grid indices + date; keep other Person 1 values STUB until then.
2.  Person 2 (terrain+satellite — STUB/CONSTANT today): fetch single SRTM 30m tile for 27.3-27.4°N,88.5-88.7°E via USGS EarthExplorer → `rasterio`/`GDAL` derive slope/elevation for S1 only → replace STUB with REAL-derived value + commit `.sample.tif` checksum; Sentinel-2/GSi stays CONSTANT until product fetched.
3.  Person 3 (labels/manifest — honest now): `manifest.sample.json:1` already uses `null`/`[]`/`status:not_available` for missing; keep that convention; once Person 1+2 deliver one REAL value each, update this doc `STUB → REAL/PROXY` for those features and fill corresponding `manifest.json` dates/tiles/checksums with computed values (never invented).
4.  Do not claim production readiness — prototype honesty rules `docs/sih26001/08_LIMITATIONS_SIH26001.md:1` apply. Scores remain susceptibility bands, not P(landslide tomorrow).

**Validation:** `python scripts/check_scaffold.py` passes, CSV has 22 cols and ≤20 rows with S1 present, manifest parses as JSON with no `FILL` strings. See `manifest.sample.json:1` for `status: not_available` convention used to remove misleading placeholders.

---

*This fixture is training-ready in shape only. It honestly documents what is missing so judges and teammates can verify progress without hidden fabrication.*
