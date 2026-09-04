# Person-3 Handoff — NGEN Labels + Remaining Features (Gangtok Pilot)

**For:** the agent/teammate taking the Person-3 lane · **Date:** 2026-09-04 (hackathon Sept 5)
**Base branch:** `feature/sih26001/ngen-pilot` (all work branches off this; PR into `feature/sih26001/demo-scaffold`)
**Contract (law):** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md` · **Schema:** `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md`
**Status map:** `docs/sih26001/NGEN_PROVENANCE_S1.md` §2 (per-feature REAL/PROXY/STUB table — update it with every change)

## 0. Current REAL/STUB map (start here, verify with the provenance doc)

REAL: S1–S4 rainfall 24h/7d/30d + all `time_window`s (IMD 2024, window 2024-06-16, same cell 27.25/88.50 for all slopes);
S1 `distance_to_road`/`distance_to_river` (Overpass 2026-09-04).
PROXY: S1 slope/elevation/aspect(248!)/curvature (Terrarium mirror, NOT USGS).
STUB (your scope): `soil_moisture`, `ndvi`, `lulc`, `lithology`, S2–S4 road/river distances,
`lineament_density`, `drain_density`, `twi`, `spi`, `previous_landslide`, `event`, `evidence_quality` (occurrence half),
`sampling.ratio` (manifest).

## 1. Workflow (every item, no exceptions)

1. `git checkout feature/sih26001/ngen-pilot && git pull && git checkout -b feature/sih26001/person3-<item>`
2. Fetch source → commit SMALL extract/sample (≤20 rows for CSVs, tiny rasters only) + extraction script + sha256.
3. Update `feature_matrix.sample.csv` values (column order FROZEN — never add/rename/reorder; check with `scripts/check_scaffold.py:24`).
4. Update `manifest.sample.json`: replace `null`/`[]`/`not_available` with real file/date/method/checksum. Convention: missing = `null`/`[]`/`status:not_available`; present = `status:available` + evidence. NEVER write `FILL`.
5. Flip the rows in `NGEN_PROVENANCE_S1.md` §2 table STUB→REAL/PROXY with evidence refs; fix the §2 counts line and §3 bullets.
6. Gates before push: `python scripts/check_scaffold.py` + `python scripts/validate_ngen_sample.py` + `python -m unittest tests.test_validate_ngen_sample` ALL green.
7. Push lane branch, open PR into `feature/sih26001/demo-scaffold`. Never commit `docs/PILOT_BRIEFING.md`, datasets, weights, `.env`.

## 2. Item A — Labels: `previous_landslide` / `event` / `evidence_quality` + `sampling.ratio` (HIGHEST VALUE)

Source: GSI Bhusanket portal — https://bhusanket.gsi.gov.in (reachable, no account for viewing; verified 2026-09-04).
Alternatives if export is awkward: NASA COOLR viewer (https://landslides.nasa.gov/viewer, CSV/SHP download, no account)
or the published Zenodo inventories (Mizoram 19 events, Dibang 537, ILSM points — see `03_DATA_PLAN_SIH26001.md` §A).
Steps:
1. Filter/download NER → Sikkim/Gangtok bbox (88.58–88.63E, 27.30–27.36N) landslide points; record export date + filter.
2. Spatial join vs S1–S4: any inventoried slide within ~300 m of a slope → `previous_landslide=1` for it, cite Bhusanket ID in provenance.
3. `event`: 1 ONLY with a dated inventory event inside the 2024-06-16 window (or its season); else 0 + `evidence_quality=season-window/approximate`.
 Negatives: random points >300 m from any known slide (`03_DATA_PLAN_SIH26001.md` §C).
4. Commit a ≤20-row filtered sample CSV + manifest `bhusanket` entry (export file, date, filter, `status:available`) + `sampling` (`positive` rule, `negative_buffer_m:300`, `ratio` = your real ratio or null).
5. If the portal yields nothing usable tonight: keep STUB, document the attempt (date + what was missing) in provenance §3. Attempt-log beats silence.
Fallback: STUB stays; demo unaffected (labels aren't served by the API).

## 3. Item B — `lithology` (MEDIUM, needs Bhukosh)

Source: GSI Bhukosh — https://bhukosh.gsi.gov.in/Bhukosh/Public (no account for viewing).
Steps: export/lithology map covering the pilot bbox → map the unit at each slope to the schema codebook (`05_FEATURE_SCHEMA_SIH26001.md`: `lithology` = GSI Bhukosh class code; if codebook values are unclear, use the rock name string + note the codebook freeze as follow-up) → update S1 (and S2–S4 only with per-slope reads, never copy-paste S1) → manifest `bhukosh` entry (new key under `sources` is allowed; manifest is not schema-frozen) + provenance flips.
Fallback: STUB (`schist` etc. stay labeled demo constants).

## 4. Item C — `lineament_density` / `drain_density` / `twi` / `spi` (HARD — read before attempting)

These need catchment-scale flow routing; the committed 64-px window is edge-corrupted for this (already documented — do not compute TWI/SPI on it).
Honest options, in order: (a) OSM rivers + DEM window → `drain_density` for S1's 270-m window ONLY, labeled PROXY-window with the edge caveat; (b) GSI structure/lineament map trace length per km² → `lineament_density` PROXY; (c) else all four stay STUB with this reason restated. Do NOT invent catchment numbers. TWI/SPI default: STUB unless you fetch a ≥5 km DEM context (USGS tile, see §6).

## 5. Item D — `ndvi` / `lulc` (MEDIUM, no account needed)

Source: Sentinel-2 via Element84 open Earth-Search STAC — https://earth-search.aws.element84.com (no account; COG rasters).
Steps: query L2A least-cloudy 2024 scene over pilot bbox → read red/NIR at S1 → `ndvi=(NIR-R)/(NIR+R)`; `lulc` from scene classification or OSM landuse as PROXY with tag. Commit product ID + date + calc in manifest (`sentinel2` entry) + tiny evidence (values + BBOX screenshot note, not the raster). Needs a COG reader: `rasterio` if present, else record the attempt and keep STUB.
Fallback: STUB constants stay tagged (`0.35`/`BUILT` labeled demo).

## 6. Item E — `soil_moisture` ERA5 (LIKELY STUB — account wall)

Needs Copernicus CDS account (https://cds.climate.copernicus.eu) — if no account exists tonight, SKIP after one logged attempt; the STUB + `reanalysis-proxy` tagging plan in the schema already covers judging. Do not fake it.

## 7. Item F — S2–S4 `distance_to_road`/`distance_to_river` (EASY if network allows)

Extend the proven pattern: copy `scripts/extract_s1_osm.py` → per-slope `around:` query (same filters, same radii) → nearest distances → update rows (per-slope reads only) → manifest `osm` entry gains per-slope lines → provenance flips.
CAUTION: `overpass-api.de` returned HTTP 406 from the lead's machine on 2026-09-04 (worked from Person-2's). If 406 persists, try `overpass.kumi.systems/api/interpreter`, else log the attempt and keep STUB. Never copy S1's 4/226 onto other slopes.

## 8. Definition of done (per PR)

- [ ] Both validators + 10/10 unittests green (paste output in PR body)
- [ ] No `FILL`, no invented numbers; every new value traces to a committed file + manifest entry + provenance row
- [ ] `NGEN_VALIDATOR.md` counts + `validate_ngen_sample.py` banner updated to match new REAL/PROXY/STUB counts
- [ ] PR body lists: files added, values changed (old→new), sources with dates, what stayed STUB and why
- [ ] File set: additive (new scripts/extracts + shared CSV/manifest/provenance/validator-banner edits). Scores, bands, roles, `slopes.json`, `roads.json`, contract — UNTOUCHED.

Judge line this lane owns: *"Every label traces to a Bhusanket ID or is marked approximate — our docs show which."*
