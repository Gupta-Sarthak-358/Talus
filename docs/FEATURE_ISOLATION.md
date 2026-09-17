# Feature — Isolation Detection & Authority Ping (Path Not Available)

**Problem (PS):** NER villages are cut off for days when the only access road blocks (landslide, debris). Current monitoring is reactive — authorities learn only after villagers call. Need predictive "no path" detection.

**What Talus does:** Predicts isolation *before* it is total. If a village's last road is at risk while its slope is High/Critical, Talus pre-alerts. If the last road is blocked, Talus escalates to `EVACUATE` and pings district/state/rescue automatically.

---

## 1. Rule (deterministic, matches `roads.json` topology)

Fixture `data/sih26001/fixtures/roads.json:1`:
- `R1` Tathangchen link — `blocked`, adjacent `S1`
- `R2` Ridge shortcut `S1-S4` — `at-risk`, adjacent `S1`
- `R3` Valley road `S3-S4` — `open`, adjacent `S3`
- `R4` Ranipool approach — `open`, adjacent `S4` (valley hub to plains)

Per-corridor shifted via `backend/app/main.py:842` `_ROAD_SHIFT` + `frontend/src/data/locations.js:241` (same constants).

**Isolation = no egress to the valley hub `S4/N4/D4`.**

```python
# backend/app/main.py:1182 _isolation_for_location(location)
adj_map = {
  "S1": ["R1","R2","R3"],
  "S2": ["R2","R3"],
  "S3": ["R3","R4"],
  "S4": ["R4"],
}
open_exits  = count(status == "open")
at_risk_exits = count(status == "at-risk")
downstream_blocked = (R4 == "blocked" and zid in {S1,S2,S3})  # bottleneck to plains
direct_blocked     = all(s == "blocked" for s in adj)
isolated = downstream_blocked or direct_blocked
may_isolate = (open_exits==0 and at_risk_exits==1 and band in {High,Critical})
           or (R2 at-risk and zid==S1 and band in {High,Critical})
```

**Downstream bottleneck:** if `R4` blocks, `S1,S2,S3` are isolated even if their own spur is open. This is the DM's real question: "who loses plains egress?"

## 2. Warning-state integration

`GET /api/warning/state?location=gangtok&lang=en` `backend/app/main.py:1342` now merges isolation:

- `isolated` → zone `state = EVACUATE`, reason `ISOLATED — R4 blocked — no egress to plains → EVACUATE`, action `EVACUATE S1 now. Stage machines at S4 valley…` `priority immediate`
- `may_isolate` → `RESTRICT`, reason `May isolate if the last road blocks — RESTRICT road`, action `RESTRICT S1 road, hold team…`

Corridor rollup becomes `EVACUATE` if any isolated, else `RESTRICT` if any `may_isolate`. `STATE_STYLE` `frontend/src/components/Alerts/WarningStateCard.jsx:6` `RESTRICT amber`, `EVACUATE red pulse`.

Effective rain uses local thresholds `data/sih26001/evidence/warning_thresholds.json:1` `S1 385 S2 395 S3 410 S4 375`, lowered 25% for 6 months after `M>5.5 <50km` (`usgs_quakes.json:1` → `seismic_n50_rate`) per `RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:28`, and SWI 3-tank `backend/app/swi.py:1`.

## 3. Ping to authorities

**Auto watcher** `backend/app/main.py:1483` `_auto_dispatch_once()` polls every `AUTO_ALERT_INTERVAL_S=60` (`env`), deduplicates `AUTO_ALERT_COOLDOWN_S=3600` per `location:zone:status`.

- Triggers on `ISOLATED/MAY_ISOLATE` from `_auto_should_fire`.
- Builds officer message via `_decisions(zid, score, "en")` + isolation reason: `[AUTO] S1 MAY_ISOLATE: only one at-risk road left … Action: Close the S1 stretch…`
- Channel: `app` always (logged to `runs/alert_dispatch.jsonl` via `_append_dispatch_log:1051`); `sms` only if `AUTO_ALERT_SMS=true` + `SMS_PROVIDER` + `SMS_API_KEY` set → `_sms_send:1004` (`msg91|fast2sms|twilio|textbelt`), else `simulated:true` logged — no fake success.
- Manual trigger for demo/judge: `POST /api/alerts/auto/trigger?location=gangtok` `backend/app/main.py:1580` returns `would_fire`.

Every dispatch is auditable:

```
GET /api/alerts/dispatch/log?limit=50
GET /api/isolation?location=gangtok
GET /api/warning/state?location=gangtok
GET /api/alerts/auto/status
```

## 4. Frontend

- `frontend/src/components/Alerts/IsolationAlertCard.jsx:1` — shown on `VillagerPage.jsx:3` (plain: "Only road to S1 is blocked. No alternative. People in S1 cannot reach the valley.") + `DistrictPage.jsx:7` + `StatePage` (action + bottleneck `R1 blocked · R2 at-risk…`). Connects to `GET /api/isolation`.
- `WarningStateCard.jsx:1` — shows per-zone `reasons` + `kit` + `action`. Isolated zones appear as `EVACUATE`.
- `GET /api/zones/{id}/exposure` `backend/app/main.py:743` merges `runout_exposure.json` buildings + `wound_map.json` + isolation → `operational_risk` (hazard amplified by exposure log).

## 5. Demo

1. Baseline `GET /api/isolation?location=gangtok` → `corridor_isolated false`, `S1 OPEN` (R3 open).
2. Officer closes `R4` (or set `roads.json` `R4 status blocked` and restart) → `GET /api/isolation` → `S1,S2,S3 ISOLATED`, `action: Stage machines at S4 valley…`.
3. `GET /api/warning/state` → `S1 EVACUATE`.
4. Watcher fires within 60s → `GET /api/alerts/dispatch/log` shows `auto:true zone_id S1 ISOLATED`.

## 6. Limitations & Next

- `roads.json` geometry is demo topology (OSM count proven `1014/226/504` `roads_osm_provenance.json:1`, trace not yet per-segment). Replace with NH310A `way 47416074` trace when approved.
- Lithology/lineament uniform `lingtse_granite_gneiss` `0.8` via `bhukosh_vector_attempt.json:1` timeout — not per-slope vector.
- Auto SMS is opt-in (`AUTO_ALERT_SMS=false` default) — prevents spam; enable only with `SMS_PROVIDER` + `SMS_TO`.

See also `docs/RESEARCH_WARNING_SYSTEMS_TW_JP_NP.md:58` road pre-emptive restriction catalogue `GET /api/roads/restrictions`.
