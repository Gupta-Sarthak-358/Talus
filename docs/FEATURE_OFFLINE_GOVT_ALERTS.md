# Feature: Authority-Only Government Alerts (Cell-Broadcast-Style) + Offline Report Sync

**PS linkage**: FR-10 (geo-tagged reports), FR-11 (multilingual early warning), FR-12 (low-network/offline), `support multilingual notifications and low-network/offline functionality for remote areas`. Mirrors the 2024-25 government drill CB alerts that appear even with no data — Talus achieves the same via PWA + SMS fallback, authority-only send.

## 1. What it does (one-liner)
- **Authorities only** can send an alert with one click; every device in that corridor/zone receives it as a system-level banner — even offline — in 5 languages (en/hi/ne/as/bn).
- **Villagers offline** can still file a geo-tagged slope/road report with photo; it queues on the phone and syncs when connectivity returns. No binary committed; SHA-256 + EXIF verified.

## 2. Govt-drill parallel
Government Cell Broadcast (CB) used a one-to-many, tower-broadcast that bypassed data/Wi-Fi and showed as a full-screen drill alert. Talus replicates the **effect** with two layers:
- **Layer 1 — App CB (works offline)**: PWA cached alert is rendered as a top-banner + drawer the next time the app opens, even with `navigator.onLine===false`. `frontend/public/sw.js:1` `CACHE talus-shell-v1` cache-first shell (`/`, `/index.html`, `/manifest.webmanifest`, `icon-192.png`) + `frontend/src/utils/pwa.js:1` `registerPWA` ensures the UI loads offline. Alert JSON is cached in `localStorage` + `runs/alert_dispatch.jsonl` audit; `AlertPanel.jsx` shows `Sync Badge: Cached on device. Queued sync when network returns.` (`alerts.syncBadge`/`alerts.cached`).
- **Layer 2 — SMS CB fallback (works with only 2G)**: When `AUTO_ALERT_SMS=true` and `SMS_PROVIDER+SMS_API_KEY` set, `backend/app/main.py:915` `_sms_send` fans out via `msg91`/`fast2sms`/`twilio`/`textbelt` to `SMS_TO` list — reaches phones with no data, like CB. Env-gated; without keys it logs `SIMULATED` — never fake `sms_ok`.

Real CB requires carrier integration (future per `RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:127`); this layered app+SMS is the honest SIH-grade substitute.

## 3. Authority-only gate
- **PIN gate** `frontend/src/services/auth.js:1` `PINS` `villager:'' open / district:1111 / state:2222 / rescue:3333 / admin:9999` stored `talus_auth` `localStorage`. `RoleSelector.jsx` intercepts `pickRole()` — non-villager prompts `LoginModal.jsx:1` (PIN). `/admin` additionally checks `auth.role===admin|state|district`.
- **Backend gate** (future JWT, currently fixture): `POST /api/alerts/dispatch` `backend/app/main.py:959` accepts `channel/app|sms&lang=en&zone_id=S1&message=…` — district/state/admin are the callers; villager UI has no send button (only `Receive` drawer). Dispatch log records `zone_id, lang, channel, auto:true|false, provider`.
- **One-click send**: `frontend/src/components/Alerts/AlertPanel.jsx:32` `handleDispatch()` → `POST /api/alerts/dispatch?channel=app|sms&lang=as|bn|…` . Language tabs `EN/HI/NE/AS/BN` (`translations.js:1` 5 tables). `App` channel = fixture `data/sih26001/fixtures/alerts.json:1` offline demo; `SMS` = env-gated real. After send, panel shows `DISPATCHED | SIMULATED | SENT · provider` + last 5 `GET /api/alerts/dispatch/log` entries. Auto-watcher also auto-fires on `EVACUATE/RESTRICT` isolation (`POST /api/alerts/auto/trigger`).

