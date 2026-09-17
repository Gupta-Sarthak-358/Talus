# NGEN Validator — 2025-11-14 Truth (12 rows, 0 STUBs)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Scope:** `data/sih26001/fixtures/feature_matrix.sample.csv` 12 rows (S1–S4 Gangtok + D1–D4 Darjeeling + N1–N4 Lachung) + `manifest.sample.json` 22-col schema.
**Frozen contract:** `SCAFFOLD_CONTRACT_SEPT5.md` — S1 27.3450,88.6000,89 Critical / S2 27.3380,88.6120,78 High / S3 27.3250,88.6065,66 Moderate / S4 27.3150,88.5950,52 Low + N/D per `NGEN_PROVENANCE_*.md` ; centre 27.3389,88.6065 CRS EPSG:4326. Per-slope sources 2025-11-14: IMD 0.25° 1901–2024 + Open-Meteo live + IMD_API_KEY gated, CCI v09.2 0.271 via `extract_soil_cci.py`, SRTM `n27_e088` Horn-1981, WorldCover `N27E087` 76.7%, OSM 1014/226/504 `roads_osm_provenance.json`.

---

## What the validator checks

`scripts/validate_ngen_sample.py` (stdlib only) checks honest fixtures — shape + honesty, not science:

| # | Check |
|---|---|
| 1 | Exact 22-column header in frozen order (no add/remove/reorder) |
| 2 | No unexpected columns |
| 3 | ≤20 rows (12 passes) |
| 4 | S1,S2,S3,S4 all present (D/N extra OK, unique IDs) |
| 5 | zone_ids unique (12) |
| 6 | Required fields not empty |
| 7 | Numeric fields valid numbers (`slope_angle`,`elevation`,`aspect`,`curvature`,`twi`,`spi`,`rainfall_24h/7d/30d_mm`,`soil_moisture` 0–1,`ndvi` −1 to 1,`distance_to_road/river`,`lineament/drain_density`,`previous_landslide`/`event` 0/1,`seismic_*`,`wound` when present) |
| 8 | Categorical fields text (`lulc`,`lithology`,`evidence_quality`) — `dated-only-negative`/`approximate` |
| 9 | No uppercase placeholder `FILL` in CSV or manifest |
| 10 | `manifest.sample.json` valid JSON |
| 11 | Manifest `pilot` contains `Gangtok` and `crs` contains `EPSG:4326` |
| 12 | No source `status:not_available` claims real `date`/`tiles`/`export`/`extract` |
| 13 | Prints provenance note: **0 STUBs** — 17 numeric+lulc REAL/PROXY-published-map/window (drain PROXY-window, lith/lineament PROXY uniform per `bhukosh_vector_attempt.json` timeout), `validate_ngen_sample.py` OK + `check_scaffold.py` SCAFFOLD OK 17-feature |

Exit 0 = valid, non-zero = invalid, beginner-friendly messages.
Related: `scripts/check_scaffold.py` checks frozen IDs/scores/bands/roles/R2-avoidance (`RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2`) + 17-feature fixture count.

---

## How to run

```powershell
# From Talus root
python scripts/validate_ngen_sample.py
# explicit paths (same defaults):
python scripts/validate_ngen_sample.py --csv data/sih26001/fixtures/feature_matrix.sample.csv --manifest data/sih26001/fixtures/manifest.sample.json
```

