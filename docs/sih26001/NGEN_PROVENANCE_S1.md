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

## 2. S1 row status — 5 REAL + 4 PROXY (2026-09-04), rest STUB/demo

The S1 rainfall columns are **REAL direct extractions** from the committed
IMD archive (see evidence below). S1 road/river distances are **REAL direct
extractions** from the Overpass API (extract JSON committed, §3). S1 DEM
derivatives (slope/elevation/aspect/curvature) are **PROXY** — computed from
an open SRTM-derived mirror (AWS Terrain Tiles Terrarium), not the USGS
N27E088 tile, with pedigree and limits stated in the manifest. All other
science features remain STUB/demo.

**CSV row (verbatim, `feature_matrix.sample.csv:2`):**
```
S1,2024-06-16,22.1,1287,248,-0.0395,8.1,12.4,14.0,327.3,712.2,0.42,0.35,BUILT,schist,4,226,1.8,2.1,1,1,dated
```
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
(226 m) is internally consistent. TWI/SPI stay STUB (catchment flow routing
would be edge-corrupted on a 64-px window); NDVI/LULC stay STUB (no COG
raster toolchain — open-STAC fetch noted as follow-up).
Antecedent-driven saturation framing matches the v2 physics chain
(`04_MODEL_PLAN_SIH26001.md` §4): June 10–16 delivered 327 mm after a
712 mm/30 d buildup. No ERA5 fetch exists, so `soil_moisture` stays STUB;
no Bhusanket Sikkim join exists, so `previous_landslide`/`event` stay STUB
(the `dated` tag now covers the REAL rainfall window, not a proven slide).

**Why STUB:** STUB = temporary placeholder. REAL = directly verified from an actual source file committed or checksumed in repo. PROXY = indirect substitute (e.g. ERA5 reanalysis, Terrarium mirror for the USGS tile). Features without such evidence stay STUB.

**Per-feature status — all 17 features + 2 keys + 2 labels (external to CSV because schema is frozen — adding a column would break `scripts/check_scaffold.py:24`). Classified per honesty rules: REAL=verified file, PROXY=indirect substitute (ERA5), CONSTANT=fixed demo value, STUB=temporary placeholder, UNKNOWN=not verified:**

| # | Feature | S1 value | Status | Why this label | Evidence that would upgrade it |
|---|---|---|---|---|---|
| — | `zone_id` | S1 | REAL (ID) | Frozen ID from contract `SCAFFOLD_CONTRACT_SEPT5.md:14` | — already frozen |
| — | `time_window` | 2024-06-16 | REAL (rainfall window) | Wettest trailing-7d spell end, IMD 2024 extraction (above) | Event-occurrence at S1 still unproven — see rows 18–19 |
| 1 | `slope_angle` | 22.1 | PROXY (mirror) | Horn-1981 on z15 Terrarium mosaic, `s1_dem_window.csv` + `extract_s1_dem.py` | USGS N27E088 tile → re-derive, replace |
| 2 | `elevation` | 1287 | PROXY (mirror) | Bilinear at exact S1 from same mosaic; town-centre cross-check 1509 m (§2) | Same USGS tile |
| 3 | `aspect` | 248 | PROXY (mirror) | Horn downslope aspect WSW (247.8), same mosaic; 68° uphill version corrected 2026-09-04 | Same USGS tile |
| 4 | `curvature` | -0.0395 | PROXY (mirror) | Laplacian central differences, same mosaic | Same USGS tile |
| 5 | `twi` | 8.1 | STUB/demo | Derived from DEM | Same SRTM tile + TWI calc |
| 6 | `spi` | 12.4 | STUB/demo | Derived from DEM | Same SRTM tile + SPI calc |
| 7 | `rainfall_24h_mm` | 14.0 | REAL | IMD NetCDF `ind2024_rfp25.nc` → `gangtok_rainfall_2024.csv`, trailing 24h to 2024-06-16 | — verified (raw slice June 1–20 sums check) |
| 8 | `rainfall_7d_mm` | 327.3 | REAL | Same extraction, trailing 7d (June 10–16 daily: 41.3+50.5+35.2+76.7+73.4+36.3+14.0) | — verified |
| 9 | `rainfall_30d_mm` | 712.2 | REAL | Same extraction, trailing 30d to 2024-06-16 | — verified |
| 10 | `soil_moisture` | 0.42 | STUB/demo | Would be PROXY if from ERA5, but no ERA5 fetch proves it | ERA5 volumetric soil water CDS API request log + date/version, tagged `reanalysis-proxy` |
| 11 | `ndvi` | 0.35 | STUB/demo (constant) | No Sentinel-2 composite proves it (`TEAM_TASKS_SEPT5.md:27` allows constant if tagged, tagged here) | Sentinel-2 L2A composite for pilot bbox + date + NDVI calc |
| 12 | `lulc` | BUILT | STUB/demo (constant) | No codebook extraction | Sentinel-2 LULC classification + codebook frozen with schema |
| 13 | `lithology` | schist | STUB/demo | No GSI Bhukosh extract proves it | GSI Bhukosh lithology export for pilot bbox + codebook |
| 14 | `distance_to_road` | 4 | REAL | Overpass extract 2026-09-04: unnamed tertiary OSM-348966165, 48 ways examined, foot-path filter logged (`s1_osm_nearest.json`) | — verified (field-check + OSM QA pass still open, `osm-qa-unverified` kept) |
| 15 | `distance_to_river` | 226 | REAL | Overpass extract 2026-09-04: unnamed stream OSM-129509880, 12 waterways in 4 km (`s1_osm_nearest.json`) | — verified |
| 16 | `lineament_density` | 1.8 | STUB/demo | Derived from geology+DEM | GSI lineaments + DEM |
| 17 | `drain_density` | 2.1 | STUB/demo | Derived from DEM | DEM drain density calc |
| 18 | `previous_landslide` | 1 | STUB/demo | No Bhusanket ID proves prior event at S1 | GSI Bhusanket NER export + NER filter + S1 spatial join |
| 19 | `event` | 1 | STUB/demo | No dated inventory event proves landslide at S1 in this window | Same Bhusanket inventory + date window; else `evidence_quality=season-window` + `missing_evidence` tag |
| 20 | `evidence_quality` | dated | PARTIAL (rainfall window dated-real; occurrence unproven) | Date 2024-06-16 is a real IMD window end; no Bhusanket ID proves a slide at S1 | Bhusanket Sikkim join, or retag occurrence claim |