## 4. Who receives / where it appears
- **Corridor + zone targeted**: `?location=gangtok|lachung|darjeeling&zone_id=S1` fans to all devices that have that corridor selected; villager page shows banner `IsolationAlertCard` + bell drawer `AlertPanel` with `severity CRITICAL/HIGH`, `roleDirectives[role]` per `data/sih26001/fixtures/alerts.json:1` + `DECISIONS_BY_BAND` `backend/app/main.py:55` (4 bands ×4 roles) + translations `DECISIONS_TRANSLATIONS`.
- **Offline receipt**: SW caches shell, so `GET /` renders without network; `IsolationAlertCard` + `WarningStateCard` last cached `GET /api/warning/state` + `GET /api/isolation` still render; new alerts appear on next online poll (15s `live/feed` + on-demand `dispatch/log`). SMS arrives even if app offline.

## 5. Offline report sync (the other half of “offline way to send reports if no connectivity”)
- **Submit** `frontend/src/components/Reports/ReportModal.jsx:1`: real file → `sha256File` (WebCrypto or fallback) + `readExifGps` JPEG APP1 parser + `makePhotoThumbnail` ≤320px canvas + `PhotoMeta` `{filename,mime,size,sha256,exif_lat/lon}` `schemas.py:258` `ReportIn` `{zone_id 12 S1-D4/N1, type, text 10-500, lat/lon pilot bbox 26.9-27.8/88.1-88.9, captured_at ISO, reporter_role, photo, consent:true}`. 15 tests `test_reports.py:1`.
- **If offline / 5xx / 429**: `saveReportOutbox` pushes `{payload, thumb, outboxId:PEND-…}` to `localStorage talus_report_outbox`; `savePhotoBackground` keeps thumb in `talus_report_photos` (bytes never committed, `.gitignore` + `PHOTO_STORE_KEY` per `TalusContext.jsx`).
- **Sync**: `frontend/src/context/TalusContext.jsx:245` `refreshReports()` flushes outbox oldest-first `POST /api/reports` → on success `savePhotoBackground` + `dropReportOutbox`; `ReportModal` shows `CloudOff` banner + `Sync` button with pending count. `GET /api/reports/queue` + `PATCH /api/reports/{id}` state machine `queued|flagged→verified|dismissed` terminal guard `backend/app/main.py:856`.

## 6. APIs
- `POST /api/alerts/dispatch?channel=app|sms&lang=en|hi|ne|as|bn&zone_id=S1&message=…` → fixture or `{simulated, sms_ok, provider}` log
- `GET /api/alerts/dispatch/log?limit=50`
- `GET /api/alerts/auto/status` / `POST /api/alerts/auto/trigger?location=gangtok`
- `POST /api/reports` `GET /api/reports/queue?status=queued` `PATCH /api/reports/{id}`
- PWA: `GET /health` `GET /manifest.webmanifest` `GET /sw.js` (cache-first shell, `/api` network-only)

## 7. Tests & verification
- Offline: DevTools → Offline → reload `/` → shell loads, `LiveFeedCard.jsx:59` shows `Sync Badge`, `ReportModal` → submit → outbox length 1 in `localStorage talus_report_outbox` → back online → `Sync` → `POST /api/reports 200` → queue shows new entry.
- Alerts: as `district_officer` (PIN 1111) open `AlertPanel` → pick `AS/BN` → `channel=SMS` → `Dispatch` → without env shows `SIMULATED` + entry in `GET /api/alerts/dispatch/log`; with `SMS_PROVIDER=textbelt` + `SMS_API_KEY` + `SMS_TO` set shows `SENT`.
- Screw: `C:\Users\satvi\Desktop\mnemo\.venv\Scripts\python.exe -m pytest backend/tests --ignore=test_api --ignore=test_causal -v` 35 passed includes `test_reports` 15 + `test_alerts_ack` + `test_dispatch`.

## 8. Limits (honest)
- Real cell broadcast needs carrier/NIC integration + DoT approval — Talus uses app+SMS fallback; not a true CB bearer (documented `RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md` and `08_LIMITATIONS`).
- Reports need `consent:true` and `captured_at` honest ISO (`backend/app/main.py:885` >1h future → 422).
- Map/zone polygons are NGEN demo-scale (12 slopes S/D/N), not Gram Panchayat household list — exposure uses `runout_exposure.json` building counts + wound 2 scars proxy.
