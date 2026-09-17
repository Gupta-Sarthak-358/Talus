# TALUS Demo Scenario — SIH26001 (live — frozen 2025-11-15)

**Status:** Live demo + training + live-blend frozen · **Trace to:** `01_REQUIREMENTS_SIH26001.md`

(Replaces nothing yet. v1 demo `docs/06_DEMO_SCENARIO.md` stays frozen for the mine track.)

---

## Pilot extent (frozen)

Gangtok pilot `27.3389/88.6065` `27.315–27.345N/88.595–88.612E` `NGEN_PROVENANCE_S1.md:10` + Lachung Valley `27.69/88.74` + Darjeeling hills `27.041/88.263` (`locations.json:1` 12 demo slopes) — Sikkim per research §3.2 (best-dated + best tile `n27_e088`). All screens below run on frozen scaffold scores `S1 89 S2 78 S3 66 S4 52` (`slopes.json:1`, live RF when `ml/models/sih26001_*v1.joblib` present else fixture fallback `data.py:308` `live_scores`) + `2936×22` training backing `metrics.md:9` OOF RF 0.9338 XGB 0.9418 + OSM 1014/226/504 `roads_osm_provenance.json:1` + SWI `swi.py:14` + warning 6-state + isolation R4 bottleneck.

## Screen 1 — NER overview (live)

GIS 5-band heatmap (`RiskMap` Leaflet) on 3 corridors (Gangtok/Lachung/Darjeeling selector). Pilot units `S1 89 Critical S2 78 High S3 66 Moderate S4 52 Low` `slopes.json:1` + per-corridor clones (`slopes.lachung.json`/`slopes.darjeeling.json`). Road overlay `R1 blocked R2 at-risk R3/R4 open` `roads.json:1` demo topology (counts 1014/226/504 proven, geometry centroid-aligned for R2 determinism). Village priority flags via `decisions` + **WarningStateCard 6-state** corridor badge + **IsolationAlertCard** OPEN/MAY_ISOLATE/ISOLATED + observed vs forecast provenance footnote (IMD 0.25° truth vs Open-Meteo live `GET /api/forecast/live:1154` / IMD gated `GET /api/forecast/imd-live:1124` + fixture fallback `GET /api/forecast/rainfall`).

## Screen 2 — "Why?" + Exposure (live)

