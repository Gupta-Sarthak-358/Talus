# TALUS ML Model Card — v1 (frozen 2025-11-15)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


Status: FROZEN. Selected via spatial GroupKFold only; temporal holdout untouched for selection. Replaces Neyveli synthetic generator-era card — see git history for that era.

## Model

| Field | Value |
|---|---|
| Estimators | RandomForestClassifier 500 trees + XGBoost 400 + LightGBM 400 (primary: RF, ensemble reported) |
| RF config | `n_estimators=500, random_state=42, max_depth` default (500-tree seed-42 frozen bundle) |
| Preprocessing | 17 numeric (spi `log1p` + seismic ×3) + `lulc` one-hot (`drop_first`); `lithology`/`lineament_density` omitted (uniform PROXY), `previous_landslide` omitted (leakage — positives ARE inventory) |
| Target | `event` season-window proxy (probabilistic susceptibility, not deterministic landslide time/place) |
| Feature set | **SIH26001 frozen 17+1** — `slope_angle, elevation, aspect, curvature, twi, spi_log, rainfall_24h/7d/30d, soil_moisture, ndvi, lulc, distance_to_road, distance_to_river, drain_density, seismic_n50_rate/dist_km/years_since` |
| Calibration | Isotonic on RF OOF (`CalibratedClassifierCV`-style prefit) + Bayes prevalence `0.5→0.01` (`confidence_real_1pct`) |
| Explainability | TreeSHAP top-5 per zone via `shap.TreeExplainer` (`sih26001_model.py` live_scores; fixture fallback when `shap` absent) |
| Live path | `ml/sih26001/reports/metrics.md` + `backend/app/sih26001_model.py` Sih26001Live (weights `ml/models/sih26001_rf_v1.joblib` + `_iso_v1.joblib`; absent → honest fixture 89/78/66/52) |

## Data

| Split | Method | n |
|---|---|---|
| Training | 2936 rows (`1468+1468` Sikkim + Darjeeling-hills inventoried + >300m background 1:1, seed 42) | 2936 |
| Spatial OOF | `GroupKFold(8)`, clusters = `KMeans-8` on coords (seed 42) | 2936 OOF |
| Temporal holdout | 673 train / 73 test dated positives + 50/50 negatives (seeded, timeless background) | test_n 807 |
| NGEN sample | 12 rows (S1–S4 Gangtok, D1–D4 Darjeeling, N1–N4 Lachung) | 12 |

Corpus: `data/sih26001/processed/feature_matrix.training.csv` (git-ignored except `.training.sample.csv`), `data/sih26001/fixtures/feature_matrix.sample.csv` (committed 12-row zero-STUB sample, `manifest.sample.json`).
GIS: SRTM n27_e088 30m, CCI v09.2 1978–2024, IMD 0.25° 1901–2024 + Open-Meteo live, Sentinel-2 2 scars, USGS 26 quakes M5+, OSM roads 1014/226/504.

## Metrics (current — Groups ensure no leakage)

### Spatial GroupKFold(8) out-of-fold

| model | AUC | Brier | ECE10 | acc@0.5 |
|---|---|---|---|---|
| LR baseline | 0.8914 | 0.1274 | 0.0409 | 0.8185 |
| **RF 500** | **0.9338** | **0.118** | 0.1153 | 0.8263 |
| **XGB 400** | **0.9418** | 0.1198 | 0.0957 | 0.8362 |
| LGBM 400 | 0.9406 | 0.1392 | 0.1275 | 0.827 |
| naive prevalence | — | 0.25 | — | — |

Per-held-out-cluster: cluster_0 n/a (single-class fold, pooled OOF disclosed) — others 0.80–1.0 (`metrics.md` table).

### Calibration

| predictor | Brier | ECE10 |
|---|---|---|
| RF raw OOF | 0.118 | 0.1153 |
| **RF isotonic OOF** | **0.0971** | **0.0** |
| naive | 0.25 | — |

`Confidence = isotonic P(elevated susceptibility)` under prototype `event` target — NOT absolute probability of a slide tomorrow.

### Prevalence correction (RECALIBRATION_NOTE.md)

```
p_real = p_cal*0.02 / (p_cal*0.02 + (1-p_cal)*1.98)  with pi_train 0.5 → pi_real 0.01
```
Score `round(p_raw*100)` frozen; bands/routing/warning unchanged; added field `confidence_real_1pct` shown as “per hillslope-day at ~1% base rate” (`GET /api/model/calib?pi_real=0.01`).

### Temporal holdout

`rf_test: AUC 0.8568 Brier 0.0978 ECE10 0.0986` on `n=807` (673/73 dated pos). Optimism caveat: isotonic fit shares OOF — temporal is the clean check.

### Threshold-consistency screen

`june_total_separator 390 mm, 87.36% points above separator; Dahal 144 mm proxy 19.07% — consistency screen, not validation` (`metrics.md`).

### Permutation importance (RF full-data screening)

Leaders: `elevation 0.0196 / 0.1934, seismic_n50_rate, distance_to_road, rainfall_30d, ndvi …` — terrain + exposure + seismic + rain; SHAP sample 5 points in manifest.

### Warning overlay (scoring frozen)

Effective rain `7d + 0.3*30d` per-zone thresholds `warning_thresholds.json` (Gangtok S1 385 S2 395 S3 410 S4 375; Lachung N1 380 N2 390 N3 405 N4 370; Darjeeling D1 400 D2 410 D3 420 D4 390) + SWI 3-tank `L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 tanh(SWI/100)` + wound + forecast + quake 25% drop — 6-state `NORMAL→EVACUATE`.

## Selection rationale

RF primary by spatial OOF (beats LR 0.8914, clean gate); XGB/LGBM best honestly reported (0.9418). 4 families within ~1 point — ceiling is information, not architecture. Isotonic chosen by Brier 0.0971 vs raw 0.118. No test-touch for selection; pre-GroupKFold numbers are superseded — do not cite.

## Known limitations

1. `event` is season-window proxy tagged `approximate` (inventory years, not exact slide days); in-situ sensors are adapter-ready.
2. Uniform lithology/lineament PROXY omitted — geology signal absent by design (Bhukosh WFS timeout 15s).
3. Per-corridor calibration deferred (<200 dated/corridor; region-specific isotonic post-hackathon).
4. Spatial GroupKFold still pools one single-class fold (cluster_0 n/a) — disclosed, not dropped.
5. `previous_landslide` excluded by leakage rule (positives ARE inventory) — history enters via dated holdout only.
6. Moderate band narrow; soil is quasi-static CCI window-mean (SWI overlays warning only).

## Reproducibility

`random_state=42` throughout; splits seed-intact; KMeans-8 seed 42; `scripts/train_sih26001.py` + `scripts/build_training_matrix.py --rebuild` (weights gitignored, reports commit). Deterministic SHAP fixture fallback when `shap` absent.