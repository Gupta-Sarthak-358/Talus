# TALUS — SIH26001 Finals Master Deck (Single Source)

> **Purpose:** Build the deck FROM this file. No other doc is authoritative.  
> **Status:** Deep-dive prototype truth — 2025-11-14 frozen + 2026-09-15 metrics, 12 demo slopes + 2936 training backing, honest gaps labeled.  
> **How to build slides:** Each `## Slide N:` below is one slide. **Title** is the slide header. **Bullets** are on-slide text (max 5). **Visual cue** is what the deck designer renders. **Speaker note** is the 60-90s verbal script (not on slide). **Evidence** is `file:line` you can open in front of judges.

**Deck meta:** 30 slides, ~18 min present + 5 min demo + 7 min Q&A. Ratio: ~6 data/AI slides, ~8 GIS/field/alerts/offline, ~4 demo/roadmap/impact. All numbers are frozen; do NOT invent new ones.

---

## Slide 1: Cover — SIH26001 · NER Hills · AI Landslide Early Warning for Connectivity

**Title:** TALUS — AI Landslide Early Warning for Connectivity | SIH26001

**Bullets:**
- **Tagline:** Don't just ask where the mountain may fail. Ask what changed, who is exposed, and what should happen next.
- **Organisation + PS:** SIH26001 — Smart Automation (SIH) — Team TALUS · NER hill states: Sikkim · Darjeeling hills (WB) · Arunachal · Meghalaya · Nagaland · Manipur · Mizoram · Tripura
- **Demo anchor:** 3 corridors live — **Gangtok S1–S4** (27.3389, 88.6065) · **Lachung N1–N4** (27.69, 88.74) · **Darjeeling D1–D4** (27.041, 88.263) — 12 demo slopes + 2936-row training spine
- **Footer:** Live RF (500) + XGB (400) → score 0–100 + calibrated confidence + 6-state warning + R4 isolation — offline-first PWA

**Visual cue:** Full-bleed NER hill-states choropleth (EPSG:4326) with 3 corridor pins + NH-10 spine highlighted red. Left: large TALUS wordmark + SIH26001 badge. Bottom bar: `docs/sih26001/ML_MODEL_CARD_V2.md` + `data/sih26001/fixtures/slopes.json` provenance strip. Dark theme `#0b1220`.

**Speaker note (45s):** “We are TALUS, SIH26001. NER loses connectivity first — a single slide on NH-10 isolates North Sikkim for days. TALUS is not a landslide detector. It is a connectivity-intelligence system: ingest 17 features → AI susceptibility 0–100 → GIS 5-band + isolation + exposure → field-verified alerts in 5 languages, offline-first. Everything you will see runs locally — no hidden API — and every gap is labeled. Slides 2–5 are the problem and the 4-pillar answer; the rest is proof.”

**Evidence:** `docs/sih26001/00_PROJECT_BRIEF_SIH26001.md:1` · `data/sih26001/fixtures/locations.json:1` · `docs/CURRENT_SYSTEM.md:7` · `frontend/public/manifest.webmanifest:1`

---

## Slide 2: Problem — Why NER. Why Connectivity First.

**Title:** NER Hill States Lose Roads Before They Lose Slopes

**Bullets:**
- **Terrain + climate trap:** 70%+ NER is hills; 1500–3000 mm monsoon in 90 days; slopes already conditioned by tectonics + road cuts — hill cutting is a time-varying disturbance, not static `distance_to_road`
- **Failure chain:** Hill cut / toe erosion → saturated soil (SWI) → slide → **R1 blocked / R2 at-risk** → valley egress (R4 bottleneck) severs → village **ISOLATED** even if its own spur is open — response delayed by hours
- **System gap (PS synthesis §2.2):** IMD 0.25° truth exists but no per-zone live blend; CCI soil is satellite not field; GSI inventories are incomplete & season-window; no road-graph isolation; no 5-band GIS with wound + runout; no offline multilingual field loop
- **What connectivity means:** Not “landslide yes/no” — **which road, which village, which hour, which action** (evacuate / restrict / hold team / stage at Ranipool)

**Visual cue:** Left: 3 photos (hill cut + saturated debris + blocked NH-310A). Right: chain diagram `Cut → Saturation (SWI) → Slide → R2 at-risk → R4 blocked → S1/S2/S3 ISOLATED`. Bottom: PS trace `R1-R13 → FR-01…FR-13`.

**Speaker note (60s):** “Judges see landslide decks that end at a heatmap. Our interview with GSI showed the real loss is connectivity — one ridge road (R2) at-risk means S1 cannot reach the valley even if S1 itself is High, not Critical. Taiwan and Japan learned this: they publish pre-emptive restriction sections before a slide, because a road condition is the evacuation condition. The PS asks for multi-source, AI, GIS, roads, weather, emergency priority, field, alerts, multilingual, offline — none of that is a heatmap alone. TALUS binds them.” Frame as conditioning + exposure, not fear.

**Evidence:** `docs/sih26001/01_REQUIREMENTS_SIH26001.md:26` (FR-01…FR-13 map) · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:58` (pre-emptive restriction) · `docs/sih26001/08_LIMITATIONS_SIH26001.md:4` (demo topology honesty) · `backend/app/main.py:1326` (`_isolation_for_location` R4 bottleneck)

---

## Slide 3: Problem — 2024 Receipts + What PS Asked For (a–f)

**Title:** 2024 Was the Receipt: Gangtok · Darjeeling Hills — and What the PS Demands

**Bullets:**
- **2024 Gangtok + Darjeeling hits:** Mangan Jun 12–13 2024 — 9 dead (6 Mangan + 3 Namchi), ~9.4 km blocked NH-10, ~1,500 tourists stranded, red alert only Jun 13 (late). Dipudara Aug 20 2024 — Teesta-V power building destroyed, Singtam-Dikchu cut, **zero casualties ONLY because precursor slides 7 days earlier forced manual evacuation** — proof early episode matters
- **PS (a) Data:** multi-source (rainfall + soil + terrain + satellite + history + roads) with provenance — not one CSV
- **PS (b) AI:** high-risk prediction with calibrated confidence + explainability, not raw score — `Brier 0.0971`, `Bayes 0.5→0.01`
- **PS (c–d) GIS + Severity:** 5-band map + roads/villages/infra + 6-state warning (NORMAL→EVACUATE) — not 3 bands
- **PS (e) Roads & (f) Field/Alerts:** risk-aware routing (avoid R2), isolation (R4 bottleneck), geo-tagged reports with EXIF+SHA256, multilingual SMS/app alerts, offline-first PWA — the last-mile loop

**Visual cue:** Timeline 2024 (Jun 12–13 Mangan, Aug 20 Dipudara, Oct 9 NH-10 19/20 Mile) with newspaper crops. Right: 6 PS cards a–f mapped to FR-01…FR-13 + TALUS module that satisfies each (check marks). Footnote: “Susceptibility ≠ probability of a specific slide tomorrow.”

**Speaker note (75s):** “We built the replay bundle to prove causality — the model saw Dipudara High for 7 days before Aug 20; officials evacuated on the 13th, saving lives. The PS is 13 asks in one sentence. We traced each to a requirement FR-01…FR-13 and to a live endpoint you can hit now — `GET /api/replay/series` for Dipudara, `GET /api/warning/state` for 6 states, `GET /api/isolation` for R4. If a judge asks ‘where is PS (e)?’ answer with roads+isolation+routing, not ‘we do roads differently’ — Japan/Taiwan already do roads, we add the wound + isolation layer.” Never say “nobody models roads”.

**Evidence:** `data/sih26001/evidence/replay_series.json:6` (Mangan + Dipudara cases, 31d series, causality note) · `docs/EVIDENCE_TALUS_COUNTERFACTUALS.md:1` · `docs/sih26001/01_REQUIREMENTS_SIH26001.md:7` (PS→FR map) · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:94` (never claim phrasing)

---

## Slide 4: Solution Overview — 4 Pillars (What We Actually Shipped)

**Title:** TALUS in One Slide — 4 Pillars, Frozen & Live

**Bullets:**
- **P1 — Ingest (17 feats):** `NGEN 22 cols` (17 numeric + lulc + 4 keys) per `zone_id + time_window` — rainfall 24h/7d/30d + soil + NDVI + distance_to_road/river + TWI/SPI + seismic ×3 + wound 0/1; every value carries provenance (`gap` → `missing_evidence`)
- **P2 — AI (RF 500 / XGB 400 / LGBM 400):** `2936 rows 1468+1468` · `GroupKFold(8)` KMeans-8 spatial OOF **RF 0.9338 / XGB 0.9418** · isotonic **Brier 0.0971** + **Bayes prevalence `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)`** → `confidence_real_1pct`; TreeSHAP top-4 per zone
- **P3 — GIS (5-band + isolation + exposure):** 5 bands Very Low<21<Low<41<Moderate<66<High<85<Critical; **RiskMap 5-band polygons** + **RoadStatusCard R1 blocked / R2 at-risk / R3,R4 open** (RISK_WEIGHT 3.0, alpha 0.2, hazard graph drops R2) + **runout** 85 buildings downstream (S2) + **wound** amber pins; **Operational risk** `hazard*(1+0.18*log1p(b)/3+0.12*wound+0.20*isolated)`
- **P4 — Field + Alerts, Offline-First:** `ReportModal` EXIF 12m·SHA256·320px thumb metadata-only → `talus_report_outbox` → 15 field tests; `AlertPanel` en/hi/ne/as/bn + app|sms (msg91/fast2sms/twilio/textbelt) + auto watcher **60s interval / 3600s cooldown**; PWA `talus-shell-v1` cache-first + icons 192/512 + `QuickStatsBar LIVE` forecast badge + Sync badge

**Visual cue:** 4-column pillar diagram, each pillar with icon + live endpoint pill (`/api/zones`, `/api/zones/{id}/explanation`, `/api/roads/status`, `/api/reports`, `/api/alerts/dispatch`). Bottom: scoring bar `89/78/66/52` over 5-band colors + `live_scores` boolean.

**Speaker note (80s):** “Pillar 1 is honesty: if lithology is uniform because Bhukosh timed out, we tag it and omit it from X — we don’t fake it. Pillar 2 is the only honest validation at this scale: GroupKFold(8) on coordinates + a 673/73 temporal holdout (n=807) with AUC 0.8568 — random splits lie when slopes are autocorrelated. Pillar 3 is the demo — deterministic R2 avoidance via hazard graph, not ‘the AI learned to avoid it’. Pillar 4 is the last mile — offline outbox with sync, not ‘store locally maybe’. All four run fully offline; live forecast is best-effort blend, never required.”

**Evidence:** `docs/CURRENT_SYSTEM.md:7` (prediction + GIS+warning overlay) · `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md:13` (17+1) · `ml/sih26001/reports/metrics.md:9` (0.9338/0.9418) · `ml/sih26001/reports/calibration.md:8` (Brier 0.0971) · `backend/app/main.py:49` (RISK_WEIGHT 3.0, alpha 0.2) · `backend/app/swi.py:14` (SWI L1=15) · `frontend/src/services/reports.js:1` (outbox) · `frontend/public/sw.js:1`

---

## Slide 5: Solution — User Outcomes (What Changes for Each Role)

**Title:** From Susceptibility to Action — Role-Specific Decisions, Not One Number

**Bullets:**
- **Villager (Yellow/Red kit):** “What” (state·band) → “Why” (top 3 reasons) → “Rainfall/effective” → 2 shelters + phone → **villager_explain in plain language** — never SHAP, never 0–100 alone
- **District officer:** closure + evacuation coordination, inspection schedule, night-movement restriction — multilingual en/hi/ne/as/bn from `DECISIONS_TRANSLATIONS`
- **State manager:** prioritise S1 over S2–S4, stage machines at Ranipool, hold one team for S2 — resource view
- **Rescue team:** risk-aware approach “from south, not ridge road” — routing avoids R2 via R3/R4; **Admin `/admin` PINs 9999/1111/2222/3333 observe health/isolation/log/provenance — hidden from villagers**

**Visual cue:** 4 role cards side-by-side, same S1 example: Villager “Avoid S1 hillside road 2 days, use valley route.” Officer “Close S1 stretch, evacuate Tathangchen upper first.” Both with Yellow/Red kit (shelters Tathangchen Hall / Ranipool School, phone 03592-221011). Bottom: “Villagers see danger/safe + map; officers see provenance + Brier.”

**Speaker note (55s):** “One score, four meanings. That is the design. If we show a villager a SHAP bar, we failed. The kit renders from `GET /api/warning/state` → `kit:{what,why,rainfall,shelters,phones,villager_explain}`. Demo line: tap S1 → ZoneIntelligencePanel → ‘Villager’ toggle → Yellow kit appears. Admin panel is PIN-gated — villagers never see it, judges do. This is Nepal’s lesson: build for officers, not scientists.”

