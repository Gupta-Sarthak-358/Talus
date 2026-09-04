# NGEN Provenance — Lachung Corridor (N1–N4)

Closes the Lachung data gap: N rows in `feature_matrix.sample.csv` are now
measured extracts, not S1 clones. Same methods as the Gangtok/Darjeeling
pipeline, new coordinates from `slopes.lachung.json`.

Script: `scripts/extract_lachung_ngen.py` (`--only local` / `--only network`;
Overpass retries; single-scene full-N coverage required).
Frozen output: `data/processed/terrain/lachung_ngen.json`
(sha256 `0764f5a2d9c69ee23299fcdb8e5781bf0a5625311b1d88d031f6809be28113a9`).

## Zone points (single source: slopes.lachung.json geometry)

| zone | lat | lon | site |
|---|---|---|---|
| N1 | 27.695 | 88.735 | Upper (Yumthang approach) |
| N2 | 27.688 | 88.747 | Road-cut (NH-310A) |
| N3 | 27.678 | 88.7415 | Mid (River Bend) |
| N4 | 27.665 | 88.730 | Valley staging |

## Per-feature pedigree (17/17 REAL/PROXY, zero STUBs)

| # | feature | N value(s) | source | tag |
|---|---|---|---|---|
| 1 | slope_angle | 35.9/24.4/37.9/27.9 | USGS SRTMGL1 v3 tile n27_e088 (local), Horn-1981 anisotropic | REAL |
| 2 | elevation | 3095/2686/2685/2542 m bilinear | same tile | REAL |
| 3 | aspect | 46/265/346/163 downslope-from-north | same tile | REAL |
| 4 | curvature | -0.0586/-0.0067/0.0080/0.0040 Laplacian | same tile | REAL |
| 5 | twi | 4.33/5.20/4.66/5.05, D8 priority-flood on Lachung window lat 27.64–27.72/lon 88.68–88.80 | same tile | REAL |
| 6 | spi | 39.6/37.3/64.0/43.4 | same window | REAL |
| 7–9 | rainfall 24h/7d/30d | 43.2/314.5/669.8, IMD 0.25° nearest cell (27.75, 88.75), wettest trailing-7d of 2024 ends **2024-06-17** (per-corridor window) | LOCAL ind2024_rfp25.nc | REAL |
| 10 | soil_moisture | 0.264 all N, CCI COMBINED TCDR v202505 June 10–16 window-mean, 7/7 valid, cell (27.625, 88.625), same flag mask | LOCAL C3S files | REAL |
| 11 | ndvi | 0.605/0.122/0.782/0.645, S2B_45RXL_20241129 (the SAME Gangtok granule covers all N), N2 scl=5 bare rest scl=4 | Element84 STAC + COG | REAL post-monsoon quasi-static |
| 12 | lulc | FOREST/BUILT/FOREST/AGRI (WC-10 9/9, WC-50 7/9, WC-10 9/9, WC-30 6/9; cross-checks NDVI incl. N2 bare road-cut) | SAME WorldCover tile N27E087 | REAL |
| 13 | lithology | chungthang_subgroup_gneiss all N | CGWB 2025: Chungthang = North-Sikkim country rock; nearest verified map Gangtok town | PROXY-published-map (not Bhukosh vector) |
| 14 | distance_to_road | 784/15/519/17 m, same Overpass filters/radii (retries for rate-limit) | Overpass | osm-qa-unverified |
| 15 | distance_to_river | 986/285/381/154 m | Overpass | measured |
| 16 | lineament_density | 0.8 all N | literature basis; Lachung INSIDE verified Bhuvan SK_LN50K_0506 bbox (88.035/27.073–88.892/28.061), no per-slope clip | PROXY-regional (Bhuvan clip = upgrade) |
| 17 | drain_density | 0.97/1.07/2.81/3.39 (≥1 km² channel cells within 300 m) | same USGS accumulation grids | PROXY-window measured |
| L1 | previous_landslide | 0 all N (nearest 800 m+: N1/N2 SKM/NS/78A10/2017/206 @1026/832 m, N3/N4 SKM/NS/78A10/2017/205 @801/1245 m) | LOCAL GSI shapefile, 693 Sikkim rows, 300 m rule | REAL-cited negatives |
| L2 | event | 0 all (INITIATION year-or-0, same rule) | — | honest 0 |
| Q | evidence_quality | dated-only-negative all N | same rule | — |
| Q | time_window | 2024-06-17 (Lachung peak) | IMD | REAL date |

## Honesty notes (do not remove)

- High-Himalaya SRTM voids: 28,011 void cells in the Lachung window (vs 0 at
  Darjeeling) neighbour-mean filled; per-slope derivatives read off the
  filled grid (logged in script output). N1's own 3x3 contained a void.
- N1 elev 3095 m is inside the Lachung absurdity gate (1800–3200 m;
  Yumthang approach is genuinely high). Measured, not tuned.
- Same-cell consequences stated: rain cell (27.75, 88.75), soil cell
  (27.625, 88.625) serve all N (0.25° limit, as Gangtok/Darjeeling).
- Frozen model scores/SHAP in slopes.lachung.json are unchanged demo
  fixtures; NGEN feeds the feature/telemetry display layer.
- All three corridors now measured: S (2024-06-16), D (2024-07-08),
  N (2024-06-17). No cloned rows remain in the sample matrix.
