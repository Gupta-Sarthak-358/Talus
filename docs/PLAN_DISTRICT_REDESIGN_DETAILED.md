# District Officer — Detailed Redesign Plan (No Stub / No Fixed Value on Map) — Handover-Grade Contract

**Role**: District Disaster Officer (DDMA) — closure, evacuation, field queue triage.  
**File**: `frontend/src/pages/roles/DistrictPage.jsx:1`  
**Goal**: Ops console where *every pixel on the map is live* — no STUB rows, no hard-coded scores, no invented sensor. Villager never sees this; district never sees VillagerHero.  
**Project safety contract**: Talus provides **risk intelligence + explainability + escalation + routing + role-specific action** — the presentation narrative `Detect → Understand → Escalate → Decide → Act` (`docs/PPT_TALUS_FINAL.md:1`). No autonomous life-safety action is executed by the frontend; human personnel remain responsible for final evacuation/closure decisions (master doc invariant).

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
- ❌ `safeZones.length` naming — suggests “safe” count while actually meaning `zones.length` (all zones). Rename to `zones.length` / `liveZones.length`.

---

## 2. What it WOULD CONTAIN (after — live-only map)

**Top sticky command bar** `ops-sticky-top` `bg-mine-darkest/95 backdrop-blur` always visible on scroll:
- `IsolationAlertCard:18` `GET /api/isolation?location=gangtok` `R4` bottleneck `ISOLATED` → `EVACUATE` / `MAY_ISOLATE` → `RESTRICT` (live).
- `WarningStateCard:6` `GET /api/warning/state 6-state NORMAL→EVACUATE` reason-stamped (`effective_rain S1 385` `warning_thresholds.json:1`, `SWI swi.py L1=15`, `wound`, `forecast Open-Meteo`, `quake 25%` `GET /api/soil/swi`) + `kit` `what/why/rain/shelters/phones` (`main.py:1415`).

**Grid `lg:grid-cols-12 7:5`:**

**Left `lg:col-span-7 sticky top-[88px] h-[640px] border-2 border-zinc-200 rounded-2xl overflow-hidden` `RiskMap` LIVE ONLY**:
- Polygons: `zones.map(z=>z.geometry.coordinates)` from `GET /api/zones?location=gangtok` (`data.store` 4 zones `S1-4` `live-rf` or `fixture` fallback per `sih26001_model.py:95`), fill `RISK_BANDS[band].badgeColor` live, **only on API success** (see §9 invariants).
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
  - Pills `zones[].risk_score/band` from `GET /api/zones`, `aria-pressed` + `role="tab"` semantics.
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
  - Row actions: `Verify report` `Dismiss` → `PATCH /api/reports/{id} {status:verified|dismissed, reviewer_role:district_officer}` + `reason` prompt, optimistic `reports` update, error toast on `409` terminal guard. Wording is **Verify report**, not **Verify hazard** (officer verifies report credibility, not geological truth).
  - Foot: `Sync` `readReportOutbox()` count + `CloudOff` badge when `navigator.onLine===false`, `POST /api/reports` `429` rate cap 20.

- `road` → `RoadStatusCard` + `RoadRestrictionCatalogue`:
  - `GET /api/roads/status` live segments `R1 BLOCKED` `R2 AT-RISK` etc (no `GET /api/...` string).
  - `GET /api/roads/restrictions` `evaluation[].restricted` `emergency_route:true` stays open badge + `GET /api/zones/{id}/exposure` `operational_risk delta` + `buildings_downstream 85`.

**Bottom**: nothing duplicated — remove current duplicate `Road Network — Operational` `RoadStatusCard` at `id="ops-alerts"` (already inside `road` tab). Keep that `id` anchor for `Multi-lang` bell scroll, but anchor scrolls to `road` tab instead.

---

## 3. What to REMOVE (stub/fixed → live/empty)

| Remove | Why stub/fixed | Replace with |
|---|---|---|
| `locations.js` hard-coded `MINE_ZONES_GEOJSON` poly use in `RiskMap` when `GET /api/zones` is 200 | fixed geometry, `8 corridors 32 zones` live via `data.store` `slopes.<state>.json` | `zones[].geometry` from `GET /api/zones` + `GET /api/zones/{id}`; **no silent substitution** — see §9 |
| `RoadStatusCard` header `GET /api/roads/status · Gangtok Corridor` | debug string, not user value | `Gangtok Corridor · 4 segments` + `live` badge |
| `RiskScoreGauge` fallback `base_risk ||15` | invented `15` | `explanation.base_value` live, if null hide SHAP with `No explanation — model fallback` |
| `RiskTrendChart` no `NOW` | visual fixed timeline | `ReferenceLine x=last.time NOW` + `◀ OBSERVED \| NOW \| FORECAST` already added, keep |
| Any `89`/`78` literal in JSX | frozen demo | `store.risk[zid]` live |
| Bottom duplicate `RoadStatusCard` outside tabs | double fetch, confusion | keep only inside `road` tab; `#ops-alerts` scrolls to tab |
| `VillagerHero`/`VillagerRoadPlain` inside district | role leak | district uses `ZoneIntelligencePanel` only |
| `safeZones.length` naming | suggests “safe” count while meaning `zones.length` | `zones.length` or `liveZones.length` if filtered; never `safeZones` |
| Bell `district.multilang` → road tab teleport | `Bell` + `multilang` + `road` are three concepts | Split: **Multilingual Alert** (opens `AlertPanel`) vs **Road Status** (opens `road` tab with `Navigation` icon) — no astrology |

