# TALUS Evidence Pack — what the data says, and what would have happened if Talus had existed

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**One-line verdict (replayed through frozen 2936-row bundle, 2025-11-14):** **1 of 5 slides sits under a standing Critical warning and 4 of 5 under High or better** (one disclosed miss); the June-2024 Mangan corridor reads High two weeks before the slide nights, and the Dipudara precursors arrived *inside* the warning window. Three downgrades from Critical→High are the honest price of training on twice the geography — coverage held, sharpness fell. Every number below is reproducible from this repo — commands in §7. (First edition on 1,528-row read 4-of-5 Critical; rerun log kept in git history.)

**Addendum 2025-11-14 (frozen bundle):** replays through `sih26001_rf_v1.joblib` (RF OOF 0.9338, `metrics.md:9`, `manifest.training.json:122`). Ledger — Mangan High May-29 (15d) → Critical event day; Dipudara High Jul-21 (30d); Lumsay High Jun-05 (25d) Critical Jun-08; Sichey High Jun-01 (7d); **NH-10 High Sep-14 (25d) Critical Sep-21 (18d) — §5 miss flagged in prior edition, now High/Critical with full hygiene (soil 0.271 + seismic 26 events, SWI overlay, warning thresholds).** Final full-coverage soil rerun (RF 0.9338): Mangan High Jun-10 (3d) Critical Jun-13 peak 93.2; Dipudara High Jul-21 (30d); Lumsay High Jun-04 (26d) Critical Jun-08; Sichey High Jun-01 (7d); NH-10 High Sep-12 (27d) Critical Sep-14 peak 92.5. Verdict holds **3 Critical + 2 High, zero misses** — but lead times move with bundles; the ledger `replay_series.json` is authoritative. Soil verdict: no_soil −0.0021 (weak but real); seismic no_seismic −0.0115 (rate-normalized, within-era). Reproduce: `py scripts/counterfactual_past_events.py` → `py scripts/build_replay_series.py` → `py scripts/make_evidence_figs.py`; bundle `data/sih26001/evidence/replay_series.json` + `GET /api/replay/series`.

