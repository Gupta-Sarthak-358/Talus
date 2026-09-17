# ML Model Card v2 (DRAFT, 2026-09-17) — SIH26001 Phase-1 prototype

Intended use: susceptibility screening prototype for the Gangtok/Sikkim pilot; NOT a safety standard, NOT a per-landslide predictor.

Training data: inventory-scale matrix (2936 rows, 764 positives from GSI shapefile + report PDF after <50m dedupe, 764 background negatives; season-window proxy target tagged approximate; full provenance in data/sih26001/manifest.training.json).

Model: RandomForestClassifier(500 trees, seed 42) + isotonic calibration; LR baseline beaten on spatial OOF (AUC 0.9345 vs 0.8913); calibrated Brier 0.0967 vs naive 0.25.

Validation: spatial GroupKFold(8) OOF (no random splits); temporal holdout skipped (only 673 dated positives <=2018 — INITIATION year-or-0); TreeSHAP per-prediction sample computed (5 points, see manifest shap_sample).

Limitations: climatology/quasi-static proxies (rain/soil/NDVI tagged); uniform lithology/lineament omitted from X; OSM center-approx distances (osm-qa-unverified); demo fixtures/scores untouched by this lane.

Post-card experiments (do not change the frozen Phase-1 model above): E-ladder
(`docs/sih26001/EXPERIMENTS_E_LADDER.md`) stress-tested this model — hard-negative
AUC 0.7804, southern-background debt found and corrected via E1.5b (+1114 southern
+540 northern negatives, experiment lane only), E12 froze the follow-on architecture
(global backbone + South specialist branch). `recent_disturbance` removed from X per E8.
