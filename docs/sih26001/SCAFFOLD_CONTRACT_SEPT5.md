# TALUS Sept-5 Scaffold Contract (frozen — 2025-11-15 truth)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


**Branch:** `SIH26001 @ 68c0c28` (former `feature/sih26001/demo-scaffold` @ `a1debe1` merged) · **Base:** `SIH26001 @ a1debe1` → `68c0c28`
**Pilot (frozen for demo):** Gangtok cluster Sikkim — 4 slopes S1–S4 frozen 89/78/66/52 + corridor extensions Darjeeling D1–D4 + Lachung N1–N4 (12 rows total) — centres `27.3389,88.6065` / `27.041,88.263` / `27.69,88.74` CRS EPSG:4326 (NGEN reprojection deferred).
**Rule:** demo runs offline on fixtures; live IMD/Open-Meteo appear as best-effort gated blend with 1 h cache, fixtures remain fallback (per `02 §5`).

This file is the **only contract** frontend/backend/data code against until Sept 5. If it is not here, do not build it.

---

## 1. IDs (frozen — do not rename)

| Slope | Village (display) | Lat | Lon | Band (frozen) | Score |
|---|---|---|---|---|---|
| S1 | Tathangchen (upper) | 27.3450 | 88.6000 | Critical | 89 |
| S2 | Chandmari (road-cut) | 27.3380 | 88.6120 | High | 78 |
| S3 | Tadong (mid) | 27.3250 | 88.6065 | Moderate | 66 |
| S4 | Ranipool (valley) | 27.3150 | 88.5950 | Low | 52 |

Extensions (same schema, not frozen 89/78/66/52): `slopes.darjeeling.json` D1 27.047,88.263 / D2 27.040,88.275 / D3 27.027,88.2695 / D4 27.017,88.258 ; `slopes.lachung.json` N1 27.695,88.735 / N2 27.688,88.747 / N3 27.678,88.7415 / N4 27.665,88.730 . All 12 in `feature_matrix.sample.csv` 22 cols, 17 numeric+lulc, `evidence_quality` dated-only-negative/approximate, **0 STUBs** (`validate_ngen_sample.py` OK).

Files (all committed, small):

```text
data/sih26001/fixtures/slopes.json ← 89/78/66/52 frozen SHAP/confidence + missing_evidence
data/sih26001/fixtures/slopes.darjeeling.json ← D1–D4 coords/scores
data/sih26001/fixtures/slopes.lachung.json ← N1–N4 coords/scores
data/sih26001/fixtures/roads.json ← road graph demo topology + status + safe vs shortest (R2 avoidance)
data/sih26001/fixtures/reports.json ← 1 officer-queue field report
data/sih26001/fixtures/alerts.json ← multilingual fixture (EN/HI/NE/AS/BN)
data/sih26001/fixtures/forecast.json ← IMD fixture + Monga/Dahal presets
data/sih26001/fixtures/feature_matrix.sample.csv ← 12-row NGEN sample (S1–S4+D1–D4+N1–N4, 22 cols 17 numeric+lulc)
data/sih26001/fixtures/feature_matrix.training.sample.csv ← 20-row training sample
data/sih26001/fixtures/manifest.sample.json ← NGEN manifest (IMD/CCI/SRTM/WorldCover/OSM 1014/226/504/seismic 26)
data/sih26001/evidence/warning_thresholds.json ← per-zone local thresholds S1 385 etc
data/sih26001/evidence/roads_osm_provenance.json ← counts 1014/226/504 proven
data/sih26001/evidence/bhukosh_vector_attempt.json ← WFS/WMS timeout 15s proof
```

Validators: `python scripts/check_scaffold.py` → **SCAFFOLD OK 17-feature, frozen 89/78/66/52, R2 avoidance (RISK_WEIGHT 3.0 alpha 0.2)** and `python scripts/validate_ngen_sample.py` → **NGEN SAMPLE OK 22 cols 12 rows no FILL** — both green before merge.

Frozen constants: `backend/app/main.py:49` **RISK_WEIGHT 3.0** + `main.py:53` **ROUTING_ALPHA 0.2** (`data.py:207` `1+weight*exposure/100` on hazard graph, `routing/comparison.py:compare_routes`). Scoring frozen `score=round(raw_proba*100)` (`sih26001_model.py:score_row`).