**Evidence:** `backend/app/main.py:55` (DECISIONS_BY_BAND) · `backend/app/main.py:86` (DECISIONS_TRANSLATIONS en/hi/ne/as/bn) · `backend/app/main.py:1575` (SHELTERS + PHONES) · `frontend/src/context/TalusContext.jsx:1` (role) · `docs/sih26001/06_DEMO_SCENARIO_SIH26001.md:48` (Admin)

---

## Slide 6: Architecture — End-to-End Diagram (Talking to the Diagram)

**Title:** Architecture — From Pixels to Panic (and Back via Field Reports)

**Bullets:**
- **Sources → NGEN:** `IMD 0.25deg 1901–2024 ind2024_rfp25.nc` + `Open-Meteo 7-day live` (+ `IMD_API_KEY` district gated) + `CCI C3S v09.2 7.5 GB 1978–2024` + `SRTM n27_e088 1arc 3601×3601` + `Sentinel-2 S2B_45RXL` + `WorldCover N27E087` + `GSI 30k + report 904pp 659–676` + `USGS 26 M5+` + `OSM 1014/226/504` → **NGEN fetch→reproject→terrain→join→label→version → `feature_matrix.sample.csv 12×22` (committed) + `feature_matrix.training.csv 2936×22` (git-ignored, 20-row sample committed)**
- **Train → Serve:** `2936 rows` → `GroupKFold(8)` KMeans-8 + temporal `673/73` → `RF 500 / XGB 400 / LGBM 400` + isotonic → `ml/models/sih26001_{rf,iso}_v1.joblib` + `backend/app/sih26001_model.py:get_live():score_row()` → `live_scores` **or honest fixture `89/78/66/52` when weights absent** (fresh clone behavior)
- **Operational overlays (scoring frozen):** `swi.py L1=15 L2=60 L3=60 a1=0.10 b1=0.12 a2=0.05 b2=0.05 a3=0.01 → tanh(SWI/100)` + **warning 6-state** per-zone thresholds `warning_thresholds.json S1 385 / S2 395 / S3 410 / S4 375` (+ quake 25% drop, forecast exceedance, wound, SWI≥0.40, effective `r7+0.3*r30`) + **isolation R4 bottleneck** `adj_map S1:[R1,R2,R3]` + **road catalogue** + **operational exposure risk**
- **Edges → Alerts + Offline:** `POST /api/reports` → `talus_report_outbox` → `sw.js talus-shell-v1` cache-first, `/api` network-only → `AlertPanel` app|sms (msg91/fast2sms/twilio/textbelt) + auto-watcher `60s/3600s` → PWA `manifest 192/512`, `QuickStatsBar LIVE` badge, Sync badge, `talus_report_photos` thumbnails

**Visual cue:** Full architecture diagram (sources top, NGEN belt, train→serve center, overlays middle, GIS left, field+alerts right, PWA shell bottom). Each box labeled with evidence pill + endpoint. Bottom strip: `docker-compose.prod.yml (postgis:16-3.4, https://talus-sih26001.onrender.com/health via docs/LIVE_HOST_EVIDENCE.md) PostGIS 16-3.4` path + `runs:/app/runs`.

**Speaker note (85s):** “Point to the diagram left to right. Emphasize the honest fallback: if someone clones the repo with no weights, the API says `scoring: fixture` and the scaffold 89/78/66/52 drives the demo — it never fabricates a live score. SWI, warning, isolation never touch the 0–100 — they overlay. The auto-watcher thread polls `GET /api/isolation` every 60 s and dispatches on ISOLATED/MAY_ISOLATE with a 3600 s cooldown. Offline is not a slide — it’s a service worker you can see in DevTools Application tab.”

**Evidence:** `docs/sih26001/02_ARCHITECTURE_SIH26001.md:9` (v2 data flow) · `docs/CURRENT_SYSTEM.md:40` (API list) · `backend/app/swi.py:14` (JMA) · `backend/app/main.py:1326` (isolation) · `backend/app/main.py:1449` (warning) · `data/sih26001/evidence/warning_thresholds.json:1` · `frontend/public/sw.js:1` · `backend/app/sih26001_model.py:1`

---

## Slide 7: Architecture — Why Frozen Scoring Is a Feature

**Title:** Why the 0–100 Never Moves When SWI/Isolation Fires

**Bullets:**
- **Scoring frozen:** `score = round(raw_proba*100)` (raw RF) drives bands 89/78/66/52; `confidence = isotonic P` · `confidence_real_1pct = Bayes(pi_train 0.5→pi_real 0.01)` — **bands, routing, warning state do NOT retrain on SWI**
- **Overlay principle:** `effective_rain = r7+0.3*r30` (Monga 390 separator) + `SWI tanh(SWI/100)` + `wound` + `forecast` + `quake 0.75×threshold` bump warning by **at most +1 level** (single bump) — then isolation overrides to RESTRICT/EVACUATE when `corridor_isolated` / `may_isolate`
- **Determinism:** `_road_graphs_for:496` builds **(full_graph + R2 shortcut, hazard_graph without R2)** — risk-aware routing **always** avoids R2 when status `at-risk`; `RISK_WEIGHT 3.0` with `alpha 0.2` guarantees it even if length diff is 0.6%
- **Fresh-clone contract:** `ZoneStore:live_scores` false → UI shows `scoring: fixture` · `store live_scores` checked at `/health`; no silent synthetic score

**Visual cue:** Split animation: left “0–100 scale” locked; right “warning 6-state + isolation” sliding on top. Small formula box `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` + `swi.py tanh`. Toggle `full vs hazard graph` with R2 edge disappearing.

**Speaker note (55s):** “If SWI changed the 0–100, we’d be threshold-hacking. The honest split is: the model says how susceptible the hill is; the warning says whether rain + saturation + wound + forecast + quake + isolation make today an action day. That is Taiwan’s static+trigger split, implemented as code. Judges: open `backend/app/main.py:1449` — you will see `level = min(level+1,3)` with a comment ‘single bump max +1’, then isolation override below it. No stacking to +2, no hidden ensemble.”

**Evidence:** `docs/RECALIBRATION_NOTE.md:1` (Bayes) · `backend/app/main.py:49` (RISK_WEIGHT) · `backend/app/main.py:496` (`_road_graphs_for`) · `docs/sih26001/02_ARCHITECTURE_SIH26001.md:24` (RF OOF) · `docs/CURRENT_SYSTEM.md:15` (GIS+warning overlay)

---

## Slide 8: Data Deep Dive (1/3) — Rainfall: Truth vs Live vs Fixture

**Title:** Rainfall — IMD Truth, Open-Meteo Live, IMD_API_KEY Gated Blend

**Bullets:**
- **Historical truth (observed):** `IMD 0.25° gridded 1901–2024` — `data/raw/imd/ind2024_rfp25.nc` via `imdpune.gov.in/cmpg/Griddata` (no account), 135×129 grid 66.5–100°E × 6.5–38.5°N; wettest Gangtok 7-day 2024: `2024-06-16 14.0/327.3/712.2` (24h/7d/30d) + 30-yr climatology `manifest.training.json:30` — **never mixed with forecast in UI**
- **Live blend (forecast):** `GET /api/forecast/live:1154` → Open-Meteo `api.open-meteo.com/v1/forecast?daily=precipitation_sum,prob_max&forecast_days=7&timezone=Asia/Kolkata` (ECMWF/GFS, 1 h cache `_LIVE_CACHE 3600s @ main.py:1103`), `coords gangtok 27.3389,88.6065` etc per `main.py:1104`
- **Gated IMD live:** `GET /api/forecast/imd-live:1124` tries `api.data.gov.in/resource/rainfall-district?api-key=IMD_API_KEY&filters[district]=East Sikkim|North Sikkim|Darjeeling` when env set; **else falls back to Open-Meteo blend with provenance label** — fixture `GET /api/forecast/rainfall` (`forecast.json` monga-mdl + dahal-144) always available
- **Causality rule:** `replay_series` asserts `series ≤ event_date` — inputs available ON each date only (IMD trailing sums + CCI/CCI fallback + one pre-event S2 scene, static terrain) — no future leak; exposed as `◀ OBSERVED | NOW | FORECAST ▶` in `RiskTrendChart`

**Visual cue:** 3-lane rainfall provenance strip: IMD 0.25° (truth) | Open-Meteo live (forecast) | IMD_API_KEY (district live) with cache badge `1h`. Small table showing 2024-06-16 24h/7d/30d + `forecast/live` response tile. Bottom: “Observed vs forecast explicitly separated” per `RESEARCH:55`.

**Speaker note (70s):** “We did not hide the coarse grid — 0.25° is ~27 km, hyperlocal cloudbursts are missed at trigger resolution. Historical truth stays in the `ind*_rfp25.nc` and the fixture. Live is Open-Meteo with a 1-hour cache; if you set `IMD_API_KEY` we hit data.gov.in district rainfall and blend it, else we fall back and label it. The replay vouches for causality — every daily row uses only trailing IMD sums — so when the slide says TALUS was High 3 days before Mangan Jun 13, it really was High on data available that morning.”

**Evidence:** `docs/sih26001/03_DATA_PLAN_SIH26001.md:13` (IMD rows) · `backend/app/main.py:1103` (`_LIVE_TTL_S 3600`) · `backend/app/main.py:1124` (`forecast_imd_live`) · `backend/app/main.py:1154` (`forecast_live`) · `data/sih26001/evidence/replay_series.json:1` (causality) · `frontend/src/components/ZoneDetails/RiskTrendChart.jsx:108` (OBSERVED/NOW/FORECAST)

---

## Slide 9: Data Deep Dive (2/3) — Terrain, Soil, Satellite

**Title:** Terrain · Soil · Satellite — What the Hill Remembers

**Bullets:**
- **SRTM n27_e088 1arc v3.tif** 3601×3601 int16 EPSG:4326 (88–89E / 27–28N) → `usgs_s234.json:1` derivatives: **slope/aspect (Horn-1981), curvature, TWI D8 priority-flood `ln(a/tanB)`, SPI `a*tanB`, drain density** on 7.7×5.9 km crop; 90 voids 0.17% neighbour-mean filled, neighbourhoods void-free
- **ESA CCI COMBINED TCDR v09.2 (DOI 10.24381/cds.d7782f18) 1978–2024, 7.5 GB** via CDS (free account, `system py311 xarray`); `data/raw/soil/v09.2/ESACCI-SOILMOISTURE-*.nc` daily; strongest pedigree vs ERA5 reanalysis (ERA5 path documented but unused `manifest.sample.json:22`); 7/7 valid `flags=[0]`, same-cell 27.375,88.625 → window-mean **0.271** all slopes (same-cell consequence stated)
- **Sentinel-2 L2A S2B_45RXL** (STAC earth-search AWS, no account): **2023-11-15 (cloud 0.02) vs 2024-11-29** → `s234_ndvi.json:1` NDVI B04/B08+SCL: **S1 0.718 veg / S2 0.139 bare road-cut / S3 0.817 veg / S4 0.468**; **ESA WorldCover 2021 v200 10m N27E087** (AWS Open Data) → `s234_lulc.json:1` 3×3 mode 9/9: **10→FOREST / 50→BUILT** (S1 FOREST, S2 BUILT, S3 FOREST, S4 BUILT) 76.7% accuracy
- **JMA 3-tank SWI** replaces single soil 0.271 for warning only: `GET /api/soil/swi` per zone `swi_for_zone(r7,r30,forecast3)` → `tanh(SWI/100)`, threshold **0.40**

**Visual cue:** 4 thumbnails: SRTM DEM hillshade with TWI overlay; CCI daily NC slice; Sentinel pair side-by-side with NDVI loss red squares (≤150 m road); WorldCover LULC tiles. Below: `manifest.sample.json:22` tag `CCI quasi-static proxy, warning upgraded via SWI`.

**Speaker note (65s):** “CCI at 0.25° is too coarse at slope scale — we say so, and we show the same 0.271 for all slopes as the honesty marker. The fix is not a higher-resolution reanalysis — it’s a physics tank model that remembers yesterday’s rain. The satellite pair is 2023-11-15 vs 2024-11-29 — one year, post-monsoon to post-monsoon — so seasonal green is controlled, road-cut loss is not. All of this is versioned in `manifest.sample.json`, not in a PDF.”

**Evidence:** `docs/sih26001/03_DATA_PLAN_SIH26001.md:31` (SRTM + derived) · `docs/sih26001/03_DATA_PLAN_SIH26001.md:24` (CCI v09.2) · `data/sih26001/processed/cache_dem_grid.npz` · `backend/app/swi.py:14` (L1=15 L2=60 L3=60) · `docs/sih26001/ML_MODEL_CARD_V2.md:17` (sources freeze)

---

## Slide 10: Data Deep Dive (3/3) — Inventories, Quakes, OSM, Bhukosh Honesty

**Title:** Inventories + Quakes + Roads — Provenanced, Not Traced

