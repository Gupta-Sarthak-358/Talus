# SIH26001 Phase-1 training metrics (2026-09-04)

Target: `event` season-window proxy (positives = inventoried Sikkim + Darjeeling-hills (WB) slides, tagged `approximate`; negatives = >300m background, seed 42). n=2936 (pos=1468). X = 14 numeric (spi log1p) + lulc one-hot (drop_first); lithology/lineament omitted (uniform PROXY), previous_landslide omitted (leakage — positives ARE inventory slides).

## Spatial GroupKFold(8) out-of-fold (clusters = KMeans-8 on coords, seed 42)

| model | AUC | Brier | ECE10 | acc@0.5 |
|---|---|---|---|---|
| LR baseline | 0.8947 | 0.1214 | 0.029 | 0.8283 |
| RF 500 trees | 0.8983 | 0.1254 | 0.0621 | 0.8208 |
| XGB | 0.9029 | 0.1328 | 0.0809 | 0.813 |
| LGBM | 0.9015 | 0.144 | 0.1122 | 0.8076 |
| naive prevalence | — | 0.25 | 0.0 | — |

## Per-held-out-cluster AUC (leave-one-cluster-out shape, KMeans labels)

| held-out cluster | LR | RF | XGB | LGBM |
|---|---|---|---|---|
| cluster_0 | n/a | n/a | n/a | n/a |
| cluster_1 | 0.6938 | 0.7248 | 0.7435 | 0.7453 |
| cluster_2 | 0.7714 | 0.7499 | 0.744 | 0.7639 |
| cluster_3 | 0.99 | 1.0 | 0.996 | 0.995 |
| cluster_4 | 0.9408 | 0.9392 | 0.9517 | 0.947 |
| cluster_5 | 0.67 | 0.6972 | 0.6852 | 0.6509 |
| cluster_6 | 0.865 | 0.8807 | 0.8993 | 0.9025 |
| cluster_7 | 0.937 | 0.9193 | 0.8854 | 0.882 |

## Temporal holdout

{
  "rule": ">= 30 dated positives per side",
  "n_train_pos_dated": 673,
  "n_test_pos_dated": 73,
  "negatives_split": "seeded 50/50 (timeless background)",
  "done": true,
  "test_n": 807,
  "rf_test": {
    "auc": 0.8189,
    "brier": 0.1216,
    "ece10": 0.1061
  }
}

## Threshold-consistency screen

{
  "june_total_separator_mm": 390.0,
  "frac_points_above_separator": 1.0,
  "median_split_mm": 557.4,
  "mean_oof_p_above_median": 0.6322,
  "mean_oof_p_below_median": 0.2805,
  "frac_pos_dailymax_ge_144": 0.2616,
  "note": "Dahal 144mm is an event-intensity threshold; our 24h proxy is a JJAS-daily-max climatology, so this fraction is a consistency screen, not a threshold validation"
}

## Permutation importance (in-sample screening, RF full-data fit)

| elevation | 0.0705 | 0.207 |
| distance_to_road | 0.0332 | 0.2005 |
| ndvi | 0.0161 | 0.0755 |
| slope_angle | 0.0034 | 0.0587 |
| soil_moisture | 0.003 | 0.0935 |
| aspect | 0.0003 | 0.0465 |
| rainfall_24h_mm | 0.0001 | 0.0529 |
| rainfall_30d_mm | 0.0001 | 0.0339 |
| distance_to_river | 0.0 | 0.0506 |
| curvature | 0.0 | 0.0372 |
| rainfall_7d_mm | 0.0 | 0.0304 |
| spi_log | 0.0 | 0.039 |
| lulc_BUILT | 0.0 | 0.0082 |
| drain_density | 0.0 | 0.0182 |
| lulc_WATER | 0.0 | 0.0037 |
| lulc_BARREN | 0.0 | 0.001 |
| twi | -0.0 | 0.036 |
| lulc_FOREST | -0.0 | 0.0073 |
| lulc_WETLAND | -0.0 | 0.0 |

SHAP sample: 5 points TreeSHAP on RF (see manifest shap_sample)
