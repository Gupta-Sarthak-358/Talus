from fastapi.testclient import TestClient
import pytest

from app.data import store
from app.main import app

client = TestClient(app)

VALID_FEATURES = {
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
    "groundwater_proxy": 0.35,
}

EVENT1 = {**VALID_FEATURES, "rainfall_24h_mm": 55.0, "rainfall_7d_mm": 210.0, "groundwater_proxy": 0.45}
EVENT2 = {**EVENT1, "crack_density": 0.6, "crack_severity": "severe", "blast_frequency_per_week": 3.0,
          "blast_vibration_ppv_mms": 12.0, "days_since_inspection": 15, "groundwater_proxy": 0.5}


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield


def test_initial_zone_state_matches_demo():
    r = client.get("/api/zones")
    assert r.status_code == 200
    zones = {z["zone_id"]: z for z in r.json()["zones"]}
    assert zones["A"]["risk_score"] == 22
    assert zones["B"]["risk_score"] == 48
    assert zones["C"]["risk_score"] == 35
    assert zones["D"]["risk_score"] == 28


def test_zone_detail_404():
    assert client.get("/api/zones/ZZZ").status_code == 404


def test_explanation_score_matches_zone_detail():
    detail = client.get("/api/zones/B").json()
    explanation = client.get("/api/zones/B/explanation").json()
    assert explanation["risk_score"] == detail["risk_score"]
    assert len(explanation["contributions"]) > 0


def test_predict_event1_target_58_to_63():
    body = {"zone_id": "B", "features": EVENT1}
    r = client.post("/api/risk/predict", json=body)
    assert r.status_code == 200
    assert 58 <= r.json()["risk_score"] <= 63


def test_predict_event2_target_68_to_74():
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT1})
    r = client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT2})
    assert 68 <= r.json()["risk_score"] <= 74


def test_trend_flags_rapid_increase():
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT1})
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT2})
    r = client.get("/api/zones/B/trend")
    assert r.json()["rapid_increase"] is True


def test_decision_returns_four_roles():
    r = client.get("/api/zones/B/decision")
    roles = [d["role"] for d in r.json()["decisions"]]
    assert roles == ["worker", "safety_officer", "mine_manager", "rescue_team"]


def test_safe_route_avoids_high_risk_zone():
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT2})
    body = {
        "start": {"zone_id": "A", "lat": 20.51, "lng": 80.115},
        "end": {"zone_id": "D", "lat": 20.58, "lng": 80.165},
    }
    r = client.post("/api/routes/safe", json=body)
    assert r.json()["avoided_zones"] == ["B"]


def test_safe_route_requires_zone_id():
    body = {
        "start": {"lat": 20.51, "lng": 80.115},
        "end": {"zone_id": "D", "lat": 20.58, "lng": 80.165},
    }
    assert client.post("/api/routes/safe", json=body).status_code == 422


def test_what_if_reaches_critical():
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT2})
    body = {"zone_id": "B", "overrides": {"rainfall_24h_mm": 80.0}}
    r = client.post("/api/simulation/what-if", json=body)
    assert r.json()["simulated"]["risk_score"] >= 80
    assert r.json()["simulated"]["risk_band"] == "Critical"


def test_what_if_rejects_negative_rainfall():
    body = {"zone_id": "B", "overrides": {"rainfall_24h_mm": -5.0}}
    assert client.post("/api/simulation/what-if", json=body).status_code == 422


def test_what_if_rejects_invalid_enum():
    body = {"zone_id": "B", "overrides": {"rock_type": "banana"}}
    assert client.post("/api/simulation/what-if", json=body).status_code == 422


def test_what_if_rejects_unknown_override_field():
    body = {"zone_id": "B", "overrides": {"rainfall_24h": 80.0}}
    r = client.post("/api/simulation/what-if", json=body)
    assert r.status_code == 422
    assert "Unknown override fields" in r.json()["detail"]


def test_what_if_empty_overrides_returns_baseline():
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT2})
    body = {"zone_id": "B", "overrides": {}}
    r = client.post("/api/simulation/what-if", json=body)
    data_json = r.json()
    assert data_json["delta"] == 0
    assert data_json["simulated"]["risk_score"] == data_json["baseline"]["risk_score"]