# TALUS v2 Sept-5 Scaffold Contract (frozen for hackathon — built)

**Branch:** `SIH26001 @ 68c0c28` (former `feature/sih26001/demo-scaffold` @ `a1debe1` merged) · **Base:** `SIH26001 @ a1debe1` → `68c0c28`
**Pilot (frozen for demo):** Gangtok cluster, Sikkim — 4 slopes S1–S4.
Centre: 27.3389, 88.6065. CRS: EPSG:4326 for demo (NGEN reprojection deferred).
**Rule:** demo runs fully offline on these fixtures. No live network.
Live IMD / SMS / cloud appear as recorded fixtures only (per `02 §5`).

This file is the **only contract** frontend, backend, and data teams code
against until Sept 5. If it is not here, do not build it.

---

## 1. IDs (frozen — do not rename)

| Slope | Village (display) | Lat | Lon | Band (frozen) | Score |
|---|---|---|---|---|---|
| S1 | Tathangchen (upper) | 27.3450 | 88.6000 | Critical | 89 |
| S2 | Chandmari (road-cut) | 27.3380 | 88.6120 | High | 78 |
| S3 | Tadong (mid) | 27.3250 | 88.6065 | Moderate | 66 |
| S4 | Ranipool (valley) | 27.3150 | 88.5950 | Low | 52 |

Files (all committed, all small):

```text
data/sih26001/fixtures/slopes.json          ← scores, bands, confidence, SHAP, missing_evidence
data/sih26001/fixtures/roads.json           ← road graph + status + safe vs shortest route
data/sih26001/fixtures/reports.json         ← 1 officer-queue field report
data/sih26001/fixtures/alerts.json          ← multilingual alert fixture (EN/HI/NE)
data/sih26001/fixtures/forecast.json        ← IMD fixture + Monga threshold preset
data/sih26001/fixtures/feature_matrix.sample.csv  ← 4-row NGEN output format (17 feats)
data/sih26001/fixtures/manifest.sample.json ← NGEN manifest format
```

Validator: `python scripts/check_scaffold.py` — must pass before any merge.

---

## 2. API shapes (v1-compatible — backend keeps paths)

Backend serves fixtures at these paths. Frontend codes to these paths only.

```text
GET  /api/zones                          → { zones: [{zone_id, risk_score, risk_band, confidence, trend}] }
GET  /api/zones/{id}                     → { zone_id, name, geometry{lat,lon}, risk_score, risk_band, confidence, trend, updated_at }
GET  /api/zones/{id}/features            → { zone_id, features{17 NER}, missing_features[] }
GET  /api/zones/{id}/explanation         → { zone_id, risk_score, base_value, contributions[{feature, shap}] }
GET  /api/zones/{id}/decision            → { zone_id, risk_score, risk_band, decisions[{role, message, action, priority}] }
GET  /api/zones/{id}/trend               → { zone_id, rapid_increase:bool, history[{t, risk_score}] }
POST /api/risk/predict                   → { zone_id, risk_score, risk_band, confidence, missing_evidence[] }
POST /api/simulation/what-if             → { zone_id, baseline{}, simulated{}, delta, contributions[] } (ML counterfactual, with caveat)
GET  /api/simulation/templates           → { templates: [{id:"monga-mdl", ...}, {id:"dahal-144", ...}] }
POST /api/simulation/causal-what-if      → { zone_id, divergence_fos, escalated_units[], timeline[] } (threshold replay)
POST /api/routes/safe                    → { risk_aware_route{path, total_cost, max_risk_exposed}, shortest_route{}, avoided_zones[] }
GET  /api/roads/status                   → { segments: [{id, status: open|at-risk|blocked, adjacent_slope}] } (NEW, fixture)
POST /api/reports                        → ReportOut (ReportIn: zone_id/type/text/lat/lon/captured_at/reporter_role/photo{sha256,exif}+consent → queued|flagged; 422 on bbox/consent/type) (LIVE `main.py:471`, 15 tests)
GET  /api/reports/queue                  → { reports: [...] } `?status=queued|verified|dismissed|flagged` (LIVE)
PATCH /api/reports/{id}                 → {status: verified|dismissed|flagged} (LIVE, terminal guard 409)
POST /api/alerts/dispatch                → { queued: n, languages: ["en","hi","ne"], fixture: true } (LIVE)
GET  /api/forecast/rainfall              → { source:"IMD-fixture", daily_mm[], preset_ref:"monga-mdl" } (LIVE)
```

Roles (frozen strings — backend `DECISIONS_BY_BAND` keys stay Critical/High/Moderate):

```text
villager | district_officer | state_manager | rescue_team
```

Bands (frozen edges for demo): <50 Very Low, 50–64 Low, 65–74 Moderate, 75–84 High, 85+ Critical.

---

## 3. Demo click path (6 screens → PS trace)

| # | Screen | Click | PS |
|---|---|---|---|
| 1 | NER overview | map loads, S1-S4 coloured, roads overlay, provenance footnote | (a)(b)(d)(f) |
| 2 | Why? | click S1 → SHAP panel + missing_evidence | (b) |
| 3 | ML what-if | raise `rainfall_24h_mm` on S3, show delta + caveat badge | (b) |
| 4 | Causal threshold | run `monga-mdl` preset, show saturation → newly escalated S3→High | (b)(f) |
| 5 | Roads + routing | S1→S4: shortest crosses at-risk R2, safe route avoids it | (d)(f) |
| 6 | Report + alert | submit test report → appears in queue; dispatch fixture → 3-language preview + sync badge | (c)(e)(g) |

Honesty lines (say out loud, also in footer footnote):
scores = susceptibility under prototype target, not P(landslide tomorrow);
soil = reanalysis proxy; sensor = fixture; bands = prototype, not safety standard.

---

## 4. Merge rules (merger enforces)

* Only merger merges to `SIH26001`. Feature branches: `feature/sih26001/<name>`.
* Conventional commits. `python scripts/check_scaffold.py` green + `start_demo.ps1` boots before merge.
* Never commit: `docs/PILOT_BRIEFING.md`, datasets, weights, `.env`.
* Fixture IDs/scores/bands/roles never change without updating this file + fixtures + validator in the same PR.