---

## 4. What to KEEP (already live, senior wants)

- `IsolationAlertCard` + `WarningStateCard` sticky top `backdrop-blur` (ops wants always visible).
- `RiskMap` `R2-avoidance` deterministic `RISK_WEIGHT 3.0` `alpha 0.2` `routing/comparison.py` — keep `full vs hazard` graphs.
- `ZoneIntelligencePanel` mounted hidden `aria-hidden` for cache correctness (already there) — keep, but document *what cache* (see §12).
- `OpsQueuePreview` `flagged` priority + `ReportModal` deep link `zoneId` preservation.
- 5-lang `GET /api/zones/{id}/decision?lang=en|hi|ne|as|bn` + `AlertPanel` `app|sms|cbe` (district sees `SMS`/`CB SIMULATED`).

---

## 5. What to ADD (gaps → live)

- Pagination + `aria-pressed` + `role="tab"` + `focus-visible:ring-2` on tab buttons (a11y §17).
- `GET /api/zones?location=gangtok|lachung|darjeeling|arunachal…mizoram` picker (8 corridors `LIVE — NGEN` vs pending honest `No data` badge already in `locations.js:290`).
- Empty states: `zones 0` → `No slopes — backend offline` `Retry`; `reports 0` → `Queue empty`; `history 0` → `No trend — check soil probe`.
- Offline indicator: `navigator.onLine` `CloudOff` in `OpsQueuePreview` + `sw.js:6` `talus-shell-v3-8state-live`.
- Freshness badges (see §8) and race guards (see §10).

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

---

## 8. Freshness Semantics — Live is not websocket unless stated

Live does **not** mean real-time push unless explicitly documented. Each District data stream has its own freshness contract:

| Stream | Source | Refresh | `updated_at` field | Stale window | UI on stale |
|---|---|---|---|---|---|
| `zones` `risk_score/band` | `sih26001_model.py:95` `score_row` + fallback frozen | `GET /api/zones` poll `TalusContext` mount + on `activeLocation` change | `store.updated_at[zone_id]` `data.now_iso()` per `ZoneStore` | >15m | `STALE` badge, retain last value only if safe, do not represent as `LIVE` |
| `rainfall` `rainfall_7d` | `ind2024_rfp25.nc` daily + `GET /api/forecast/live` 1h cache `Open-Meteo` | daily batch + `QuickStatsBar` `getForecastLive` | `forecast_live.fetched_at` + `features.rainfall_*_mm` is JJAS window date `2024-06-16/07-08/17` per `manifest.sample.json:7` | >24h for forecast, `time_window` for NGEN | show `Effective rain 541mm (thr 385)` with `generated_at` |
| `AWS gauges` | `GET /api/aws/gauges` `aws_ingest.py:39` open-meteo 15-min `past_days=7` | 10-min `CACHE` `aws_gauges.json` | `generated_at` ISO per gauge `ts` | >20m | `STALE` `CloudOff` |
| `warning/state` | `GET /api/warning/state` reason-stamped 6-state | on `WarningStateCard` mount + location change, not websocket | `generated_at` + per-reason `rainfall`/`SWI`/`wound` timestamps | >15m | `UNAVAILABLE` if `trust/3` |
| `roads` | `GET /api/roads/status` `roads.json:1` + `GET /api/roads/restrictions` catalogue | on `RoadStatusCard` mount + after `PATCH` reports | `generated_at` per `road_restrictions` | >1h | `STALE` retain last `segments[]` with amber badge, never invent `open` |
| `sensors` `live/feed` | `GET /api/live/feed` `runs/live_feed.json` simulator `local_sensor_sim.py --interval 30` | `LiveFeedCard` `poll 15s` | `feed.generated_at` + `served_from:simulator|sample` | >60s | `UNAVAILABLE` hide pins, never reuse last `rain_1h` as live |
| `reports queue` | `GET /api/reports/queue` in-mem `main.py:725` `_REPORTS` | `TalusContext` mount + after `POST`/`PATCH` + `Sync` | `created_at` + `captured_at` honest ISO (`main.py:885` >1h future →422) | N/A (queue is source) | `CloudOff` `readReportOutbox()` count |
| `isolation` | `GET /api/isolation` `R4 bottleneck` | `IsolationAlertCard` mount | `generated_at` | >15m | `UNAVAILABLE` hide, never assume `OPEN` |

UI must distinguish `LIVE` / `STALE` / `UNAVAILABLE` via badge + text, not colour alone. Never silently keep showing a stale `CRITICAL` as live. `TalusContext` exposes `updated_at` + `fetchedAt` per resource; `WarningStateCard` already shows `generated_at` and `corridor_state`.

---

## 9. Non-Negotiable Invariants — Must Not Break