Expected success output (excerpt):
```
Checking CSV: data/sih26001/fixtures/feature_matrix.sample.csv
...
NGEN SAMPLE OK: schema 22 cols, S1-S4 present (12 rows S/D/N), ≤20 rows, honest manifest, no FILL.
SCAFFOLD OK: 17-feature, frozen 89/78/66/52, R2 avoidance (RISK_WEIGHT 3.0 alpha 0.2)
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

Tests use temporary copies (`tempfile`) and never modify fixtures permanently. They cover: valid 12-row sample, missing column, missing S1, duplicate ID, uppercase FILL, >20 rows, invalid numeric, invalid manifest, wrong CRS/pilot, dishonest `not_available`.

Existing scaffold check still runs separately:

```powershell
python scripts/check_scaffold.py
# SCAFFOLD OK 17-feature, R2 avoidance deterministic
```

---

## What 0 STUBs means (2025-11-15 truth)

| Tag | Meaning | S example |
|---|---|---|
| **STUB** | temporary placeholder, no source | **0 remain** |
| **REAL** | directly verified from committed source file | IMD 0.25° `ind2024_rfp25.nc` → 14.0/327.3/712.2 (S) ; CCI `extract_soil_cci.py` 0.271 7/7 valid ; SRTM `n27_e088` Horn/D8/`usgs_s234.json` 28.5°/1290 m etc ; Sentinel-2 `S2B_45RXL_20241129` 0.718/0.139/0.817/0.468 ; WorldCover `N27E087` 76.7% FOREST/BUILT ; OSM 1014/226/504 `roads_osm_provenance.json` ; USGS 26 quakes `usgs_quakes.json` |
| **PROXY-published-map** | indirect substitute tagged, stronger than STUB | `lingtse_granite_gneiss` uniform (Bhukosh WFS timeout 15s both `bhukosh_vector_attempt.json:1`) ; lineament 0.8 uniform (Bhuvan SK_LN50K_0506 verified, no per-slope clip) |
| **PROXY-window** | measured but window-scale | `drain_density` 0.0 S1 (D 0.0 all, N 0.97–3.39) inside 271-m / 300 m |

Current sample: **17 numeric + lulc all REAL/PROXY, 0 STUBs**, `evidence_quality` dated-only-negative/approximate, frozen 89/78/66/52 scored via `score=round(raw_proba*100)` (scaffold when weights absent). Training 2936 1468+1468 GroupKFold8 RF **0.9338** XGB **0.9418** Brier isotonic **0.0971** `calibration.md:8` — validator ensures shape/honesty, not Brier.

---

## What evidence is required to upgrade PROXY→REAL

Per `03_DATA_PLAN_SIH26001.md` + `05_FEATURE_SCHEMA_SIH26001.md`:

| Feature | Needs for REAL |
|---|---|
| Terrain `slope/elev/aspect/curv/TWI/SPI` | Already REAL: SRTM 30 m `n27_e088` + `rasterio`/`GDAL` Horn-1981 + TWI/SPI + `usgs_s234.json` checksum ; IMD 1901-2024, wound 2 scars vet queue `wound_map.json`, runout 85 buildings S2 `runout_exposure.json` |
| Rainfall `24h/7d/30d` | Already REAL hist: IMD 0.25° NetCDF + `extract_gangtok_rainfall.py` log + live `GET /api/forecast/live:1154` + gated `GET /api/forecast/imd-live:1124` |
| Soil `0–1` | Already REAL: CCI TCDR v09.2 `extract_soil_cci.py` 7/7 valid → mean 0.271 ; SWI `swi.py:14` L1=15 L2=60 L3=60 is warning overlay |
| NDVI/LULC | Already REAL: Sentinel-2 L2A ID + /vsicurl/ calc ; WorldCover 10 m codebook 10→FOREST 50→BUILT |
| Lithology | **Bhukosh vector clip per-slope** (WFS GetCapabilities succeeded, polygon download) — currently timeout, so PROXY-published-map remains honest |
| Road/river | Already counts-proven: OSM Overpass sikkim+bbox extract + `roads_osm_provenance.json` 1014/226/504 + `osm-qa-unverified` ; geometry demo deterministic for R2 avoidance (`RISK_WEIGHT 3.0` `alpha 0.2` `comparison.py`) — full traces on demand |
| Labels `previous_landslide/event` | GSI Bhusanket 30k export + haversine 300 m join ; `event` requires dated in-window |
| Seismic | Already REAL: USGS FDSN 26 M5+ 1965–2024 `usgs_quakes.json:1` → 3 feats per-zone |

Every REAL upgrade must fill `manifest.sample.json` entry: real `date`, `tiles`/`export`/`extract`, `checksums` — never invented. Until then keep `status:not_available` `date:null`.

---

*Run both green before merge: `python scripts/check_scaffold.py` and `python scripts/validate_ngen_sample.py`.*