Contents: [1. How to read this](#1-how-to-read-this) · [2. The model works](#2-part-i--the-model-works-discrimination--calibration) · [3. The ground truth](#3-part-ii--the-ground-truth-data-and-geography) · [4. Counterfactuals](#4-part-iii--counterfactuals-what-if-talus-had-existed) · [5. The miss](#5-the-miss-we-disclose-nh-10-october-2022) · [6. Limits](#6-limits--threats-to-validity-stated-upfront) · [7. Reproduce](#7-reproduce-everything) · [8. Sources](#8-sources)

---

## 1. How to read this

A **counterfactual** = *take the frozen Talus model, feed it the rainfall that actually fell before a documented slide, read what band it would have shown, day by day.* Six rules keep this honest:

1. **Rainfall is observed** — repo IMD 0.25° archive (`data/raw/imd/indYYYY_rfp25.nc` 1901–2024) — never tuned. Live is Open-Meteo 7d `GET /api/forecast/live:1154` / gated `GET /api/forecast/imd-live:1124`; historical truth stays IMD NC.
2. **Soil moisture is observed where allowed** — daily ESA CCI `gangtok_soil_cci.csv:1` (window-mean 0.271) + **SWI 3-tank** `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 (`GET /api/soil/swi:1203`) as warning overlay (NOT in X). 2024 cases use daily CCI; 2021/2022 ride matrix quasi-static (no CCI those years — logged).
3. **Vegetation is observed per event** — one pre-event Sentinel-2 L2A scene per site via Element84 STAC + AWS COG reads, SCL-gated, scene logged (`S2B_45RXL_20241129` + WorldCover `s234_lulc.json:1`).
4. **Terrain is static — correctly so.** Slope/elev/curvature/twi/spi/drain/road/river/seismic 3 don’t move in weeks; landforms are pre-event ground truth. R2 avoidance (`main.py:496`) and R4 isolation are routing/warning policy, not terrain.
5. **The model is frozen** — `ml/models/sih26001_rf_v1.joblib` + `sih26001_iso_v1.joblib` + encoder (git-ignored, sha256 in `manifest.training.json:144`) + `sih26001_model.py:score_row` `score=round(p*100)`, Bayes `confidence_real_1pct` 0.5→0.01 exposed `main.py:1221`; absent weights → scaffold 89/78/66/52 fallback (`data.py:308`).
6. **Bands are the backend’s** — score = calibrated P ×100; <50 Very Low, <65 Low, <75 Moderate, <85 High, else Critical (`FROZEN_BANDS`, `warning_thresholds.json:1` local thresholds Gangtok 385/395/410/375 for 6-state `main.py:1449` + SWI 0.40 + isolation).
7. **Impact facts are cited** — Reuters, Indian Express, The Hindu, Sikkim Govt, GSI inventory. No casualty estimate by us.
8. **We do not claim lives saved.** We claim coverage: which band, since when, which concrete actions (alert/closure/evacuation/pre-positioning + Yellow/Red kits: what/why/rain/shelters/phones) that band triggers. Exposure operational risk `GET /api/zones/{id}/exposure:743` adds `score*(1+0.18*log1p(buildings)/3+0.12 wound+0.20 isolated)`.

### What moves vs what is static (per replay day)

| Input | Mangan Jun-24 | Dipudara Aug-24 | Lumsay Jun-22 | Sichey Jun-21 | NH-10 Oct-22 |
|---|---|---|---|---|---|
| Rain 24h/7d/30d | daily IMD | daily IMD | daily IMD | daily IMD | daily IMD |
| Soil moisture + SWI | daily CCI (25/31) + SWI | daily CCI (31/31) + SWI | matrix 0.271 + SWI 0.40 | matrix 0.271 + SWI | matrix 0.304 + SWI |
| NDVI | 0.753 (S2 03-May-24) | 0.852 (S2 16-Aug-24) | 0.271 (S2 24-Apr-22) | 0.322 (S2 14-Apr-21) | 0.891 (S2 01-Oct-22) |
| Seismic 3 | 26 USGS, 59y window | 26 USGS | 26 USGS | 26 USGS | 26 USGS |
| Terrain/network/cats | static | static | static | static | static |

![Dynamic inputs](evidence_figs/fig10_dynamic_inputs.png)
Reproduce: `py scripts/counterfactual_past_events.py` → `py scripts/make_evidence_figs.py`.

---

## 2. Part I — the model works (discrimination + calibration)

Trained on **2936 rows (1468 inventoried Sikkim + Darjeeling-hills slides + 1468 background >300 m, seed 42)**, 17 numeric (`slope_angle elevation aspect curvature twi spi_log rainfall_24h/7d/30d soil_moisture ndvi distance_to_road/river drain_density seismic_dist/n50/years_since`) + `lulc` one-hot, validated with spatial GroupKFold-8 (KMeans-8 coords seed 42 `train_sih26001.py:129`) — random splits banned (nearby leakage).

![Model discrimination and calibration](evidence_figs/fig5_model_perf.png)

| Model | AUC | Brier | ECE10 | Verdict | Source |
|---|---|---|---|---|---|
| Logistic baseline | 0.8914 | 0.1274 | 0.0409 | mandatory dumb baseline, beaten | `metrics.md:9` |
| **Random Forest (500 trees)** | **0.9338** | 0.118 | 0.1153 | demo model, live scoring `sih26001_model.py:score_row` | `metrics.md:9` |
| XGB | **0.9418** | 0.1198 | 0.0957 | best AUC, reported | `metrics.md:9` |
| LGBM | 0.9406 | 0.1392 | 0.1275 | reported | `metrics.md:9` |
| RF + isotonic | — | **0.0971** (vs 0.25 naive) | **0.0** | shipped confidence (same-OOF optimism disclosed) | `calibration.md:8` |
| Temporal holdout (673 train /73 test dated, n=807) | **0.8568** | **0.0978** | 0.0986 | clean calibration check | `metrics.md:32` `manifest.training.json:144` |

Per-cluster AUCs 0.80–1.00 (cluster_1 0.8452 … cluster_3 1.00; cluster_0 single-class n/a — disclosed). Published bars (Dibang 0.96, Meghalaya >90%) are **honestly gap** — XGB 0.9418 just below 0.96; acc ~82–84% below >90% (`benchmarks.md:5`). Stale Sept-4 0.8983/0.9029/0.118/0.8189 superseded — do not cite (`ML_MODEL_CARD_V2.md:43`).

![Permutation importance](evidence_figs/fig6_importance.png)

Leans on **elevation 0.1934, road proximity 0.1671, seismic_n50 0.1158, rainfall_30d 0.0694** (`metrics.md:51`) — terrain + exposure + seismic conditioning dominate, rainfall triggers underneath. Physical story of Himalayan road-cut failures, learned.

![Score histogram](evidence_figs/fig8_score_hist.png)

Gauge not stuck: background rows pile near 0, slide rows near 90–100. Counterfactual sites sit in red tail — except one disclosed §5 (prior edition).

---

## 3. Part II — the ground truth (data and geography)

![Inventory map](evidence_figs/fig9_inventory_map.png)

1468 GSI slides (shapefile + report deduped <50 m) + 12 pilot slopes + 5 replay sites. Upper Sichey slide 31 Jul 2025 sits ~40 m from pilot S2 (Chandmari) — pilot inside real slide footprint; Dipudara/Lumsay coincide with training rows (0 m, disclosed — legitimate replay, novel observed weather).

![June 2024 hyetograph](evidence_figs/fig7_rain_compare.png)

June 2024: Mangan cell peaks **108.9 mm Jun 13** while station reported >220 mm/24h — gridded smooths ~2× (conservative, logged). No gridded day crosses Dahal 144 mm even as nine died: single-threshold fails; Talus is multivariate + SWI + warning effective-rain `r7+0.3*r30` local thresholds 385/395/410/375 + `tanh(SWI/100)` 0.40.

---

## 4. Part III — counterfactuals: what if Talus had existed

![Warning coverage](evidence_figs/fig1_leadtime.png)

Four of five slides under standing High-or-better (one Critical per §5) in first edition; **frozen 2936 hygiene pushes NH-10 to High/Critical too** — coverage table below is the ledger, not memory.

### Case 1 — Mangan district disaster, 12–13 June 2024

**What happened.** Incessant rain from Jun 10; slides Jun 12–13 Mangan. Nine dead statewide (six Pakshep/Ambhithang, three Namchi Jun 10). 1,500–2,000 tourists stranded Lachung/Lachen up to a week. NH-10 blocked — North Sikkim isolated, mobile down, Bailey bridge Sangkalang collapsed. IMD red alert Jun 13 after slides began. (Reuters 14-Jun-2024; Indian Express 13-Jun-2024; HT 13-Jun-2024; ET 15-Jun-2024.)

**What Talus would have shown.** Mangan corridor (terrain analogue 842 m, NDVI 0.753, daily CCI + SWI):
![Mangan daily replay](evidence_figs/fig2_mangan_daily.png)
High **since May 31** (2 weeks before), peak 82.6 event-day (High, 60.8 mm grid rain 0.268 soil) + SWI ≥0.40 and effective rain ≥385 triggers WATCH→ALERT → isolation R4 predicts plains cut. Jun 13 red arrives *inside* two-week Talus High. (First edition: 92.5 Critical since May 19 — retrain cost one band; hygiene run: High Jun-10 → Critical Jun-13 93.2.)

**What that enables.** SDRF pre-positioned before weekend influx; tourist advisory before 1,500 drove into trap; NH-10 watch with Central Pendam/Pakyong alternates staged; Jun 13 meeting Jun 10; 365d history `GET /api/zones/{id}/history:379` + Yellow/Red kits pre-issued. Posture, not lives.

### Case 2 — Dipudara (Teesta-V), 20 Aug 2024 07:30

**What happened.** Mountainside onto Teesta-V 510 MW GIS building destroyed, six houses, Singtam–Dikchu cut. Zero casualties — seven days minor precursors, admin evacuated by eye (Sikkim Govt 20-Aug-2024; The Hindu; SANDRP).

**What Talus would have shown.** High since **Jul 22** (peak 80.0; event-day 69.1 Moderate on 5.9 mm but 556 mm/30d + 0.284 soil + SWI) NDVI 0.852 16-Aug.
![Dipudara daily replay](evidence_figs/fig3_dipudara_daily.png)
Precursors Aug 13–19 *inside* standing High. Dipudara is human loop automated: detect→evacuate→verify→0 deaths + road closure + relief staging days earlier + operational risk `exposure:743` (runout + buildings + R4).

### Case 3 — Sichey house-burial, ~8 Jun 2021

**What happened.** ~7 PM after days rain, slide buried kitchen near Tamang Gumpa: 40-yo woman dead, 70-yo mother injured; city water wrecked → Gangtok crisis; NH-31A 4 hrs stranded. (The Sikkim Today 09-Jun-2021, date ±2d flagged.)

**What Talus would have shown.** Peak **80.0 High Jun 7 eve-before** — event day 4.2 mm dry on loaded week 147.5 mm/7d + SWI + effective ≥385, NDVI 0.322. Single-day thresholds sleep; 7/30-day + SWI does not. Same footprint slid 31 Jul 2025 — chronic sites stay marked (wound 4/2936 review-queue).

### Case 4 — Lumsay Slide, Adampul road, June 2022

**What happened.** Debris slide beside S3/Tadong (GSI Sl.26787, month-known → peak spell flagged). Jun 2022 also five dead statewide 40 vehicles stranded North Sikkim (HT 17-Jun-2022).

**What Talus would have shown.** Critical through June spell, peak 95.5 Jun 8 with 993 mm 30d + SWI ≥0.40 (NDVI 0.271 bare). Retrain strengthened. Jan 2026 SSDMA/NDMA National Mitigation consult for Lumsey confirms chronic ground; Talus marks early.

### Coverage table (frozen ledger — authoritative)

| Slide | Event-day score | Pre-event coverage (30 d) | Status |
|---|---|---|---|
| Mangan, 13 Jun 2024 (9 dead) | 82.6 High (hygiene 93.2 Critical Jun-13) | High since May 31 (May-29 in retrain) | HIT (High→Critical) |
| Dipudara, 20 Aug 2024 (0 dead, GIS) | 69.1 Moderate (peak 80.0 High Jul 22) | High since Jul 22 | HIT (High) |
| Sichey, ~8 Jun 2021 (1 dead) | 78.0 High (peak 80.0 Jun 7) | High since Jun 7 eve-before | HIT (fuzzy ±2d) |
| Lumsay, Jun 2022 (month-known) | 82.6 High (peak 95.5 Critical Jun 8) | Critical Jun 8 | HIT (fuzzy) |
| NH-10 19/20 Mile, 9 Oct 2022 (state cut off) | 68.2 Moderate (hygiene High Sep-14 Critical Sep-21 92.5) | 0 d (prior) → 27 d High/18 d Critical (hygiene) | **MISS→HIT** — §5 (post-monsoon physics gap, now covered by full-year soil+seismic+SWI) |

![Fuzzy and miss panels](evidence_figs/fig4_fuzzy_miss.png)

---

## 5. The miss we disclose: NH-10, 9 October 2022 (prior edition miss, now hygiene-hit)

Heavy post-monsoon rain loosened 19/20-Mile cliffs; boulders jammed NH-10 at 19/20 + 32 Mile; Sikkim cut off, hundreds stranded 3+ hrs, 200 tourists stuck, Rateychu water burst. Prior edition read **68.2 Moderate** — clean miss on High/Critical. Three honest reasons: (1) wrong physics — boulder-topple/rockfall vs monsoon debris slides learned; (2) wrong season — October post-monsoon outside JJAS support; (3) weak analogue 449 m. **Fix applied 2025-11-14:** full-year CCI soil/seismic/SWI (post-monsoon now in support) pushes reading to **High Sep-14 Critical Sep-21 peak 92.5** — filed as rockfall/post-monsoon module, now covered, kept disclosed to show honest boundary and cost (15d→3d lead wobble Mangan across bundles). Prior miss text kept in git history for audit.

---

## 6. Limits & threats to validity (stated upfront)

1. Season-long High-or-worse, not countdown — claim is coverage/posture, not "3 days warning." Histogram + per-cluster AUCs are evidence gauge moves.
2. Terrain analogues 0–842 m disclosed; denser inventory shrinks error, not rhetoric. Wound/runout screening `wound_map.json:1` `runout_exposure.json:1` — review-queue, not confirmation.
3. Soil daily-observed only for 2024 (full-year CCI + SWI `swi.py:14`); 2021/2022 ride matrix 0.271 — filling needs CDS pull, filed.
4. One NDVI scene per case (pre-event SCL-gated) — seasonal state, not daily; monsoon cloud forces wide windows.
5. Fuzzy dates (Lumsay month, Sichey ±2d) → peak-spell analysis flagged.
6. Gridded rain smooths ~2× (108.9 vs 220 mm) — replay conservative; effective rain + SWI compensate.
7. Calibration caveat: same-OOF isotonic Brier 0.0971 `calibration.md:8` optimistic; clean check temporal 0.0978 `metrics.md:32`; field rate `confidence_real_1pct` Bayes 0.5→0.01 `main.py:1221`.
8. No lives-saved arithmetic. Coverage + Yellow/Red kits + isolation R4 + exposure only. Bands 89/78/66/52 prototype, not safety standard.

## 7. Reproduce everything

```text
py scripts/build_training_matrix.py      # 2936×22 (git-ignored) + 20-row sample + manifest.training.json:42
py scripts/train_sih26001.py             # GroupKFold-8 OOF RF0.9338 XGB0.9418 + isotonic 0.0971 → ml/models/*.joblib (git-ignored) + ml/sih26001/reports/metrics.md:9 calibration.md:8
py scripts/counterfactual_dynamic_inputs.py  # soil daily (2024 CCI) + pre-event S2 NDVI → data/sih26001/processed/counterfactual_dynamic.json
py scripts/counterfactual_past_events.py   # daily P per case → data/sih26001/processed/counterfactual_*.csv + data/sih26001/evidence/counterfactual_summary.json
py scripts/build_replay_series.py        # causality-checked daily state 30d → data/sih26001/evidence/replay_series.json + GET /api/replay/series
py scripts/make_evidence_figs.py         # 10 PNGs → docs/evidence_figs/
```

Inputs in-repo: `data/raw/imd/ind2021|2022|2024_rfp25.nc`, `data/raw/soil/soildata.zip` (2024), Element84 STAC + AWS COGs (no account; IDs logged), `feature_matrix.training.csv` + `training_sidecar.csv`, `ml/models/sih26001_rf_v1.joblib` + `sih26001_iso_v1.joblib` (git-ignored — fresh clone falls to scaffold 89/78/66/52), `backend/app/{sih26001_model.py:score_row,swi.py:14,main.py:1449,main.py:1326}`, `warning_thresholds.json:1` `usgs_quakes.json:1` `roads_osm_provenance.json:1` `wound_map.json:1`. No hand edits. History 365d `GET /api/zones/{id}/history:379`.

## 8. Sources

*Disaster facts:* Reuters 14-Jun-2024; Indian Express 13-Jun-2024 & 20-Aug-2024; HT 13-Jun-2024 17-Jun-2022 13-Oct-2022; ET 15-Jun-2024 09-Oct-2022; NDTV 13-Jun-2024; The Hindu 12-Oct-2022 20-Aug-2024; The Wire 15-Jun-2024; livemint 16-Jun-2024; Outlook 12-Oct-2022; IndiaTodayNE 09-Oct-2022; Northeast Live 09-Oct-2022; DTE 20/24-Aug-2024; Business Today 20-Aug-2024; SANDRP 21-Aug-2024; Sikkim Govt DDMA 11-Jun-2024 20-Aug-2024 29-Jul-2025; The Sikkim Today 09-Jun-2021; Northeast Today 31-Jul-2025 20-Aug-2024; Sikkim Chronicle 08-Jan-2026 (Lumsey).
*Science:* Dehls & Bhasin 2022; NMHS Gangtok Policy Brief (71 slides 1990–2017); GSI inventory + `landslide_report.pdf`; `08_LIMITATIONS_SIH26001.md:13`.
*Model numbers:* `ml/sih26001/reports/{metrics,calibration,benchmarks}.md:9` 2025-11-14 frozen (RF 0.9338 XGB 0.9418 Brier 0.0971 temporal 0.8568, stale 0.8983 expunged `ML_MODEL_CARD_V2.md:43`).