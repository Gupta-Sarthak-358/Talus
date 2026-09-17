# Handover — District Officer Page: What Is Currently Contained (Long Form)

**For**: Next developer doing the upgrade. Read this before touching `frontend/src/pages/roles/DistrictPage.jsx:1`.
**Why this doc is long**: District is the ops console — the only place where an officer has 30 seconds to decide *close road? evacuate?* — so every pixel must be understood before you change it. No TL;DR.

**Stack**: React 18 + Tailwind + Leaflet 1.9 + Recharts + `TalusContext.jsx:1` (live `GET /api/*` only, no mock). 8 corridors, 32 zones `S1-4 N1-4 D1-4 AR1-4 AS1-4 MN1-4 ML1-4 MZ1-4`, frozen `S1 89/78/66/52` `SCAFFOLD_CONTRACT_SEPT5.md:14`, live `sih26001_model.py:95` `RF 0.9345` `GroupKFold8` or fallback. Tests `49 passed 2 skipped` `validate_ngen_sample.py:49` `32×22`.

---

## 0. Where Villager ends, District begins

- **Villager** `VillagerPage.jsx:1` `VillagerHero` + 4 large taps + `RiskMap` always + `VillagerRoadPlain` + 2 `villager-tap` CTAs. No SHAP, no queue, no Brier. Purpose: *binary* — safe or not, which road to avoid, in mother tongue `translations.js:8` `en/hi/ne/as/bn`.
- **District** must never show `VillagerHero` and Villager must never see district queue/SHAP. The handover doc you need for District is the inverse: *triage* — which slope first, which road to close, which field report to verify, and what to tell State.

If you show a villager the `OpsQueuePreview` you leak unverified field reports. If you hide `IsolationAlertCard` from district you hide that `R4` bottleneck isolates `S1,S2,S3`.

---

## 1. Top Bar — Who, Where, How Many

**File**: `DistrictPage.jsx:24`
```jsx
<div className="bg-zinc-900 text-white rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
  <span className="font-black tracking-wide">{t('role.district_officer')} — {t('district.closure')}</span>
  <span className="text-zinc-300 font-mono">{safeZones.length} slopes · {t('district.sub')}</span>
</div>
```
- **What it is**: Identity + scope. `t('role.district_officer')` → `District Disaster Officer — Closure & Evacuation` (5-lang `translations.js:1`). `safeZones.length` is `zones.length` from `GET /api/zones?location=gangtok` (`TalusContext.jsx:91` `getZones(activeLocation)`). `t('district.sub')` = `slopes · live · score + calibrated % + SHAP drivers` — tells officer this number is live, not frozen.
- **Data live?** Yes — `zones` live from `ZoneStore` `backend/app/data.py:281` `live_scores=True` (`4/4` per corridor, see `health store:gangtok live_scores=True`). Fallback is frozen `89/78/66/52` only when `sih26001_rf_v1.joblib` missing — currently `live 4/4` per `curl /api/zones?location=gangtok`.
- **Upgrade note**: Keep it sticky-less; this bar is not the `ops-sticky-top` below. Don't add district name here — `locationData.label` lives in `QuickStatsBar` / `CorridorComparison` on State. District is single-corridor at a time.

---

## 2. Primary CTAs — The Two Jobs

**File**: `DistrictPage.jsx:29`
```jsx
<Link to="/reports" className="flex-1 py-2.5 bg-zinc-900 …"> {t('district.review_queue')} — {safeReports.length}</Link>
<button onClick={() => document.getElementById('ops-alerts')?.scrollIntoView({ behavior: 'smooth' })} className="px-4 py-2.5 bg-white border-2 border-zinc-900 …"><Bell /> {t('district.multilang')}</button>
```
- **What it is**: Officer has two jobs: *triage field reports* and *send multilingual alerts*. The `— {safeReports.length}` badge is `reports.length` from `GET /api/reports/queue` (`TalusContext.jsx:95` `getReportsQueue()`). `safeReports = reports || []` — handles `null` before first fetch.
- **Data live?** Yes — `GET /api/reports/queue` returns `[{id:REP-003, zone_id:S2, type:crack, text:…, lat/lon pilot bbox 26.9-27.8/88.1-88.9, captured_at ISO, reporter_role, photo{filename,mime,size,sha256,exif_lat/lon}, consent:true, status:queued|flagged, flagged_reason, created_at}]`. `15` tests `test_reports.py:1`. Photo bytes never committed (`.gitignore` `PHOTO_STORE_KEY` `reports.js:1` `talus_report_photos` + `talus_report_outbox` outbox).
- **Why `scrollIntoView` for second CTA**: `district.multilang` is `Bell` → `AlertPanel.jsx:92` drawer, but district also has inline `Road Network — Operational` at `id="ops-alerts"` bottom (legacy). The button scrolls there — after your upgrade it should switch tab to `road` instead (see §6).
- **Upgrade note**: Keep `flex-1` so first CTA dominates; officer's thumb hits Queue first. Don't add a third CTA here — State has `Export Panchayat CSV`, Rescue has `Exposure`.

