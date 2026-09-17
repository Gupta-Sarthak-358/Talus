# TALUS Limitations — SIH26001

**Status:** Built — frozen 2025-11-15 · **Source:** `docs/SIH26001_RESEARCH.md` §11.3–§11.4

## What we do NOT claim

- We are **not** replacing GSI RLFS — we complement it with AI/ML (observed rainfall truth remains IMD 0.25° 1901–2024; live is Open-Meteo blend, IMD gated).
- We are **not** doing real-time InSAR (requires hardware).
- We are **not** deploying IoT sensors (A-LEWS/AmritaWNA's domain) — CCI v09.2 + SWI is the satellite+physics proxy.
- We do **not** predict exact landslide locations/times — we predict susceptibility (season-window proxy tagged `approximate`).
- We do **not** predict flash floods — rainfall is a landslide-trigger proxy, not a hydrological flood model. Road blockages are covered as derived road-status + isolation (R4 bottleneck), not flood mapping.
- We do **not** claim field-validated production accuracy — this is a prototype with honest Brier/ECE and temporal holdout.
- We do **not** claim Gram Panchayat-scale mapping from 12 demo slopes.

## Honest limitations (say before asked — 2025-11-15 truth)

1. **Satellite CCI soil moisture 0.271 window-mean, not in-situ sensors** — resolution `0.25°` same-cell all slopes `manifest.sample.json:22` (flags 7/7 valid), limits at slope scale (cf. Marino et al. 2020). `CCI v09.2` stronger than `ERA5` but still quasi-static; **SWI 3-tank** `backend/app/swi.py:14` (L1=15 L2=60 L3=60 a1=0.10 b1=0.12) blends rainfall + forecast to mitigate, but warning layer only — scoring stays frozen `raw_proba*100`.
2. **Inventory incompleteness** — season-window positives tagged `approximate`; `673/73 dated` (`manifest.training.json:144` n=807) temporal anchor honest but undated majority remains. `previous_landslide` omitted from X leakage (`positives ARE` slides). Candidate sidecar `reports.json:1` is the mitigation, not a fix.
3. **Static model core** — conditioning factors don't change in demo; only rainfall + soil + NDVI (quasi-static `S2B_45RXL_20241129` `s234_ndvi.json:1`) are dynamic time-varying inputs. `lithology`/`lineament` uniform `0.8` `lingtse_granite_gneiss` omitted from `X` `manifest.training.json:263` — **Bhukosh PROXY-published-map** (`bhukosh_vector_attempt.json:1` WFS/WMS timeout 15s both 2025-11-14) is logged, not hidden. Re-run `--wfs` when vector reachable.
4. **OSM rural gaps + demo topology** — `1014` Gangtok / `226` Lachung / `504` Darjeeling Overpass counts `evidence/roads_osm_provenance.json:1` example 47416074 NH310A trunk prove presence, but **R1–R4 geometry is centroid-aligned deterministic** for pedagogical R2 avoidance + R4 isolation (`data.py:118` `GRAPH`, `main.py:496` `_road_graphs_for` hazard graph drops R2). `osm-qa-unverified` kept. Full OSM traces available on demand (Darjeeling 504 required 429/504 backoff, Lachung 226 sparse Himalayan network not missing data).
5. **No live sensor integration** in the prototype — adapter fixture + `live_feed.sample.json` → `GET /api/live/feed:1248` (simulator `runs/live_feed.json` wins, sample fallback). Live scores require `ml/models/sih26001_*v1.joblib` (git-ignored); fresh clone falls back to scaffold 89/78/66/52 honestly (`data.py:308` `live_scores`).
6. **IMD live rainfall requires subscription** — `GET /api/forecast/imd-live:1124` tries `api.data.gov.in` when `IMD_API_KEY` set, else falls back to `GET /api/forecast/live:1154` Open-Meteo blend (1h cache, 7-day). Historical truth stays `ind2024_rfp25.nc` fixtures `GET /api/forecast/rainfall`. No silent fake live.
7. **IMD grid coarseness** (~27 km) misses hyperlocal cloudbursts — same-cell `27.25/88.50` `manifest.training.json:30` all Sikkim `1991-2020` climatology proxy `rainfall_30d 390-712` `metrics.md:39` is screening, not intensity validation. Forecast exceedance thresholds 50mm day /150mm week are prototype bands, not safety standards.
8. **Wound / runout are screening approximations** — `wound_map.json:1` 4 candidates review-queue (roadside NDVI loss ≥0.3 ≤150m road, SCL-gated, 10–20m pixels miss narrow cuts, seasonal clearing or missed cloud may false-positive); `runout_exposure.json:1` steepest-descent on SRTM 30m steps, stop <5°/1.8km, exposure fetch capped 400/zone undercounts dense towns, schematic geometry may run 200m+ off-slope — all labeled as such in bundle method notes and via `GET /api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe`` / `GET /api/runout/exposure:1276`.
9. **Demo-geography ≠ NER-wide** — 12 demo slopes (S1–S4 Gangtok + N1–N4 Lachung + D1–D4 Darjeeling, `locations.json:1`) are frozen fixtures, not Gram Panchayat-scale mapping. Full NER tiling is roadmap, not MVP — say proactively.
10. **12-slope scaffold is honest, not operational** — `slopes.json:1` S1 89 S2 78 S3 66 S4 52 are frozen demo truths; live RF `sih26001_model.py:score_row` may shift them when weights present. Bands are prototype operational bands, not safety standards — `calibrated Brier 0.0971` same-OOF optimism `calibration.md:8`, clean check temporal `Brier 0.0978` `metrics.md:32`; field field rate ~1% view is `confidence_real_1pct` Bayes, not the 0–100 score.
11. **Multilingual NER coverage needs community co-design** beyond the pilot matrix `en/hi/ne/as/bn` `main.py:86`; villagers see only danger/safe + map, admin observability is intentionally hidden from field view.
12. **Auth is demo-PIN, not real RBAC** — `frontend/src/services/auth.js:1` PINS 9999/1111/2222/3333 localStorage `talus_auth`; real JWT is post-hackathon.
13. **Stale numbers must never be quoted** — Do not cite RF OOF 0.8983 / XGB 0.9029 / Brier 0.118 / temporal 0.8189 (Sept 4 frozen). Current truth is **RF 0.9338 XGB 0.9418 Brier 0.0971 (isotonic) / temporal AUC 0.8568 Brier 0.0978** `metrics.md:9` `calibration.md:8` `metrics.md:32` (2025-11-15). Previous 0.8983 is expunged here.
14. **E-ladder findings bound the headline 0.93** — hard-negative stress 0.7804, corrected pooled 0.8950, matched pooled 0.8478 (`EXPERIMENTS_E_LADDER.md`). Southern-background debt corrected in the experiment lane (E1.5b +1114, E1.5c +540 northern top-up); prod matrix/scores untouched. Open debts: Darjeeling has zero dated ≥2019 positives (temporal evaluation impossible there); southern calibration rests on thin data; north pool road SMD −0.791 residual; `recent_disturbance` removed from X (4/2936 nonzero) pending rebuild as disturbance score.

## Field reporting — demo honesty (built, now PWA)

* Citizen/field reports are **unverified input** — `verified` status requires an officer `PATCH` review (`main.py:942`, demo role via PIN switcher; real auth + moderation are post-hackathon). Until verified, a report never promotes to a training `event` or a `previous_landslide` label — it lives in a candidate sidecar with `crowd-verified` + officer ID + photo SHA256. `POST /api/alerts/ack:1076` is the companion real ack record (`acks` in-memory), not a fake ledger.
* Photo/video **bytes are never committed** (metadata-only lane per contract §4 + `.gitignore:46`); only `{filename,mime,size_bytes,sha256,exif_lat,exif_lon}` is stored, with an explicit `consent: true` gate. EXIF vs claimed >200m is flagged; unsupported mime is flagged; per-boot rate cap 20 is a demo guard, not production moderation. Background thumbnail `talus_report_photos`.
* Offline outbox is `localStorage talus_report_outbox` `frontend/src/services/reports.js:1` + retry + sync badge **plus** `public/sw.js:1` `CACHE talus-shell-v1` app-shell cache (`/api` network-only) + `public/manifest.webmanifest:1` 192/512 maskable. Full background-sync + content moderation are post-hackathon, but the shell works offline.

## Carryover discipline from v1

- Confidence is calibrated P(elevated susceptibility) at 0.5 prevalence, never "probability of failure"; field 1% view is a separate `confidence_real_1pct` via Bayes `GET /api/model/calib:1221` formula `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)`.
- ML counterfactuals labeled counterfactual; causal claims via scenario engine only (`POST /api/simulation/what-if:567` vs `POST /causal-what-if:629`).
- Every score ships with missing evidence. A confident-looking number with hidden gaps is a bug, not a feature.
- Observed vs forecast always separated: IMD 0.25° truth (`ind2024_rfp25.nc`) vs Open-Meteo live blend vs IMD_API_KEY gated district API — never silently mixed.
- Yellow/Red kits (what/why/rain/shelters/phones + villager_explain) are the villager truth; admin panel (`/admin`) holds technical provenance (Brier, OSM counts, Bhukosh timeout, thresholds) hidden from field.

---

**2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched):**

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT
