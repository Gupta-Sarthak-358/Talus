# ML Model Card v2 (DRAFT, 2026-09-04) — SIH26001 Phase-1 prototype

Intended use: susceptibility screening prototype for the Gangtok/Sikkim pilot; NOT a safety standard, NOT a per-landslide predictor.

Training data: inventory-scale matrix (1528 rows, 764 positives from GSI shapefile + report PDF after <50m dedupe, 764 background negatives; season-window proxy target tagged approximate; full provenance in data/sih26001/manifest.training.json).

Model: RandomForestClassifier(500 trees, seed 42) + isotonic calibration; LR baseline beaten on spatial OOF (AUC 0.921 vs 0.8895); calibrated Brier 0.1019 vs naive 0.25.

Validation: spatial GroupKFold(8) OOF (no random splits); temporal holdout skipped (only 21 dated positives <=2018 — INITIATION year-or-0); TreeSHAP per-prediction deferred (package absent; permutation importance in ml/sih26001/reports/metrics.md).

Limitations: climatology/quasi-static proxies (rain/soil/NDVI tagged); uniform lithology/lineament omitted from X; OSM center-approx distances (osm-qa-unverified); demo fixtures/scores untouched by this lane.
