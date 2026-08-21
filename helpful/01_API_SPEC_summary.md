# API Spec Summary (docs/05_API_SPEC.md)

Status: **FROZEN for MVP** — build exactly this. Do not rename fields, do not
add fields, do not change status codes without updating the spec.

## Base

- Base path: `/api`
- Format: JSON
- Prototype host: `http://127.0.0.1:8000`
- Errors: `{"detail": "..."}` with appropriate HTTP status

## Endpoints at a glance

```
GET    /api/zones                     → list all zones + risk state
GET    /api/zones/{id}                → one zone detail + geometry
GET    /api/zones/{id}/features       → current 12 feature values
GET    /api/zones/{id}/trend          → risk history + escalation flag
GET    /api/zones/{id}/explanation    → SHAP contributions
GET    /api/zones/{id}/decision       → role-specific recommendations
POST   /api/risk/predict              → risk from supplied features
POST   /api/routes/safe               → risk-aware route (vs shortest)
POST   /api/simulation/what-if        → risk under changed conditions
```

---

## 1. GET /api/zones

Lists all zones with current risk.

```json
{
  "zones": [
    {"zone_id": "A", "risk_score": 32, "risk_band": "Low", "confidence": 0.74, "trend": "stable"}
  ]
}
```

## 2. GET /api/zones/{id}

Zone detail including geometry reference.

```json
{
  "zone_id": "B",
  "name": "Zone B — NW bench",
  "geometry": {"type": "Polygon", "coordinates": []},
  "risk_score": 48,
  "risk_band": "Moderate",
  "confidence": 0.78,
  "trend": "rising",
  "updated_at": "2026-08-19T09:00:00Z"
}
```

**404** if zone does not exist.

## 3. GET /api/zones/{id}/features

Current feature values. Note `missing_features` array — evidence gaps are
reported here, never by changing field types.

```json
{
  "zone_id": "B",
  "features": {
    "rainfall_24h_mm": 35.0,
    "rainfall_7d_mm": 140.0,
    "slope_angle_deg": 58.0,
    "slope_height_m": 45.0,
    "rock_type": "sandstone",
    "crack_density": 0.42,
    "crack_severity": "moderate",
    "blast_frequency_per_week": 2.0,
    "blast_vibration_ppv_mms": 9.5,
    "days_since_inspection": 12,
    "prior_incident": 0,
    "groundwater_proxy": 0.35
  },
  "missing_features": ["vibration_sensor"]
}
```

## 4. GET /api/zones/{id}/trend

```json
{
  "zone_id": "B",
  "rapid_increase": true,
  "history": [
    {"t": "2026-08-19T08:00:00Z", "risk_score": 41},
    {"t": "2026-08-19T09:00:00Z", "risk_score": 48},
    {"t": "2026-08-19T10:00:00Z", "risk_score": 61}
  ]
}
```

## 5. GET /api/zones/{id}/explanation

```json
{
  "zone_id": "B",
  "risk_score": 86,
  "base_value": 45,
  "contributions": [
    {"feature": "rainfall_24h_mm", "shap_value": 14.2},
    {"feature": "crack_density", "shap_value": 12.8},
    {"feature": "slope_angle_deg", "shap_value": 9.1},
    {"feature": "blast_vibration_ppv_mms", "shap_value": 4.9}
  ]
}
```

## 6. GET /api/zones/{id}/decision

Four roles, same risk, different message:

```json
{
  "zone_id": "B",
  "risk_score": 86,
  "risk_band": "Critical",
  "decisions": [
    {"role": "worker",          "message": "Avoid Zone B", "action": "safe route guidance", "priority": "immediate"},
    {"role": "safety_officer",  "message": "Prioritize inspection of Zone B", "action": "early risk intervention", "priority": "high"},
    {"role": "mine_manager",    "message": "Coordinate evacuation of Zone B", "action": "operational decision", "priority": "high"},
    {"role": "rescue_team",     "message": "Use safer approach route to Zone B", "action": "risk-aware response", "priority": "standby"}
  ]
}
```

## 7. POST /api/risk/predict

Request — same 12 features (note: `crack_severity` is optional in the spec
example — the model runs on the rest):

```json
{
  "zone_id": "B",
  "features": {
    "rainfall_24h_mm": 55.0, "rainfall_7d_mm": 210.0, "slope_angle_deg": 60.0,
    "slope_height_m": 48.0, "rock_type": "sandstone", "crack_density": 0.6,
    "blast_frequency_per_week": 3.0, "blast_vibration_ppv_mms": 12.0,
    "days_since_inspection": 20, "prior_incident": 1, "groundwater_proxy": 0.6
  }
}
```

Response:

```json
{
  "zone_id": "B",
  "risk_score": 86,
  "risk_band": "Critical",
  "confidence": 0.82,
  "missing_evidence": ["vibration_sensor"]
}
```

## 8. POST /api/routes/safe

Request:

```json
{
  "start": {"zone_id": "E", "lat": 20.5, "lng": 80.1},
  "end":   {"zone_id": "G", "lat": 20.6, "lng": 80.2}
}
```

Response — compare risk-aware vs shortest, plus which zones were avoided:

```json
{
  "risk_aware_route": {"path": [{"lat": 20.5, "lng": 80.1}, {"lat": 20.55, "lng": 80.15}, {"lat": 20.6, "lng": 80.2}], "total_cost": 3.2, "max_risk_exposed": 42},
  "shortest_route":    {"path": [{"lat": 20.5, "lng": 80.1}, {"lat": 20.53, "lng": 80.15}, {"lat": 20.6, "lng": 80.2}], "total_cost": 2.1, "max_risk_exposed": 86},
  "avoided_zones": ["B"]
}
```

## 9. POST /api/simulation/what-if

Request:

```json
{
  "zone_id": "B",
  "overrides": {"rainfall_24h_mm": 80.0, "blast_frequency_per_week": 5.0}
}
```

Response:

```json
{
  "zone_id": "B",
  "baseline":   {"risk_score": 48, "risk_band": "Moderate", "confidence": 0.78},
  "simulated":  {"risk_score": 71, "risk_band": "High", "confidence": 0.75},
  "delta": 23,
  "contributions": [
    {"feature": "rainfall_24h_mm", "shap_value": 14.2},
    {"feature": "blast_frequency_per_week", "shap_value": 6.3}
  ]
}
```

---

## Shared enums (use these exact strings)

| Concept | Values |
|---|---|
| Risk bands | `Very Low`, `Low`, `Moderate`, `High`, `Critical` |
| Trends | `stable`, `rising`, `rapidly_increasing` |
| Roles | `worker`, `safety_officer`, `mine_manager`, `rescue_team` |

## Housekeeping

- Frontend develops against a checked-in mock JSON fixture (planned under
  `backend/tests/fixtures/`) mirroring these examples exactly — create it.
- If the spec changes: update spec + architecture doc in the same PR.
