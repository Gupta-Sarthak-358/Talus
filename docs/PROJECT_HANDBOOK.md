# TALUS PROJECT HANDBOOK — SIH26001 NER (MDoNER, Disaster Management)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Status: 2025-11-15 · Single source of truth for SIH26001. If any other doc conflicts, this one wins on current-state claims. Historical Neyveli docs are archives, not specs.**

---

## 1. What TALUS Is (30 sec)

TALUS is a **risk-aware decision-support system for NER landslides**, built for SIH26001 (Team Sangyan, MDoNER). It converts fragmented NER signals — IMD rainfall, CCI soil moisture, SRTM DEM derivatives, Sentinel-2 NDVI / WorldCover LULC, OSM roads, USGS quakes, GSI health — into a slope-level susceptibility **0–100 + calibrated confidence + missing_evidence**, explains *why* via **real TreeSHAP**, tracks escalation via **warning state**, checks **isolation**, routes **risk-aware**, and runs **what-if** + field reporting.

**Differentiation:** Detect → Understand → Escalate → Decide → Act. Not just prediction — the decision layer around it. Multilingual (en/hi/ne/as/bn) + offline-first + officer-grade actions.

**Philosophy:** *ML scores the observed present. Physics-inspired overlays (SWI, effective rain, wound, forecast, quake) escalate the warning — scoring stays frozen.*

---

## 2. The Two Layers (most important fact)

```text
SCORING LAYER (frozen, honest fallback)
  NGEN row (17 numeric + lulc) -> sih26001_model.py Sih26001Live
  14 base + 3 seismic-memory (+ spi_log) -> encoder -> RF predict_proba -> isotonic
  -> score 0-100 + confidence (p_cal) + confidence_real_1pct (Bayes 0.5→0.01)
  -> band Very Low/Low/Moderate/High/Critical -> TreeSHAP top-4

WARNING LAYER (overlay, never mutates score)
  effective_rain (r7+0.3*r30, per-zone 375-420) + SWI 3-tank (L1=15 L2=60 L3=60)
  + wound (NDVI drop) + Open-Meteo forecast + quake -25% + trend + isolation
  -> warning NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE (reason-stamped kit)
```

Never feed fake sensors into scoring. Live NGEN only; absent weights → frozen fixture scores from `slopes.json` (never invented).

---

## 3. Data Provenance (know what is REAL)

| Class | Items | Source / File |
|---|---|---|
| **Real / observed** | IMD 0.25° daily 1901–2024 gridded (ind*_rfp25.nc); SRTM 30m n27_e088_1arc_v3.tif (GLO-30); CCI soil v09.2 1978-2024; OSM highway ways (Overpass, 1014 Gangtok inc NH310A, 226 Lachung, 504 Darjeeling); USGS 26 M5+ <50km (usgs_quakes.json); Sentinel-2 L2A 2023-11-15/2024-11-29 (2 scars) | `data/sih26001/evidence/` |
| **Published / PROXY** | GSI lithology/lineament published map (uniform → omitted from X, honestly tagged PROXY-published-map; Bhukosh WFS timeout), NDVI/WorldCover LULC | `feature_matrix.sample.csv` REAL/PROXY col, zero STUBs |
| **Derived** | 17 NGEN features (slope, elevation, aspect, curvature, TWI, SPI log1p, rain 24h/7d/30d, soil, NDVI, dist road/river, drain density + seismic x3) + SWI tank model + effective rain + runout steepest-descent | `ml/sih26001`, `backend/app/swi.py`, `data.py` |
| **Synthetic / scenario** | Road R1-R4 demo topology (centroid-aligned for deterministic R2 avoidance), decision messages, fixture simulations | `roads.json`, `forecast.json` |

**Never claim:** live WFS lithology, traced OSM routing geometry, or landslide probability. Data disclaimer: *"Quasi-static proxies for time-varying inputs; tagged approximate; lithology lithology uniform PROXY."*

---

## 4. The Model (frozen, reproducible)