---

## 3. Sticky Command Bar — Always Visible (Ops Wants It)

**File**: `DistrictPage.jsx:35`
```jsx
<div className="ops-sticky-top space-y-3 bg-mine-darkest/95 backdrop-blur py-2 -mx-3 px-3 sm:mx-0 sm:px-0 sm:bg-transparent sm:backdrop-blur-none sm:static">
  <IsolationAlertCard />
  <WarningStateCard />
</div>
```
- **What it is**: `ops-sticky-top` is `position:sticky` `top:[88px]` on desktop, so when officer scrolls the `grid 7:5` below, `Isolation + Warning` stay in viewport — like Taiwan’s `ARDSWC` ops board.
- **`IsolationAlertCard.jsx:18`** `GET /api/isolation?location=gangtok` — deterministic road-network egress to valley hub `S4/N4/D4`. `R4==blocked → S1,S2,S3 ISOLATED` (no plains egress), `adj_map S1:[R1,R2,R3] S2:[R2,R3] S3:[R3,R4] S4:[R4]`, `open==0 && at-risk==1 && High/Critical → MAY_ISOLATE` predictive. UI: `ISOLATED` red `ShieldAlert` `EVACUATE now. Stage machines at S4 valley` / `MAY_ISOLATE` amber `AlertTriangle` `Hold team for R2/R3`. Live, no stub.
- **`WarningStateCard.jsx:6`** `GET /api/warning/state?location=gangtok&lang=en` `6-state NORMAL→WATCH→ALERT→CRITICAL→RESTRICT→EVACUATE` (`_WARN_STATES` `main.py:1308`). Each `state` has `reasons[]` reason-stamped: `Risk score 69 (Moderate)`, `Effective rain 541mm ≥385 (Monga separator)` `warning_thresholds.json:1` `S1 385`, `SWI 3-tank` `swi.py:1` `L1=15 L2=60 L3=60`, `Recent disturbance nearby (NDVI drop) BigGIS wound` `wound_map.json:1` 2 scars vet queue `4/2936`, `Forecast  ...` `Open-Meteo 15-min`, `Post-quake window` `seismic_years_since ≤0.5y` `usgs_quakes.json:1` `25%` threshold drop, `Borders blocked segment R1`. Also `kit` `what/why/rainfall/shelters Tadong Hall/Ranipool School/phones 03592-221011` `main.py:1415`. Live, not frozen bands alone.
- **Upgrade note**: Keep both, in this order (`Isolation` first — road cut is more urgent than score). Don't add `QuickStatsBar` here — it lives on State, not ops console.

---

## 4. Main Grid — 60% Map, 40% Intel

**File**: `DistrictPage.jsx:40`
```jsx
<div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
  <div className="lg:col-span-7 xl:col-span-7 h-[640px] lg:sticky lg:top-[88px] order-2 lg:order-1 border-2 border-zinc-200 rounded-2xl overflow-hidden">
    <RiskMap />
  </div>
  <div className="lg:col-span-5 xl:col-span-5 space-y-3 order-1 lg:order-2">
    {/* tabs */}
  </div>
</div>
```
- **What it is**: On desktop, map `7` is left sticky, intel `5` is right scrollable. On mobile, intel (`order-1`) comes before map (`order-2`) so officer sees `Isolation+Warning` then intel before scrolling to map — intentional `AGENTS.md:3` surgical mobile-first.
- **Why `order` swap**: Mobile screen is narrow; officer's thumb wants decision before pan.