1. District never renders `VillagerHero` or villager-only components.
2. Villager never receives `SHAP`, `OpsQueuePreview`, `road restriction catalogue`, or downstream exposure (`buildings 85`) details.
3. Risk scores, bands, confidence, `SHAP` and `geometry` come from **API data** (`GET /api/zones*` etc), not JSX literals.
4. No JSX hard-coded risk scores (`89`, `78`, `69`).
5. No static `sensor IDs` (`IMD-GTK-01` etc) — sensors only from `GET /api/live/feed`.
6. No fabricated report `timestamps`, `coordinates` or `statuses`.
7. No automatic life-safety action is executed by the frontend (`Dispatch` requires officer click + `POST /api/alerts/dispatch`).
8. `Verify/Dismiss` actions require backend `PATCH` `200` confirmation; `409` terminal guard is authoritative.
9. Optimistic UI updates must rollback on API failure (`409`/`4xx`).
10. Every live-data failure must be visible to the officer (`ErrorState` / `UNAVAILABLE` / `STALE`, never blank).
11. A stale API response must never overwrite newer state (see §10).
12. Switching corridors (`activeLocation`) must invalidate corridor-specific data (`zones`, `roads`, `isolation`, `warning`, `reports` filter).
13. Map geometry must use **API geometry when API succeeds** (see §10).
14. Static `MINE_ZONES_GEOJSON` is permitted only as an **explicitly documented failure state** (`ErrorState` with `Fallback` label + `Retry`), never silent substitution.
15. All officer actions (`Verify`, `Dismiss`, `Dispatch`, `Restrict`) must remain **auditable** (`runs/alert_dispatch.jsonl`, `runs/cbe_dispatch.jsonl`, `PATCH reviewer_role`, `TalusContext` `reports` history).

Master doc: Talus avoids autonomous evacuation and keeps human personnel responsible — presentation `Detect → Understand → Escalate → Decide → Act` and `08_LIMITATIONS` frame prototype data limitations explicitly.

---

## 10. Geometry Fallback — Exact Contract (Resolves Contradiction)

Prior draft said both *static fallback when 200* and *fallback only on !ok* — **exactly one contract now**:

```
API 200 + valid geometry (coordinates.length ≥3, centroid finite)
        ↓
Use API geometry  → render polygons

API 200 + missing/invalid geometry (empty, not finite, wrong CRS)
        ↓
ErrorState / degraded state  → "Map geometry unavailable — retry"
        ↓
DO NOT silently substitute static MINE_ZONES_GEOJSON

API !ok / network failure / timeout
        ↓
ErrorState  → "Backend offline — retry"
        ↓
Optional static geometry ONLY if explicitly labelled
“Fallback geometry — API unavailable (retry)” + Retry button
```

For an ops console, silently displaying old/static polygon when backend says something else is **worse than an error** — officer could close the wrong stretch. This aligns with project philosophy *missing evidence should be surfaced, not hidden*.

---

## 11. API Contract Table — Developer Contract

