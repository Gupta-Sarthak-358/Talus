# Feature 1 — Auto-Ping Authorities When No Road Remains (Isolation Engine)

**Status:** Built (2025-11-14) — `GET /api/isolation` + `GET /api/warning/state` + auto watcher `POST /api/alerts/auto/trigger`. Proven in `backend/app/main.py:1182`.

**Problem (PS a+d+f):** In NER landslides often cut *the only road* (Tathangchen link R1, ridge shortcut R2, valley bottleneck R4 Ranipool). Villages become physically isolated *after* the slide, when trucks/NGOs cannot enter. Manual reporting (“road blocked” phone call) is too late. System must *predict* isolation *before* the last road fails and *ping* officers the moment isolation occurs.

## 1. What the feature does

- **Before slide (May-Isolate):** When a slope is `High/Critical` and its village has only one `at-risk` road left (`R2` ridge shortcut `at-risk` while `S1` is `High 75+`), system raises `MAY_ISOLATE` + `RESTRICT` warning: “Single road left to S1 while High — if it blocks, village is cut off — restrict road, hold team”.
- **After slide (Isolated):** When the valley bottleneck `R4` (Ranipool approach, `emergency_route:true`) becomes `blocked`, all upstream villages `S1,S2,S3` (and `N1,N2,N3` / `D1,D2,D3`) are marked `ISOLATED` — “no egress to plains”. `S1` with `R1+R2+R3` all `blocked` is also `ISOLATED` even if `R4` is open. Corridor state jumps to `EVACUATE` (above `CRITICAL`).

Both states are *deterministic road-network* checks, not model scores — slope adjacency is irrelevant, only road egress to the valley hub `S4/N4/D4`.

## 2. How it is built

**Data:** `data/sih26001/fixtures/roads.json:1` 4 segments per corridor:
- `R1 Tathangchen link — blocked, adjacent_slope S1`
- `R2 Ridge shortcut S1-S4 — at-risk, adjacent_slope S1`
- `R3 Valley road S3-S4 — open, adjacent_slope S3`
- `R4 Ranipool approach — open, adjacent_slope S4, emergency_route:true` (`data/sih26001/evidence/road_restriction_catalogue.json:1` 12/8/5/3 historical slides).

Per-corridor geometry is shifted via `_ROAD_SHIFT` `backend/app/main.py:843` `gangtok (0,0) lachung (+0.35,+0.135) darjeeling (-0.298,-0.337)`. OSM presence verified `data/sih26001/evidence/roads_osm_provenance.json:1` 1014/226/504 ways (NH310A trunk 47416074), geometry stays demo topology for `R2-avoidance` determinism (`RISK_WEIGHT 3.0 ROUTING_ALPHA 0.2`).

**Engine:** `_isolation_for_location(location)` `backend/app/main.py:1189`:
```
r4_blocked = R4==blocked
downstream_blocked = r4_blocked and zid in {upper, mid, N2/D2}
direct_blocked = all(adj==blocked)
isolated = downstream_blocked or direct_blocked
may_isolate = (open==0 and at_risk==1 and band in High/Critical) or (R2 at-risk and upper High/Critical)
zones_out[].status = ISOLATED|MAY_ISOLATE|OPEN, reason, adjacent_roads/statuses, score/band
corridor_isolated / may_isolate + action: "Isolation: S1,S2,S3 cut off. Stage machines at S4 valley, dispatch rescue from south"
```

**Warning merge:** `GET /api/warning/state` `backend/app/main.py:1342` loads wound `wound_map.json`, forecast `Open-Meteo` 7d, quake `seismic_years_since`, local thresholds `warning_thresholds.json`, SWI `swi.py`. Then merges isolation: `ISOLATED → state=EVACUATE priority immediate`, `MAY_ISOLATE → RESTRICT priority high`. Corridor rollup `max(WARN_STATES)` with `EVACUATE` on top.