**5 of 17 science features are REAL (rainfall 24h/7d/30d + road/river distances); 4 are PROXY (Terrarium-mirror DEM derivatives); `time_window` is a REAL rainfall-window date. The rest remain STUB/demo.** Grid representativeness (~13 km nearest-cell) is disclosed in the manifest and stays a stated limit; DEM mirror pedigree and OSM QA limits are stated with the values.

---

## 3. Gangtok source evidence in this repository (2026-09-04)

*   ✅ IMD rainfall: `data/raw/imd/ind2024_rfp25.nc` (national 0.25° grid, covers NER) → extraction `scripts/extract_gangtok_rainfall.py` → `data/processed/imd/gangtok_rainfall_2024.csv` (366 rows, sha256 in manifest). Grid cell 27.25N 88.50E — verified nearest cell for **all four slopes** (S2 27.338/88.612, S3 27.325/88.6065, S4 27.315/88.595 all resolve to 27.25/88.50), so S2–S4 carry identical REAL rain values for window 2024-06-16. Consequence of 0.25° coarseness, disclosed: rain does not differentiate slopes; static terrain features do.
*   ✅ OSM spatial: Overpass `overpass-api.de` 2026-09-04 → extraction `scripts/extract_s1_osm.py` → `data/processed/terrain/s1_osm_nearest.json` (query + endpoint + counts + nearest ids, sha256 in manifest). QA stays `osm-qa-unverified`.
*   ✅ DEM mirror (PROXY): AWS Terrain Tiles Terrarium z15 3×3 (SRTM-derived, open, no account) → extraction `scripts/extract_s1_dem.py` (stdlib PNG decode + numpy Horn/Laplacian) → `data/processed/terrain/s1_dem_window.csv` (64×64 audit grid, sha256 in manifest). NOT the USGS N27E088 tile — see manifest `limit`.
*   No USGS EarthExplorer / NASA Earthdata SRTM tile for Gangtok (Neyveli tiles in `data/processed/terrain/` only — unrelated, do not cite)
*   No ERA5 CDS request for Sikkim, no `soil_moisture` provenance
*   No Sentinel-2 L2A composite for Gangtok, no NDVI/LULC raster (no COG raster toolchain — open-STAC fetch is the no-account follow-up)
*   No GSI Bhukosh lithology export for Sikkim
*   No GSI Bhusanket Sikkim-filtered CSV + export date (→ Person 3 with labels)
*   Phase-0 checklist `03_DATA_PLAN_SIH26001.md:154` all `[ ]` (unchecked)

Validator `scripts/check_scaffold.py:1` confirms **schema and frozen scores only** — it does not verify scientific provenance. Passing the validator does not mean the numbers are real.

See honest manifest `data/sih26001/fixtures/manifest.sample.json:1` — IMD, OSM, and DEM-mirror entries are `status: available` with file/script/method/checksum; ERA5, Sentinel-2, and Bhusanket stay `status: not_available`, `date: null` until fetched honestly.

---

## 4. Neyveli data is unrelated — do not use as Gangtok evidence

*   `data/grounding_manifest.md:1`, `data/processed/terrain/*`, `ml/data_generation/*`, and the `neyveli_*` files under `data/processed/imd/` describe **Neyveli Mine-II** (≈11.5°N, 79.5°E, lignite mine) — the legacy v1 track. Exception: `data/processed/imd/gangtok_rainfall_2024.csv` is the Gangtok-pilot extraction (§2) and IS citable for S1 rainfall.
*   That terrain (Copernicus GLO-30 tile `N11E079`), rainfall (Neyveli 1901–2024), geotech, and blast constants **must not** be cited as evidence for Gangtok slopes.
*   Confusing the two locations would be fabrication. This document explicitly separates them.

