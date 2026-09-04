# TALUS v2 Demo Scenario — SIH26001 (live — frozen 2026-09-04)

**Status:** Live demo + training-backed — `SIH26001 @ 68c0c28` · **Trace to:**
`01_REQUIREMENTS_SIH26001.md`

(Replaces nothing yet. v1 demo `docs/06_DEMO_SCENARIO.md` stays frozen for
the mine track.)

---

## Pilot extent (frozen)

Gangtok pilot `27.3389/88.6065` `27.315-27.345N/88.595-88.612E` `NGEN_PROVENANCE_S1.md:10` — chosen per research §3.2 (best-dated Sikkim + best tile `n27_e088`). All screens below run on the frozen pilot + recorded fixtures (no live network) — scores `S1 89 S2 78 S3 66 S4 52` `slopes.json:1`, training `1528×22` backing `metrics.md:9`.

## Screen 1 — NER overview (live)

GIS heatmap, 5-band colors. Pilot units `S1 89 Critical S2 78 High S3 66 Moderate S4 52 Low` `slopes.json:1`. Road overlay `R1 blocked R2 at-risk R3/R4 open` `roads.json:1` `R2` avoided. Village priority flags via `decisions`.

## Screen 2 — "Why?" (live)

Tree SHAP panel: `S1 distance_to_road 12.5 rainfall_7d 9.0 slope 7.5 soil 5.0` `slopes.json:1` + `shap_sample` 5-pt `manifest.training.json:shap_sample` `metrics.md:51` `elevation/road/ndvi` top.

## Screen 3 — ML what-if (live)

`POST /api/simulation/what-if` `S3 66→74 delta 8` `forecast.json:1` `66→74` with caveat badge (off-manifold). Frontend `WhatIfDrawer` shows `baseline/simulated` + `flagged` if needed.

## Screen 4 — Causal what-if (live)

`POST /api/simulation/causal-what-if` threshold replay `Monga E=-11.10+0.62D` `monga-mdl` + `Dahal >144` `dahal-144` `forecast.json:1` → saturation trajectory `groundwater +15mm` `evidence_timeline` `scenario_service.py:64` (physical causes, not SHAP).

## Screen 5 — Roads + routing (live)

`S1→S4` shortest via `R2 at-risk` vs risk-aware via `R3/R4` `roads.json:1` `avoided_segments ["R2"]`, `max_risk_exposed 89→66` `backend/app/main.py:254`.

## Screen 6 — Field report + alert (LIVE: geo-tagged reporting, officer review, offline outbox)

*   **Submit:** ReportForm (Screen 6 / field app) → `POST /api/reports` with validated `ReportIn`:
    `zone_id` S1–S4 (frozen), `type` crack | slope_movement | blocked_road | other, `text` 10–500,
    `lat/lon` inside pilot bbox 27.20–27.40 / 88.40–88.70 (rejected outside), `captured_at` ISO (honest timestamp, future >1h rejected),
    `reporter_role` villager | field_officer, `photo` metadata-only `{filename,mime,size_bytes,sha256,exif_lat,exif_lon}` (no binary in repo per contract §4 + `.gitignore:46`; bytes never committed, SHA256 + EXIF GPS read client-side), `consent: true` required. EXIF vs claimed >200m → `flagged` with reason; bad mime → `flagged`; text/type/zone validation → 422; per-boot rate cap 20 (demo guard).
*   **Queue:** `GET /api/reports/queue` (`?status=queued|verified|dismissed|flagged`) renders OfficerQueue (newest first, status pills + flagged reason) + Leaflet markers (click → popup with details + status). Fixture `data/sih26001/fixtures/reports.json` ships one `REP-001` (S2 crack, photo meta with SHA256 + matching EXIF, consent true).
*   **Review:** `PATCH /api/reports/{id}` `{status: verified|dismissed|flagged, reviewer_role, reason}` — only `queued|flagged → verified|dismissed|flagged`; `verified|dismissed` are terminal (409 on re-transition). Demo header `reviewer_role` is role-toggle only (real auth post-hackathon per limitations).
*   **Offline outbox (FR-12 demo beat):** pending reports in `localStorage talus_report_outbox` (frontend, no service worker per `08_LIMITATIONS:6` — out of scope) — auto-retry on `online` + manual "Sync now"; header/queue sync badge (`synced ✓ / N pending`) is the offline proof.
*   **Candidate label linkage — honesty-critical:** `verified` does NOT auto-flip `event`/`previous_landslide` (same rule as inventory joins — no invented dates). Verified reports append to a `candidate_labels` sidecar (in-review JSON, git-ignored or fixture-capped) with `crowd-verified` + officer ID + photo SHA256, surfaced in missing-evidence/provenance UI. `event=1` still requires a dated, in-window occurrence.
*   **Rehearsal script (exact):** (1) submit S2 crack report live → appears in queue + map marker, (2) queue filter `?status=queued` shows it, (3) toggle offline → submit → pending badge `1 pending`, (4) reconnect → auto-sync → `synced ✓`, (5) officer verify `PATCH → verified`, (6) dispatch alert fixture with 3-language preview (`en/hi/ne`).

## Rehearsal checklist (activate at freeze)

- [ ] Pilot extent + fixtures reproduce deterministically
- [ ] Scores/confidence match committed calibration artifact
- [ ] SHAP values match model artifact
- [ ] Off-manifold caveat spoken before Screen 3
- [ ] Threshold preset + divergence numbers reproduce
- [ ] Routing avoids the documented segment
- [ ] No network calls; everything local/ recorded fixture
- [ ] Limitations slide ready (see `08_LIMITATIONS_SIH26001.md`)

## PS (a)–(g) traceability checklist

| PS bullet | Covered in | Demo screen |
|---|---|---|
| (a) multi-source data (rain, moisture, satellite, terrain, history) | NGEN + FR-01 | Screen 1 (provenance footnote) |
| (b) AI/ML high-risk prediction | FR-02/03/04 | Screens 1–2 |
| (c) real-time alerts to admins + communities | FR-11 (+ FR-06 roles) | Screen 6 (fixture) |
| (d) GIS mapping of roads, villages, infrastructure | FR-07/09 | Screens 1, 5 |
| (e) geo-tagged citizen/field uploads | FR-10 | Screen 6 (officer queue) |
| (f) dashboards: severity, roads, weather forecast, emergency priority | FR-09 | Screens 1, 5 |
| (g) multilingual + offline | FR-12 | Screen 6 (2+ languages, sync pass) |
| Expected Solution: IMD/satellite/sensor integration | Sensor adapter (02 §5, 03 §A) | Fixture noted Screen 1 |
| Expected Solution: cloud + offline sync | Cloud path (02 §5) | Architecture slide, not live demo |

## Explicitly NOT claimed (carry into the frozen version)

- Scores are not probability of a specific landslide; confidence is calibrated
  P(elevated susceptibility) under the prototype target.
- No in-situ sensors were used; deployment needs partner feeds.
- Bands are prototype operational bands, not safety standards.