**Bullets:**
- **GSI Bhusanket 30,842 all-India** `GSI_Landslide_Inventory.shp.zip` + **report PDF 904 pp (p659–676) 764 deduped Sikkim `manifest.training.json:42`** + `evidence/sikkim_join.json:6` 693 haversine join (S2 hit 286.7 m SK/ESK/78A11/2019/02) + **Monga & Ganguli 2026 (490 NEH 2006–2019), Mihu 2026 (537), ILSM 154,329 (Zenodo), NASA COOLR** → dedup <50 m, `evidence_quality` per row, undated season-window JJAS tagged `approximate`
- **USGS FDSN 26 M5+ 1965–2024 (26.5–28.5N / 87.5–89.5E)** `usgs_quakes.json:1` → per-zone `seismic_dist_km / n50_rate / years_since` via `sih26001_model.py:_seismic_lookup` 59-y window (2024-1965); warning-conditioned `*0.75` if `seismic_years_since ≤180/365 && n50>0` (`main.py:1525`)
- **OSM 1014 Gangtok / 226 Lachung / 504 Darjeeling** `roads_osm_provenance.json:1` (Overpass `way["highway"](bbox)`, example way **47416074 NH310A trunk**) — **geometry is centroid-aligned deterministic R1–R4 (not OSM trace)** for pedagogical R2-avoidance + R4 bottleneck (`data.py:118` `GRAPH`, `main.py:496` hazard graph); counts are the **honesty proof**, full OSM traces available on demand; `osm-qa-unverified` kept
- **GSI Bhukosh WFS/WMS timeout 15 s both 2025-11-14** `bhukosh_vector_attempt.json:1` → **PROXY-published-map uniform `lingtse_granite_gneiss`** + lineament **0.8 km/km²**, uniform → **omitted from X** (not hidden, `manifest.training.json:263`); re-run `extract_lithology.py --wfs` when vector reachable; **wound 4/2936** `wound_as_feature.json:1` rare feature kept

**Visual cue:** Inventory map Sikkim 764 deduped points + quake stars (26) + OSM road density heatmap with “Demo topology” badge. Center: timeout screenshot + lithology uniform chip `lingtse_granite_gneiss`. Bottom: `evidence/provenance` pills.

**Speaker note (70s):** “Every other deck shows OSM as perfect geometry. We fetched 1014/226/504 and show the count — but we tell you the R1–R4 you see routing on is a fixture, not the OSM trace. That is why the avoidance is deterministic and reproducible, and why the judge can re-run it. Bhukosh vector timed out on both WFS and WMS on 2025-11-14 — we logged the JSON and run uniform; when the vector comes back we swap it, no schema change. Inventory dated-negatives are `673/73` temporal split; undated majority stays approximate.”

**Evidence:** `docs/sih26001/03_DATA_PLAN_SIH26001.md:54` (inventories) · `data/sih26001/evidence/usgs_quakes.json:1` · `data/sih26001/evidence/roads_osm_provenance.json:1` · `data/sih26001/evidence/bhukosh_vector_attempt.json:1` · `data/sih26001/evidence/wound_as_feature.json:1` · `backend/app/sih26001_model.py:1` (`_seismic_lookup`)

---

## Slide 11: Feature Schema — 22 Cols, NUMERIC 17, What Crosses the ML Boundary

**Title:** Feature Schema — 22 Cols = 17 Numeric + lulc + 4 Keys

**Bullets:**
- **Keys (not in X):** `zone_id` (S1–S4/N1–N4/D1–D4) · `time_window` (date or JJAS season-window) · `event` (0/1) · `evidence_quality` (`approximate`/clean) — flows to `missing_evidence`
- **NUMERIC 17 (in X):** `slope_angle / elevation / aspect / curvature / twi / spi→spi_log (log1p) / rainfall_24h/7d/30d / soil_moisture / ndvi / distance_to_road / distance_to_river / drain_density / seismic_dist_km / seismic_n50_rate / seismic_years_since / wound`; categorical `lulc` (FOREST/BUILT/BARREN/WATER/WETLAND, WorldCover codebook 10→FOREST) one-hot `drop_first`
- **Omitted by design (NOT in X):** `lithology` uniform PROXY-published-map · `lineament_density 0.8` uniform · `previous_landslide` leakage (`positives ARE inventory slides`); `swi / effective_rain / isolation / warning_state` are **operational overlays**, scoring stays frozen
- **Contract:** `feature_matrix.sample.csv:1` 12 rows ×22 cols committed · `feature_matrix.training.sample.csv` 20 rows · `feature_matrix.training.csv` 2936×22 git-ignored (Drive/LFS) · `Encoder ColumnTransformer (scaler + one-hot) → RF 500 max_depth 12 min_samples_leaf 2`

**Visual cue:** Feature provenance table (sample) with Source + In X? ✓/✗ pills + per-zone evidence chips (`usgs_s234.json`, `ind2024_rfp25.nc 14.0/327.3/712.2`, `roads_osm_provenance.json`). Top: `NUMERIC 17` badge + `spi → spi_log` arrow + `lulc one-hot` chip. Bottom: “Missingness contract: nulls reported, never silently imputed.”

**Speaker note (60s):** “The schema is the contract. NGEN may hold richer internals; only these 22 cross into training/inference, and any new field needs an ADR. If a row arrives with lithology uniform, we don’t learn lithology — we surface ‘bhukosh-PROXY-published-map-uniform’ in missing_evidence and lower no hidden confidence. SPI is log1p because raw SPI is heavy-tailed and would dominate splits. Ask to see `05_FEATURE_SCHEMA_SIH26001.md` — every feature has a source row.”

**Evidence:** `docs/sih26001/05_FEATURE_SCHEMA_SIH26001.md:13` (22 cols, 17+1) · `data/sih26001/fixtures/feature_matrix.sample.csv:1` · `docs/CURRENT_SYSTEM.md:71` (22 cols) · `data/sih26001/processed/feature_matrix.training.csv:1`

---

## Slide 12: AI / ML — Validation Is the Product

**Title:** Spatial GroupKFold(8) + Temporal Holdout — Do Not Cite 0.8983

**Bullets:**
- **Why GroupKFold:** slopes within a cluster are autocorrelated — random split AUC 0.99 lies; we do **KMeans-8 on coords (seed 42) → GroupKFold(8)** `train_sih26001.py:129` — per-cluster LOOCV shape logged (`cluster_0 single-class n/a` is expected, not a bug)
- **OOF (current, 2025-11-14, supersedes 2026-09-04 stale 0.8983):** **LR 0.8914 | RF 0.9338 Brier 0.118 | XGB 0.9418 Brier 0.1198 | LGBM 0.9406** — best single XGB 0.9418 shipped, no ensemble (honest gap to Dibang 0.96, stated); LR baseline beaten by +0.042
- **Temporal clean check (≥30 dated/side `train_sih26001.py:54`):** `673 train /73 test dated pos` (`manifest.training.json:144`, test n 807) → **RF AUC 0.8568 · Brier 0.0978 · ECE10 0.0986** — the only number without same-OOF optimism
- **Other screens:** permutation importance top `elevation 0.1934 / distance_to_road 0.1671 / seismic_n50 0.1158`; threshold screen `frac pos ≥144mm (Dahal) 0.1907` (climatology, not intensity validation, stated in `metrics.md:43`); `Brier vs naive 0.25` shows signal

**Visual cue:** Left: GroupKFold fissure map (8 colors). Center: metrics table + per-cluster LOOCV heatmap (cluster_0 gray). Right: temporal split arrow `≤2018 (673) → ≥2019 (73)`. Big cross-out “0.8983” → “0.9338/0.9418 (2025-11-15)”. Bottom: “Say before judges find it: stale numbers are expunged.”

**Speaker note (75s):** “We keep the old 0.8983 crossed out on purpose — one team member will be tempted to quote it, it is stale. The per-cluster `n/a` is not a failure — KMeans put a single-class cluster alone; that tells you leakage would have been hidden by random split. Temporal is the judge-proof number: 73 dated slides after 2019 held out, AUC 0.8568. Confusion matrix, reliability diagram, learning curve, transfer curve in `docs/assets/evidence/` are all from this OOF. Never present training accuracy — present OOF + temporal Brier.”

**Evidence:** `ml/sih26001/reports/metrics.md:9` (GroupKFold) · `ml/sih26001/reports/metrics.md:32` (temporal 673/73) · `ml/sih26001/reports/metrics.md:51` (importance) · `docs/sih26001/ML_MODEL_CARD_V2.md:26` (table) · `docs/sih26001/08_LIMITATIONS_SIH26001.md:13` (stale numbers) · `scripts/train_sih26001.py:129` · `scripts/train_sih26001.py:54`

---

## Slide 13: AI / ML — Calibration, Bayes, Explainability (No Black Box)

**Title:** Calibrated Confidence, Real-World Base Rate, Real TreeSHAP

**Bullets:**
- **Isotonic calibration:** RF OOF → isotonic `Brier 0.0971 ECE 0.0` vs raw 0.118 vs naive 0.25 `calibration.md:8` — **same-OOF optimism disclosed**, clean check temporal **Brier 0.0978**; confidence = `P(elevated susceptibility)` under season-window target, **never** “probability a slide will occur here tomorrow”
- **Bayes prevalence correction (RECALIBRATION_NOTE):** Training is balanced `pi_train 0.5` but field prevalence `pi_real≈0.01` → `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` → exposed as **`confidence_real_1pct`** (shim) via `GET /api/model/calib?pi_real=0.01` + `sih26001_model.py:score_row`; **score 0–100 stays frozen from raw proba** (bands unchanged)
- **TreeSHAP top-4 (live):** `sih26001_model.py:explain_row` via `shap.TreeExplainer` per zone (optional dep, fixture fallback when absent) → `base_value + contributions`, e.g. **S1 distance_to_road 12.5 / rainfall_7d 9.0 / slope 7.5 / soil 5.0** `slopes.json:1` + 5-pt sample `manifest.training.json:shap_sample`; exposed at `GET /api/zones/{id}/explanation:334` → `ShapChart` + `missing_evidence`
- **Off-manifold caveat:** single-feature overrides that break correlations are flagged, not silently numbered (`WhatIfDrawer` badge) — ML what-if `S3 66→74 Δ8` `forecast.json:1` is labeled counterfactual; causal claims via `POST /causal-what-if:629`

**Visual cue:** Reliability diagram (calibration.md) left, formula `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` center, TreeSHAP waterfall S1 right. Below: `confidence 0.82 → confidence_real_1pct 2.1% / hillslope-day @1% base`.

**Speaker note (70s):** “Calibration is what makes a probability honest. We show both views — prototype 50% (the lab) and 1% (the field) — and we never move the band when we rescale. If `shap` isn’t installed where the server runs, the API returns the fixture SHAP — still a watermark that we thought about explainability, not that we hid failure. Say: ‘confidence is P(elevated susceptibility) under season-window, field view is Bayes 1%’ — villager kit translates that to ‘Evacuate now via valley route’.”

**Evidence:** `ml/sih26001/reports/calibration.md:8` · `docs/RECALIBRATION_NOTE.md:1` · `backend/app/main.py:1221` (`/api/model/calib`) · `backend/app/sih26001_model.py:1` (`score_row` + `explain_row` + `shap.TreeExplainer`) · `data/sih26001/fixtures/slopes.json:16` (S1 SHAP) · `frontend/src/components/ZoneDetails/ShapChart.jsx:1`

---

## Slide 14: GIS / Routing — 5-Band Map + Roads + Runout + Wound

**Title:** RiskMap 5-Band — But Roads, Villages & Exposure Are the Overlay

**Bullets:**
- **RiskMap.jsx:** Leaflet polygons with `RISK_BANDS` — **Very Low<21<Low<41<Moderate<66<High<85<Critical** `docs/CURRENT_SYSTEM.md:14`; per-corridor selector Gangtok/Lachung/Darjeeling; zone cards `RiskScoreGauge 0–100 + confidence + confidence_real_1pct` + `MissingEvidenceCard` + `ZoneIntelligencePanel`
- **RoadStatusCard:** `R1 blocked (historically 12 slides) · R2 at-risk (8) deterministic · R3 open (5, emergency_route true) · R4 open (3, emergency_route true, bottleneck)` `roads.json:1` + `road_restriction_catalogue.json:1`; routing `POST /api/routes/safe:421` **shortest via R2 vs risk-aware via R3+R4** `avoided_zones [R2]`, `max_risk_exposed 89→66`, costs `RISK_WEIGHT 3.0 α=0.2`; distance rendered in frontend via haversine, not raw graph cost (degrees)
- **Runout screening:** `GET /api/runout/exposure:1276` — steepest-descent on SRTM 30 m steps, stop <5°/1.8 km, void-centroid seeds from 30 m ring; exposure fetch capped 400/zone (dense towns undercounted, stated) → **S2 Chandmari ~85 buildings downstream** (400 seen), S1 0, S3 1 — shown as `ExposureCard` `buildings_downstream`
- **Wound amber:** `GET /api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` review-queue pins (≤150 m road, NDVI loss ≥0.3, SCL-gated both dates, before 0.4) — **not confirmed cuts**, seasonal clearing may false-positive, 10–20 m pixels miss narrow cuts — drives warning bump only