### 4a. `RiskMap.jsx:1` — The Only Map, Live-Only

**What it renders (today)**:
- **Zones**: `zones.map(z=>z.geometry.coordinates)` — **currently from `frontend/src/data/locations.js:11` `MINE_ZONES_GEOJSON` static** (S1 4 coords). **Will be** `zones[].geometry` from `GET /api/zones` live (see upgrade §8). Fill `RISK_BANDS[band].badgeColor` live, no `89` literal. Pulse dot at `centroid` when `HIGH/CRITICAL` `mapLayers.hazardGlow`.
- **Roads**: `GET /api/roads/status?location=gangtok` `segments[].coordinates` live (demo trace per `08_LIMITATIONS` but **coordinates live from API**, not hard-coded import; provenance `roads_osm_provenance.json:1` `1014/226/504` lives in `/admin`). Colors `blocked red` `at-risk amber dashed` `open green`.
- **Sensors**: `GET /api/live/feed` `sensorPins` only; `role==='district_officer'` shows small `SIM` badge `frontend/src/components/RiskMap/RiskMap.jsx` `role !== villager` check, villager shows no badge. No static `sensorIds:["IMD-GTK-01"]` — removed.
- **Runout**: `GET /api/runout/exposure` `85` buildings downstream `S2` dashed red — **district sees it** (needs exposure), villager does not after redesign (villager saw `screening` label, now `Runout path` plain). Tooltip `S2 85 buildings`.
- **Wound**: `GET /api/wounds` `2` scars `Vegetation change near R2` — district sees `field-check` note, no `REVIEW` badge.
- **Routing**: `POST /api/routes/safe` `riskAwareRoute` green solid vs `shortestRoute` red dashed via `R2` — live `RISK_WEIGHT 3.0` `alpha 0.2` `routing/comparison.py`.
- **Controls**: `MapLegend` `Runout path` / `Vegetation change` toggles, `tileMode osm/dark/light`, `MapController` flyTo on `activeLocation` change (8 corridors `gangtok/lachung/darjeeling/arunachal/assam/manipur/meghalaya/mizoram` `locations.js:290`).

**What is stub today that must be live after you upgrade**:
- ❌ Zone polygons **currently static fallback** `MINE_ZONES_GEOJSON` when `GET /api/zones` is 200 — you must flip to `zones[].geometry` live as primary, fallback only on `!ok` → `ErrorState`.
- ✅ Everything else on map is already live (no `FILL`).

---

## 5. Right Tabs — The Three Intel Modes

**File**: `DistrictPage.jsx:45`

```jsx
<div className="bg-white border-2 border-zinc-200 rounded-2xl p-1 flex gap-1">
  {[
    ['intel', 'Intel'],
    ['queue', `Queue ${safeReports.filter(r=>r.status==='flagged').length ? `· ${safeReports.filter(r=>r.status==='flagged').length} flagged` : ''}`],
    ['road', 'Road'],
  ].map(([k,label])=>(
    <button key={k} onClick={()=>setTab(k)} aria-pressed={tab===k}
      className={`flex-1 py-2 rounded-xl text-xs font-black ${tab===k?'bg-zinc-900 text-white':'text-zinc-600 hover:bg-zinc-100'}`}>
      {label}
    </button>
  ))}
</div>
<div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 min-h-[280px]">
  {tab==='intel' && <ZoneIntelligencePanel />}
  {tab==='queue' && <OpsQueuePreview reports={safeReports} t={t} />}
  {tab==='road' && <RoadStatusCard />}
</div>
<div className="hidden" aria-hidden><ZoneIntelligencePanel /></div> // keep mounted for cache correctness
```

### 5a. `intel` → `ZoneIntelligencePanel.jsx:1`

**What it is**: The slope dossier. Not for villager.