TreeSHAP panel: `S1 distance_to_road 12.5 rainfall_7d 9.0 slope 7.5 soil 5.0` `slopes.json:1` (or live `sih26001_model.py:explain_row` top-4 when weights present) + `shap_sample` 5-pt `manifest.training.json:shap_sample` `metrics.md:51` `elevation/road/ndvi` top. New: **ExposureCard** `GET /api/zones/{id}/exposure:743` operational risk `score* (1+0.18*log1p(buildings)/3 +0.12 wound +0.20 isolated)` + runout path `GET /api/runout/exposure` + wound detail `GET /api/wounds` + `GET /api/panchayat/tiles` (100) + `GET /api/terrain/copernicus` + `GET /api/aws/gauges` + `GET /api/db/status` + `POST /api/alerts/cbe``.

## Screen 3 — ML what-if (live, labeled counterfactual)

`POST /api/simulation/what-if:567` `S3 66→74 delta 8` `forecast.json:1` `ml_whatif_demo` with caveat badge (off-manifold). Frontend `WhatIfDrawer` + `SimulationDiffCard` shows `baseline/simulated` + `flagged` if needed. Live path `data.py:apply_overrides` requires model; scaffold path `_fixture_what_if:1737` serves frozen demo for S-zones.

## Screen 4 — Causal what-if + SWI (live)

`POST /api/simulation/causal-what-if:629` threshold replay `Monga E=-11.10+0.62D` `monga-mdl` + `Dahal >144` `dahal-144` `forecast.json:1` → SWI saturation trajectory `backend/app/swi.py:14` + `GET /api/soil/swi:1203` JMA 3-tank blend `swi_for_zone(rain7,rain30,forecast3)` `tanh(SWI/100)` (physical causes, not SHAP) + `GET /api/model/calib:1221` Bayesian recalibration card `0.5→0.01`.

## Screen 5 — Roads + Routing + Isolation (live)

`S1→S4` shortest via `R2 at-risk` vs risk-aware via `R3/R4` `roads.json:1` `avoided_segments ["R2"]`, `max_risk_exposed 89→66` `backend/app/main.py:421`. Selector `RoadStatusCard` per `GET /api/roads/status:832` + `GET /api/roads/restrictions:798` catalogue evaluation. New: **Isolation engine** `GET /api/isolation:1441` `_isolation_for_location:1326` — R4 bottleneck (`R4 blocked ⇒ S1/S2/S3 isolated`), `may_isolate` predictive (one at-risk road left + High/Critical), action string rendered in header and admin. **WarningStateCard** 6 states `GET /api/warning/state:1449` may override corridor to RESTRICT/EVACUATE when isolation fires. Auto watcher `POST /api/alerts/auto/trigger:1728` can fire a demo isolation alert now.

## Screen 6 — Field report + alert + offline PWA (LIVE: geo-tagged, officer review, outbox, SW)

* **Submit:** ReportModal / Screen 6 field app → `POST /api/reports:879` with validated `ReportIn`: `zone_id` S1–S4+N1–N4+D1–D4 (12, frozen), `type` crack | slope_movement | blocked_road | other, `text` 10–500, `lat/lon` inside pilot bbox 27.20–27.40 / 88.40–88.70 (rejected outside), `captured_at` ISO (future >1h rejected), `reporter_role` villager | field_officer, `photo` metadata-only `{filename,mime,size_bytes,sha256,exif_lat,exif_lon}` (no binary in repo per contract §4 + `.gitignore:46`; bytes never committed, SHA256 + EXIF GPS read client-side), `consent: true` required. EXIF vs claimed >200m → `flagged` with reason; bad mime → `flagged`; text/type/zone validation → 422; per-boot rate cap 20 (demo guard).
* **Queue:** `GET /api/reports/queue:932` (`?status=queued|verified|dismissed|flagged`) renders OfficerQueue (newest first, status pills + flagged reason) + Leaflet markers (click → popup with details + status). Fixture `data/sih26001/fixtures/reports.json` ships one `REP-001` (S2 crack, photo meta with SHA256 + matching EXIF, consent true). Background photo cache `talus_report_photos`.
* **Review:** `PATCH /api/reports/{id}:942` `{status: verified|dismissed|flagged, reviewer_role, reason}` — only `queued|flagged → verified|dismissed|flagged`; `verified|dismissed` terminal (409 on re-transition). Demo role via PIN switcher (real auth post-hackathon per limitations §8).
* **Offline outbox (FR-12 demo beat, now PWA):** pending reports in `localStorage talus_report_outbox` `frontend/src/services/reports.js:1` auto-retry on `online` + manual "Sync now"; `public/sw.js:1` cache-first shell (`CACHE talus-shell-v1`, `/api` network-only) + `public/manifest.webmanifest:1` (icons 192/512 maskable) so app shell works offline — header/queue sync badge (`synced ✓ / N pending`) is the offline proof.
* **Candidate label linkage — honesty-critical:** `verified` does NOT auto-flip `event`/`previous_landslide` (same rule as inventory joins — no invented dates). Verified reports append to a `candidate_labels` sidecar (in-review JSON, git-ignored or fixture-capped) with `crowd-verified` + officer ID + photo SHA256, surfaced in missing-evidence/provenance UI. `event=1` still requires a dated, in-window occurrence. `POST /api/alerts/ack:1076` real ack record also demonstrated.
* **Alerts lane:** `POST /api/alerts/dispatch:959` fixture broadcast `en/hi/ne` `alerts.json:1` or `?channel=sms` env-gated (`SMS_PROVIDER`/`SMS_API_KEY`/`SMS_TO`, otherwise SIMULATED logged `alert_dispatch.jsonl:1051`), log `GET /api/alerts/dispatch/log:1062`. Auto watcher `_auto_watcher_loop:1702` fires on isolation (60s interval, 3600s cooldown, `AUTO_ALERT_ENABLED/SMS`, `GET /api/alerts/auto/status:1721`).
* **Rehearsal script (exact):** (1) submit S2 crack report live → appears in queue + map marker, (2) queue filter `?status=queued` shows it, (3) toggle offline → submit → pending badge `1 pending` + app shell still renders via sw.js, (4) reconnect → auto-sync → `synced ✓`, (5) officer verify `PATCH → verified`, (6) dispatch alert fixture with 3-language preview (`en/hi/ne`) + admin log, (7) break R4 (`R4 blocked`) → `GET /api/isolation` shows S1–S3 ISOLATED, `GET /api/warning/state` corridor EVACUATE, (8) `POST /api/alerts/auto/trigger` fires isolation auto-alert, (9) drag history slider `GET /api/zones/{id}/history:379` → RiskTrendChart NOW, (10) `GET /api/forecast/live` shows observed vs forecast split + IMD gated provenance.

## Screen 7 — History slider NOW (built)

`GET /api/zones/{id}/history:379` `seed 91` 365-day `daily_history` `model_service.py:daily_history` + `RiskTrendChart` slider positions NOW on the trajectory (not session prediction logs). Evidence timeline `scenario_service.py:64` feeds the drawer.

## Screen 8 — Admin observability (built, PIN-gated)

`/admin` (`AdminPage.jsx:1`) — **villagers never see this**. Officers see actions; villagers see only danger/safe + map. Admin panel shows: `GET /health:234` store/live_scores checks, `GET /api/isolation:1441` bottleneck, `GET /api/alerts/dispatch/log:1062` multilingual dispatch ledger, `GET /api/reports/queue` triage, `roads_osm_provenance.json:1` counts 1014/226/504, Brier/calibration, warning thresholds, OSM truth vs demo topology disclosure. PINs: `auth.js:1` 9999 admin /1111 district /2222 state /3333 rescue (localStorage `talus_auth`, `DEMO_PINS`).

## Rehearsal checklist (frozen 2025-11-15)

- [x] Pilot 3 corridors + fixtures reproduce deterministically (12 slopes, 35/35 tests)
- [x] Scores/confidence match calibrated artifact (RF 0.9338 XGB 0.9418 Brier 0.0971, `confidence_real_1pct` documented)
- [x] TreeSHAP values match live model artifact (top-4, `sih26001_model.py:explain_row`)
- [x] Off-manifold caveat spoken before Screen 3 (flagged badge)
- [x] Threshold preset + SWI divergence numbers reproduce (Monga/Dahal + SWI 0.40 + local 385/395/410/375)
- [x] Routing avoids documented R2 segment; isolation via R4 bottleneck demonstrated; may_isolate pre-alert spoken
- [x] Observed vs forecast split explained (IMD truth vs Open-Meteo blend + IMD_API_KEY gated)
- [x] No silent stale OSM geometry — counts 1014/226/504 stated, demo topology disclosed
- [x] Offline PWA proof: sw.js shell + outbox → `1 pending` → `synced ✓`
- [x] Isolation auto-alert trigger demonstrated (`/api/alerts/auto/trigger`)
- [x] History slider NOW demonstrated
- [x] Admin panel `/admin` PIN triage + limitations slide ready (see `08_LIMITATIONS_SIH26001.md`)

## PS (a)–(g) traceability checklist (frozen)

| PS bullet | Covered in | Demo screen |
|---|---|---|
| (a) multi-source data (rain CCI, soil SWI, satellite WorldCover/Sentinel-2, terrain SRTM, history GSI/USGS) | NGEN + FR-01 + 03_DATA_PLAN A/B | Screen 1 provenance footnote + live/IMD blend + admin OSM counts |
| (b) AI/ML high-risk prediction | FR-02/03/04 + 04_MODEL_PLAN | Screens 1–2 + 4 calib |
| (c) real-time alerts to admins + communities | FR-11 (+ FR-06 roles, auto watcher 60s) | Screen 6 fixture + isolation auto + log |
| (d) GIS mapping of roads, villages, infrastructure + isolation | FR-07/09 | Screens 1, 5 (RiskMap + RoadStatus + IsolationAlert + WarningState + Exposure) |
| (e) geo-tagged citizen/field uploads + review + ack | FR-10 + FR-11 ack | Screen 6 queue + PATCH + ack |
| (f) dashboards: severity, roads, weather forecast (observed vs forecast), emergency priority + history | FR-09 + FR-13 NOW | Screens 1, 5, 7, 8 admin |
| (g) multilingual + offline PWA | FR-12 en/hi/ne/as/bn + sw.js 192/512 | Screen 6 (4 languages, sw.js + outbox sync) |
| Expected Solution: IMD/satellite/sensor integration | Sensor adapter (02 §5, 03 §A) + live blend | Screen 1 + §8 limit (IMD live needs key) |
| Expected Solution: cloud + PostGIS + offline sync | Cloud path (02 §5, docker-compose.prod.yml (postgis:16-3.4, https://talus-sih26001.onrender.com/health via docs/LIVE_HOST_EVIDENCE.md):1 PostGIS) + PWA | Architecture + admin health, not live flood-scale |

## Explicitly NOT claimed (carry into the frozen version)

- Scores are not probability of a specific landslide; confidence is calibrated P(elevated susceptibility) under season-window target; field 1% view is Bayes `confidence_real_1pct`, not the 0–100 score.
- No in-situ sensors were used; deployment needs partner feeds (CCI is satellite-observed, still 0.25° cell; SWI is rainfall-derived).
- Bands are prototype operational bands, not safety standards.
- OSM road geometry is demo topology (counts 1014/226/504 honestly proven, traces not E2E).
- 12 demo slopes ≠ Gram Panchayat-scale mapping.