---

## 2. API shapes (v1-compatible — backend keeps paths)

Backend serves fixtures at these paths. Frontend codes to these paths only.

```text
GET /health · GET /
GET /api/zones?location=gangtok|lachung|darjeeling → { zones: [{zone_id, risk_score, risk_band, confidence, confidence_real_1pct, trend}] }
GET /api/zones/{id} → { zone_id, name, geometry{lat,lon}, risk_score, risk_band, confidence, trend, updated_at }
GET /api/zones/{id}/features → { zone_id, features{17 numeric+lulc}, missing_features[] }
GET /api/zones/{id}/explanation → { zone_id, risk_score, base_value, contributions[{feature, shap}] } (TreeSHAP top-4 live or fixture)
GET /api/zones/{id}/decision → { zone_id, risk_score, risk_band, decisions[{role, message, action, priority}] }
GET /api/zones/{id}/trend → { zone_id, rapid_increase:bool, history[{t, risk_score}] }
GET /api/zones/{id}/history → { daily_history 365d slider NOW }
GET /api/zones/{id}/exposure → { hazard, exposure{runout, buildings 85 max S2, wound, isolation}, operational_risk }
POST /api/risk/predict → { zone_id, risk_score, risk_band, confidence, missing_evidence[] }
POST /api/simulation/what-if → { zone_id, baseline{}, simulated{}, delta, contributions[] } (ML counterfactual, caveat)
GET /api/simulation/templates → { templates: [{id:"monga-mdl", ...}, {id:"dahal-144", ...}] }
POST /api/simulation/causal-what-if → { zone_id, divergence_fos, escalated_units[], timeline[] } (threshold replay)
GET /api/forecast/rainfall → { source:"IMD-fixture", daily_mm[], preset_ref:"monga-mdl" } (fixture)
GET /api/forecast/live?location= → { source:"Open-Meteo", daily[{date,precip_mm,prob_max_pct}], provenance } (7d, 1h cache main.py:1154)
GET /api/forecast/imd-live?location= → { source:"IMD data.gov.in"+Open-Meteo blend, gated by IMD_API_KEY } (main.py:1124)
GET /api/soil/swi?location= → { swi_model:"JMA 3-tank L1=15 L2=60 L3=60 a1=0.10...", zones[{zone_id, swi, soil_moisture}] } (swi.py:14)
GET /api/warning/state?location= → { corridor_state: NORMAL…EVACUATE, corridor_zone, states[{zone_id, state, reasons[], kit{what/why/shelters/phones}}], isolation } (6-state, thresholds warning_thresholds.json:1 S1 385 S2 395 S3 410 S4 375)
GET /api/isolation?location= → { corridor_isolated, may_isolate, isolated_zones, zones[{zone_id, status, reason}], action } (R4 bottleneck main.py:1326)
GET /api/roads/status?location= → { segments: [{id, status: open|at-risk|blocked, adjacent_slope}] } (per-corridor shifted R1–R4)
GET /api/roads/restrictions?location= → { catalogue, evaluation[] }
POST /api/routes/safe {start,end,location} → { risk_aware_route{path, total_cost, max_risk_exposed}, shortest_route{}, avoided_zones[] } (R2 deterministically avoided, alpha 0.2)
GET /api/runout/exposure → { zones[{path, length_m, drop_m, buildings_n, road_m}] } (screening, S2 85 buildings max)
GET /api/wounds → { corridors{gangtok:{candidates:[{lat/lon/seg, ndvi_pre/post, drop}]}, lachung:0, darjeeling:0} } (2 scars vet queue)
GET /api/live/feed → { feed, served_from } + GET /api/live/audit + GET /api/replay/series
POST /api/reports → ReportOut (ReportIn: zone_id/type/text/lat/lon/captured_at/reporter_role/photo{sha256,exif}+consent → queued|flagged; 422 bbox/consent/type) (15 tests)
GET /api/reports/queue?status=queued|verified|dismissed|flagged (LIVE)
PATCH /api/reports/{id} → {status: verified|dismissed|flagged} (terminal guard 409)
POST /api/alerts/dispatch?channel=app|sms&lang=en → { queued: n, languages: ["en","hi","ne"], fixture: true } + log
GET /api/alerts/dispatch/log + POST /api/alerts/ack + GET /api/alerts/ack + GET /api/alerts/auto/status + POST /api/alerts/auto/trigger
GET /api/model/calib?pi_real=0.01 → { formula:"p_real=...", note }
```

