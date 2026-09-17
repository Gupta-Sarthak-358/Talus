# Feature: Isolation — “Only Road Blocked” & Authority Ping

**PS linkage**: FR-07 (road connectivity), FR-09 (GIS), FR-11 (alerts), FR-13 (exposure). Solves: *what if the only road is landslide-blocked and a village loses egress to valley/plains?* System predicts isolation before it happens and pings authorities.

## 1. What it does (one-liner)
If a village’s only egress road is blocked (or down to one at-risk road while slope risk is High/Critical), the system raises `ISOLATED` (or `MAY_ISOLATE` pre-alert), escalates warning state to `EVACUATE`/`RESTRICT`, shows a plain-language banner to villagers/officers, logs an authority alert, and (when enabled) auto-dispatches SMS/app.

## 2. User-visible behavior
- **Villager** `role/villager` sees `IsolationAlertCard.jsx:1`:  
  `Isolation — S1 cut off. Only road to S1 is blocked. No alternative. People in S1 cannot reach valley via S4.` + `Stage machines at S4`. No scores, no Brier.
- **District/State** sees same + `WarningStateCard.jsx:6` state becomes `EVACUATE` (red pulse) with reason `ISOLATED — R4 approach blocked — no egress to plains → EVACUATE`. Pre-alert shows `May isolate if last road blocks — RESTRICT road` (amber).
- **Rescue** gets `isolated_zones` list to prioritize air/heavy-lift.
- **No extra click needed** — isolation is derived from live `roads/status` + live `risk_band` every request; authorities are pinged via auto-watcher without manual dispatch.

## 3. Backend contract
**File**: `backend/app/main.py:1182` `_isolation_for_location()`
- **Inputs**: `GET /api/roads/status?location=gangtok` `R1 blocked / R2 at-risk / R3 open / R4 open` (`data/sih26001/fixtures/roads.json:1` demo topology, provenance `roads_osm_provenance.json:1` 1014/226/504 ways count) + live `store.risk`/`risk_band` per `sih26001_model.py:95` (or frozen 89/78/66/52).
- **Bottleneck rule** (deterministic, matches fixture):
  - `R4 == blocked` → `S1,S2,S3` (`N1,N2,N3` etc) `ISOLATED` — no plains egress even if own spur open.
  - Else per-zone `adj_map`: `S1:[R1,R2,R3] S2:[R2,R3] S3:[R3,R4] S4:[R4]` ; `all blocked` → `ISOLATED`.
  - `open==0 && at-risk==1 && band High/Critical` → `MAY_ISOLATE` ; `R2 at-risk && S1 High/Critical` → `MAY_ISOLATE` (pre-alert).
- **Outputs**: `GET /api/isolation?location=gangtok` → `{corridor_isolated, corridor_may_isolate, isolated_zones:[S1], at_risk_zones, valley_hub:S4, bottleneck:{R1..R4}, zones:[{zone_id, isolated, may_isolate, status:ISOLATED|MAY_ISOLATE|OPEN, adjacent_roads/statuses, reason, score, band}], action, generated_at}`.

**Warning integration**: `GET /api/warning/state?location=gangtok&lang=en` `backend/app/main.py:1342` merges isolation:
- `ISOLATED` → `state=EVACUATE` `action: EVACUATE S1 now… immediate`
- `MAY_ISOLATE` → `state=RESTRICT` (if was ALERT/CRITICAL) → `RESTRICT S1 road, hold team… high`

**Auto-ping**: `backend/app/main.py:1476` `_auto_should_fire()` + `auto_watcher_loop` (`AUTO_ALERT_ENABLED=true` `AUTO_ALERT_INTERVAL_S=60` `AUTO_ALERT_COOLDOWN_S=3600`): every 60s scans all corridors, builds `[AUTO] S1 ISOLATED: … Action: …`, chooses `channel=sms` if `AUTO_ALERT_SMS=true && SMS_PROVIDER+SMS_API_KEY` else `app`, logs to `runs/alert_dispatch.jsonl` via `_append_dispatch_log` (no fake success). Endpoints `GET /api/alerts/auto/status` + `POST /api/alerts/auto/trigger?location=gangtok` for demo/judge. Manual officer dispatch also available `POST /api/alerts/dispatch?channel=app|sms&lang=en&zone_id=S1`.

## 4. Frontend wiring
- `frontend/src/components/Alerts/IsolationAlertCard.jsx:1` polls `GET /api/isolation` per `activeLocation` (no `SIM` badge for villager path) → `Isolated` red `ShieldAlert` / `May isolate` amber `AlertTriangle` with `R1…R4` bottleneck + `action`.
- `frontend/src/pages/roles/VillagerPage.jsx:3` + `DistrictPage.jsx:7` mount card above map.
- `frontend/src/components/Routing/RoadStatusCard.jsx:1` shows segment statuses `R1 BLOCKED` `R2 AT-RISK` etc; isolation uses same source.

## 5. Risk prediction link
Isolation status is **predictive** via `may_isolate` + `warning_state` threshold overlay (`warning_thresholds.json S1 385`, SWI `swi.py L1=15 L2=60 L3=60`, `effective_rain ≥ thr_q` with quake factor 0.75). After a certain level (High/Critical + last road at-risk) it pre-alerts authorities *before* the road actually blocks — exactly “it predicts the risk, after a certain level it would alert”.

## 6. Who is pinged
- `AdminPanel.jsx` `/admin` (PIN 9999 etc) dispatch log shows `auto:true isolation_status:ISOLATED` per zone; district/state/rescue dashboards show isolation banner; villagers see plain banner. SMS (when `SMS_PROVIDER=msg91|fast2sms|twilio|textbelt` + `SMS_API_KEY` + `SMS_TO` set) sends to `SMS_TO` list; otherwise `app` fixture logged as `SIMULATED` — never fake `sms_ok:true`.

## 7. Tests & verification
- `backend/tests/test_warning_state.py:1` includes `RESTRICT/EVACUATE` (6-state) and reason-stamp checks.
- Manual: `curl /api/isolation?location=gangtok` → `corridor_isolated false` baseline; set `R4` to `blocked` in `roads.json` → `S1,S2,S3 ISOLATED` + `GET /api/warning/state` → `EVACUATE S1` + `POST /api/alerts/auto/trigger` → `fired:true` entry in `GET /api/alerts/dispatch/log`.

## 8. Limits (honest)
- Geometry demo topology aligned to centroids (counts proven 1014/226/504, not OSM trace) per `roads_osm_provenance.json` + `08_LIMITATIONS_SIH26001.md`.
- Lithology uniform PROXY until `bhukosh_vector_attempt.json` WFS reachable — isolation does not use lithology.
- No Gram Panchayat household list — exposure uses `runout_exposure.json` buildings (S2 85) + wound 2 scars as proxy.
