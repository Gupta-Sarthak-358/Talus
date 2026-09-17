# CBE (Cell Broadcast Entity) Contract — Carrier Bearer Beyond SMS

**Why beyond SMS**: Govt drill CB bypasses SMS queue, shows as system alert even with Do Not Disturb, no number needed. Requires DoT/NIC + carrier CBE integration (RESEARCH:127). Talus keeps same `POST /api/alerts/dispatch` contract; CB is a second bearer.

**Contract**:
```
POST /api/alerts/cbe
Headers: Authorization: Bearer <ADMIN_JWT> (future), Content-Type: application/json
Body: {
  "area": "gangtok|S1|district:east-sikkim|polygon:[...]",
  "message": {"en":"Tathangchen landslide — evacuate via valley", "hi":"...", "ne":"..."},
  "severity": "Extreme|Severe",
  "expires_at": "2025-11-14T12:00:00Z",
  "channel": "CB"
}
Response: { "cbe_id":"CBE-20251114-001", "area":..., "broadcast":"queued", "provider":"sachet|carrier-cbe|stub", "simulated":true }
Audit: runs/cbe_dispatch.jsonl (no PII, area + message + provider status)
```

**Env-gated**:
```
CBE_PROVIDER=sachet|carrier
CBE_API_URL=https://cbe.dot.gov.in/api/broadcast
CBE_API_KEY=***
```
When absent (SIH demo), endpoint logs to `runs/cbe_dispatch.jsonl` with `simulated:true` — never fake `broadcast:success` (like SMS lane `main.py:959`). When set, it POSTs to CBE and logs `cbe_id` + http code.

**Frontend**: `AlertPanel.jsx` channel toggle `app|sms|CB` — CB only visible to `admin/state` (PIN 9999/2222), shows `CB bearer (DoT)` badge + `Simulated until CBE provisioned`.

**Verification**: `curl -X POST /api/alerts/cbe -d '{"area":"S1","message":{"en":"test"}}'` → `simulated:true` now, `broadcast:queued` after CBE key.