**Visual cue:** Screenshot of `RiskMap` with 5-band zones (leaflet) + `RoadStatusCard` R1–R4 chips + `RouteComparisonCard` S1→S4 shortest red dashed vs risk-aware solid green + runout spaghetti (S2 long) + wound amber triangles near R2/R3. Basemap OSM/CARTO toggle (`osm` default, no key).

**Speaker note (65s):** “Click S1 in the demo — the map shows the score, but the decision comes from the warning state + isolation, not the color. Routing: shortest tries the ridge shortcut via R2 (at-risk); risk-aware closes it via hazard graph and goes valley. Distance on the card is haversine km from centers — `total_cost` on the API is graph degrees + weighted risk, never shown as km. Runout is a screening approximation labeled as such — we say so on the card, not a debris-flow simulator claim.”

**Evidence:** `frontend/src/components/RiskMap/RiskMap.jsx:1` (`RISK_BANDS`, `MapLegend`, `RoadOverlay`, `VillageLayer`) · `frontend/src/components/Routing/RoadStatusCard.jsx:1` (R1–R4) · `backend/app/main.py:421` (`POST /routes/safe`) · `backend/app/main.py:496` (hazard graph drops R2) · `data/sih26001/evidence/runout_exposure.json:1` (S2 85) · `data/sih26001/evidence/wound_map.json:1` (candidates)

---

## Slide 15: Isolation Feature Deep Dive — Who Is Cut Off, Before the Cut

**Title:** Isolation = R4 Is the Bottleneck — MAY_ISOLATE Saves Hours, Not Lives Alone

**Bullets:**
- **Egress, not slope adjacency:** isolation is **road-network egress to the valley hub S4/N4/D4**; even if upstream spur is open, `R4 blocked → S1/S2/S3 ISOLATED` (`_isolation_for_location:1326`) — rule deterministic + matches fixture topology `S1:[S2,S3] S2:[S1,S3] S3:[S1,S2,S4] S4:[S3]` (`data.py:118` `GRAPH`)
- **Per-zone `adj_map` (Gangtok example):** `S1->[R1,R2,R3]` · `S2->[R2,R3]` (ridge/valley via S1/S3) · `S3->[R3,R4]` · `S4->[R4]` (shifted to N*/D* via `locations.js` offsets 0.35,0.135 / -0.298,-0.337); `open_exits = sum(s=="open")`, `at_risk_exits = sum(s=="at-risk")`, `downstream_blocked = R4 blocked && zid in {S1,S2,S3}`, `direct_blocked = all(blocked)`
- **Predictive MAY_ISOLATE (pre-alert):** `open_exits==0 && at_risk==1 && band High/Critical` → **one at-risk road left** + strong slope; OR `R2 at-risk && upper S1 High/Critical` → **single ridge shortcut pre-alert** — reason-stamped, exposed as `GET /api/isolation:1441` `{status ISOLATED|MAY_ISOLATE|OPEN, reason, adjacent_statuses, score, band}` + header + admin
- **Warning override:** `isolation.corridor_isolated` → corridor_state becomes **EVACUATE** (`main.py:1601`); isolated zones rewritten `state=EVACUATE` with `ISOLATED — R4 … no egress to plains`; `may_isolate` corridor becomes **RESTRICT**; auto-watcher fires on both (see Slide 22)

**Visual cue:** Isolation circuit diagram: R4 as bottleneck switch; upstream villages as bulbs; R1/R2/R3 as parallel feeds. Right: `IsolationAlertCard` screenshots ISOLATED (red) vs MAY_ISOLATE (amber) with bottleneck strip `R1 · R2 · R3 · R4`. Bottom: `adj_map` code block.

**Speaker note (70s):** “We learned this from Taiwan/Japan: connectivity is the warning, not the hill. S4 is the valley hub — it never isolates itself; upstream villages isolate through it. The MAY_ISOLATE is the honest win — one road left, slope High, tell the community to keep the valley route clear and hold a team. Demo: block R4 (via fixture toggle or simply note R1 blocked is current state) → `GET /api/isolation` shows S1–S3 ISOLATED; the warning state (next slide) flips to EVACUATE without the 0–100 moving. Point to the code — no ML in isolation, pure graph logic, testable in 15 lines.” Never claim we invented road-risk.

**Evidence:** `backend/app/main.py:1326` (`_isolation_for_location`) · `backend/app/data.py:118` (`GRAPH`) · `backend/app/main.py:496` (`_road_graphs_for` + `_ROAD_SHIFT` gangtok 0/0, lachung 0.35/0.135, darjeeling -0.298/-0.337) · `frontend/src/components/Alerts/IsolationAlertCard.jsx:1` · `docs/FEATURE_ISOLATION.md:1`

---

## Slide 16: SWI Tank Model — The Memory the Hill Needs

**Title:** SWI 3-Tank (JMA) — L1=15 L2=60 L3=60 — Warning-Overlay Only

**Bullets:**
- **Okada 1992 (JMA) simplified:** Tank1 surface `L1=15 mm a1=0.10 b1=0.12` ⋯ Tank2 subsurface `L2=60 a2=0.05 b2=0.05` ⋯ Tank3 groundwater `L3=60 a3=0.01`; `inflow = daily rainfall (observed 7 d uniform + tail (30 d−7 d)/23 + forecast next 3 d)`; `SWI = S1+S2+S3 mm` → normalized **`tanh(SWI/100)`** (JMA warms ~120–160 mm, 100 mm tanh midpoint) `backend/app/swi.py:14`
- **Why:** CCI 0.271 is same-cell all slopes (0.25°) — quasi-static; SWI blends rainfall memory (antecedent 30 d + forecast) into saturation trajectory — **model scoring stays frozen on soil_moisture 0.271** (17 feats), SWI never enters X; warning logic uses `SWI ≥0.40` (`_WARN_SWI_SOIL`) vs `soil ≥0.32` single-value gate
- **Endpoints:** `GET /api/soil/swi:1203` per zone `{zone_id, swi 0–1, soil_moisture, forecast_blend bool}` (forecast from `_LIVE_CACHE` when present) → `swi_for_zone(r7,r30,forecast3)` · warning reads `swi_for_zone` same function (`main.py:1540`)
- **Honesty:** SWI is rainfall-derived saturation proxy, not in-situ piezometer; Bhukosh/lineament remain uniform, second-order effect stated; no InSAR claim

**Visual cue:** 3-tank stack diagram (L1/L2/L3 with a/b arrows) + tanh curve `SWI mm → 0–1` with JMA 120–160 warning band + `tanh(100)=0.76` mid. Right: `GET /api/soil/swi` response tiles per zone + code `swi.py:14` pin.

**Speaker note (50s):** “Tank 1 is surface — fast. Tank 2 is subsurface — slower. Tank 3 is groundwater — slowest. Rain fills Tank1; excess infiltrates via b’s down, outflow via a’s across. We pass daily sums, not intensity — so hyperlocal bursts hide in the uniform split, and we say so. The number you see is `tanh(SWI/100)` — 0–1, comparable to soil_moisture, but it carries memory. It bumps warning only, costs no retrain.”

**Evidence:** `backend/app/swi.py:14` (`swi_from_series` + `swi_for_zone`) · `backend/app/main.py:1203` (`GET /soil/swi`) · `docs/sih26001/03_DATA_PLAN_SIH26001.md:27` (CCI vs SWI) · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:46` (soil-water memory) · `docs/FEATURE_OFFLINE_GOVT_ALERTS.md:1` (provenance)

---

## Slide 17: Road Catalogue + Operational Risk — From Hazard to Priority

**Title:** Road Catalogue × Exposure → Operational Risk = “Who Gets Hit First”

**Bullets:**
- **Catalogue (`road_restriction_catalogue.json:1`):** per-segment historical slide count + rule + `emergency_route` flag: **R1 12 true historical / not emergency** (Restrict if `effective≥local && SWI≥0.35`); **R2 8 / not emergency** (Restrict if `S1 score≥65 + isolated or SWI≥0.40`); **R3 5 / emergency true** (Restrict only `effective≥450 && SWI≥0.45`); **R4 3 / emergency true** (last egress, `effective≥500 or SWI≥0.50`, 12 h typical) — `GET /api/roads/restrictions:798` evaluates `should_restrict` from `GET /warning/state` current states
- **Operational risk (hazard × exposure):** `GET /api/zones/{id}/exposure:743` → `hazard{score,band}` + `exposure{runout, buildings_downstream, wound_near, isolation}` → **`op_score = score*(1+0.18*log1p(buildings)/3 + 0.12*wound + 0.20*isolated else 0.08*may_isolate)` → `op_band, delta`** (e.g. S2 78→op 91 delta+13 due to 85 buildings + wound near R2)
- **GIS tie:** `ExposureCard` + `RunoutExposure` path + `Wound detail` rendered under each zone; warning `kit.shelters` / `phones` join here (see Slide 24)
- **Policy:** **emergency routes R3/R4 require higher bar** — evaluated per `rule.emergency_route` check in `main.py:819`; not officer discretion — catalogue note `“Counts from GSI 30k vs OSM 200 m buffer — not a legal order, officer confirms via field queue”`

**Visual cue:** Table R1–R4 with `historical_slides | emergency_route | rule | typical_closure_hours` + restriction evaluation pills `restricted? true/false · reason`. Right: Operational risk formula with log1p curve + example S2 bump.

**Speaker note (55s):** “Hazard says how ready the hill is to fail. Operational risk says who it hits and whether you can get them out. Japan’s MLIT publishes pre-emptive restriction sections exactly like this catalogue — we are explicit that our counts come from GSI 30k vs OSM 200 m buffer and the routing trace is demo — an officer still confirms via the field queue. Demo: click S2 → see `GET /zones/S2/exposure` + op_score 91 vs hazard 78 — that is the ‘why truck goes to S2 first’.”

**Evidence:** `data/sih26001/evidence/road_restriction_catalogue.json:1` · `backend/app/main.py:798` (`road_restrictions`) · `backend/app/main.py:743` (`zone_exposure`, log1p formula) · `frontend/src/components/Routing/ExposureCard.jsx:1` · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:58` (pre-emptive restriction)

---

## Slide 18: Wound — From Distance-to-Road to “Where People Are Changing the Hill”

**Title:** Wound = Roadside NDVI Loss as a Time-Varying Wound, Not a Static Distance

**Bullets:**
- **Method (review queue, NOT confirmed cuts):** Sentinel-2 pair **pre 2023-11-15 vs post 2024-11-29 (both S2 L2A, STAC earth-search, SCL-gated)**; `was-vegetated ≥0.4`, `drop ≥0.3`, `≤150 m of road`, roadside only → `wound_map.json:1` candidates; **Gangtok 2 scars near R2/R3**, Lachung 0, Darjeeling 0 (cloud_gap 144) — plus up to 400 sampled points/corridor; `wound_as_feature.json:1` counts **4 candidates** within 800 m review → `fraction 4/2936 0.00136`
- **As a feature:** `recent_disturbance 0/1` binary (800 m buffer `wound_as_feature.json:method`) appended to X (rare, 4/2936) — expected marginal **+0.01 AUC**, kept as screened feature even though shuttle value low; not leaked (≤150 m road, SCL-gated, not post-event)
- **How it matters today:** wound_near bump flag in `GET /warning/state` (reason “Recent disturbance nearby — BigGIS wound” + `bump_reasons Single bump max+1`) + wound_near in `GET /zones/{id}/exposure`; mapped on `RiskMap` as amber pins + dedicated layer toggle `mapLayers.wounds`
- **Limits honest:** seasonal clearing or missed cloud may false-positive; **10–20 m pixels miss narrow cuts**; before/after scenes are one year apart post-monsoon → vegetation seasonality controlled, but re-greening hides old cuts; all labeled as such in bundle `method` note

**Visual cue:** Left: Sentinel pair chips (2023 vs 2024) with NDVI drop squares + road buffer. Center: `wound_map.json` → `wound_as_feature.json` pipeline (SCL → NDVI → distance → review queue → 0/1). Right: `RiskMap` amber pins + warning reason chip “Recent wound nearby”.

**Speaker note (50s):** “Static `distance_to_road` never changes — hill cutting does. The wound is our BigGIS answer: hill cuts remove vegetation, NDVI drops, we catch the loss within 150 m of a road. It is a review queue — officer confirms — and on the warning it only adds one bump. As a model feature it is rare (4/2936), adds about one point of AUC, but on the map it answers ‘where changed last’. Wording (research-safe): ‘recent anthropogenic disturbance as a time-varying evidence layer’ — never ‘we invented road risk’.”