**Auto-ping:** Background watcher `backend/app/main.py:1506` (`AUTO_ALERT_ENABLED=true`, `_AUTO_INTERVAL_S=60`, `_AUTO_COOLDOWN_S=3600` dedup `location:zone:status`):
- Every 60s `_auto_should_fire` scans `GET /api/isolation` for `ISOLATED/MAY_ISOLATE`.
- Fires `POST /api/alerts/dispatch?channel=app| sms` per zone with message `[AUTO] S1 ISOLATED: R4 blocked — no egress to plains. Action: Close S1 stretch, evacuate Tathangchen upper first.` + officer decision per `DECISIONS_BY_BAND` `main.py:55` (en/hi/ne/as/bn).
- Channel `app` logs to `runs/alert_dispatch.jsonl` (`_append_dispatch_log:1051` no keys logged); channel `sms` attempts `msg91/fast2sms/twilio/textbelt` `main.py:915` only if `SMS_PROVIDER+SMS_API_KEY` set, else `simulated:true` — never fake success. Manual demo: `POST /api/alerts/auto/trigger?location=gangtok` returns `would_fire`.

**Frontend:** `frontend/src/components/Alerts/IsolationAlertCard.jsx:1` polls `GET /api/isolation?location=`:
- `ISOLATED` → red `ShieldAlert` “Isolation — S1 cut off. Only road to S1 is blocked. No alternative. People in S1 cannot reach the valley via S4. Bottleneck R1 blocked · R2 at-risk · R4 open. Stage machines at S4 valley… Alert sent to district & state authorities — response prioritized for isolated villages”.
- `MAY_ISOLATE` → amber `AlertTriangle` “May isolate — S1 at risk. Single road left while High — if it blocks, village cut”. Villager sees plain language, officer sees same + road IDs.
Shown on `VillagerPage.jsx:3` + `DistrictPage.jsx:7` above map. `AdminPanel` `/admin` `AdminPage.jsx` Isolation table shows `buildings_downstream` + `wound_near` counts.

**Ops risk:** `GET /api/zones/{id}/exposure` `main.py:743` merges hazard `score/band` + runout `runout_exposure.json` `buildings_n` + wound + isolation into `operational_risk score = hazard*(1+0.18 log1p(buildings)/3+0.12 wound+0.20 isolated)` — used for triage when isolated.

## 3. What authorities see (clean product)

- **Villager (`role/villager` open):** Big `EVACUATE S1` banner, map with `R4` blocked red, `RESTRICT S1 road, use valley route` in mother tongue, no Brier/IMD provenance.
- **District Officer (PIN 1111):** `IsolationAlertCard` + `WarningStateCard` `EVACUATE S1 → EVACUATE S1 now. Stage machines at S4`. One-tap `Reports` queue, roads `R4` red, route engine already avoids `R2`.
- **State/Rescue:** Same + cross-corridor triage (`lachung/darjeeling` via selector).

No “verified/provenance” sentences in field views — full `osm_provenance`, `Brier`, `warning_thresholds.json`, `swi.py` live in `/admin`.

## 4. Testing the drill

1. Baseline: `GET /api/isolation?location=gangtok` → `corridor_isolated false`.
2. Simulate slide: temporarily set `R4 status=blocked` in `roads.json` or via admin “Close segment” (future `POST /api/roads/close`), rerun `GET /api/isolation` → `S1,S2,S3 ISOLATED`, `GET /api/warning/state` → `corridor_state EVACUATE`, `IsolationAlertCard` red.
3. Auto-ping: `POST /api/alerts/auto/trigger?location=gangtok` → `fired:true, would_fire:[S1 ISOLATED …]`, `GET /api/alerts/dispatch/log?limit=5` shows `[AUTO]` entries with `auto:true`.
4. Recovery: set `R4=open` → `OPEN` again, watcher respects 1h cooldown (`_AUTO_LAST`).

## 5. Honest limits

- Geometry demo topology (counts proven, not OSM trace) per `roads_osm_provenance.json`. Real NH310A trace replace is future, isolation *logic* unchanged.
- 12 demo slopes `S1-4 N1-4 D1-4`, not Gram Panchayat scale. `R4` bottleneck assumption fits Gangtok pilot, needs per-corridor bottleneck config for full NER.
- SMS in pilot is `simulated` unless DoT/NDMA credentials provisioned — see `docs/FEATURE_CELL_BROADCAST_OFFLINE.md`.
