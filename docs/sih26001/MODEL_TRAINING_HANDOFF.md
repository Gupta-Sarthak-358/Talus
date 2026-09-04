# MODEL TRAINING HANDOFF — Inventory-Scale Susceptibility (SIH26001)

**For:** the agent/teammate taking the training lane (parallel to backend reporting)
**Date:** 2026-09-04 (hackathon Sept 5) · **Branches:** base `SIH26001 @ fc181f0` (also `demo-scaffold` / `ngen-pilot` synced)
**New branch:** `feature/sih26001/model-training` (branch off `SIH26001`, PR into `SIH26001`)
**Contract:** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md` §1 (S1–S4 frozen) · **Schema:** `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md:16` (22-col, 17 science + keys)
**Model plan (law):** `docs/sih26001/04_MODEL_PLAN_SIH26001.md` — read it before any code

Paste-ready prompt for a new agent is at the bottom. The rest is the full spec.

---

## 0. Current state — why training is feasible now, but not on the pilot fixture

*   **Pilot fixture:** `data/sih26001/fixtures/feature_matrix.sample.csv:1` is `n=4` with `event=0,0,0,0` single-class (plus `previous_landslide` has 1 positive). No binary learner trains there — any fit would be fabrication. Fitting is a pipeline smoke test only.
*   **Inventory-scale material already local + verified:**
    *   693 Sikkim shapefile points (all-India `GSI_Landslide_Inventory.shp.zip` → all 693 Sikkim `sikkim_join.json:6`) + 777 PDF Sikkim records (`landslide_report.pdf` p659-676 → `sikkim_report_gangtok.csv`:7 Gangtok rows) → expect ~1k unique after dedupe. Triggering is Rainfall* on bbox slides (`sikkim_join.json` 6 rows + PDF histories) — rainfall-trigger holds.
    *   IMD 0.25° 1901–present archive `data/raw/imd/ind*.nc` → pilot cell 27.25/88.50 verified for all slopes `scripts/extract_gangtok_rainfall.py:1`, same method scales to per-event climatology.
    *   CCI soil 2024-06-10–16 `data/processed/soil/gangtok_soil_cci.*` (ESA CCI TCDR v202505) + USGS 30m tile `data/raw/dem/n27_e088_1arc_v3.tif` → `data/processed/terrain/usgs_s234.json:1` (6 DEM derivatives), NDVI `s234_ndvi.json`, WorldCover LULC `s234_lulc.json` (rasterio /vsicurl), OSM distances `s234_osm_nearest.json`, lithology `s234_lithology.json` + lineament `s234_lineament.json` — all patterns are reusable, not just pilot constants.
    *   V1 training/benchmark apparatus `ml/training/` + `ml/benchmark/` + `ml/evaluation/` is reusable (RF 500 trees, isotonic calibration, SHAP).
*   **Honest blocker:** `INITIATION` is year-or-0, PDF histories are month/year only — no dated per-event 24h/7d window. Use season-window proxy (monsoon climatology, see §2) tagged `approximate` per `07_ASSUMPTIONS:5`, with a dated-only sensitivity run.

Demo protection: `TEAM_TASKS_SEPT5:24` Lane C — training is upside, not a demo blocker. Max demo touch = 1 fixture-score swap + model card, only if the run is clean.

## 1. Workflow (every time)

```bash
git clone https://github.com/Gupta-Sarthak-358/Talus.git && cd Talus
git fetch origin && git checkout SIH26001 && git pull
git checkout -b feature/sih26001/model-training
# Gates before any PR:
python scripts/check_scaffold.py  # must stay green
python scripts/validate_ngen_sample.py  # must stay green
python -m unittest discover -s tests -p "test_*.py" -v
```

1. Fetch/build → commit SMALL extracts/samples + script + sha256 to `manifest.sample.json` or a new `manifest.training.json` (both allowed; training artifact stays git-ignored).
2. Join → git-ignored `data/sih26001/processed/feature_matrix.training.parquet` or `.csv` + a committed `*.training.sample.csv` (≤20 rows) in the same 22-col schema.
3. Train → `ml/sih26001/` reports committed, models `ml/models/*.joblib` git-ignored `/.gitignore:78`.
4. PR into `SIH26001` with gate outputs pasted + method note. Never touch `slopes.json`/`roads.json`/`reports.json`/contract/scores/bands/roles/fronted pages.

## 2. What to build (inventory-scale)

### Positives
*   Dedupe the two Sikkim sources by haversine (<50m) → expect ~1k unique. Filter to study area = USGS tile bbox 88–89E/27–28N (or fetch n28 tile if you expand — freeze the choice in the manifest). Use state `Sikkim` + district `East Sikkim`/`Gangtok District` already parsed in `scripts/extract_sikkim_labels.py:1` + `scripts/extract_sikkim_report.py:1`.
*   Coordinates from shapefile `sikkim_gangtok_sample.csv` + PDF `sikkim_report_gangtok.csv`; year from `INITIATION`/history (year-only is fine — tag `approximate`).

### Negatives
*   Sample random points `>300m` from any positive (`03_DATA_PLAN:135`, `07_ASSUMPTIONS:6`), ratio 1:1 or 1:2, inside the same tile bbox. Log the buffer + seed.

### Features per point (~14, STUBs logged)
*   DEM 6: re-use `scripts/extract_usgs.py:1` pattern (bilinear elev + Horn slope/aspect + Laplacian curvature + D8 TWI/SPI) on the committed tile — no mirror.
*   Rain (proxy, honest): monsoon climatology at nearest IMD cell (event-year June mean + max 7-day spell at 27.25/88.50), not trailing 24h — INITIATION cannot support the latter. Tag proxy in `evidence_quality`.
*   Soil: window-mean from `scripts/extract_soil_cci.py:1` pattern (CCI, not ERA5 — CCI is stronger pedigree). Same-cell consequence stated.
*   NDVI: pinned Sentinel-2 scene `S2B_45RXL_20241129` + WorldCover LULC `s234_lulc.json` (10m, 3x3 mode) as quasi-static state — same justification as pilot.
*   OSM distances: download one Geofabrik Sikkim extract locally (do not hammer Overpass × 2k) → per-point haversine locally.
*   Lithology/lineament: pilot values are PROXY-published-map uniform — keep them uniform or omit for this prototype and log the delta from the 22-col demo fixture.

### Train + validate (`04_MODEL_PLAN:37-50`)
*   Baseline LR → RF (500 trees per v1) → optional XGB per plan.
*   Mandatory: spatial-cluster CV (`GroupKFold` on clusters, never random row split — `04_MODEL_PLAN:41`), isotonic calibration with Brier/ECE (`model_service.py:38` pattern), temporal holdout `train ≤2018 / test 2019+` if years allow, threshold cross-check vs Monga 2026 (`E = -11.10 + 0.62*D`) + Dahal 144mm.
*   Reports: `ml/sih26001/reports/{metrics,calibration,benchmarks}.md` committed. Model card `docs/sih26001/ML_MODEL_CARD_V2.md` draft.

## 3. Deliverables & gates

*   **Definition of done:** beats LR on spatial-held-out + calibration reported (Brier/ECE), not a magic AUC. Dibang AUC 0.96 / Meghalaya >90% are targets, not promises.
*   **Allowed demo touch:** `Lane C` — at most one `slopes.json` score swap + model card, only if the run is clean. Otherwise present as "training-ready" with matrix+manifest shape proof.
*   **Never:** fabricate dates to make per-event 24h windows, train on `n=4`, commit datasets/weights/`.env`/`PILOT_BRIEFING.md`, or add `FILL`.

## 4. Risks & mitigations

*   Overpass × 2k → use local OSM extract.
*   COG reads × 1k → single pinned scene.
*   Tile bounds → freeze to n27_e088 bbox in manifest or fetch n28 upfront.
*   Single-class pilot trap → builder must assert both `event` classes before training.

## 5. Questions for the requester (before you start)

1. **Target:** season-window susceptibility proxy (`approximate`, recommended — matches `07_ASSUMPTIONS:5`) vs strict dated-event (near-zero positives, not viable)?
2. **Study area:** tile-bounded n27_e088 (recommended, no downloads) vs full Sikkim (+ n28 tile fetch)?
3. **Ambition for Sept 5:** Phase 1 + model card with ≤1 swap (recommended if clean) vs training-ready only (zero swaps)?

---

## Paste-ready prompt for a new agent

```
You are the model-training agent for TALUS SIH26001 (NER landslide, hackathon Sept 5).
Setup: git clone https://github.com/Gupta-Sarthak-358/Talus.git && cd Talus && git fetch origin && git checkout SIH26001 && git pull && git checkout -b feature/sih26001/model-training
Then read docs/sih26001/MODEL_TRAINING_HANDOFF.md — it is your complete spec: data locations, dedupe/negative rules, per-point feature reuse (USGS, IMD climatology proxy, CCI soil, pinned Sentinel-2/WorldCover, local OSM), validation protocol from docs/sih26001/04_MODEL_PLAN_SIH26001.md (spatial-cluster CV mandatory, temporal holdout, isotonic Brier/ECE, LR baseline), deliverables, and gates.
Hard rules: never train on data/sih26001/fixtures/feature_matrix.sample.csv (n=4 single-class); expect ~1k unique Sikkim positives after dedupe + buffered negatives; train prototype on ~14 features (lithology/lineament stay PROXY uniform or omitted — log the delta); INITIATION is year-or-0 so use season-window proxy tagged approximate; study area frozen to n27_e088 tile 88-89E/27-28N unless you fetch n28; training matrix is git-ignored (commit ≤20-row sample only), models ml/models/*.joblib git-ignored, reports ml/sih26001/reports/ committed; max demo touch is 1 slopes.json score swap + model card only if clean, else training-ready; never commit datasets/weights/.env/docs/PILOT_BRIEFING.md and never use FILL; gates before PR: python scripts/check_scaffold.py && python scripts/validate_ngen_sample.py && python -m unittest discover -s tests -p "test_*.py" -v all green, paste outputs in PR body into SIH26001.
Questions for the owner: target season-window vs dated-event, tile-bounded vs full Sikkim, Phase 1+card vs training-ready only — default to recommended if no answer.
```