Roles (frozen strings — `DECISIONS_BY_BAND` keys Critical/High/Moderate):

```text
villager | district_officer | state_manager | rescue_team
```

Bands (frozen edges for demo): <50 Very Low, 50–64 Low, 65–74 Moderate, 75–84 High, 85+ Critical.

Training backing (not in fixtures, git-ignored): 2936 rows 1468+1468 GroupKFold8 RF 0.9338 XGB 0.9418 Brier isotonic 0.0971 `metrics.md:9` `calibration.md:8`. IMD 0.25° 1901-2024 + CCI v09.2 0.271 via `extract_soil_cci.py` + `lingtse_granite_gneiss` PROXY-published-map `bhukosh_vector_attempt.json` WFS timeout 15s + lineament 0.8 + DEM SRTM n27_e088 Horn-1981 TWI/SPI + Sentinel-2 S2B_45RXL 0.718/0.139/0.817/0.468 + WorldCover N27E087 76.7% + seismic 26 USGS M5+ + routing `routing/comparison.py` R2 avoidance `RISK_WEIGHT 3.0` `alpha 0.2`.

---

## 3. Demo click path (6 screens → PS trace, + history/admin)

| # | Screen | Click | PS |
|---|---|---|---|
| 1 | NER overview | map loads 3 corridors (S 89/78/66/52 + D/N), S1–S4 coloured, roads overlay R1–R4, isolation badge, warning 6-state badge, provenance footnote IMD 0.25° truth + CCI + WorldCover + OSM 1014/226/504 | (a)(b)(d)(f) |
| 2 | Why? + Exposure | click S1 → SHAP top-4 + missing_evidence + Exposure 85 buildings S2 + wound 2 scars | (b) |
| 3 | ML what-if | raise `rainfall_24h_mm` on S3, show delta + caveat badge | (b) |
| 4 | Causal + SWI | run `monga-mdl` preset, show saturation → S3→High + SWI 3-tank `swi.py:14` L1=15 L2=60 L3=60, `GET /api/soil/swi` | (b)(f) |
| 5 | Roads + routing + isolation | S1→S4: shortest crosses at-risk R2, safe avoids it (`RISK_WEIGHT 3.0 alpha 0.2` hazard graph) ; R4 blocked ⇒ S1/S2/S3 ISOLATED | (d)(f) |
| 6 | Report + alert + PWA | submit report → queue ; dispatch fixture → 3-language preview + sync badge + outbox `1 pending → synced ✓` via `sw.js` | (c)(e)(g) |
| 7 | History | drag 365d slider `GET /api/zones/{id}/history:379` → RiskTrendChart NOW | (f) |
| 8 | Admin | `/admin` PIN 9999/1111… shows Brier 0.0971, OSM counts, Bhukosh timeout, thresholds S1 385 | (f) |

Honesty lines (footer footnote): scores = susceptibility under prototype target, not P(landslide tomorrow); soil = CCI satellite-observed 0.271 + SWI physics overlay; sensor = fixture adapter; bands = prototype, not safety standard.

---

## 4. Merge rules (merger enforces)

* Only merger merges to `SIH26001`. Feature branches: `feature/sih26001/<name>`.
* Conventional commits. **Both validators green** (`check_scaffold.py` SCAFFOLD OK 17-feature + `validate_ngen_sample.py` NGEN SAMPLE OK) **and** `start_demo.ps1` boots before merge.
* Never commit: `docs/PILOT_BRIEFING.md`, raw datasets (`ind*.nc`, `SRTM`, `CCI` NCs), weights (`*.joblib` → git-ignored), `.env`/`IMD_API_KEY`.
* Fixture IDs/scores/bands/roles never change without updating this file + fixtures + validators in same PR. R2 avoidance (`RISK_WEIGHT 3.0` `alpha 0.2`) and `warning_thresholds.json` thresholds are part of frozen contract.