- **Training matrix:** 2936 rows (1468+1468) 2936×22 (1468 pos = Sikkim inventory 693 shp + 777 PDF → 764 deduped + Darjeeling-hills positives; 1468 neg = >300m background, seed 42). Columns: 17 numeric (17 numeric + lulc) + lulc one-hot + 2 keys.
- **Features:** `slope_angle, elevation, aspect, curvature, twi, spi_log, rainfall_24h_mm, rainfall_7d_mm, rainfall_30d_mm, soil_moisture, ndvi, distance_to_road, distance_to_river, drain_density` + `seismic_dist_km, seismic_n50_rate, seismic_years_since` (per-zone as-of-2024 from USGS). `lulc` categorical. `previous_landslide` excluded (LEAK +0.0531).
- **Training:** GroupKFold(8) spatial clusters (KMeans-8 on coords, seed 42) + temporal 673/73 dated holdout. RF 500 trees + XGB 400 + LGBM 400 + isotonic. Reports: `ml/sih26001/reports/metrics.md`.
- **OOF (current):** RF 0.9338 (Brier 0.118 ECE 0.1153), XGB 0.9418 (0.1198/0.0957), LGBM 0.9406. Temporal RF test 0.8568 (Brier 0.0978). **Do not quote stale numbers — GroupKFold above is current.**
- **Calibration:** isotonic Brier 0.0971 vs raw 0.118 (OOF). Confidence = calibrated P(elevated susceptibility).
- **Recalibration (RECALIBRATION_NOTE.md):** Bayes prevalence correction `p_real = p_cal*0.02/(p_cal*0.02+(1-p_cal)*1.98)` for field base rate ~1%. Score frozen; adds `confidence_real_1pct`. SWI overlays warning state only.
- **Live scoring:** `backend/app/sih26001_model.py` — encoder + RF + isotonic → `{score, confidence, confidence_real_1pct, band, raw_proba}`; se `sih26001_model.get_live()`. Missing weights / row invalid → None → fixture fallback, `live_scores` false (honest).
- **Explainability:** `explain_row(top_k=4)` via `shap.TreeExplainer` — `base_value` + sorted `contributions` (fallback: fixture SHAP from `slopes.json`).

---

## 5. Warning State & Isolation (RESEARCH:22/47/50/43)

**6 states:** NORMAL → WATCH → ALERT → CRITICAL → RESTRICT → EVACUATE (ordered `_WARN_STATES` in `main.py`).

Per zone: start from band (Low=0, Moderate=1, High=2, Critical=3), then reason-stamp:

- Effective rain `r7 + 0.3*r30 ≥ local threshold (warning_thresholds.json: Gangtok S1 385 S2 395 S3 410 S4 375, Lachung N1 380 N2 390 N3 405 N4 370, Darjeeling D1 400 D2 410 D3 420 D4 390)` — Monga 390 separator, scores unchanged.
- Heavy 7d ≥150 / building ≥80 (quake-conditioned ×0.75).
- SWI (swi.py 3-tank) ≥0.40 → bump one level (tank S1=15 S2=60 S3=60, a/b per JMA Okada 1992).
- Wound nearby BigGIS (<0.008° of zone), forecast exceedance Open-Meteo (≥50 today or ≥150/7d from `_LIVE_CACHE`), trend `rapidly_increasing`, quake window (M5.5 <50km within 180d → thresholds 25% threshold drop, RESEARCH:28).
- Isolation overlay: R4 blocked → upstream isolated → EVACUATE; at-risk RESTRICT. Bumps max +1.

**Isolation:** `GET /api/isolation` — R4 is downstream bottleneck to plains; R1/R2→S1, R3→S3, R4→S4. Returns `corridor_isolated / corridor_may_isolate`, per-zone `ISOLATED/MAY_ISOLATE/OPEN`, reasons, `action`.

---

## 6. The GIS & Corridors

- **Corridors:** Gangtok S1-S4 (27.3389,88.6065), Lachung N1-N4 (+0.35,+0.135), Darjeeling D1-D4 (-0.298,-0.337) — locations.js / data.py shifts match. `docs/PILOT_REVIEW.md`.
- **DEM:** SRTM 30m `n27_e088_1arc_v3.tif`; derived TWI/SPI/curvature etc. CCI soil v09.2 (quasi-static proxy until in-situ), NDVI Sentinel-2, WorldCover LULC.
- **Wound:** `wound_map.json` — 2 candidates (S1/R2 Δ0.457, S3/R3 Δ0.436) from matched Nov scenes, REVIEW QUEUE not confirmed cuts.
- **Runout:** `runout_exposure.json` — steepest-descent screening + buildings/road meters (approximation, labeled).
- **OSM:** Proven 1014/226/504 ways (roads_osm_provenance.json, trunk NH310A id 47416074) — geometry demo, count is proof.

---

## 7. API (FastAPI, backend/app/main.py — 35/35 tests)

