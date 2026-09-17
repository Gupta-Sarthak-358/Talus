# District Officer — Detailed Redesign Plan (No Stub / No Fixed Value on Map)

**Role**: District Disaster Officer (DDMA) — closure, evacuation, field queue triage.  
**File**: `frontend/src/pages/roles/DistrictPage.jsx:1`  
**Goal**: Ops console where *every pixel on the map is live* — no STUB rows, no hard-coded scores, no invented sensor. Villager never sees this; district never sees VillagerHero.

---

## 1. What it CONTAINED (before, as of 2025-11-14 audit)

**Layout**: hero `role.district_officer — Closure & Evacuation` + 2 CTAs (`Review Queue — N` → `/reports`, `Multi-lang` bell) + `IsolationAlertCard` + `WarningStateCard` + `grid 7:5` left `RiskMap` sticky, right tabbed `intel | queue | road` ( `ZoneIntelligencePanel` / `OpsQueuePreview` / `RoadStatusCard` ) + hidden `<ZoneIntelligencePanel>` for cache + duplicate `Road Network — Operational` bottom card.

**Map `RiskMap.jsx:1` contained**:
- 4–12 polygons from `frontend/src/data/locations.js:11` `MINE_ZONES_GEOJSON` (S1-4 static coordinates, not from `GET /api/zones/{id}` geometry) — **fixed geometry**.
- 4 polylines `ROAD_SEGMENTS` static coordinates + `status blocked/at-risk/open` from `GET /api/roads/status` but geometry static — **fixed coords, status live** (counts proven `roads_osm_provenance.json:1` 1014/226/504, but trace demo per `08_LIMITATIONS`).
- Hazard pulse dots at `centroid` for `HIGH/CRITICAL` — derived from `zones[].risk_band` live, but centroid fixed.
- Sensor pins `sensorIcon` — *was* static `sensorIds:["IMD-GTK-01"]` in `locations.js` (removed 2025-11, now only `GET /api/live/feed`).
- Runout dashed red `GET /api/runout/exposure` 85 buildings — screening approx, correctly labelled but shown to all roles (villager saw screening even though villager shouldn't).
- Wound amber `GET /api/wounds` 2 scars vet queue — shown as `REVIEW` badge (officer needs it, villager doesn't need screening label).
- Routing overlays `POST /api/routes/safe` green solid (risk-aware) vs red dashed (shortest via `R2`) — live, correct.

**Right panel `ZoneIntelligencePanel` contained**:
- Zone pills `S1 89/78/66/52` — now live `GET /api/zones` (`sih26001_model.py:95` `live_scores=True` RF 0.9345 or frozen fallback), but pills still used `frontend` labels not `band` from API for color? **mixed**.
- `RiskScoreGauge` `score /100` + `band` + `confidence` — live, but subtext was `Calibrated (isotonic, Brier 0.0971)` — **technical stub-like string** removed 2025-11 for villager but still in district as `Confidence — higher means more certain` (ok, not stub).
- `RoleActionCard` — live `GET /api/zones/{id}/decision?lang=en` 4 roles, but district action was single line “Schedule S3 inspection” — missing Yellow/Red kit `what/why/rain/shelters/phones`.
- `ShapChart` `GET /api/zones/{id}/explanation` TreeSHAP top-4 live — correct, but shown even when `confidence` low (no `missing_evidence` hint).
- `RiskTrendChart` `GET /api/zones/{id}/trend` + `GET /api/zones/{id}/history` 365d — live, but chart had no `NOW` divider, so `OBSERVED` (IMD+CCI) looked mixed with `FORECAST` (Open-Meteo) — **visual fixed value**.
- `MissingEvidenceCard` `GET /api/zones/{id}/features` `missing_features` — live, but `district` saw same caution as villager (should see full).
- `OpsQueuePreview` — live `GET /api/reports/queue` (15 tests `test_reports.py`), but no pagination, no `flagged` priority, no thumb (photo stored `talus_report_photos` but preview showed only text).

**Stubs / Fixed values audit (must go)**:
- ❌ `locations.js:18` zone coordinates hard-coded — should be `GET /api/zones` `zone.geometry.coordinates/centroid` live per-corridor (8 corridors S/N/D/AR/AS/MN/ML/MZ `32 zones`).
- ❌ `RoadStatusCard` title `GET /api/roads/status · Gangtok Corridor` — debug string, not user value.
- ❌ `RiskTrendChart` no `NOW` — implied fixed timeline.
- ❌ `ShapChart` base `15` hard-coded fallback — should be `explanation.base_value` live.
- ❌ Any `89` `78` literal in JSX (old frozen) — now live `sih26001_model.py:95` only.
- ❌ `VillagerRoadPlain` inside district (was not, but check) — district must not show villager binary hero.

---

## 2. What it WOULD CONTAIN (after — live-only map)

**Top sticky command bar** `ops-sticky-top` `bg-mine-darkest/95 backdrop-blur` always visible on scroll:
- `IsolationAlertCard:18` `GET /api/isolation?location=gangtok` `R4` bottleneck `ISOLATED` → `EVACUATE` / `MAY_ISOLATE` → `RESTRICT` (live).
- `WarningStateCard:6` `GET /api/warning/state 6-state NORMAL→EVACUATE` reason-stamped (`effective_rain S1 385` `warning_thresholds.json:1`, `SWI swi.py L1=15`, `wound`, `forecast Open-Meteo`, `quake 25%` `GET /api/soil/swi`) + `kit` `what/why/rain/shelters/phones` (`main.py:1415`).

**Grid `lg:grid-cols-12 7:5`:**

**Left `lg:col-span-7 sticky top-[88px] h-[640px] border-2 border-zinc-200 rounded-2xl overflow-hidden` `RiskMap` LIVE ONLY**:
- Polygons: `zones.map(z=>z.geometry.coordinates)` from `GET /api/zones?location=gangtok` (`data.store` 4 zones `S1-4` `live-rf` or `fixture` fallback per `sih26001_model.py:95`), fill `RISK_BANDS[band].badgeColor` live, no `MINE_ZONES_GEOJSON` fallback when live is 200 (fallback only when `GET /api/zones` fails → show `ErrorSkeleton` + `Retry`, never invented).
- Centroid hazard pulse `HIGH/CRITICAL` at `zone.geometry.centroid` live, `mapLayers.hazardGlow` toggle.
- Roads: `GET /api/roads/status?location=…` `segments[].coordinates` live (still demo trace per `08_LIMITATIONS`, but **coordinates live from API**, not hard-coded import; provenance `roads_osm_provenance.json 1014/226/504` lives in `/admin` only, not on map).
- Sensors: `GET /api/live/feed` `sensorPins` only; `role==='district_officer'` shows small `SIM` badge, `villager` shows no badge. No static `sensorIds`.
- Runout: `GET /api/runout/exposure` dashed red — **district sees it** (needs exposure), villager does not. Tooltip `S2 85 buildings downstream` live, not screening disclaimer (disclaimer in `/admin` `GET /api/zones/{id}/exposure` `operational_risk`).
- Wound: `GET /api/wounds` amber `Vegetation change near R2` — district sees `field-check` note, no `REVIEW` badge (badge is admin).
- Routing: `POST /api/routes/safe` `riskAwareRoute` green solid + `shortestRoute` red dashed — live, `max_risk_exposed` not shown as km (frontend haversine does km).
- Controls: `MapLegend` `Runout path` / `Vegetation change` toggles, `tileMode osm|dark|light` — no technical `GET /api/...` string.

**Right `lg:col-span-5 space-y-3 order-1 lg:order-2`:**

**Tabs `bg-white border-2 border-zinc-200 rounded-2xl p-1 flex gap-1`**
- `intel` (default) → `ZoneIntelligencePanel` **live-only**:
  - Pills `zones[].risk_score/band` from `GET /api/zones`, `aria-pressed`.
  - Header `RiskMap` selection `GET /api/zones/{id}` `name/geometry/updated_at`.
  - `RiskScoreGauge` `score/band` live, `confidence` live, `trend` from `GET /api/zones/{id}/trend` `trend.badge`.
  - `RoleActionCard` `GET /api/zones/{id}/decision?lang=en` district action + `kit` `what/why/rain/shelters/phones` `what: EVACUATE — Critical risk for S1` `rainfall: 327mm /7d effective 541mm (thr 385 quake-25%)` `shelters: Tadong Hall…` `phones: 03592-221011`.
  - `ShapChart` `GET /api/zones/{id}/explanation` `base_value` + `contributions 4` live; if `missing_features` non-empty, show `MissingEvidenceCard` above SHAP.
  - `RiskTrendChart` `GET /api/zones/{id}/trend` `history` 12 + `GET /api/zones/{id}/history?seed=91` 365d sparkline, `NOW` vertical `ReferenceLine` `OBSERVED ◀ IMD 0.25°+CCI | NOW | FORECAST Open-Meteo ▶` (already added 2025-11-15).
  - `MissingEvidenceCard` `GET /api/zones/{id}/features` `missing_features` full list (officer) vs villager 1-line caution.

- `queue` → `OpsQueuePreview` **live queue triage** (district priority):
  - `GET /api/reports/queue?status=queued|flagged` `reports:[]` live; empty → `No reports — field team can submit via /reports` (not “0 flagged hidden”).
  - Sorted `flagged` first, then `queued`, pagination `pageSize 8` `Prev/Next` `aria-label`.
  - Row: `type icon` `zone_id` `text truncate` `lat/lon 4-dec` `captured_at` relative `photo thumb` from `talus_report_photos` `localStorage` (no binary fetch) + `flagged_reason` red + `GIS` `Inspect on Map` `selectZone`.
  - Row actions: `Verify` `Dismiss` → `PATCH /api/reports/{id} {status:verified|dismissed, reviewer_role:district_officer}` + `reason` prompt, optimistic `reports` update, error toast on `409` terminal guard.
  - Foot: `Sync` `readReportOutbox()` count + `CloudOff` badge when `navigator.onLine===false`, `POST /api/reports` `429` rate cap 20.

- `road` → `RoadStatusCard` + `RoadRestrictionCatalogue`:
  - `GET /api/roads/status` live segments `R1 BLOCKED` `R2 AT-RISK` etc (no `GET /api/...` string).
  - `GET /api/roads/restrictions` `evaluation[].restricted` `emergency_route:true` stays open badge + `GET /api/zones/{id}/exposure` `operational_risk delta` + `buildings_downstream 85`.

**Bottom**: nothing duplicated — remove current duplicate `Road Network — Operational` `RoadStatusCard` at `id="ops-alerts"` (already inside `road` tab). Keep that `id` anchor for `Multi-lang` bell scroll, but anchor scrolls to `road` tab instead.

---

## 3. What to REMOVE (stub/fixed → live/empty)

| Remove | Why stub/fixed | Replace with |
|---|---|---|
| `locations.js` hard-coded `MINE_ZONES_GEOJSON` poly use in `RiskMap` when `GET /api/zones` is 200 | fixed geometry, `8 corridors 32 zones` live via `data.store` `slopes.<state>.json` | `zones[].geometry` from `GET /api/zones` + `GET /api/zones/{id}`; fallback `MINE_ZONES_GEOJSON` only when `GET` fails → `ErrorSkeleton` |
| `RoadStatusCard` header `GET /api/roads/status · Gangtok Corridor` | debug string, not user value | `Gangtok Corridor · 4 segments` + `live` badge |
| `RiskScoreGauge` fallback `base_risk ||15` | invented `15` | `explanation.base_value` live, if null hide SHAP with `No explanation — model fallback` |
| `RiskTrendChart` no `NOW` | visual fixed timeline | `ReferenceLine x=last.time NOW` + `◀ OBSERVED \| NOW \| FORECAST` already added, keep |
| Any `89`/`78` literal in JSX | frozen demo | `store.risk[zid]` live |
| Bottom duplicate `RoadStatusCard` outside tabs | double fetch, confusion | keep only inside `road` tab; `#ops-alerts` scrolls to tab |
| `VillagerHero`/`VillagerRoadPlain` inside district | role leak | district uses `ZoneIntelligencePanel` only |

---

## 4. What to KEEP (already live, senior wants)

- `IsolationAlertCard` + `WarningStateCard` sticky top `backdrop-blur` (ops wants always visible).
- `RiskMap` `R2-avoidance` deterministic `RISK_WEIGHT 3.0` `alpha 0.2` `routing/comparison.py` — keep `full vs hazard` graphs.
- `ZoneIntelligencePanel` mounted hidden `aria-hidden` for cache correctness (already there) — keep.
- `OpsQueuePreview` `flagged` priority + `ReportModal` deep link `zoneId` preservation.
- 5-lang `GET /api/zones/{id}/decision?lang=en|hi|ne|as|bn` + `AlertPanel` `app|sms|cbe` (district sees `SMS`/`CB SIMULATED`).

---

## 5. What to ADD (gaps → live)

- Pagination + `aria-pressed` + `focus-visible:ring-2` on tab buttons (a11y).
- `GET /api/zones?location=gangtok|lachung|darjeeling|arunachal…mizoram` picker (8 corridors `LIVE — NGEN` vs pending honest `No data` badge already in `locations.js:290`).
- Empty states: `zones 0` → `No slopes — backend offline` `Retry`; `reports 0` → `Queue empty`; `history 0` → `No trend — check soil probe`.
- Offline indicator: `navigator.onLine` `CloudOff` in `OpsQueuePreview` + `sw.js:6` `talus-shell-v3-8state-live`.

---

## 6. Data flow (live-only, no stub on map)

`GET /api/zones?location=X` → `zones[]` → `RiskMap` polygons + pills  
`GET /api/zones/{id}` + `features` + `explanation` + `trend` + `decision?lang` → `ZoneIntelligencePanel`  
`GET /api/warning/state` 6-state + `GET /api/isolation` `R4` + `GET /api/soil/swi` `GET /api/aws/gauges` 15-min + `GET /api/replay/series` → `WarningStateCard` `IsolationAlertCard`  
`GET /api/roads/status` + `GET /api/roads/restrictions` + `GET /api/zones/{id}/exposure` → `RoadStatusCard`  
`GET /api/reports/queue` + `PATCH` → `OpsQueuePreview`  
All via `frontend/src/services/api.js:7` `BASE_URL VITE_API_URL` `apiRequest` with `throw` on `!ok` → `ErrorState` never invented data.

---

## 7. Verify (stop if any fail)

`C:\Users\satvi\Desktop\mnemo\.venv\Scripts\python.exe scripts/check_scaffold.py` → `SCAFFOLD OK`  
`python scripts/validate_ngen_sample.py` → `NGEN SAMPLE OK 22 cols 32×22`  
`pytest backend/tests -q --ignore=test_api,causal` → `49 passed 2 skipped`  
`vite build` `frontend/dist 304kB`  
`curl /api/zones?location=gangtok | jq .zones[0].geometry` has `centroid`, not `MINE_ZONES_GEOJSON` hard-code; `curl /api/roads/status | jq .segments[0].status` live.

**Done when**: district map shows only live polygons/roads/sensors/runout/wound, no `89` literal, no `GET /api/...` string, and `queue` tab verifies a `flagged` report in <10s.