| Endpoint | Consumer | Required fields | Refresh | Failure |
|---|---|---|---|---|
| `GET /api/zones?location=X` | `RiskMap`, Zone pills, `Layout` badge | `zones[].id`, `zones[].geometry.coordinates`, `zones[].geometry.centroid`, `zones[].risk_score`, `zones[].risk_band`, `zones[].confidence`, `zones[].trend`, `updated_at` | `TalusContext` mount + `activeLocation` change, `warning` poll `60s` | `ErrorState` full page + `Retry` |
| `GET /api/zones/{id}` | `ZoneIntelligencePanel` header | `zone_id`, `name`, `geometry`, `risk_score`, `risk_band`, `trend`, `updated_at` | on `selectZone` | `ErrorState` in panel |
| `GET /api/zones/{id}/features` | `MissingEvidenceCard` | `features: {slope_angle…15}`, `missing_features[]` | on `selectZone` | Partial: show `No evidence` |
| `GET /api/zones/{id}/explanation` | `ShapChart` | `base_value`, `contributions[{feature, shap_value} top-4]` | on `selectZone` | `No explanation — model fallback` |
| `GET /api/zones/{id}/trend` | `RiskTrendChart` | `history[{t,risk_score} 12]`, `rapid_increase` | on `selectZone` | Partial: show `No trend` |
| `GET /api/zones/{id}/history?seed=91` | `RiskTrendChart` 365d | `points[{day,fos…}]` 365 | on `selectZone` | hidden |
| `GET /api/zones/{id}/decision?lang=en\|hi\|ne\|as\|bn` | `RoleActionCard` + kit | `decisions[{role,message,action,priority}]` → `kit{what,why,rainfall,shelters,phones,villager_explain}` | on `selectZone` + `lang` | `ErrorState` |
| `GET /api/warning/state?location=X&lang=en` | `WarningStateCard`, auto-watcher | `states[{zone_id,state,score,band,reasons[],action,kit}], corridor_state, corridor_zone, isolation` | mount + location, `auto 15m` | `ErrorState` `UNAVAILABLE` |
| `GET /api/isolation?location=X` | `IsolationAlertCard` | `valley_hub, bottleneck{R1..R4}, zones[{isolated,may_isolate,status,reason}], action` | mount `IsolationAlertCard` | `ErrorState` |
| `GET /api/soil/swi?location=X` | `WarningStateCard` SWI reason | `zones[{zone_id,swi 0-1, soil_moisture}]` | with `warning` | Partial |
| `GET /api/aws/gauges` | `LiveFeedCard`, `WarningStateCard` | `gauges[{id,location,rain_10min_mm,qa,ts}] interval 10min served_from` | `poll 15s` | `STALE` |
| `GET /api/roads/status?location=X` | `RoadStatusCard`, `RiskMap` | `segments[{id,status,adjacent_slope,coordinates,description}]` | mount + after reports | `ErrorState` |
| `GET /api/roads/restrictions?location=X` | `RoadStatusCard` road tab | `evaluation[{segment_id,restricted,reason,emergency_route}]` | with `roads` | `ErrorState` |
| `GET /api/zones/{id}/exposure` | `ExposureCard`, `road` tab | `hazard{score,band}, exposure{runout,buildings_downstream,wound_near,isolation}, operational_risk{score,band,delta}` | on `selectZone` + `exposure` | Partial |
| `GET /api/reports/queue?status=queued\|flagged` | `OpsQueuePreview` | `reports[{id,zone_id,type,text,lat,lon,captured_at,reporter_role,photo{sha256,exif},status,flagged_reason,created_at}]` | mount + `Sync` + after `PATCH` | `ErrorState` + `CloudOff` count |
| `PATCH /api/reports/{id}` `{status:verified|dismissed}` | `OpsQueuePreview` actions | `id, status, flagged_reason` or `409` terminal | on `Verify/Dismiss` | `409` → rollback + toast `already verified` |
| `POST /api/alerts/dispatch?channel=app\|sms|cbe&lang=&zone_id=&message=` | `AlertPanel` dispatch | `provider, sms_ok/simulated, broadcast` + `runs/alert_dispatch.jsonl` | on `Dispatch` | `502` with `fallback` link |
| `POST /api/alerts/cbe` | `AlertPanel` CB `SIMULATED` | `area, message{en,hi…}, simulated, broadcast, cbe_id` → `runs/cbe_dispatch.jsonl` | on `CB Dispatch` | `simulated:true` until `CBE_API_KEY` |
| `GET /api/live/feed` | `RiskMap` sensor pins | `feed.zones[zone].{rain_1h_mm,soil_delta,battery,rssi,status}, served_from:simulator|sample` | `poll 15s` | hide pins, never fake |
| `GET /health` | `AdminPanel`, `Footer` | `status ok,degraded, checks{store:gangtok, fixture:…}` | mount | `degraded` |

Minimum JSON shapes are the `ZONE` example in `data/sih26001/fixtures/slopes.json:8` + `feature_matrix.sample.csv:1` `22` cols. All lists are allowed empty — empty → `EmptyState`, not `0` hidden.

---

## 12. State Ownership — Who Owns What

```md
TalusContext (global, live):
- zones, reports, roads, activeLocation, locationData, live feed
- selectedZoneId, selectedZoneData (detail cache)
- riskSummary, alerts, alertDispatchData
- is*Open (drawers/modals), activeSimulation, activeRoutePlan
- loading, zoneLoading, simulationLoading, error, refreshData
- lang, t, supportedLangs, role, currentRoleMeta, mapLayers
- Fetched at: health + db/status on mount

DistrictPage (local):
- active tab: 'intel' | 'queue' | 'road' (useState 'intel')
- local pagination: queue page, per-tab scroll
- local UI expansion/collapse (none yet — add if needed)

ZoneIntelligencePanel (local + context):
- selectedZoneId (from context, but panel owns loading skeleton)
- selected zone detail cache (zone, features, explanation, trend, decision)
- explanation/trend/features loading (zoneLoading from context)

OpsQueuePreview (local + context):
- page (8 rows/page)
- optimistic report status (queued→verified rollback on 409)
- action error state (toast)
- Sync pending count from readReportOutbox()

RiskMap (local + context):
- layer visibility (mapLayers.sensors/hazardGlow/routes/roads/runout/wounds)
- tileMode (osm/dark/light)
- map viewport (leaflet internal) + MapController flyTo center/zoom
- temporary map selection (selectZone on polygon click)

LocationSelector (local + context):
- activeLocation sync via switchLocation (invalidates corridor-specific data)
```

Never put `reports`, `selectedZone`, `roads`, `activeLocation` into four different local `useState` — they belong in `TalusContext`. District owns only `tab` + pagination.

---

## 13. Data Freshness — LIVE vs STALE vs UNAVAILABLE

Live does **not** mean websocket unless explicitly stated (`live/feed` is poll `15s`, `warning` is `auto 15m` via `@app.on_event startup` `main.py:1759`). Each response exposes `updated_at` / `generated_at` / `fetched_at` / `ts`:

- `GET /api/zones` → `ZoneStore.updated_at` per `data.py:281` `now_iso()` on `reset` + `recompute`
- `GET /api/forecast/live` → `fetched_at` + `cache_ttl_s 3600`
- `GET /api/aws/gauges` → `generated_at` + per-gauge `ts`
- `GET /api/warning/state` + `isolation` + `roads` + `soil/swi` → `generated_at`
- `GET /api/reports/queue` → `created_at` + `captured_at` (honest ISO, `>1h` future → `422` `main.py:885`)

**UI must show** `LIVE` `STALE` `UNAVAILABLE` badge + `generated_at` relative (`2m ago`), never silently keep showing stale `CRITICAL` as live. Current `WarningStateCard` + `IsolationAlertCard` + `OpsQueuePreview` `CloudOff` already do — keep.

If data exceeds freshness window (see §8): retain last value **only if safe** (e.g., `roads` retain `segments[]` with amber `STALE`), otherwise hide (`sensors` hide pins when `live/feed` `!ok`).

---

## 14. Async Race Safety — Stale Must Not Overwrite Fresh

Every `zone/location`-dependent request must be **cancellable or guarded** against stale responses:

```jsx
let cancelled = false;
apiRequest(`/zones/${zoneId}`).then(d => { if (!cancelled && zoneId===selectedZoneId) setData(d); })
// or AbortController per TalusContext selectZone
```

A response may update state **only if it still corresponds to currently active `location/zone/requestKey`**.

**Applies to**: `selectZone` rapid clicks `S1→S2` (B finishes first, A must not overwrite S2), `activeLocation gangtok→lachung`, `ward queue refresh` vs `PATCH`, `warning/isolation` refresh vs `activeLocation` change, `RiskMap` `activeLocation` flyTo.

This bug never appears in 30s demo and appears when judge clicks like they try to break the universe — guard now.

---

## 15. Decision Provenance — Why This Recommendation

Backend preserves **why** (`reason_codes` + `evidence`), not just `action: EVACUATE`:

```json
{
  "zone_id": "S1",
  "state": "EVACUATE",
  "action": "EVACUATE S1 now. Stage machines at S4 valley",
  "reason_codes": ["HIGH_RISK","HEAVY_RAIN","ISOLATION_RISK"],
  "evidence": [
    {"source": "risk_model", "value": 69, "band": "Moderate", "model_version": "rf-v1", "calibration": "isotonic"},
    {"source": "rainfall", "value": 541, "window": "effective_rain 7d+0.3*30d", "threshold": 385, "local": 385, "quake_factor": 0.75},
    {"source": "swi", "value": 1.0, "threshold": 0.4, "model": "JMA 3-tank L1=15"},
    {"source": "wound", "value": 0.45, "near": true, "seg": "R2"},
    {"source": "isolation", "value": "R4 blocked", "valley_hub": "S4"}
  ],
  "generated_at": "2026-09-17T08:45:56Z",
  "model_version": "sih26001_rf_v1 (RF 500 + isotonic, 2936 1468+1468)",
  "feature_schema_version": "22 cols 17 numeric + lulc + recent_disturbance",
  "data_timestamp": "2024-06-16 S window"
}
```

**Current `kit` already has `what/why/rainfall/shelters/phones/villager_explain`** (`main.py:1415`) — extend to `reason_codes` + `evidence[]` + `generated_at` + `model_version` for `TrustLedger` future. State page already consumes `TrustLedgerCard.jsx:39` `4/5 median 7d` — this provenance fuels it.

Talus docs already emphasize *explainability, confidence, missing evidence, auditable decisions*.

---

## 16. Model / Version Provenance — Don't Pretend Divine Revelation

API should expose internally (not giant block to officer):

```text
model_version: sih26001_rf_v1 (RF 500 + isotonic, 2936)
calibration_version: isotonic spatial-OOF (Brier 0.0967) + Bayes p_real 0.5→0.01
feature_schema_version: 22 cols (17 numeric+lulc+recent_disturbance, 32 zones)
data_timestamp: per-zone time_window (S 2024-06-16, D 2024-07-08, N 2024-06-17)
explanation_version: TreeSHAP top-4 sih26001_model.py:151
```

Frontend may optionally show `Risk updated 2m ago · Model RF-v1` (footer of `RiskScoreGauge`), not a technical block. Training plan already treats calibration as engine, not decoration (`docs/sih26001/04_MODEL_PLAN.md:9`).

---

## 17. Queue Specification — Formal Contract (Most Operationally Important)

State machine (in-mem `main.py:725` `_REPORTS`, never auto-promotion):

```
queued ───────→ verified
  │                ↑
  └──────────→ dismissed

flagged ──────→ verified
  │                ↑
  └──────────→ dismissed

verified ──X→ anything   (terminal)
dismissed ─X→ anything   (terminal)
```

- `queued` → officer can `Verify` or `Dismiss`
- `flagged` (EXIF>200m or mime whitelist) → officer can `Verify` (overrides flag) or `Dismiss`
- `verified` / `dismissed` → **terminal** — District UI cannot modify → `PATCH` `409` `already verified — cannot transition` `main.py:856`

`409` is **authoritative**: rollback optimistic state.

### Verify wording