**Evidence:** `data/sih26001/evidence/wound_map.json:1` (2 scars, sampled 409, cloud_gap) · `data/sih26001/evidence/wound_as_feature.json:1` (4/2936, 0.00136) · `backend/app/main.py:1556` (wound_near bump) · `docs/sih26001/03_DATA_PLAN_SIH26001.md:74` (wound/screening) · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:35` (BigGIS)

---

## Slide 19: Observed vs Forecast — The Line Called NOW (and Why Replay Is Causal)

**Title:** `RiskTrendChart` — `◀ OBSERVED — IMD 0.25° + CCI | NOW | FORECAST — Open-Meteo ▶`

**Bullets:**
- **NOW is the contract:** `RiskTrendChart.jsx:86` draws `NOW` vertical (`ReferenceLine x=history[last].time`, sky-blue dashed) with 75 (High) / 85 (Critical) frozen thresholds; left of NOW = **`daily_history` 365-day deterministic seed 91** from `model_service.py:daily_history` + `GET /api/zones/{id}/history:379`; right of NOW = **forecast daily** from `GET /api/forecast/live:1154` (Open-Meteo 7 d) — **never silently mixed** (research §2 explicitly requires separation)
- **Replay (history that answers When):** `GET /api/replay/series` → **5 cases × up to 31 d series** = Mangan Jun 2024 (lead High→Critical Jun 10→13), Dipudara Aug 2024 (7-day precursor High), Lumsay Jun 2022 (77% Critical), Sichey Jun 2021, NH-10 Oct 2022 (`replay_series.json:1`, 2207-line bundle, `causality: series <= event_date`) — replay engine asserts inputs available ON each date only (trailing IMD sums, same/prior-day CCI, one pre-event S2, static terrain)
- **`early_episode_definition`:** contiguous High-or-worse runs separated by ≥3 calm days, counting runs before final pre-event run — shown in `ReplayCard` as lead-time ledger; Dipudara precursor saved lives narrative
- **Bottom legend / footer:** `◀ OBSERVED … | NOW | FORECAST … ▶` + caption “Causality: replay_series uses only inputs available ON each date — no future leak.”

**Visual cue:** Trend chart mock with NOW line + 75/85 bands + history wiggle left, forecast dots right in sky-blue. Below: replay mini-cards (Mangan 93.2 Critical Jun 13, green lead arrow) + causality lock icon.

**Speaker note (60s):** “Drag the history slider NOW — that is not session prediction logs, it’s 365 deterministic daily scores from `daily_history` seed 91. Forecast dots come from `forecast/live`. The replay is the audit — hit `GET /api/replay/series`, pick `mangan-jun2024`, you will see the score was High on Jun 10, Critical on Jun 12, before the red alert on Jun 13. Dipudara shows 7 days of precursor High — that is why 2,000 tourists were moved on Aug 13. Say: ‘Observed vs forecast explicitly separated, causality asserted at build’ — Japan’s architecture does the same past|now|future split.”

**Evidence:** `frontend/src/components/ZoneDetails/RiskTrendChart.jsx:86` (ReferenceLine x=NOW + 75/85) · `backend/app/main.py:379` (`GET /history` 365-day) · `backend/app/main.py:1154` (`forecast/live`) · `data/sih26001/evidence/replay_series.json:1` (5 cases, causality) · `frontend/src/components/Replay/ReplayCard.jsx:1`

---

## Slide 20: Field Reporting — Metadata-Only, EXIF-Verified, Officer-Gated Queue

**Title:** Field Reports — Photo Never Leaves the Device; Metadata + EXIF Do

**Bullets:**
- **ReportModal.jsx lane:** real local `File` → **EXIF GPS parser `readExifGps` (APP1/TIFF GPS IFD, JPEG only; PNG/WebP/MP4 → null)** + **SHA256 `sha256File` (crypto.subtle or pure-JS fallback `sha256Sync` for plain-HTTP LAN)** + **thumbnail `makePhotoThumbnail 320 px JPEG 0.7`** (background store) — `ACCEPTED_MEDIA image/jpeg|png|webp|video/mp4`, `MAX 10 MB`, `CONSENT true required`, `zone_id S1–S4/N1–D4 (12)`, `type crack|slope_movement|blocked_road|other`, `text 10–500 chars`, `lat/lon pilot bbox 27.20–27.40/88.40–88.70`, `captured_at ISO (future>1 h rejected)`, rate cap 20/boot
- **POST payload `ReportIn` → `POST /api/reports:879`:** `{zone_id,type,text,lat,lon,captured_at,reporter_role villager|field_officer, photo:{filename,mime,size_bytes,sha256,exif_lat,exif_lon}|null, consent}` — **bytes never committed** (`.gitignore:46` LOCAL ONLY), `PhotoMeta` only; `talus_report_photos` (thumbs) + `talus_report_outbox` (pending) in `reports.js:1`
- **Honesty gates:** EXIF vs claimed `>200 m → flagged “EXIF GPS Xm from claimed (>200m)”` + unsupported mime → flagged + text/type/zone/captured_at validation → 422; `flagged_reason` shown; background outbox eligibility `isOutboxEligible: 4xx≠429 not eligible; only 429|5xx|network → queue`
- **Queue & review:** `GET /api/reports/queue?status=queued|verified|dismissed|flagged:932` (fixture ships one `REP-001` S2 crack) → OfficerQueue + Leaflet markers; `PATCH /api/reports/{id}:942` `{status verified|dismissed|flagged, reviewer_role, reason}` — only `queued|flagged → verified|dismissed|flagged`, **verified/dismissed terminal (409)**; verified appends sidecar `candidate_labels` (crowd-verified + officer ID + SHA256) — **never auto-flips `event`/`previous_landslide`**

**Visual cue:** Left: ReportModal form (photo preview + hash 12-char + EXIF badge “Device GPS … from file / No GPS found”) → POST arrow → Queue pills. Right: Queue screenshot (REP-001), flagged amber banner, Sync badge `1 pending → synced ✓`. Bottom: `15 tests @ backend/tests/test_reports.py:1` + `talus_report_outbox` + `sw.js`.

**Speaker note (75s):** “We never post bytes. The file stays client-side; a 320-px JPEG thumb stays in `talus_report_photos` for the queue display. The POST carries only filename/mime/size/SHA256 + EXIF lat/lon (or null) + claimed lat/lon + consent. If EXIF is >200 m from claimed, we flag it for the officer — not reject — so a villager with wrong zone still reports but the officer checks. Demo shows `PATCH → verified` turning flagged→verified, and terminal guard 409 if you try to double-verify. Pollute the trust ledger is a bug, not a feature — that is why candidate labels are a sidecar.”

**Evidence:** `frontend/src/components/Reports/ReportModal.jsx:1` (`ACCEPTED_MEDIA`, `MAX_MEDIA_BYTES 10 MB`, `ReportIn` mapping, thumbnail/sha/exif, consent, `talus_report_outbox` fallback) · `frontend/src/services/reports.js:1` (`PHOTO_STORE_KEY talus_report_photos`, `OUTBOX_KEY talus_report_outbox`, `makePhotoThumbnail 320`, `sha256File`, `readExifGps` APP1/TIFF) · `backend/app/main.py:879` (`POST /reports` ReportIn→ReportOut) · `backend/app/main.py:722` (`_report_flagged_reason` 200 m) · `backend/tests/test_reports.py:1` (15 tests)

---

## Slide 21: Alerts — Warning State Machine (6 States, Reason-Stamped, Local Thresholds)

**Title:** Warning States: NORMAL → WATCH → ALERT → CRITICAL → RESTRICT → EVACUATE

**Bullets:**
- **Per-zone 6-state engine `GET /api/warning/state:1449`:** `RISK_BAND 0–3` (Low→Critical) + **single bump +1** max for non-isolation reasons + **isolation override** (see Slide 15) — `states[]` per zone `{zone_id, state, score, band, reasons[], action{message,priority}, kit{what,why,rainfall,shelters,phones,villager_explain}}` + `corridor_state` max
- **Fuel (reason-stamped, never silent):** `effective r7+0.3*r30` vs **`warning_thresholds.json:1` per-zone local (Gangtok S1 385 / S2 395 / S3 410 / S4 375; Lachung N1 380/N2 390/N3 405/N4 370; Darjeeling D1 400/D2 410/D3 420/D4 390)** (+ **quake 25% drop `*0.75` if `seismic_years_since ≤0.49y && n50>0`** 26 USGS, research:28) + `rain 7d heavy 150 / building 80` (quake-conditioned) + **`SWI 3-tank L1=15 L2=60 L3=60 a1=0.10… → tanh(SWI/100) ≥0.40` (JMA)** vs soil 0.32 + **wound proximity** + **forecast exceedance `today≥50 mm || week≥150 mm`** + **trend rapid** + **quake window** — each appends to `reasons` + at most one adds `bump_reasons`
- **Card:** `WarningStateCard.jsx:1` `STATE_STYLE` 6 colors (NORMAL emerald … EVACUATE red pulse) + `Siren` header + reasons joined `·` + officer action `ChevronRight` + corridor badge `highest: STATE · zone_id`
- **Honesty:** thresholds are **operational, not learned** (Taiwan-style per-zone, calibrated post-event `0.9*old+0.1*event_effective`); bands stay frozen; villagers see kit, not state%; `/admin` sees thresholds

**Visual cue:** Vertical state ladder NORMAL→EVACUATE with local threshold chips S1 385 … S4 375 beside it. Right: `WarningStateCard` mock (S1 CRITICAL · S2 ALERT … reasons “Effective rain 412mm ≥385 … SWI 0.43 …”) + officer action line.

**Speaker note (65s):** “Read the reasons: ‘Effective rain 412 mm ≥385 (local 385) · Heavy 7-day 160 mm ≥150 · SWI 0.43 ≥0.40 · Recent wound nearby · Forecast 55 mm today’ — that is the audit. Thresholds are not one NER number — they are per zone, lowered 25% for 6 months after a nearby quake (Taiwan conditioning). The bump logic is capped: even if three reasons fire, level rises at most one — isolation alone can jump to EVACUATE. The kit below is what the village actually gets (next slide).”

**Evidence:** `data/sih26001/evidence/warning_thresholds.json:1` (per-zone 385/395/410/375) · `backend/app/main.py:1449` (`warning_state`, `_WARN_STATES 6`, `_WARN_SWI_SOIL 0.40`, `_WARN_EFFECTIVE_RAIN 390`, quake `0.75`) · `backend/app/swi.py:14` (SWI) · `frontend/src/components/Alerts/WarningStateCard.jsx:1` (STATE_STYLE) · `backend/app/main.py:1575` (kit shelters/phones)

---

## Slide 22: Alerts — Isolation Alert + AlertPanel + Auto Watcher (60 s / 3600 s)

**Title:** Who Gets the Alert, in What Language, Over What Channel, Without You Clicking

**Bullets:**
- **IsolationAlertCard.jsx:1:** `GET /api/isolation?location=` → `corridor_isolated / may_isolate` guards render (null if OPEN); **ISOLATED red pulse + ShieldAlert** “S1,S2 cut off — only road blocked — no alternative — cannot reach valley via S4” + bottleneck line `R1…R4` + `action` string; **MAY_ISOLATE amber** `AlertTriangle` “Single road left while High/Critical” + `Route` action + `Radio` footer “Alert sent to district & state — isolated villages prioritized”
- **AlertPanel (multilingual + dual-channel):** 5 langs **`en/hi/ne/as/bn`** `main.py:86` `DECISIONS_TRANSLATIONS` (devanagari, Bengali script); buttons **APP (fixture) vs SMS (env-gated)** → `POST /api/alerts/dispatch:959` `?channel=app|sms&lang&zone_id&message` — **fixture broadcast `alerts.json` en/hi/ne when `channel=app`**; **SMS adapters when `channel=sms` + `SMS_PROVIDER in {msg91,fast2sms,twilio,textbelt}` + `SMS_API_KEY` + `SMS_TO|TWILIO_SID/FROM`**: `_sms_send` (textbelt POST + fast2sms GET + msg91 flow + twilio Basic) — every dispatch appended to `runs/alert_dispatch.jsonl` via `_append_dispatch_log` **without key**, never fake successes; `GET /dispatch/log?limit=:1062` + `GET /alerts/ack` + `POST /ack:1076` real ack
- **Auto watcher (the op that judges test):** `_auto_watcher_loop:1702` daemon thread at startup if `AUTO_ALERT_ENABLED true` (default), `interval 60 s` `AUTO_ALERT_INTERVAL_S` / `cooldown 3600 s` `AUTO_COOLDOWN_S` — scans `_auto_should_fire` per location → dedup key `location:zone:status` via `_AUTO_LAST`; **fires on ISOLATED / MAY_ISOLATE**, builds officer message from `_decisions`, logs both app + hi entry; manual demo trigger `POST /api/alerts/auto/trigger:1728` returns `{would_fire, fired}`

**Visual cue:** Left: IsolationAlertCard pulses. Center: AlertPanel with 5-lang chips EN/HI/NE/AS/BN + app|sms toggle + `DISPATCHED | msg91 SIMULATED` pill + dispatch log strip. Right: Auto watcher timeline `60 s poll → 3600 s cooldown → runs/alert_dispatch.jsonl`.

**Speaker note (70s):** “Tomorrow the officer doesn’t sit clicking dispatch — the auto watcher does, every 60 s, deduped 3600 s so you don’t spam. In demo mode with no SMS key, we log SIMULATED with provider ‘none’ — honestly, we never claim an SMS was sent. The AlertPanel preview lets the judge see the Bangla message before it would send. Tap `POST /alerts/auto/trigger` — it tells you what would_fire before it fires. Isolation + warning + exposure feed the message, not the 0–100.”

**Evidence:** `frontend/src/components/Alerts/IsolationAlertCard.jsx:1` (OPEN/MAY_ISOLATE/ISOLATED, bottleneck) · `frontend/src/components/Alerts/AlertPanel.jsx:1` (en/hi/ne/as/bn, app|sms, dispatch/log) · `backend/app/main.py:86` (translations) · `backend/app/main.py:959` (`dispatch`) · `backend/app/main.py:1004` (`_sms_send msg91/fast2sms/twilio/textbelt`) · `backend/app/main.py:1702` (`_auto_watcher_loop`) · `backend/app/main.py:1721` (`auto/status`, `auto/trigger`) · `backend/tests/test_alerts_ack.py:1` · `runs/alert_dispatch.jsonl`

---

## Slide 23: Offline — The App Works When the Hill Doesn’t

**Title:** Offline-First = PWA Shell + Forecast Badge + Outbox + Sync Badge

**Bullets:**
- **Service worker `sw.js:1`:** `CACHE talus-shell-v1` + **`SHELL [/,/index.html,manifest.webmanifest,icons]`** cache-first on install `skipWaiting` + activate prune + **`fetch` handler: same-origin GET cache-first (app shell + chunks), `/api` network-only (never served stale)** → app shell renders offline, `/api` shows the app’s offline badge, not stale numbers
- **Manifest `manifest.webmanifest:1`:** `name TALUS — NER…`, `display standalone`, `theme #0b1220`, **icons `icon-192.png (any maskable)` + `icon-512.png` (any maskable)** + `favicon.svg`; `scope .` + `start_url .`
- **Live proof without network (QuickStatsBar + sw.js):** `QuickStatsBar.jsx:1` shows **`LIVE {precip_mm}mm · {prob}%` from `GET /forecast/live` when online**; offline the bar keeps the shell+LIVE badge rationale, map keeps last corridor; **field keeps `talus_report_photos` thumbnail store + `talus_report_outbox` outbox** (`reports.js:1` `PHOTO_STORE_KEY`, `OUTBOX_KEY`, `makePhotoThumbnail 320`, `saveReportOutbox`)
- **Sync lane:** `reports.js:1` outbox **auto-retry on `online` event + manual “Sync now”** `ReportModal.handleSync`; `AlertPanel` sync badge `synced ✓ / N pending` (`AlertPanel.jsx:138` offline_note/queued); **`GET /api/reports/queue` never cached**, `GET /api/alerts/dispatch/log` provenance shows SIMULATED vs SENT

