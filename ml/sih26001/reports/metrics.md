# SIH26001 Phase-1 training metrics (2026-09-17)

Target: `event` season-window proxy (positives = inventoried Sikkim + Darjeeling-hills (WB) slides, tagged `approximate`; negatives = >300m background, seed 42). n=2936 (pos=1468). X = 17 numeric (spi log1p + seismic x3) + lulc one-hot (drop_first); lithology/lineament omitted (uniform PROXY), previous_landslide omitted (leakage — positives ARE inventory slides).

## Spatial GroupKFold(8) out-of-fold (clusters = KMeans-8 on coords, seed 42)

| model | AUC | Brier | ECE10 | acc@0.5 |
|---|---|---|---|---|
| LR baseline | 0.8913 | 0.1275 | 0.0411 | 0.8185 |
| RF 500 trees | 0.9345 | 0.1165 | 0.111 | 0.83 |
| XGB | 0.9421 | 0.12 | 0.0968 | 0.8338 |
| LGBM | 0.9406 | 0.1392 | 0.1275 | 0.827 |
| naive prevalence | — | 0.25 | 0.0 | — |

## Per-held-out-cluster AUC (leave-one-cluster-out shape, KMeans labels)

| held-out cluster | LR | RF | XGB | LGBM |
|---|---|---|---|---|
| cluster_0 | n/a | n/a | n/a | n/a |
| cluster_1 | 0.6629 | 0.8456 | 0.8707 | 0.8652 |
| cluster_2 | 0.7589 | 0.8267 | 0.8184 | 0.8257 |
| cluster_3 | 0.993 | 1.0 | 0.998 | 0.996 |
| cluster_4 | 0.9436 | 0.9861 | 0.9948 | 0.9914 |
| cluster_5 | 0.7045 | 0.8071 | 0.7953 | 0.7991 |
| cluster_6 | 0.8587 | 0.8566 | 0.9043 | 0.8985 |
| cluster_7 | 0.9377 | 0.9476 | 0.9691 | 0.9632 |

## Temporal holdout

{
  "rule": ">= 30 dated positives per side",
  "n_train_pos_dated": 673,
  "n_test_pos_dated": 73,
  "negatives_split": "seeded 50/50 (timeless background)",
  "done": true,
  "test_n": 807,
  "rf_test": {
    "auc": 0.8573,
    "brier": 0.0967,
    "ece10": 0.0976
  }
}

## Threshold-consistency screen

{
  "june_total_separator_mm": 390.0,
  "frac_points_above_separator": 0.8736,
  "median_split_mm": 546.8,
  "mean_oof_p_above_median": 0.4979,
  "mean_oof_p_below_median": 0.3279,
  "frac_pos_dailymax_ge_144": 0.1907,
  "note": "Dahal 144mm is an event-intensity threshold; our 24h proxy is a JJAS-daily-max climatology, so this fraction is a consistency screen, not a threshold validation"
}

## Permutation importance (in-sample screening, RF full-data fit)

| elevation | 0.0227 | 0.1906 |
| seismic_n50_rate | 0.0097 | 0.1113 |
| distance_to_road | 0.0068 | 0.1624 |
| rainfall_30d_mm | 0.0011 | 0.0707 |
| ndvi | 0.0009 | 0.043 |
| seismic_years_since | 0.0001 | 0.0467 |
| soil_moisture | 0.0001 | 0.0545 |
| rainfall_24h_mm | 0.0 | 0.0545 |
| slope_angle | 0.0 | 0.0296 |
| seismic_dist_km | 0.0 | 0.0511 |
| rainfall_7d_mm | 0.0 | 0.0502 |
| distance_to_river | 0.0 | 0.0353 |
| lulc_WETLAND | 0.0 | 0.0 |
| lulc_FOREST | 0.0 | 0.0053 |
| drain_density | 0.0 | 0.0094 |
| aspect | 0.0 | 0.0211 |
| spi_log | 0.0 | 0.0191 |
| curvature | 0.0 | 0.0162 |
| lulc_BARREN | 0.0 | 0.0007 |
| recent_disturbance | 0.0 | 0.0 |
| lulc_BUILT | 0.0 | 0.0054 |
| lulc_WATER | 0.0 | 0.0058 |
| twi | 0.0 | 0.0172 |

SHAP sample: 5 points TreeSHAP on RF (see manifest shap_sample)