---

## 5. What is required to upgrade each feature to REAL or PROXY

Per `03_DATA_PLAN_SIH26001.md:1` and `05_FEATURE_SCHEMA_SIH26001.md:1`:

*   **SRTM terrain (slope/elevation/aspect/curvature/twi/spi):** ✅ PROXY done for 4 of 6 (2026-09-04) via Terrarium mirror (`extract_s1_dem.py` + committed 64×64 window + town-centre cross-check). Still open: USGS N27E088 tile via EarthExplorer/Earthdata → re-derive → promote PROXY→REAL. TWI/SPI stay STUB until catchment-scale flow routing exists (window calc would be edge-corrupted).
*   **IMD rainfall (24h/7d/30d):** ✅ DONE for S1 (2026-09-04) — `ind2024_rfp25.nc` → `extract_gangtok_rainfall.py` → `gangtok_rainfall_2024.csv`, window 2024-06-16. Method stands for S2–S4 (same script, same grid).
*   **Soil moisture:** Fetch ERA5 volumetric soil water via CDS API for pilot period → store request JSON + version/date. Tag everywhere as `reanalysis-proxy` (`05_FEATURE_SCHEMA_SIH26001.md:50`).
*   **NDVI/LULC:** Fetch Sentinel-2 L2A cloud-free composite for pilot bbox via Copernicus Open Access Hub → log product ID, date, NDVI calc. Constants allowed only if tagged as STUB (done here).
*   **Lithology:** Export GSI Bhukosh lithology for pilot bbox → log export date + codebook. Map to `05_FEATURE_SCHEMA_SIH26001.md:34`.
*   **Roads/rivers:** ✅ DONE for S1 (2026-09-04) — Overpass extract + committed JSON + manifest entry, QA kept `osm-qa-unverified` until field-checked.
*   **Lineament/drain density:** Derive from GSI + DEM as above → log method.
*   **previous_landslide / event:** Filter GSI Bhusanket NER inventory (37,903+ points) for Gangtok bbox + ISRO Atlas / NASA COOLR → commit filtered CSV sample (≤20 rows) + export date. Negative samples: `>300 m` buffer (`03_DATA_PLAN_SIH26001.md:135`) + `evidence_quality` tag. Spatial-cluster CV required later (`04_MODEL_PLAN_SIH26001.md`).
*   **Every run:** Write `manifest.json` with source versions, download dates, seeds `[42]`, CRS/grid, sha256 — committed alongside code (`03_DATA_PLAN_SIH26001.md:145`). Full matrix stays git-ignored (`data/processed/*` ignored), only `*.sample.csv` in repo.

---

## 6. Limitations and next steps

**Current limitations (honest):**
*   5 of 17 Gangtok values are REAL (S1 rainfall + OSM) and 4 are PROXY (DEM mirror); the rest are STUB/demo — not usable for model training beyond shape-checking.
*   IMD grid representativeness (~13 km nearest-cell) disclosed; Bhusanket IDs, tile names (DEM), and ERA5 requests still missing — verifiable from repo history.
*   No `ngen/` pipeline exists yet (`Test-Path ngen` = False) — NGEN is documentation-only on this branch.
*   CSV cannot carry per-feature tags without breaking frozen schema (`05_FEATURE_SCHEMA_SIH26001.md:59` boundary rule + `check_scaffold.py:24` header check). Tags live here until schema ADR adds a provenance sidecar.

**Next steps (no invention, no huge download):**
1.  Person 1 (rain — REAL for S1 today): extend the same script to S2–S4 cells (same grid, same 2024 window rule) → one row each; ERA5 soil moisture still needs a CDS fetch — stays STUB until then.
2.  Person 2 (terrain+satellite — 6 verified today: 2 REAL OSM + 4 PROXY DEM): remaining STUBs are TWI/SPI (need catchment flow routing + USGS tile), NDVI/LULC (need L2A COG + raster toolchain), all documented above.
3.  Person 3 (labels/manifest — honest now): IMD/OSM/DEM-mirror manifest entries are filled; keep `null`/`[]`/`status:not_available` convention for ERA5, Sentinel-2, Bhusanket. Lithology + lineament/drain_density ride with Person 3 (Bhukosh export + GSI+DEM catchment work) — decided 2026-09-04, see commit.
4.  Do not claim production readiness — prototype honesty rules `docs/sih26001/08_LIMITATIONS_SIH26001.md:1` apply. Scores remain susceptibility bands, not P(landslide tomorrow).

**Validation:** `python scripts/check_scaffold.py` passes, CSV has 22 cols and ≤20 rows with S1 present, manifest parses as JSON with no `FILL` strings. See `manifest.sample.json:1` for `status: not_available` convention used to remove misleading placeholders.

---

*This fixture is training-ready in shape, with S1 rainfall + OSM REAL-verified and DEM derivatives as stated PROXY. It honestly documents what is missing so judges and teammates can verify progress without hidden fabrication.*