**Contains**:
- **Pills** `zones.map(z=>z.id)` `S1 4` + `band` live `GET /api/zones`, `aria-pressed` `selectedZoneId`, `risk_band` color. Tap → `selectZone(z.id)` `GET /api/zones/{id}` `GET /api/zones/{id}/features` `explanation` `trend` `decision?lang`.
- **Header** `GET /api/zones/{id}` `name/geometry/updated_at` `risk_score/band` `trend` live.
- **`RiskScoreGauge`** `score/band` live, `confidence` live `0.58-0.82`, `trend.badge` live. Subtext was `Calibrated (isotonic, Brier…)` — now `Confidence — higher means more certain` (clean, not `Brier 0.0971` — that lives in `/admin` `GET /api/model/calib` `p_real 0.5→0.01`).
- **`RoleActionCard`** `GET /api/zones/{id}/decision?lang=en` district action + `kit` `what: EVACUATE — Critical risk for S1` `why: Risk score 69; Effective rain 541mm ≥385; SWI…` `rainfall: 327mm /7d effective 541mm (thr 385)` `shelters: [Tadong Hall, Ranipool School]` `phones: 03592-221011` `villager_explain` (villager sees this elsewhere). Live.
- **`ShapChart`** `GET /api/zones/{id}/explanation` `base_value` + `contributions 4` `TreeSHAP top-4` `sih26001_model.py:151` live; if `missing_features` non-empty, banner above. Uses `explanation.base_value` live, not fallback `15`.
- **`RiskTrendChart`** `GET /api/zones/{id}/trend` `history 12` + `GET /api/zones/{id}/history?seed=91` `365d` live, `NOW` vertical `ReferenceLine` `OBSERVED ◀ IMD 0.25°+CCI | NOW | FORECAST Open-Meteo ▶` (added 2025-11-15, prevents mixing). No `GET /api/forecast` curve inside — forecast lives in `WarningStateCard` reason `Forecast  …`.
- **`MissingEvidenceCard`** `GET /api/zones/{id}/features` `missing_features` — officer sees full `soil probe window`, `lineament 0.8 uniform`, etc; villager sees 1-line caution.

**What to keep**: All, but paginate `history` if `>60` dots `dot={history.length>60?false:{r:3}}` already there.

### 5b. `queue` → `OpsQueuePreview`

**What it is**: Live triage of unverified field reports — the reason district opens the app.

**Contains**:
- `GET /api/reports/queue?status=queued|flagged` `reports:[]` live; empty → `No reports — field team can submit via /reports` (not “0 flagged hidden”).
- Sorted `flagged` first, then `queued`, pagination `pageSize 8` `Prev/Next` `aria-label` (you add).
- Row: `type icon` `zone_id` `text truncate` `lat/lon 4-dec` `captured_at` relative `photo thumb` from `talus_report_photos` `localStorage` (no binary fetch) + `flagged_reason` red (`EXIF >200m` / `mime whitelist`) + `GIS Inspect on Map` `selectZone` + `flagged 12m` badge.
- Row actions: `Verify` `Dismiss` → `PATCH /api/reports/{id} {status:verified|dismissed, reviewer_role:district_officer, reason}` → optimistic `reports` update, error toast on `409` terminal guard `queued|flagged→verified|dismissed` (`main.py:856`).
- Foot: `Sync` `readReportOutbox()` count + `CloudOff` `navigator.onLine===false`, `POST /api/reports` `429` rate cap 20.

**What was stub before**: `OpsQueuePreview` was not there — `ZoneIntelligencePanel` showed only one report. Now it is the triage.

### 5c. `road` → `RoadStatusCard` + Catalogue

**What it is**: Road truth + pre-emptive advice.

**Contains**:
- `GET /api/roads/status` live segments `R1 BLOCKED` `R2 AT-RISK` `R3 OPEN` `R4 OPEN` (no `GET /api/...` string header — now `Gangtok Corridor · 4 segments`).
- `GET /api/roads/restrictions` `evaluation[].restricted` `emergency_route:true stays open` + `GET /api/zones/{id}/exposure` `operational_risk delta` `buildings_downstream 85` `runout` — district sees *restriction even when open* (`Adjacent S1 is ALERT (69) — pre-emptive restriction per catalogue 12 slides` `road_restriction_catalogue.json:1`).
- **Villager never sees this catalogue** — only district+rescue.