| Group | Endpoint | Notes |
|---|---|---|
| Health | `GET /health` | store:gangtok live_scores + fixtures ok; `GET /` shows frozen ML version |
| Zones | `GET /api/zones` / `GET /api/zones/{id}/explanation (TreeSHAP)` / `GET /api/zones/{id}/exposure` / `features` / `trend` / `history?seed=91` / `decision?lang=` | TreeSHAP live or fixture; decisions FR-06 roles × 5 langs |
| Warning | `GET /api/warning/state?location=&lang=` | 6 states, reasons + kit (what/why/rain/shelters/phones/villager_explain) |
| Isolation | `GET /api/isolation?location=` | deterministic bottleneck logic |
| Soil | `GET /api/soil/swi?location=` | 3-tank per zone, forecast blend |
| Roads | `GET /api/roads/status?location=` `GET /api/roads/restrictions?location=` | catalogue + evaluation (emergency_route guard) |
| Forecast | `GET /api/forecast/live?location=` (Open-Meteo, 1h cache) `GET /api/forecast/imd-live?location=` (IMD_API_KEY gated → fallback) `GET /api/forecast/rainfall` (fixture thresholds monga-mdl/dahal-144) | never 500s when key absent |
| Alerts | `POST /api/alerts/dispatch?channel=app|sms&lang=&zone_id=&message=` `GET /api/alerts/dispatch/log` `POST /api/alerts/ack` `GET /api/alerts/ack` | sms via msg91/fast2sms/twilio/textbelt (env SMS_PROVIDER+SMS_API_KEY+SMS_TO), every dispatch logged to `runs/alert_dispatch.jsonl` (no fake success) |
| Auto | `GET /api/alerts/auto/status` `POST /api/alerts/auto/trigger?location=` | watcher `AUTO_ALERT_ENABLED` (default true), interval 60s, cooldown 3600s, AUTO_ALERT_SMS gate |
| Reports | `POST /api/reports` `GET /api/reports/queue?status=` `PATCH /api/reports/{id}` | EXIF/mime flagging, consent required, rate cap 20 |
| Live | `GET /api/live/feed` `GET /api/live/audit?limit=` | simulator wins, sample fallback |
| Evidence | `GET /api/replay/series` `GET /api/runout/exposure` `GET /api/wounds` `GET /api/model/calib?pi_real=0.01` | committed bundles |
| Routing/Sim | `POST /api/routes/safe` `POST /api/simulation/what-if` `POST /api/simulation/causal-what-if` `GET /api/simulation/templates` `POST /api/risk/predict` | R2 always closed to risk-aware routing |

---

## 8. Frontend Dashboard

**Launch:**
```powershell
powershell -ExecutionPolicy Bypass -File .\start_all.ps1   # :8000 + :5173
# or: cd backend; uvicorn app.main:app --reload   +   cd frontend; npm run dev
# live-only (no mock): VITE_API_URL=http://localhost:8000/api
```

**Map & cards:**
- `RiskMap.jsx` — Leaflet, 5-band heatmap via `RISK_BANDS`, roads colored by status, hazard glow markers, live sensor pins (from `/api/live/feed`, labeled SIMULATED), runout dashed red, wound icons.
- `WarningStateCard.jsx` — corridor_state badge + per-zone STATE_STYLE (6 colors) + reasons + action priority.
- `IsolationAlertCard.jsx` — isolated vs may-isolate banner, bottleneck string, action route.
- `RiskTrendChart.jsx` — Recharts line (thresholds 75/85, NOW vertical, OBSERVED◀ vs FORECAST▶), causality footer.
- `RoadStatusCard.jsx` — R1-R4 grid (blocked/at-risk/open), R2 avoidance note.
- `QuickStatsBar` — rainfall + LIVE forecast badge (sky pill).
- `AlertPanel.jsx` — 5-lang toggle (en/hi/ne/as/bn), app/sms channel toggle, dispatch + log tail, queued badge.
- `RiskScoreGauge.jsx` — villager words vs officer % + certainty bar.
- `AdminPanel` at `/admin` (`AdminPage.jsx`) — health/isolation/log/queue/provenance (PIN gate 9999/1111/2222/3333).
- `RoleSelector.jsx` + `LoginModal.jsx` via `services/auth.js` — PINS `villager open, 1111, 2222, 3333, 9999 admin`; `talus_auth` persisted; Admin can open all.

---

## 9. Offline & Cloud