- **Verify report** = officer confirms *field report itself is credible* (photo+GPS+text+consent honest, not spoofed)
- **Verify hazard** = officer confirms *physical event occurred* (geological truth)

Those are not identical. For safety/audit, use **Verify report** (current `OpsQueuePreview` `Verify` button should tooltip `Verify report credibility`), not `Verify hazard`.

Terminal rows cannot be modified through District UI — admin may add `reason` but not reopen.

---

## 18. Report Confidence vs Risk Confidence — Separate Streams

```md
Risk confidence (0.58-0.82) ≠ field-report verification status (queued|flagged|verified|dismissed)

Model confidence = certainty/quality of ML estimate (isotonic `confidence`, `confidence_real_1pct` 0.01 Bayes)
Report status = operational review state of submitted evidence (EXIF 12m SHA256, flagged >200m)
```

Don't let UI imply `Flagged report = low risk confidence` or `Verified report = model confidence increased`. They are independent evidence streams. `TalusContext` keeps them separate (`riskSummary` vs `reports`), `ZoneIntelligencePanel` shows `MissingEvidenceCard` (model) separately from `OpsQueuePreview` (reports).

---

## 19. Safety-Critical Language

District UI may display:
- `Recommended action`
- `Recommended evacuation`
- `Hold response team`
- `Pre-emptive restriction`
- `Verify field report`
- `Risk-aware route` (lower modeled operational risk)

Avoid UI wording that implies autonomous authority:
- `System orders evacuation`
- `Guaranteed safe`
- `No risk`
- `Rockfall will occur`
- `Route is completely safe`
- `EVACUATE` without `Recommended` prefix (currently `EVACUATE S1 now.` → should be `Recommended evacuation: S1`)

Risk-aware route = lower *modeled* operational risk (`RISK_WEIGHT 3.0` `ROUTING_ALPHA 0.2` `routing/comparison.py:1` hazard graph `R2 dropped`), **NOT** guaranteed physical safety. Internal terminology → `Risk-Aware Route`, user-facing → `Recommended Route` (`t('route.safe_title')`).

---

## 20. Risk-Band Contract — Single Source

```md
### Risk Band Contract (prototype operational, not DGMS safety-factor)

0–49   Very Low  #5e7f3a
50–64  Low       #a68a3c
65–74  Moderate  #d99a24
75–84  High      #d96b24
85–100 Critical  #c74732
# RISK_BANDS frontend/src/data/constants.js:1  backend/app/model_service.py:35
```

> These are **prototype operational bands defined by scaffold contract** `SCAFFOLD_CONTRACT_SEPT5.md:14`, not DGMS FoS thresholds. `ML_MODEL_CARD_V2.md:1` + `08_LIMITATIONS` explicitly warn thresholds aren't production safety standards.

---

## 21. Mobile Behavior Matrix — Don't Stack Blindly

Villager `order-1 intel → order-2 map` is intentional; keep for District but adapted:

| Component | Desktop | Mobile |
|---|---|---|
| Sticky command bar `ops-sticky-top` | `sticky top-[88px] backdrop-blur` always visible | Normal flow `static` compact `py-1` (no blur) to save height |
| Map `RiskMap` `7 cols` | `sticky top-[88px] h-[640px]` | Full width `h-[520px]` *below* intel (order-1 intel first) |
| Intel `ZoneIntelligencePanel` `5 cols` | `5 cols` scrollable | Full width |
| Tabs `intel|queue|road` | Horizontal | Horizontal `overflow-x-auto` scroll |
| Queue `OpsQueuePreview` 8/page | `8 rows` table-like | Card `compact` rows `type+zone+flag` |
| SHAP `ShapChart` | Horizontal chart `Recharts` | Vertical when `history.length>60` `dot=false` |
| Road catalogue | Full `evaluation[]` | Stacked `segment_id` + `restricted` badge |
| Map controls `MapLegend` | Overlay `bottom-4 left-4` | Compact `bottom-2 left-2 w-56` |
| Warning+Isolation sticky | Sticky | Normal (so map gets height) |

Don't “fix” mobile by stacking 640px map above decision — officer would scroll past `EVACUATE`.

---

## 22. Accessibility — Hard Requirement

- Tabs use **real** `role="tab"` `aria-selected` `aria-controls` — current `aria-pressed` on `button` is `role=button` fallback; upgrade to `role=tablist` + `role=tab`.
- Buttons have accessible names (`aria-label` `Villager safe route` etc `VillagerPage.jsx:1` already `aria-label`).
- Risk cannot be communicated by **colour alone** — every `HIGH/CRITICAL` has text `CRITICAL` + icon `AlertTriangle`/`ShieldAlert` + `RiskBadge` `Risk Score 69 Moderate` (already in `RiskMap.jsx` `Tooltip`).
- Queue actions have explicit labels `Verify report` `Dismiss report` `aria-label` + `title` with `queued→verified` transition.
- Keyboard focus remains visible `focus-visible:ring-2` on `villager-tap` + tabs.
- Map markers provide textual `Popup` `Tooltip` (zone name + `risk_score` + `SHAP` primary) — already `RiskMap.jsx`.

