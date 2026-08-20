# Talus API Specification

**Status:** Frozen for MVP · Trace to: `docs/01_REQUIREMENTS.md`, `docs/02_ARCHITECTURE.md`

This contract is the **seam** that lets the six-person team develop in parallel:

- Frontend can develop against mocked JSON.
- Backend can develop without waiting for frontend.
- ML can develop without waiting for backend.

**If this spec changes, update it and the architecture doc in the same PR.**

> **Feature name source of truth:** every value under `features` and `overrides` below must match exactly the ML-facing schema in **`docs/05_FEATURE_SCHEMA.md`** — that document owns the 12 field names/types/enums. This file only shows their shape in JSON.

---

## Base

- Base path: `/api`
- Format: JSON
- Prototype host: `http://127.0.0.1:8000`
- Errors: `{"detail": "..."}` with appropriate HTTP status.

---

## Endpoint List

```text
GET    /api/zones
GET    /api/zones/{id}
GET    /api/zones/{id}/features
GET    /api/zones/{id}/trend
GET    /api/zones/{id}/explanation
GET    /api/zones/{id}/decision

POST   /api/risk/predict
POST   /api/routes/safe
POST   /api/simulation/what-if
```

---

## GET /api/zones

Lists all mine zones with their current risk state.

**Response `200`:**

```json
{
  "zones": [
    {
      "zone_id": "A",
      "risk_score": 32,
      "risk_band": "Low",
      "confidence": 0.74,
      "trend": "stable"
    }
  ]
}
```

## GET /api/zones/{id}

Zone detail including geometry reference.

**Response `200`:**

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

**`404`** if the zone does not exist.

## GET /api/zones/{id}/features

Current feature values for the zone.

**Response `200`:**

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

## GET /api/zones/{id}/trend

Risk history and escalation status.

**Response `200`:**

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

## GET /api/zones/{id}/explanation

SHAP feature contributions for the zone's current risk.

**Response `200`:**

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

## GET /api/zones/{id}/decision

Role-specific recommendations for the zone's current state.

**Response `200`:**

```json
{
  "zone_id": "B",
  "risk_score": 86,
  "risk_band": "Critical",
  "decisions": [
    {"role": "worker", "message": "Avoid Zone B", "action": "safe route guidance", "priority": "immediate"},
    {"role": "safety_officer", "message": "Prioritize inspection of Zone B", "action": "early risk intervention", "priority": "high"},
    {"role": "mine_manager", "message": "Coordinate evacuation of Zone B", "action": "operational decision", "priority": "high"},
    {"role": "rescue_team", "message": "Use safer approach route to Zone B", "action": "risk-aware response", "priority": "standby"}
  ]
}
```

---

## POST /api/risk/predict

Compute risk for a zone from current features.

### Request

```json
{
  "zone_id": "B",
  "features": {
    "rainfall_24h_mm": 55.0,
    "rainfall_7d_mm": 210.0,
    "slope_angle_deg": 60.0,
    "slope_height_m": 48.0,
    "rock_type": "sandstone",
    "crack_density": 0.6,
    "blast_frequency_per_week": 3.0,
    "blast_vibration_ppv_mms": 12.0,
    "days_since_inspection": 20,
    "prior_incident": 1,
    "groundwater_proxy": 0.6
  }
}
```

### Response `200`

```json
{
  "zone_id": "B",
  "risk_score": 86,
  "risk_band": "Critical",
  "confidence": 0.82,
  "missing_evidence": ["vibration_sensor"]
}
```

---

## POST /api/routes/safe

Compute a risk-aware route between two points.

### Request

```json
{
  "start": {"zone_id": "E", "lat": 20.5, "lng": 80.1},
  "end": {"zone_id": "G", "lat": 20.6, "lng": 80.2}
}
```

### Response `200`

```json
{
  "risk_aware_route": {
    "path": [{"lat": 20.5, "lng": 80.1}, {"lat": 20.55, "lng": 80.15}, {"lat": 20.6, "lng": 80.2}],
    "total_cost": 3.2,
    "max_risk_exposed": 42
  },
  "shortest_route": {
    "path": [{"lat": 20.5, "lng": 80.1}, {"lat": 20.53, "lng": 80.15}, {"lat": 20.6, "lng": 80.2}],
    "total_cost": 2.1,
    "max_risk_exposed": 86
  },
  "avoided_zones": ["B"]
}
```

---

## POST /api/simulation/what-if

Recompute risk under simulated changed conditions.

### Request

```json
{
  "zone_id": "B",
  "overrides": {
    "rainfall_24h_mm": 80.0,
    "blast_frequency_per_week": 5.0
  }
}
```

### Response `200`

```json
{
  "zone_id": "B",
  "baseline": {"risk_score": 48, "risk_band": "Moderate", "confidence": 0.78},
  "simulated": {"risk_score": 71, "risk_band": "High", "confidence": 0.75},
  "delta": 23,
  "contributions": [
    {"feature": "rainfall_24h_mm", "shap_value": 14.2},
    {"feature": "blast_frequency_per_week", "shap_value": 6.3}
  ]
}
```

---

## Shared Enumerations

### Risk bands

```text
Very Low | Low | Moderate | High | Critical
```

### Trends

```text
stable | rising | rapidly_increasing
```

### Roles

```text
worker | safety_officer | mine_manager | rescue_team
```

---

## Mock JSON

Frontend development should start from a checked-in mock JSON fixture (planned under `backend/tests/fixtures/`) mirroring these examples exactly.