**Visual cue:** DevTools Applications pane (sw.js talus-shell-v1, manifest 192/512). Phone frames: offline “1 pending” (amber) → online “synced ✓” (emerald) on the report queue. QuickStatsBar LIVE chip green.

**Speaker note (45s):** “Turn off the laptop Wi-Fi and the map still loads — shell is cached, `/api` is not, the sync badge says so. Submit a report offline — `talus_report_outbox` holds it, reconnect → Sync now flushes via `GET /reports/queue` + `PATCH` triage. IMD live requires a key; offshore the IMD lane falls back to Open-Meteo blend — we label it, never hide it. Nepal’s lesson: low-network is the requirement, not a feature.”

**Evidence:** `frontend/public/sw.js:1` (`talus-shell-v1`, `SHELL`, `/api` network-only) · `frontend/public/manifest.webmanifest:1` (192/512, standalone) · `frontend/src/services/reports.js:1` (`PHOTO_STORE_KEY talus_report_photos`, `OUTBOX_KEY talus_report_outbox`, `makePhotoThumbnail 320`) · `frontend/src/components/RiskSummary/QuickStatsBar.jsx:1` (LIVE badge) · `frontend/src/components/Reports/ReportModal.jsx:121` (`handleSync`) · `docs/sih26001/01_REQUIREMENTS_SIH26001.md:92` (PWA offline)

---

## Slide 24: Yellow / Red Kits — What the Village Actually Reads

**Title:** From 89/78/66/52 to “Avoid the Ridge Road. Use the Valley Route.”

**Bullets:**
- **Warning kit payload (`GET /api/warning/state:1449 → states[].kit + corridor_state`):** `{what: "CRITICAL — High risk for S1", why: reasons[:3], rainfall: "160mm /7d effective 412mm (thr 385)", shelters: [Tadong Community Hall (27.325,88.606), Ranipool Primary School (27.315,88.595)], phones: "03592-221011 (DDMA) · SDRF 03592-220888", villager_explain: officer plain message + band}` — **what/why/rain/shelters/phones + villager_explain** per `RESEARCH:44` action-oriented (Yellow=prepare, Red=evacuate)
- **Per-corridor shelters + phones:** `main.py:1575` `SHELTERS gangtok: [Tadong Community Hall, Ranipool Primary School] | lachung: [Lachung Monastery Hall, Yumthang Road Shelter] | darjeeling: [Ghoom Relief Center, Lebong Hall]` + `PHONES gangtok 03592-221011 / lachung 03592-269022 / darjeeling 0354-2254233` — displayed in `ZoneIntelligencePanel` + warning card, rendered in `lang en/hi/ne/as/bn` via `_decisions(lang)`
- **Color logic (not decoration):** `RoleActionCard / WarningStateCard` mapping ensures villager view is danger/safe + map; admin view (`/admin`) holds provenance Brier 0.0971, OSM 1014/226/504, Bhukosh timeout, thresholds 385/395/410/375 — hidden from field
- **Yellow vs Red threshold:** Yellow = ALERT (prepare, keep valley route clear); Red = CRITICAL→RESTRICT→EVACUATE (close + evacuate) — triggered by SWI≥0.40 + effective≥local + isolation R4 — wording honest analog `RESEARCH:44`

**Visual cue:** Two kit cards side by side: Yellow (WATCH/ALERT, “Caution on Tadong paths during rain. Shelters: …”) and Red (CRITICAL/EVACUATE, “Avoid S1 hillside road 2 days. Shelters: … Phones: 03592-221011”). Small map snippet with red isolation overlay.

**Speaker note (50s):** “This is the slide a villager would understand. The model’s 89 is not here — ‘Avoid the S1 hillside road for 2 days. Use the valley route. Shelters: Ranipool Primary School. Call 03592-221011.’ is here. Drill it: ask any judge to read the Bangla version — we have it. Worst line to say on this slide is ‘the SHAP value is 12.5’ — villagers don’t read SHAP.”

**Evidence:** `backend/app/main.py:1575` (`SHELTERS`, `PHONES`, `kit:{what,why,rainfall,shelters,phones,villager_explain}`) · `backend/app/main.py:1449` (warning kit per zone) · `frontend/src/components/ZoneDetails/RoleActionCard.jsx:1` · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:43` (Yellow=prepare, Red=evacuate + what/why/rain/shelters/phones) · `docs/sih26001/01_REQUIREMENTS_SIH26001.md:50` (role-based decisions)

---

## Slide 25: History Replay — 365-Day Slider + 31-Day Replay Series (5 Events)

**Title:** History = 365-Day Daily History (NOW Slider) + 31-Day Replay per Past Event

**Bullets:**
- **Daily history (NOW):** `model_service.py:daily_history` → `GET /api/zones/{id}/history:379` `seed 91` deterministic **365-day `daily_history`** (not session logs) + `evidence_timeline` `scenario_service.py:64` → `RiskTrendChart.jsx` slider positions NOW on trajectory; left of NOW = OBSERVED (IMD + CCI), right = FORECAST (Open-Meteo)
- **Replay series bundle:** `GET /api/replay/series` → **5 cases × 31 d** (`replay_series.json:1` 2207 lines) — Mangan Jun 12–13 2024, Dipudara Aug 20 2024, Lumsay Jun 2022 (month-fuzzy), Sichey Jun 2021 (date-fuzzy), NH-10 19/20 Mile Oct 9 2022 (post-monsoon) — each row `date,score,band,rain_24h,rain_7d,rain_30d,soil,ndvi,drivers[]` with `event_date`, `analogue row/distance/lulc`, `sources`, `soil_source`, `ndvi_source`
- **Causality guarantee:** bundle `causality` key asserts **inputs available ON each date only** — script `scripts/build_replay_series.py` enforces `series ≤ event_date` at build; drivers are honest (building/easing/drying); no future NDVI leak
- **Frontend:** `ReplayCard` renders timeline + lead-time ledger (`early_episode_definition: contiguous High-or-worse runs ≥3 calm days apart`); isolation/warning cross-badges on replay days where `R4 blocked`

**Visual cue:** History slider (365) above replay tabs (5 events). Pick Mangan → score curve climbs Low (61.9) → High (79.7 Jun 10) → Critical (93.2 Jun 13) with rain/soil rows + `drivers` chips. Causality lock badge.

**Speaker note (60s):** “History answers ‘how did we get here?’ Replay answers ‘when would we have known?’ The daily_history is seed 91 deterministic so the judge sees the same 365 days you rehearsed. Replay is the trust builder — Mangan was High three days before the red alert; Dipudara had a 7-day High episode that saved 2,000 people because officials acted on precursor, not the main slide. The bundle is committed at `data/sih26001/evidence/replay_series.json` — not a live query — so it never 500s. Cafe line: ‘replay asserts causality at build’.”

**Evidence:** `backend/app/main.py:379` (`GET /history` 365-day) · `data/sih26001/evidence/replay_series.json:1` (5 cases, 31 d, causality, early_episode) · `frontend/src/components/Replay/ReplayCard.jsx:1` · `docs/sih26001/06_DEMO_SCENARIO_SIH26001.md:44` (Screen 7 NOW)

---

## Slide 26: Live Demo Script — 3 Corridors, Simulator Lane, Judge’s Phone (Rehearsed)

**Title:** Live Demo — 3 Corridors + Simulator Ticks + Judge’s Phone QR

**Bullets:**
- **Setup (ps1):** `.\start_all.ps1` → backend `:8000` + frontend `:5173`; verify `GET /health:234` shows `store:gangtok ok (4 zones, live_scores=true|false)` + `fixture:… ok` + `version 0.1.0`; **if fresh clone → `live_scores false` is the honest path** — speak “fixture scores, not live — same UI, same decisions”
- **Simulator (PS sensor adapter proof):** `python scripts/local_sensor_sim.py --interval 30` → ticks `runs/live_feed.json` + `runs/sim_audit.jsonl` every 30 s (rain `1h mm`, soil delta, battery, rssi) → frontend `RiskMap` sensor pins (label SIMULATED) poll `GET /api/live/feed` + `GET /api/live/audit`; fallback when off: `data/sih26001/fixtures/live_feed.sample.json` committed; geography switch via `LocationSelector` Gangtok→Lachung→Darjeeling (suffix S→N→D, shift offsets 0/0.35/-0.298)
- **Rehearsed path (6 min, 10 steps, exact):** ① S2 crack report (`POST /reports` → queued + marker) ② queue filter `?status=queued` ③ offline → submit → pending badge `1 pending` (sw.js shell still renders) ④ reconnect → auto-sync → `synced ✓` ⑤ officer `PATCH → verified` (terminal guard demo) ⑥ dispatch alert `app en` + 3-lang preview en/hi/ne + `GET /dispatch/log` ⑦ `R4 blocked` → `GET /isolation` S1–S3 ISOLATED + `GET /warning/state` EVACUATE ⑧ `POST /alerts/auto/trigger` isolation auto-alert ⑨ drag history slider `GET /history:379` → RiskTrendChart NOW + `GET /forecast/live` observed vs forecast split + IMD gated provenance ⑩ ADMIN `/admin` PIN **9999** (villager 2222/1111/3333) shows health/isolation/log/provenance
- **Judge phone:** frontend QR from `vite --host` → judge’s phone loads same PWA `manifest 192/512`; RiskMap layers (hazardGlow, runout, wounds, sensors, routes) + RoleSelector `villager/district_officer/state_manager/rescue_team` + LanguageSelector en/hi/ne/as/bn + Route modal `S1→S4 shortest via R2 (89) vs risk-aware via R3+R4 (66) avoided R2`

**Visual cue:** Phone render wall (judge phone QR + laptop). Numbered step chips ①–⑩ with API pills. Bottom: “All local, no network required for ①–⑩ — live forecast shown as gated blend, not silent dependency.”

**Speaker note (65s):** “Rehearse with `.\stop_all.ps1` then `.\start_all.ps1` — cold boot should hit `/health` in <2 s. Run the simulator for 2 minutes before judges walk in, then `GET /api/live/audit?limit=3` is the receipt. The demo has exactly 10 beats — do not skip the offline toggle and the admin PIN. If the judge asks ‘IMD live?’ answer `IMD_API_KEY` gated → `GET /forecast/imd-live` with provenance, else Open-Meteo blend — never claim a live IMD panel without a key.”

**Evidence:** `docs/sih26001/06_DEMO_SCENARIO_SIH26001.md:41` (10-step script) · `scripts/local_sensor_sim.py:1` (`--interval 30`, `runs/live_feed.json`) · `backend/app/main.py:234` (`/health`) · `backend/app/main.py:1248` (`/live/feed fallback`) · `backend/app/main.py:1308` (`/live/audit`) · `frontend/src/components/Header/LocationSelector.jsx:1` · `frontend/public/manifest.webmanifest:1` · `start_all.ps1:1`

---

## Slide 27: Roadmap — WILL BE ADDED (Honest Future, Not Hand-Waving)

**Title:** What WILL Be Added — Cloud, Panchayat, People, Proofs

**Bullets:**
- **Dense gauges + 10-min SWI:** district AWS/ARG gauges (10-min) + probe soil (0–1 volumetric) → NGEN fetch `sensor` adapter (already designed `02 §5.1`, `03 §A`) → `swi_for_zone` with observed sub-daily + forecast blend + per-corridor isotonic reweight (needs ≥200 dated/corridor)
- **LiDAR + BigGIS tiling:** post-monsoon LiDAR depth + repeated Sentinel wound tiling at Gram Panchayat scale (12 slopes → Panchayat tiling via NGEN expansion) — terrain TWI/SPI at 5 m + wound review queue automation (sister-wall vet)
- **Panchayat-scale NGEN + GSI tiling:** expand `feature_matrix.training.csv 2936 → Panchayat polygons` with same 17 feats + local thresholds calibration `0.9*old+0.1*event_effective` per `warning_thresholds.json` method; per-corridor isotonic after ≥200 dated/corridor
- **CB bearer + PostGIS cloud:** Cell Broadcast bearer integration (CB honestly FUTURE per `FEATURE_CELL_BROADCAST_OFFLINE.md`), SMS gateway env-gated → push → CB; `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) **PostGIS 16-3.4** (`POSTGRES_DB talus` + `pg_isready` health + `api` `DATABASE_URL postgres://…` + `AUTO_ALERT_*` + `IMD_API_KEY` + volume `runs:/app/runs`); CDN map tiles + `frontend/dist` via api static, cloud sync offline queue server-wins