Especially: **Do not rely on red/amber/green alone** — District officer must see `CRITICAL` text, not merely red polygon.

---

## 23. Observability / Debug Mode — Dev-Only Panel

```md
## Developer Diagnostics (dev-only, hidden in prod)

Active location: gangtok
Zones: 4/4 live (live_scores=True)
Road segments: 4 (R1 blocked, R2 at-risk, R3 open, R4 open)
Reports: 7 queued / 2 flagged / 1 verified
Warning: ALERT (S1)  Reason: Effective rain 541mm ≥385, SWI 1.0, wound
Isolation: OPEN  MayIsolate: S1? false
Last refresh: 17:31:24  (warning) / 17:31:10 (roads) / 17:30:59 (zones)
Model: rf-v1 500 trees Brier 0.0967  Calibration: isotonic + Bayes 0.5→0.01
Feature schema: 22 cols 17+restore  (recent_disturbance as 18th overlay)
Geometry: API  (fallback: none / fallback labelled)
Fallbacks: none  (or: API !ok → fallback geometry labelled)
Auto watcher: enabled interval 900s last_keys: gangtok:S1:OPEN …

[Copy diagnostics]
```

Not visible to officer in production — toggle via `?debug=1` + `AdminPanel.jsx:1` already shows `System health` `/health` + `System health` `postgis/fixture`.

This makes debugging the **live-only contract** (§9 invariant 10, §10) trivial: you see immediately if `Geometry: fallback` when it should be `API`.

---

## 24. One Thing Changed In Handover Itself — Naming

`safeZones.length` → `zones.length` / `liveZones.length`

If the array contains *all* zones (live or not), don't call it `safeZones` (implies “number of safe zones”). Current `DistrictPage.jsx:17` `const safeZones = zones || []` (and `safeReports`) — rename:

```jsx
const liveZones = zones || [];
const queueReports = reports || [];
{zones.length} slopes → {liveZones.length} slopes
Review Queue — {queueReports.length}
```

Tiny mismatch that becomes a bug in six weeks when someone filters `safeZones = zones.filter(z=>z.risk_band==='LOW')` and the header suddenly says `2 slopes` while map shows `4`.

---

## 25. Multilang CTA — UI Astrology Fix

Current `DistrictPage.jsx:29`:
```jsx
<Bell /> {t('district.multilang')}
```
scrolls to `Road Network — Operational` (road tab) — **bell + multilang + road are three concepts**.

Split:

- **Multilingual Alert** → opens `AlertPanel.jsx:92` drawer `POST /api/alerts/dispatch?channel=app|sms&lang=en|hi|ne|as|bn` (already `AlertPanel` has `CB SIMULATED` `Runout path` etc) — keep `Bell` icon.
- **Road Status** → switches tab to `road` `setTab('road')` + `scrollIntoView(#ops-alerts)` — use `Navigation`/`Route` icon, label `Road Status` `t('road.status')`.

Don't make a bell-shaped button secretly teleport into the road tab.

```jsx
<Link to="/reports" ...>{t('district.review_queue')} — {liveZones.length}</Link>
<button onClick={()=>setIsAlertsDrawerOpen(true)} className="…"><Bell /> {t('alerts.dispatch')}</button>
<button onClick={()=>{setTab('road'); document.getElementById('ops-alerts')?.scrollIntoView()}} className="…"><Navigation /> Road Status</button>
```

---

## 26. Definition of Done — Test Matrix (Executable Checklist)

```md
### District Acceptance Tests

[ ] Load District → 4 live zones appear (or 8 corridors → 32 when arunachal etc) `GET /api/zones?location=gangtok` 200
[ ] Zone polygon geometry comes from API `zones[0].geometry.coordinates` (inspect `RiskMap` prop, not `MINE_ZONES_GEOJSON`)
[ ] No hard-coded risk score appears in rendered map (grep `89` `78` in `DistrictPage.jsx` 0 hits)
[ ] Select S1 → `score`/`explanation`/`trend`/`features`/`decision` load (`Network` 200)
[ ] Select S2 rapidly → stale S1 response cannot overwrite S2 (guard `selectedZoneId` check)
[ ] Switch `intel → queue → road` → no unnecessary duplicate fetch (verify `Network` 1× `GET /api/reports/queue`, not 3×)
[ ] Flagged report appears before queued report (sort check)
[ ] Verify report → row updates optimistically to `verified` → `PATCH 200` keeps it; `409` → rolls back + toast `already verified`
[ ] Dismiss report → `dismissed` terminal, cannot `Verify` again (button disabled)
[ ] Offline `navigator.onLine===false` → `CloudOff` badge + `Sync` count visible, `ReportModal` queues to `talus_report_outbox`
[ ] API failure (`GET /api/zones 500` via devtools block) → `ErrorState` visible, no silent fallback polygon
[ ] Stale data (>15m) → `STALE` badge on `WarningStateCard` (see §8)
[ ] Road restriction shown even if segment is `OPEN` (`GET /api/roads/restrictions evaluation[].restricted true` when `S1 ALERT`)
[ ] `IsolationAlertCard` remains visible while scrolling (`ops-sticky-top` sticky)
[ ] `Critical` zone has text label `CRITICAL`, not only red fill (`RiskMap` `Tooltip` + `RiskBadge`)
[ ] Risk-aware route differs from shortest route (`POST /api/routes/safe` `avoided_zones` non-empty when `R2 at-risk`)
[ ] Villager route `role/villager` contains no `SHAP`/`OpsQueuePreview`/`road catalogue` (audit `VillagerPage.jsx`)
[ ] District contains no `VillagerHero` / `VillagerRoadPlain`
[ ] `Tab` has `role=tab` `aria-selected` + `focus-visible:ring-2`
[ ] `Switching corridors gangtok→lachung` invalidates `S1` detail cache (observe `Network` new `GET /api/zones?location=lachung`)
[ ] `Verify report` wording, not `Verify hazard`
[ ] `Risk-aware route` wording, not `Guaranteed safe`
```