- **PWA:** `frontend/public/sw.js` (cache-first shell `/, /index.html, favicon, manifest, icons`, `/api` network-only, cache `talus-shell-v1`) + `manifest.webmanifest` (theme #0b1220, icons 192/512 maskable). Installable on judge phone via laptop URL.
- **Outbox:** `services/reports.js` — failed report queued to `localStorage talus_report_outbox` (+ thumbnail via `talus_report_photo_bg`), flushed on refresh.
- **Docker:** `Dockerfile` multi-stage (python:3.11 slim + node:20 build), gdal/geos, `HEALTHCHECK curl /health`, `EXPOSE 8000`. `docker-compose.yml` (api + optional sim profile) + `docker-compose.prod.yml` (postgis 16-3.4, DATABASE_URL). See `docs/DEPLOY_CLOUD.md` — file-backed when DATABASE_URL absent (honest fallback).
- **Live host:** Render/Fly/AWS via `docs/DEPLOY_CLOUD.md`; env `CORS_ORIGINS, DATABASE_URL, AUTO_ALERT_*, SMS_*, IMD_API_KEY`.

---

## 10. Demo Script (5 min, deterministic)

1. Map: Gangtok S1–S4 heatmap + R1 blocked / R2 at-risk (propose EVIDENCE: 1014 OSM ways, geometry demo).
2. Click S1 → Score + Confidence + TreeSHAP top-4 + missing_evidence.
3. WarningStateCard: note effective rain 390 local + SWI 0.40 + wound → reason stamps.
4. IsolationAlertCard: R4 bottleneck → S1 may_isolate pre-alert.
5. QuickStatsBar LIVE badge + RiskTrendChart NOW line (observed vs forecast separation).
6. AlertPanel: switch hi/ne/as/bn + toggle sms (env-gated) → check Admin log.
7. Report flow: field report → queue flagged/verified on /admin.

Close with methodology: GroupKFold(8) spatial, recalibration Bayes 0.5→0.01, OSM proven geometry.

---

## 11. Known Limitations (say BEFORE judges find them)

1. Bhukosh WFS timeout → lithology uniform PROXY-published-map (omitted from X) — documented, not hidden.
2. OSM geometry demo topology (deterministic R2 avoidance); count 1014/226/504 is the proof.
3. IMD live needs IMD_API_KEY; otherwise IMD-live → Open-Meteo fallback (labeled).
4. CCI soil quasi-static proxy; SWI overlays warning only.
5. Inventory 764 deduped, 1991-2020 climatology tagged approximate, lithology uniform.
6. SHAP explains the model, not the slope; bands are prototype thresholds; final decisions with qualified personnel.
7. 672/764 undated positives still use climatology for time-varying features.

---

## 12. Panel Q&A (ready answers)

**"Is your data real?"** → "IMD 0.25° 1901-2024, SRTM 30m, CCI v09.2, OSM 1014/226/504 ways, USGS 26 quakes, Sentinel-2 — all committed evidence. Lithology is published-map PROXY (uniform, excluded), soil quasi-static until sensors. NGEN rows are REAL/PROXY-tagged, zero STUBs."

**"Where does 68 come from?"** → "Live RF raw_proba→score, grouped-8 OOF 0.9338. Bands from FoS-derived thresholds, not learned. Confidence is isotonic P(elevated susceptibility), Bayes-corrected to ~1% field rate for the judge view."

**"Why not IMD live everywhere?"** → "Data.gov.in needs a key and has rate limits. We gate on IMD_API_KEY and always keep the labeled Open-Meteo fallback so the demo never 500s. Historical truth is the committed IMD netCDF."

**"Are roads real?"** → "Presence is real (Overpass counts proved), geometry is demo centroid chain to keep R2 avoidance deterministic and teachable. Full OSM traces available — we chose pedagogy over prettiness."

**"Production need?"** → "Mining/DM partner sensor feed (rain/soil real-time), WFS restore or field lithology, ≥200 dated positives/corridor for per-region recalibration, DGMS-certified thresholds, JWT auth for admin."

---

## 13. Repository Map

```text
ml/sih26001/            reports/metrics.md, calibration.md, models (rf+iso joblib)
data/sih26001/fixtures/ feature_matrix.sample.csv / slopes*.json / roads/forecast/alerts/live_feed.sample
data/sih26001/evidence/ roads_osm_provenance.json, warning_thresholds.json, wound/runout/replay/usgs_quakes
backend/app/            main.py (35/35), data.py, sih26001_model.py, swi.py, model_service.py
frontend/src/           RiskMap.jsx, WarningStateCard.jsx, IsolationAlertCard.jsx, RiskTrendChart.jsx,
                        AlertPanel.jsx, AdminPage.jsx, services/auth.js, TalusContext.jsx
frontend/public/        sw.js + manifest.webmanifest + icons 192/512
docs/                   CURRENT_SYSTEM, RECALIBRATION_NOTE, DEPLOY_CLOUD, PRESENTATION_EVIDENCE
```

*Every number here is from committed code or evidence. If you can't reproduce it, treat it as wrong and check.*