**Visual cue:** Roadmap swimlane: Now (3 corridors, PWA, fixture topology, 0.9338) → Next (N sensors, 10-min SWI) → Later (LiDAR, Panchayat, per-corridor calib) → Cloud (PostGIS, CB, CDN).

**Speaker note (55s):** “Every ‘WILL BE’ has an adapter already in code — sensor fetch, per-corridor thresholds, per-corridor calibration hooks, PostGIS compose. We do not claim CB today — we say bearer is future, env-gated SMS is today. When judges push ‘scale?’, answer 12→Panchayat tiling with same 17-feature contract — no new schema until an ADR says so. Quote deployment appendix: cloud is config, not rewrite (`docs/CURRENT_SYSTEM.md:67` Cloud row, `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md)).”

**Evidence:** `docs/sih26001/02_ARCHITECTURE_SIH26001.md:191` (sensor adapter §5.1) · `docs/sih26001/03_DATA_PLAN_SIH26001.md:84` (sensor feeds) · `docs/sih26001/08_LIMITATIONS_SIH26001.md:9` (Panchayat gap) · `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) (PostGIS 16-3.4) · `docs/FEATURE_CELL_BROADCAST_OFFLINE.md:1` (CB honest)

---

## Slide 28: Impact — Connectivity, Lives, Hours Saved (Taiwan Honest Wording)

**Title:** Impact We Can Claim vs Impact We Will Measure

