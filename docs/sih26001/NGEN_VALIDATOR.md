# NGEN Validator — Gangtok Pilot

**Scope:** Gangtok cluster, Sikkim only — `data/sih26001/fixtures/feature_matrix.sample.csv` + `data/sih26001/fixtures/manifest.sample.json`
**Frozen contract:** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md` — S1 (27.3450,88.6000,89 Critical), S2 (27.3380,88.6120,78 High), S3 (27.3250,88.6065,66 Moderate), S4 (27.3150,88.5950,52 Low), centre 27.3389,88.6065, CRS EPSG:4326, 22-col schema.

---

## What the validator checks

`scripts/validate_ngen_sample.py` (stdlib only) checks the honest demo fixtures — not science:

1. Exact 22-column header in frozen order (no add/remove/reorder)
2. No unexpected columns
3. ≤20 rows
4. S1, S2, S3, S4 all present
5. zone_ids unique
6. Required fields not empty
7. Numeric fields are valid numbers (`slope_angle`, `elevation`, `aspect`, `curvature`, `twi`, `spi`, `rainfall_24h/7d/30d_mm`, `soil_moisture` 0–1, `ndvi` −1 to 1, `distance_to_road/river`, `lineament/drain_density`, `previous_landslide`/`event` 0/1)
8. Categorical fields are text (`lulc`, `lithology`, `evidence_quality`)
9. No uppercase placeholder `FILL` in CSV or manifest
10. `manifest.sample.json` is valid JSON
11. Manifest declares `pilot` contains `Gangtok` and `crs` contains `EPSG:4326`
12. No source with `status:not_available` claims a real `date`/`tiles`/`export`/`extract`
13. Always prints a clear warning: current values are STUB/demo and not scientifically validated.

Exit 0 = valid, non-zero = invalid, with beginner-friendly messages.

Related: `scripts/check_scaffold.py` checks frozen IDs/scores/bands/roles for the demo; this validator checks the NGEN sample shape + honesty.

---

## How to run

```powershell
# From E:\TALUS\Talus
python scripts/validate_ngen_sample.py
# explicit paths (same defaults):
python scripts/validate_ngen_sample.py --csv data/sih26001/fixtures/feature_matrix.sample.csv --manifest data/sih26001/fixtures/manifest.sample.json
```

Expected success output (excerpt):
```
Checking CSV: data/sih26001/fixtures/feature_matrix.sample.csv
...
WARNING: This sample contains STUB/demo values and is NOT scientifically validated...
NGEN SAMPLE OK: schema 22 cols, S1-S4 present, ≤20 rows, honest manifest, no FILL.
```

Expected failure example (missing column):
```
VALIDATION FAILED: 1 issue(s) found:
 1. CSV header mismatch...
Fix the issues above, then re-run: python scripts/validate_ngen_sample.py
```

## How to run the tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
# or single file:
python -m unittest tests.test_validate_ngen_sample -v
```

Tests use temporary copies of the fixtures (`tempfile`) and never modify `data/sih26001/fixtures/` permanently. They cover: valid sample, missing column, missing S1, duplicate ID, uppercase FILL, >20 rows, invalid numeric, invalid manifest, wrong CRS/pilot, dishonest `not_available`.

Existing scaffold check still runs separately:

```powershell
python scripts/check_scaffold.py
```

---

## What STUB/demo means

* **STUB** = temporary placeholder value to prove the pipeline shape. The number looks plausible but has no source file behind it.
* **CONSTANT** = same as STUB but deliberately fixed for the demo (e.g. `ndvi=0.35`, `lulc=BUILT` — allowed by `docs/sih26001/TEAM_TASKS_SEPT5.md:27` if tagged).
* **REAL** = directly verified from a committed source file (e.g. SRTM tile `N27E088` → `elevation` at 27.3450,88.6000 with checksum).
* **PROXY** = indirect substitute, e.g. ERA5 `soil_moisture` (must be tagged `reanalysis-proxy` and have a CDS request log).
* Current sample: **14 of 17 science features are REAL on every slope** (rainfall 24h/7d/30d + road/river distances + NDVI + LULC + all six DEM derivatives + soil moisture) and **drain density is PROXY** (measured window) + `zone_id` REAL (frozen ID) + **labels REAL-joined** (S2 previous_landslide=1 with Bhusanket ID; all events 0 with logged reason); only lithology/lineament stay STUB/demo. See `docs/sih26001/NGEN_PROVENANCE_S1.md` for the per-feature table and why.

The sample is **not training-ready science data** — it is shape-only. The validator will fail if anyone labels a STUB as REAL without evidence.

---

## What evidence is required to upgrade to REAL or PROXY

Per `docs/sih26001/03_DATA_PLAN_SIH26001.md` + `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md`:

* **Terrain** `slope_angle/elevation/aspect/curvature/twi/spi`: SRTM 30m tile covering 27.3–27.4°N,88.5–88.7°E (USGS EarthExplorer) + `rasterio`/`GDAL` derivation + committed `*.sample.tif` checksum + tile name/date/CRS in `manifest.json`.
* **Rainfall** `24h/7d/30d_mm`: IMD 0.25° daily NetCDF for pilot bbox + `imdlib` extract log + file name/grid/date.
* **Soil moisture** `0–1`: CCI TCDR daily download + per-slope window-mean extract → REAL (done 2026-09-04).
* **NDVI/LULC**: Sentinel-2 L2A composite product ID + date + NDVI calc; codebook frozen with schema.
* **Lithology**: GSI Bhukosh export for pilot bbox + export date + codebook.
* **Road/river**: OSM Overpass/Geofabrik sikkim extract + extract date + QA tag `osm-qa-unverified` + distance calc in metres.
* **Labels** `previous_landslide/event/evidence_quality`: GSI Bhusanket NER-filtered CSV + export date + S1 spatial join; negatives `>300 m` buffer.

Every upgrade must also fill the honest `manifest.sample.json` entry: real `date` (not null), real `tiles`/`export`/`extract`, computed `checksums` — never invented. Until then, keep `status:not_available`, `date:null`, `tiles:[]`, `export:null`, `checksums:{}`.

---

*Run both validators green before any merge: `python scripts/check_scaffold.py` and `python scripts/validate_ngen_sample.py`.*
