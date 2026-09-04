# NGEN Provenance — Darjeeling Corridor (D1–D4)

Closes the Darjeeling data gap: D rows in `feature_matrix.sample.csv` are now
measured extracts, not S1 clones. Same methods as the Gangtok S1–S4 pipeline
(`NGEN_PROVENANCE_S1.md`), new coordinates from `slopes.darjeeling.json`.

Script: `scripts/extract_darjeeling_ngen.py` (`--only local` / `--only network`).
Frozen output: `data/sih26001/processed/darjeeling_ngen.json`
(sha256 `8a494f03ee30014b9d24407c03abe6abaae55f9c99a020371a60fdc28f0ec81c`).

## Zone points (single source: slopes.darjeeling.json geometry)

| zone | lat | lon | site |
|---|---|---|---|
| D1 | 27.047 | 88.263 | Ghoom (upper) |
| D2 | 27.040 | 88.275 | Hill Cart Rd road-cut |
| D3 | 27.027 | 88.2695 | Lebong (mid) |
| D4 | 27.017 | 88.258 | Valley staging |

## Per-feature pedigree (17/17 REAL/PROXY, zero STUBs)

| # | feature | D value(s) | source | tag |
|---|---|---|---|---|
| 1 | slope_angle | 18.9/29.8/27.0/40.6 | USGS SRTMGL1 v3 tile n27_e088 (local; Darjeeling inside 88–89E/27–28N), Horn-1981 anisotropic | REAL |
| 2 | elevation | 2019/1715/1970/2306 m bilinear | same tile | REAL |
| 3 | aspect | 238/43/145/126 downslope-from-north | same tile | REAL |
| 4 | curvature | 0.0026/0.0066/-0.0013/-0.0211 Laplacian | same tile | REAL |
| 5 | twi | 5.08/5.48/5.38/4.57, D8 priority-flood on Darjeeling window lat 27.00–27.07/lon 88.23–88.29 | same tile | REAL |
| 6 | spi | 18.9/78.7/56.0/70.9 | same window | REAL |
| 7–9 | rainfall 24h/7d/30d | 20.4/397.0/1209.2, IMD 0.25° nearest cell (27.00, 88.25), wettest trailing-7d of 2024 ends **2024-07-08** (per-corridor window; S rows stay 2024-06-16) | LOCAL ind2024_rfp25.nc | REAL |
| 10 | soil_moisture | 0.297 all D, CCI COMBINED TCDR v202505 June 10–16 window-mean, 7/7 valid, cell (27.125, 88.375), same flag mask | LOCAL C3S files | REAL |
| 11 | ndvi | 0.688/0.848/0.880/0.821, S2B_45RXK_20241129 (sibling granule of Gangtok scene, same date, cloud 0.02%), all scl=4 | Element84 STAC + COG | REAL post-monsoon quasi-static |
| 12 | lulc | FOREST all D (WC-10, 3x3 agree 9/9) | SAME WorldCover tile N27E087 (covers Darjeeling) | REAL |
| 13 | lithology | darjeeling_gneiss all D | Gangtok DRAP p71/p118 names Darjeeling Gneiss as regional unit | PROXY-published-map (not Bhukosh vector) |
| 14 | distance_to_road | 71/29/354/6 m, same Overpass filters/radii (retries for rate-limit) | Overpass | osm-qa-unverified |
| 15 | distance_to_river | 234/520/314/326 m | Overpass | measured |
| 16 | lineament_density | 0.8 all D | Himalayan-50K literature basis; **Darjeeling figure NOT consulted** | PROXY-regional (Bhuvan WB-clip = upgrade) |
| 17 | drain_density | 0.0 all D (no ≥1 km² channel cells within 300 m) | same USGS accumulation grids | PROXY-window measured |
| L1 | previous_landslide | D2=1 (WB/DAR/78A08/2015/78 @242.7 m, INIT 2007), D3=1 (WB/DAR/78A08/2015/59 @231.9 m, INIT 2007), D1/D4=0 | LOCAL GSI shapefile, 1862 WB rows, 300 m rule | REAL-cited |
| L2 | event | 0 all (INITIATION year-only, same rule as Sikkim) | — | honest 0 |
| Q | evidence_quality | approximate (D2/D3), dated-only-negative (D1/D4) | same rule | — |
| Q | time_window | 2024-07-08 (Darjeeling peak; differs honestly from S 2024-06-16) | IMD | REAL date |

## Honesty notes (do not remove)

- D4 slope 40.6°/elev 2306 m is steep but inside the same absurdity gates as
  Gangtok (slope ≤ 80°, elev 1500–2600 m for the Darjeeling ridge; Tiger Hill
  2590 m is 3 km south). Measured, not tuned.
- Same-cell consequences stated: rain cell (27.00, 88.25) and soil cell
  (27.125, 88.375) serve all D (0.25° representativeness limit, as Gangtok).
- Sentinel granule lesson: Gangtok granule 45RXL did **not** cover D3/D4 — the
  picker now requires single-scene full-D coverage (45RXK, same date).
- Frozen model scores/SHAP in slopes.darjeeling.json are unchanged demo
  fixtures; NGEN feeds the feature/telemetry display layer.
- Lachung N-rows remain S1-clones (next lane); only Darjeeling was in scope.