**Hidden keep**: `<div className="hidden" aria-hidden><ZoneIntelligencePanel /></div>` — keeps `ZoneIntelligencePanel` mounted so `selectZone` cache (`data.store` + `model_service daily_history`) stays hot when you switch tabs — senior dev insisted on this for `OPS cache correctness`.

---

## 6. Bottom Anchor — Legacy Duplicate to Remove

**File**: `DistrictPage.jsx:71`
```jsx
<div id="ops-alerts" className="bg-white border-2 border-zinc-200 rounded-2xl p-4">
  <h3 className="text-xs font-black text-zinc-900">Road Network — Operational</h3>
  <div className="mt-2"><RoadStatusCard /></div>
</div>
```
- **What it is**: Duplicate `RoadStatusCard` outside tabs, anchored by `id="ops-alerts"` so the top `Bell` `district.multilang` button `scrollIntoView({behavior:'smooth'})` scrolls here.
- **Upgrade**: Remove duplicate `RoadStatusCard` outside tabs — keep the `id` anchor but make it scroll to `road` tab instead (`setTab('road'); document.getElementById('ops-alerts')?.scrollIntoView()`). Double fetch is waste.

---

## 7. Data Flow (Live-Only, No Stub on Map) — The Contract You Must Keep

```
GET /api/zones?location=gangtok  → zones[]  → RiskMap polygons + pills (live, fallback MINE_ZONES only on !ok → ErrorState)
GET /api/zones/{id} + features + explanation + trend + decision?lang  → ZoneIntelligencePanel (intel)
GET /api/warning/state 6-state + GET /api/isolation R4 + GET /api/soil/swi + GET /api/aws/gauges 15-min + GET /api/replay/series → WarningStateCard + IsolationAlertCard (sticky)
GET /api/roads/status + GET /api/roads/restrictions + GET /api/zones/{id}/exposure → RoadStatusCard (road tab)
GET /api/reports/queue + PATCH → OpsQueuePreview (queue tab)
All via frontend/src/services/api.js:7 BASE_URL VITE_API_URL apiRequest with throw on !ok → ErrorState, never invented.
```

**Fixed values that are *not* stubs** (keep): `locations.js:290` 8 corridors `gangtok…mizoram` `27.0844,93.6053` etc — these are *centers* for `Map flyTo`, not scores. `RISK_BANDS` `50/65/75/85` `SCAFFOLD_CONTRACT_SEPT5.md:14` frozen, `RISK_WEIGHT 3.0` `alpha 0.2` `routing/comparison.py`.

**Stubs that must never return on map** (gone: `FEATURE_ISOLATION` 2025-11): `89` literal in JSX, `12m` fixed, `sensorIds:["IMD-GTK-01"]` static, `FILL`, `STUB` rows. Validator `validate_ngen_sample.py:49` `32×22` `MAX_ROWS 40` + `check_scaffold.py:1` `SCAFFOLD OK 89/78/66/52` guard this.

---

## 8. Verify (Stop If Any Fail) — Your Upgrade Definition of Done

```bash
C:\Users\satvi\Desktop\mnemo\.venv\Scripts\python.exe scripts/check_scaffold.py  # SCAFFOLD OK
python scripts/validate_ngen_sample.py  # NGEN SAMPLE OK 22 cols 32×22 MAX_ROWS 40
pytest backend/tests -q --ignore=test_api,causal  # 49 passed 2 skipped
npm run build  # frontend/dist 304kB vite 6.21s
curl /api/zones?location=gangtok | jq .zones[0].geometry  # has centroid, not MINE_ZONES hard-code
curl /api/roads/status | jq .segments[0].status  # live
```
**Done when**: district map shows *only* live polygons/roads/sensors/runout/wound, no `89` literal, no `GET /api/...` string on `RoadStatusCard`, and `queue` tab verifies a `flagged` report in <10s with thumb + `Verify`.

---

**Next**: Same surgical diff for `StatePage.jsx` (matrix → `CorridorComparison` `operational_risk`, `PanchayatTiles` 100, `TrustLedger`) and `RescuePage.jsx` (red banner `ExposureCard` `RouteComparison` green vs red) — Villager stays light (<50KB, no SHAP).