Turns handover from documentation into **executable mental checklist** — exactly what prevents decorative dashboard syndrome.

---

## 27. Fetch/Cache Policy — When, Not Just What

```
Page load (District mount)
 ├─ GET /api/zones?location=X            (TalusContext, once)
 ├─ GET /api/warning/state?location=X   (WarningStateCard, once)
 ├─ GET /api/isolation?location=X       (IsolationAlertCard, once)
 ├─ GET /api/roads/status?location=X    (RoadStatusCard, once)
 ├─ GET /api/reports/queue              (TalusContext, once)
 └─ GET /api/panchayat/tiles?          (State only, lazy)

Zone selection (selectZone S1)
 ├─ GET /api/zones/S1                   (ZoneIntelligencePanel, per zone)
 ├─ GET /api/zones/S1/features          (MissingEvidence)
 ├─ GET /api/zones/S1/explanation       (ShapChart)
 ├─ GET /api/zones/S1/trend             (RiskTrendChart)
 ├─ GET /api/zones/S1/decision?lang=en  (RoleActionCard kit)
 └─ GET /api/zones/S1/exposure          (ExposureCard, road tab lazy)
 └─ GET /api/zones/S1/history?seed=91   (365d, lazy)

Road tab (first open)
 └─ GET /api/roads/restrictions?location=X  (if not already cached)
 └─ GET /api/soil/swi?location=X             (if Warning needs SWI)

Queue tab (first open)
 └─ (no fetch — reports already in TalusContext; refresh only on explicit Sync)

Location change (gangtok→lachung)
 └─ invalidate all corridor-specific resources: zones, roads, isolation, warning, reports filter, selectedZoneId
 └─ do not reuse S1 cache for N1

Never:
- fetch same endpoint once per rendered component (e.g., ZoneIntelligencePanel and hidden duplicate both fetch — deduplicate via TalusContext)
- refetch hidden ZoneIntelligencePanel unnecessarily (keep mounted hidden is intentional to preserve cache/state — document *what* cache: selectedZone detail + explanation/trend/features)
- refetch reports every tab switch (reports live in TalusContext, tab switch is local state only)
```

`ZoneIntelligencePanel` hidden `aria-hidden` exists to preserve `selectedZoneId` + `explanation/trend/features` cache — not just “senior dev insisted”. Document it.

---

## 28. Static Data Classification — Reference vs Stub

Every static artifact is one of:

| File | Classification |
|---|---|
| `frontend/src/data/locations.js` `LOCATIONS` centers/zooms | **UI reference geometry** (map flyTo, not score) |
| `frontend/src/data/locations.js` `MINE_ZONES_GEOJSON` | **Fallback/reference geometry** (allowed only per §10, labelled fallback) |
| `data/sih26001/evidence/warning_thresholds.json` `S1 385` | **Operational configuration** (local thresholds) |
| `data/sih26001/evidence/road_restriction_catalogue.json` | **Decision catalogue** (historical slides 12/8/5/3) |
| `data/sih26001/fixtures/slopes.json` `S1 89` | **Prototype reference data** (frozen demo when `live_scores=False`) |
| `RISK_BANDS` `50/65/75/85` `constants.js` `model_service.py:35` | **Prototype configuration** (operational bands, not DGMS FoS) |
| `data/sih26001/evidence/roads_osm_provenance.json` `1014/226/504` | **Data provenance** (OSM count proof, geometry still demo per `08_LIMITATIONS`) |
| `data/sih26001/evidence/copernicus_dem_comparison.json` | **Data provenance** (BigGIS proxy) |
| `sensor IDs` `IMD-GTK-01` etc | **Prohibited static data** (removed — `GET /api/live/feed` only) |
| `FILL` / `STUB` rows `feature_matrix.sample.csv` | **Prohibited** (`validate_ngen_sample.py:49` `no FILL`, `MAX_ROWS 40`) |
| `TalusContext` `zones/reports/roads` | **Live data** (from API) |

This table makes it impossible to mistake configuration (`warning_thresholds`) for “fake data” — the exact confusion the next developer would otherwise have.

---

**Build now with invariants + contracts above — and the ops console will survive the enthusiastically clicking judge.**

Start with §9 invariants + §10 geometry + §11 API table as the DistrictPage contract — that is the win state the reviewer asked for.
