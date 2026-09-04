# TALUS v2 Demo Scenario — SIH26001 (skeleton, NOT frozen)

**Status:** Skeleton — numbers will be frozen against the real v2 model once
it exists. Do not quote any number here to judges. · **Trace to:**
`01_REQUIREMENTS_SIH26001.md`

(Replaces nothing yet. v1 demo `docs/06_DEMO_SCENARIO.md` stays frozen for
the mine track.)

---

## Pilot extent

TBD by ADR (candidate: best-dated-inventory district cluster — Sikkim or
Nagaland, per research §3.2). All screens below run on the frozen pilot +
frozen scenario with recorded fixtures (no live network).

## Screen 1 — NER overview

GIS heatmap, 5-band colors. Pilot units colored by score/band. Road overlay
shows open / at-risk / blocked. Village priority flags visible.

*Freeze later: unit count, band distribution, fixture IDs.*

## Screen 2 — "Why?" (selected high-risk unit)

Tree SHAP panel: base value + top contributions with NER feature names
(e.g. `distance_to_road`, `rainfall_7d_mm`, `slope_angle`, `soil_moisture`).

*Freeze later: real SHAP values from the trained model. Say out loud what the
top drivers are and which evidence is missing.*

## Screen 3 — ML what-if (counterfactual) + documented caveat

Raise `rainfall_24h_mm` on a moderate unit; show score movement **with the
off-manifold caveat**: "Single-feature overrides break realistic correlations,
so this is a counterfactual, not a causal answer. For causal questions we use
the rainfall scenario engine."

*Freeze later: input values, output scores.*

## Screen 4 — Causal what-if (rainfall threshold scenario)

Threshold replay: Monga 2026 MDL curve (E = −11.10 + 0.62×D) and/or
Dahal–Hasegawa >144 mm/day preset over the pilot monsoon window. Show
saturation trajectory → FoS divergence → newly escalated units + evidence
timeline with physical causes (not SHAP).

*Freeze later: preset definition, divergence numbers, escalated unit IDs.*

## Screen 5 — Roads + routing

Risk-aware route between two pilot points avoids a high-risk segment;
shortest path crosses it. Road-status panel lists at-risk/blocked segments.

*Freeze later: origin/destination, avoided segments.*

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