**Bullets:**
- **Connectivity (honest, now):** Deterministic **R2 avoidance** `RISK_WEIGHT 3.0 α 0.2` + **R4 isolation detection** (`_isolation_for_location`) + **pre-emptive restriction catalogue** per segment (historical 12/8/5/3) + risk-aware `S1→S4 89→66` → valley truck avoids ridge road before closure → **hours saved vs hours lost** ledger via replay (when did warning first reach ALERT/CRITICAL vs when red alert actually issued Jun 13)
- **Lives (honest analog, not claim):** Taiwan ARDSWC analogue — location-specific effective rain + quake-conditioned thresholds + SWI + BigGIS + action-oriented Yellow/Red kits (what/why/rain/shelters/phones) + cell broadcast is how Taiwan cut debris-flow casualties — **TALUS copies the operational pattern, not the outcome**; add “isolated-village prioritization” (exposure `buildings + wound + isolation`) to resource triage (S2 with 85 buildings + wound > S1 alone)
- **Hours saved (measured in replay):** Mangan lead: **High Jun 10 → Critical Jun 12 → Critical Jun 13** vs IMD red alert Jun 13; Dipudara **7-day precursor High** (precursor evac saved 0 casualties We claim `lead days vs alert date` per `replay_series` + `early_episode`, not mortality prediction
- **What we won’t claim:** replacement of GSI RLFS, InSAR validation, production accuracy at field prevalence, Gram Panchayat maps today — say before asked (`08_LIMITATIONS:1` 13 limits)

**Visual cue:** 3 metric cards: Connectivity (hours vs alert), Analog (Taiwan checkmarks), Lead-time ledger (Mangan timeline 61.9→79.7→84.6→93.2). Footnote “Physics-informed, evidence-driven — TW-validated pattern, NER-provenanced.” Bottom disclaimer strip “Prototype operational bands, not safety standards.”

**Speaker note (60s):** “The honest impact sentence is: ‘TALUS copies Taiwan’s strongest operational ideas — local thresholds, SWI, BigGIS, pre-emptive roads, action kits — then adds the isolation + wound intelligence we built, and we measure lead time on committed replay, not on synthetic slides.’ Dipudara’s zero casualties happened because people evacuated on precursor slides — TALUS would have been High for 7 days. Mangan’s red alert came the same day as the slide — TALUS was Critical the night before. We show the ledger, we don’t claim lives we haven’t earned.”

**Evidence:** `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:94` (positioning) · `data/sih26001/evidence/replay_series.json:397` (Mangan Jun 10 79.7) · `data/sih26001/evidence/replay_series.json:442` (Dipudara 7-day High) · `docs/sih26001/08_LIMITATIONS_SIH26001.md:6` (not claiming RLFS replacement etc) · `frontend/src/components/Replay/ReplayCard.jsx:1`

---

## Slide 29: Benchmarks vs TW / JP / HK / TH — Where We Beat the Global, Where We Don’t

**Title:** Benchmark Honesty — Best Single XGB 0.9418, Not an Ensemble Claim

**Bullets:**
- **NER published spectrum:** Dibang XGB **0.96** → TALUS best XGB **0.9418 just below** (honest gap, not ensemble-inflated); Meghalaya ensemble **>90% acc** → TALUS **82–84% acc@0.5 below** (honest gap); Monga `E=-11.10+0.62D` / Dahal `>144 mm/day` rendered as scenario templates `monga-mdl/dahal-144` (`forecast.json:1`) — screen `frac_pos ≥144 0.1907` is climatology, not intensity validation (`metrics.md:39`)
- **Global benchmark:** NASA LHASA 2.0 (global) vs NER XGB **0.9418 — NER-specific beats global over NER (expected); LHASA doubles as fallback prior for sparse pixels — blend, don’t hide** (`04_MODEL_PLAN:54`)
- **Table (from research §7, now shipped):**

| Capability | Taiwan ARDSWC | Japan JMA/MLIT | Hong Kong GEO | Thailand? | TALUS (now) |
|---|---|---|---|---|---|
| Terrain susceptibility | Yes | Yes | Yes | Yes | **Yes (17 feats, 22 cols)** |
| Rainfall triggering (obs) | Yes (local) | Yes | Yes (rain gauges) | Yes | **Yes (IMD 0.25° truth)** |
| Live rainfall blend | Strong | Strong | Strong | Yes | **Yes (Open-Meteo 7d, IMD_API_KEY gated)** |
| Antecedent / SWI 3-tank | Yes | **Strong (JMA)** | Yes | Limited | **Yes (L1=15 L2=60 L3=60, tanh)** |
| Local thresholds | Strong | Strong | Strong | Regional | **Yes (per-zone 385–420, quake 25%)** |
| Earthquake conditioning | Explicit | Yes | Relevant | Relevant | **Yes (USGS 26, per-zone)** |
| Satellite + BigGIS wound | Strong | Strong | Growing | Growing | **Yes (Sentinel pair, wound 0/1)** |
| Road risk + closures | **Strong** | **Strong** | Strong | Important | **Yes (1014/226/504 proven, R4 bottleneck)** |
| Exposure / runout | Yes | Yes | Yes | Yes | **Yes (screening, capped 400)** |
| Field + community | Strong | Strong | Strong | Strong | **Yes (EXIF+SHA256, verified queue)** |
| Multilingual + offline | Relevant | Relevant | Relevant | Critical | **Yes (en/hi/ne/as/bn + PWA)** |
| Cell broadcast | Yes | Yes | Yes | Limited | **Future (SMS today, CB honest future)** |
| AI/ML + explainability | Increasing | Increasing | Increasing | Growing | **Core (RF+XGB+LGBM+TreeSHAP)** |

- **Net:** We beat the global baseline where it matters (local NER data, road-aware), we trail the best NER academic ensemble by ~2 pp — shipped openly.

**Visual cue:** Table with checkmarks + amber gaps (Meghalaya acc). Bottom: “No ensemble shipped — best single XGB 0.9418 wins.” + “LHASA fallback prior kept” chip.

**Speaker note (60s):** “We are not 0.96 — say so first. Dibang paper’s 0.96 came from an ensemble over one basin; our 0.9418 is best-single XGB over Sikkim+Darjeeling hills via GroupKFold(8) — that gap is honest and explainable (basin vs 3 corridors, seasonality vs daily). LHASA is global and coarse — we beat it over NER, but we keep it as a fallback prior for sparse pixels instead of hiding it. That honesty is what GSI respects. If pushed ‘why not ensemble?’, say ‘talk’s cheap, Brier is cheap — ensemble added 0.003 AUC but hid calibration; we shipped best single.’”

**Evidence:** `ml/sih26001/reports/metrics.md:9` (0.9418) · `ml/sih26001/reports/benchmarks.md:1` · `docs/sih26001/04_MODEL_PLAN_SIH26001.md:48` (targets table 0.96/0.9418) · `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:110` (capability comparison table) · `ml/sih26001/reports/metrics.md:39` (threshold screen)

---

## Slide 30: Team + Q&A — The Lines You Will Not Say

**Title:** Team — Who Built What + Trap Phrases That Lose the Finals

**Bullets:**
- **Team lane ownership (say who owns what):** NGEN + data ingest (Member: terrain/SW soil/Satellite) → Model Research/Member2 (RF+XGB, GroupKFold8, Brier, TreeSHAP) → GIS & Routing (RiskMap/Roads/Isolation/SWI) → Field & Alerts (ReportModal/PWA/AlertPanel/auto-watcher) → PM/Cloud & Demo (PostGIS, simulators, QR)
- **Never say:** “Nobody models roads” (TW/JP disprove) · “Nobody does earthquake memory” (TW disproves) · “Our model is 0.99” (leakage) · “Real-time InSAR / live Bhukosh lithology / live CB today” (we tag PROXY & CB future honestly) · “Score 89 predicts a landslide tomorrow” (score is susceptibility 0–100, field `confidence_real_1pct` is Bayes 1%) · stale “RF 0.8983”
- **Say instead:** “Recent anthropogenic disturbance as time-varying wound layer” · “Seismic history as persistent conditioning + 25% threshold drop” · “Pre-emptive restriction catalogue (Japan-validated) + deterministic R4 isolation” · “Observed IMD truth vs Open-Meteo live — explicitly separated, forecast never silently mixed” · “Scoring frozen, warning overlays via SWI/isolations” · “Per-zone thresholds + quake conditioning, provenance-logged”
- **Hard Q&A swaps:** BHUKOSH: “WFS timeout 15s both 2025-11-14, logged in `bhukosh_vector_attempt.json`; lithology uniform `lingtse_granite_gneiss` omitted from X, not hidden” · OSM: “Counts 1014/226/504 prove presence, R1–R4 fixture keeps R2 determinism, full traces available on demand” · IMD LIVE: “Requires `IMD_API_KEY`; else Open-Meteo blend + IMD historical truth, labeled — never silent fake” · 0.25°: “Misses hyperlocal bursts — we say so, SWI mitigates, not fixes” · 12 SLOPES ≠ PANCHAYAT: `08_LIMITATIONS §9` roadmap

**Visual cue:** Team photo grid with lane pills. Right: 2-column “Never say / Say instead” red/emerald cards. Bottom: `GET /health` QR + `docs/sih26001/08_LIMITATIONS_SIH26001.md:6` “Say before asked” strip.

**Speaker note (60s + Q&A setup):** “Close with lane ownership — judges remember who to drill. Rehearse the four worst traps out loud with the evidence file open on the second screen — don’t wing them. When unsure, don’t defend — show the JSON: open `roads_osm_provenance.json`, `bhukosh_vector_attempt.json`, `warning_thresholds.json`, `replay_series.json causality`. The brand close is research phrasing: ‘We don’t just map the mountain. We map where people are changing it.’ Then QR for their phone — map first, provenance second, limits third.”

**Evidence:** `docs/sih26001/TEAM_TASKS_SEPT5.md:1` · `docs/SIH26001_RESEARCH.md:94` (phrasing) · `docs/sih26001/08_LIMITATIONS_SIH26001.md:1` (13 limits) · `data/sih26001/evidence/bhukosh_vector_attempt.json:1` · `data/sih26001/evidence/roads_osm_provenance.json:1` · `ml/sih26001/reports/metrics.md:9`

---

## Appendix — API Checklist + File Map + Validators Green (Give to Judges)

**Title:** Appendix — All 13 FRs in One Table, Plus the 35/35 Proof

**Bullets:**
- **API checklist (13 FRs → endpoints, all reachable offline except live gated blend):**
  `GET /health` · `GET /api/zones?location=` · `GET /zones/{id}` · `GET /zones/{id}/features|trend|explanation|decision|history|exposure` · `GET /api/live/feed|audit` · `GET /forecast/rainfall|live|imd-live` · `GET /soil/swi` · `GET /warning/state` + `GET /model/calib?pi_real=0.01` · `GET /isolation` · `GET /roads/status?location=` · `GET /roads/restrictions` · `POST /routes/safe` · `POST /risk/predict` · `POST /simulation/what-if` + `causal-what-if` · `GET /simulation/templates` · `GET /replay/series` · `GET /runout/exposure` + `GET /wounds` · `POST /reports` + `GET/queue?status=` + `PATCH /reports/{id}` · `POST /alerts/dispatch?channel=app|sms` + `GET /dispatch/log` + `POST/GET /alerts/ack` + `GET/POST /alerts/auto/*`

- **File map (where truth lives, single source bolded):**
  `**docs/CURRENT_SYSTEM.md:1** single source wins` · `data/sih26001/fixtures/feature_matrix.sample.csv:1` (12×22) · `data/sih26001/processed/feature_matrix.training.csv` (2936×22) + `.training.sample.csv` 20 rows · `data/sih26001/evidence/{warning_thresholds,roads_osm_provenance,bhukosh_vector_attempt,usgs_quakes,wound_map,runout_exposure,replay_series,road_restriction_catalogue}.json:1` · `ml/models/sih26001_{rf,xgb,lgb,iso}_v1.joblib` (git-ignored, sha256 in `manifest.training.json:144`) · `ml/sih26001/reports/{metrics,calibration,benchmarks,physics}.md` · `backend/app/{main.py:1,si h26001_model.py:1,swi.py:14,data.py:1,model_service.py:1}` · `frontend/{RiskMap,WarningStateCard,IsolationAlertCard,RoadStatusCard,RiskTrendChart,AlertPanel,ReportModal,QuickStatsBar}` · `frontend/public/{sw.js:1,manifest.webmanifest:1}` + `frontend/src/services/reports.js:1` · `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) PostGIS ` · `runs/{live_feed.json,alert_dispatch.jsonl,sim_audit.jsonl}`

- **Validators green + tests 35/35:**
  `python scripts/check_scaffold.py` → `SCAFFOLD OK` (frozen S1 89/S2 78/S3 66/S4 52, bands, roles, R2 avoided, en/hi/ne, monga-mdl/dahal-144, 22-col feature order) · `python scripts/validate_ngen_sample.py` → `NGEN OK` (22 cols, 17 numeric, 0 STUBs) — per `data.py:308` live/fixture; `pytest backend/tests/` **35/35 tests green** — `test_api.py` · `test_warning_state.py` · `test_wounds.py` · `test_runout_exposure.py` · `test_reports.py` (15 field) · `test_alerts_ack.py` · `test_live_feed.py` · `test_multiloc_routes_roads.py` · `test_causal.py` (all location-aware)

- **Give-away QR sheet:** `/health` + `/api/zones?location=gangtok` + `/api/warning/state?location=gangtok` + `/api/isolation?location=gangtok` + `/admin` PIN 9999 (printed, not projected) — proves live vs fixture honesty, not just slides

**Visual cue:** Checklist ticked green + file-tree snippet + `SCAFFOLD OK / NGEN OK` badges + `35/35` pytest badge + QR strip (4 QRs).

**Speaker note (30s + handover):** “Leave this slide up during Q&A — it is the answer map. If a judge asks ‘prove offline without Wi-Fi?’, point at the sw.js row and the outbox sync badge. If they ask ‘where is PS (e)?’ point at `/roads/status` + `/isolation` + `POST /routes/safe`. If they ask ‘show me calibrated, not claimed?’, open `calibration.md:8` and `GET /model/calib?pi_real=0.01` — p_real formula lives there. Keep `check_scaffold.py` terminal open — run it live if they look skeptical.”

**Evidence:** `docs/CURRENT_SYSTEM.md:22` (API 35/35) · `scripts/check_scaffold.py:1` (SCAFFOLD OK) · `scripts/validate_ngen_sample.py:1` (NGEN OK) · `backend/tests/test_reports.py:1` (15) · `backend/app/main.py:234` (`/health` checks) · `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md:1` (frozen contract) · `docs/sih26001/NGEN_VALIDATOR.md:1`

---

## Build Notes for the Deck Designer (not a slide)

- **Colors:** `#0b1220` theme + `RiskMap` bands Very Low `#5e7f3a` … Critical `#c74732` (match `RISK_BANDS`). **Visual cue** specs use `RiskMap.jsx:129` `getZoneFillColor`. Keep `R2 at-risk #d97706 dashed 5,5` verbatim.
- **Fonts:** headline `Space Grotesk` or `Spline Sans` + body `Inter` is fine — research deck used Manrope; anything legible beats anything generic. Roundness `ROUND_EIGHT` max.
- **Maps:** use `RiskMap` Leaflet polygons directly — do NOT redraw with Google MyMaps. Basemap OSM `tile.openstreetmap.org` (no key). Attribute `© OpenStreetMap & CARTO` per `RiskMap.jsx:168`.
- **Photos:** NER hills, NH-310A, 2024 clippings — no stock AI hills. Wind effect: wound NDVI scar, not AI.
- **No UI slop:** no pastel gradient blobs, no 3 floating cards with generic shadows, no “AI-powered revolution” header. Every visual must trace to an evidence file in this md.
- **Export:** Deck + this md + `data/sih26001/evidence/*.json` in a `docs/` handout on the judge table print — judges keep the appendix.

## Voice & Trap Phrases (for rehearsal, not the deck)

- **Taiwan analog opener:** “Taiwan ARDSWC is the closest overall analog — terrain, rainfall, roads, disaster needs. We copied its strongest ideas: static+trigger split, per-zone effective rain thresholds post-quake 25%, SWI tank model, BigGIS wound, pre-emptive road restrictions, what/why/shelters/phones kits + cell broadcast intent. Then we added isolation R4 + wound-as-feature.”
- **Minus-one honesty line:** “We are RF 0.9338 / XGB 0.9418, not 0.96 — ensemble would add little and hide calibration; best single ships.”
- **Road line:** “Road risk is not our novelty — Taiwan/Japan already close roads. Our novelty is recent anthropogenic disturbance as a time-varying layer plus R4 bottleneck isolation that turns road status into village isolation status in one graph step.”
- **Sensor line:** “Sensor adapter exists today, fixture-proven at `GET /api/live/feed` — live gauges swap the parser, not the schema.”
- **Cloud line:** “Cloud is config, not rewrite — `docker-compose.prod.yml` (postgis:16-3.4) PostGIS 16-3.4 + api healthcheck + `runs:/app/runs` volume already prove it.”

## Evidence Index (grep this for any claim you will defend)

- IMD 0.25° historical truth `data/raw/imd/ind2024_rfp25.nc` → `docs/imd_netcdf_inspection.md` + `docs/sih26001/03_DATA_PLAN_SIH26001.md:15`
- Open-Meteo 7-day live `backend/app/main.py:1111` + cache `backend/app/main.py:1103` + `/forecast/live:1154` + IMD gated `backend/app/main.py:1124`
- CCI v09.2 7.5 GB `data/raw/soil/v09.2/` CDS `docs/SOIL_DATA_FETCH_GUIDE.md` + `manifest.sample.json:22` 0.271 + `docs/sih26001/03_DATA_PLAN_SIH26001.md:24`
- SRTM n27_e088 1arc `data/sih26001/processed/cache_dem_grid.npz` + `docs/sih26001/NGEN_PROVENANCE_S1.md:10` + `docs/sih26001/03_DATA_PLAN_SIH26001.md:31`
- GSI 30k `GSI_Landslide_Inventory.shp.zip` + report 904pp `docs/sih26001/03_DATA_PLAN_SIH26001.md:54` + `manifest.training.json:42` 764
- USGS 26 M5+ `data/sih26001/evidence/usgs_quakes.json:1` + `_seismic_lookup` `backend/app/sih26001_model.py:1`
- Sentinel2 pair `data/sih26001/evidence/wound_map.json:1` + `docs/sih26001/03_DATA_PLAN_SIH26001.md:39` + `s234_ndvi.json:1`
- WorldCover N27E087 `s234_lulc.json:1` + `manifest.sample.json:1`
- OSM 1014/226/504 `data/sih26001/evidence/roads_osm_provenance.json:1` + demo topology `backend/app/data.py:118` + hazard graph `backend/app/main.py:496`
- Bhukosh timeout `data/sih26001/evidence/bhukosh_vector_attempt.json:1` PROXY
- Training 2936 `data/sih26001/processed/feature_matrix.training.csv` + manifests `manifest.training.json:144` + sample 20 rows
- Metrics GroupKFold8 `ml/sih26001/reports/metrics.md:9` + temporal 673/73 `ml/sih26001/reports/metrics.md:32` + Brier `ml/sih26001/reports/calibration.md:8`
- Bayes `docs/RECALIBRATION_NOTE.md:1` + `backend/app/main.py:1221` `confidence_real_1pct`
- SWI `backend/app/swi.py:14` + `backend/app/main.py:1203` `GET /soil/swi`
- Isolation `backend/app/main.py:1326` + `frontend/src/components/Alerts/IsolationAlertCard.jsx:1` + `docs/FEATURE_ISOLATION.md`
- Warning `backend/app/main.py:1449` + `data/sih26001/evidence/warning_thresholds.json:1` (385/395/410/375)
- Road catalogue `data/sih26001/evidence/road_restriction_catalogue.json:1` + `backend/app/main.py:798`
- Exposure `backend/app/main.py:743` + `frontend/src/components/Routing/ExposureCard.jsx`
- Wound `data/sih26001/evidence/wound_as_feature.json:1` 4/2936 + `data/sih26001/evidence/wound_map.json:1`
- Trend `frontend/src/components/ZoneDetails/RiskTrendChart.jsx:86` NOW + `backend/app/main.py:379`
- Replay `data/sih26001/evidence/replay_series.json:1` 5×31d causality `frontend/src/components/Replay/ReplayCard.jsx`
- Reports `frontend/src/components/Reports/ReportModal.jsx:1` + `frontend/src/services/reports.js:1` + `backend/app/main.py:879`
- Alerts `frontend/src/components/Alerts/AlertPanel.jsx:1` + `backend/app/main.py:86` (en/hi/ne/as/bn) + `backend/app/main.py:959` + `backend/app/main.py:1702` auto watcher
- Offline `frontend/public/sw.js:1` + `frontend/public/manifest.webmanifest:1` + `frontend/src/services/reports.js:1` outbox + `frontend/src/components/RiskSummary/QuickStatsBar.jsx:1` LIVE
- Benchmarks `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:110` + `ml/sih26001/reports/metrics.md:9`
- Team & traps `docs/sih26001/TEAM_TASKS_SEPT5.md:1` + `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:94`
- Scaffold/validators `scripts/check_scaffold.py:1` + `scripts/validate_ngen_sample.py:1` + `backend/tests/` 35/35

## Single-Source Contract (who wins when docs conflict)

`docs/CURRENT_SYSTEM.md` wins over every other PPT or ml doc when numbers conflict (e.g., 0.8983 vs 0.9338 — 0.9338 wins; Brier 0.118 raw vs 0.0971 isotonic wins as labeled). This file is the deck implementation of that contract.

---

*Generated for SIH26001 finals — deep dive, not summary. Build from here, rehearse from `docs/sih26001/06_DEMO_SCENARIO_SIH26001.md:41` 10-step, prove with `scripts/check_scaffold.py` + `python -m pytest -q` 35/35 before stage.*
