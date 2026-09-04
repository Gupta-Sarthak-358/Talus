# SIH26001 Phase-1 training metrics (2026-09-04)

Target: `event` season-window proxy (positives = inventoried Sikkim slides, tagged `approximate`; negatives = >300m background, seed 42). n=1528 (pos=764). X = 14 numeric (spi log1p) + lulc one-hot (drop_first); lithology/lineament omitted (uniform PROXY), previous_landslide omitted (leakage — positives ARE inventory slides).

## Spatial GroupKFold(8) out-of-fold (clusters = KMeans-8 on coords, seed 42)

| model | AUC | Brier | ECE10 | acc@0.5 |
|---|---|---|---|---|
| LR baseline | 0.8895 | 0.1363 | 0.0686 | 0.8037 |
| RF 500 trees | 0.921 | 0.1111 | 0.0688 | 0.8495 |
| naive prevalence | — | 0.25 | 0.0 | — |

## Per-held-out-cluster AUC (leave-one-cluster-out shape, KMeans labels)

| held-out cluster | LR | RF |
|---|---|---|
| cluster_0 | 0.9207 | 0.9296 |
| cluster_1 | 0.7624 | 0.8188 |
| cluster_2 | 0.9871 | 1.0 |
| cluster_3 | 0.9269 | 0.9337 |
| cluster_4 | 0.6646 | 0.7996 |
| cluster_5 | 0.9879 | 0.9958 |
| cluster_6 | n/a | n/a |
| cluster_7 | 0.8525 | 0.8333 |

## Temporal holdout

{
  "rule": ">= 30 dated positives per side",
  "n_train_pos_dated": 21,
  "n_test_pos_dated": 71,
  "negatives_split": "seeded 50/50 (timeless background)",
  "done": false,
  "reason": "only 21 dated positives <=2018 / 71 >=2019 (672/764 positives undated) \u2014 below rule; skipped, not fudged"
}

## Threshold-consistency screen

{
  "june_total_separator_mm": 390.0,
  "frac_points_above_separator": 1.0,
  "median_split_mm": 484.0,
  "mean_oof_p_above_median": 0.5119,
  "mean_oof_p_below_median": 0.351,
  "frac_pos_dailymax_ge_144": 0.1047,
  "note": "Dahal 144mm is an event-intensity threshold; our 24h proxy is a JJAS-daily-max climatology, so this fraction is a consistency screen, not a threshold validation"
}

## Permutation importance (in-sample screening, RF full-data fit)

| elevation | 0.0641 | 0.2024 |
| distance_to_road | 0.0479 | 0.2462 |
| ndvi | 0.012 | 0.0848 |
| slope_angle | 0.0021 | 0.0565 |
| aspect | 0.0006 | 0.0457 |
| soil_moisture | 0.0001 | 0.0791 |
| distance_to_river | 0.0 | 0.0483 |
| rainfall_24h_mm | 0.0 | 0.045 |
| twi | 0.0 | 0.0323 |
| spi_log | 0.0 | 0.0338 |
| curvature | 0.0 | 0.0332 |
| rainfall_30d_mm | 0.0 | 0.0264 |
| drain_density | 0.0 | 0.019 |
| rainfall_7d_mm | -0.0 | 0.0252 |
| lulc_BUILT | -0.0 | 0.0087 |
| lulc_FOREST | -0.0 | 0.0081 |
| lulc_BARREN | -0.0 | 0.0011 |
| lulc_WATER | -0.0 | 0.0037 |
| lulc_WETLAND | -0.0 | 0.0003 |

SHAP deferred (package absent); permutation+impurity above instead.
