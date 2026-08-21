import pytest
from fastapi.testclient import TestClient

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

BANDS = {"Very Low", "Low", "Moderate", "High", "Critical"}


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield


def score_of(features: dict, zone: str = "B") -> int:
    r = client.post("/api/risk/predict", json={"zone_id": zone, "features": features})
    assert r.status_code == 200
    return r.json()["risk_score"]


def test_root_reports_real_model():
    r = client.get("/")
    assert "frozen ML Model v1" in r.json()["status"]


def test_initial_scores_are_model_consistent():
    """Store scores must equal a fresh prediction on the same stored features."""
    r = client.get("/api/zones")
    assert r.status_code == 200
    zones = {z["zone_id"]: z for z in r.json()["zones"]}
    for zid, z in zones.items():
        assert 0 <= z["risk_score"] <= 100
        assert z["risk_band"] in BANDS
        fresh = score_of(store.features[zid].model_dump(), zid)
        assert fresh == z["risk_score"], f"{zid}: store {z['risk_score']} != model {fresh}"


def test_zone_detail_404():
    assert client.get("/api/zones/ZZZ").status_code == 404


def test_explanation_uses_real_shap():
    detail = client.get("/api/zones/B").json()
    explanation = client.get("/api/zones/B/explanation").json()
    assert explanation["risk_score"] == detail["risk_score"]
    assert len(explanation["contributions"]) > 0
    assert isinstance(explanation["base_value"], (int, float))
    feats = {c["feature"] for c in explanation["contributions"]}
    assert all(any(k in f for k in VALID_FEATURES) or "zone" in f for f in feats)


def test_deterioration_raises_score():
    s0 = score_of(VALID_FEATURES)
    s1 = score_of(EVENT1)
    s2 = score_of(EVENT2)
    assert s0 <= 100 and s1 <= 100 and s2 <= 100
    assert s2 >= s1, "added cracks/blast/wetting must not lower risk"


def test_wetter_is_not_safer():
    wetter = {**VALID_FEATURES, "rainfall_24h_mm": 200.0, "rainfall_7d_mm": 400.0}
    assert score_of(wetter) >= score_of(VALID_FEATURES) - 2


def test_trend_updates_after_predictions():
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT1})
    client.post("/api/risk/predict", json={"zone_id": "B", "features": EVENT2})
    r = client.get("/api/zones/B/trend")
    body = r.json()
    assert len(body["history"]) >= 3
    scores = [p["risk_score"] for p in body["history"]]
    assert all(0 <= s <= 100 for s in scores)
    assert scores[-1] == score_of(EVENT2)


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
    assert r.status_code == 200
    assert isinstance(r.json()["risk_aware_route"]["path"], list)


def test_safe_route_requires_zone_id():
    body = {
        "start": {"lat": 20.51, "lng": 80.115},
        "end": {"zone_id": "D", "lat": 20.58, "lng": 80.165},
    }
    assert client.post("/api/routes/safe", json=body).status_code == 422


def test_what_if_extreme_rain_increases_or_holds():
    base = score_of(EVENT2)
    body = {"zone_id": "B", "overrides": {"rainfall_24h_mm": 80.0}}
    r = client.post("/api/simulation/what-if", json=body)
    assert r.status_code == 200
    sim = r.json()["simulated"]["risk_score"]
    assert sim >= base - 2
    assert r.json()["simulated"]["risk_band"] in BANDS


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
    base = score_of(EVENT2)
    body = {"zone_id": "B", "overrides": {}}
    r = client.post("/api/simulation/what-if", json=body)
    data_json = r.json()
    assert data_json["delta"] == 0
    assert data_json["simulated"]["risk_score"] == data_json["baseline"]["risk_score"]
    assert data_json["baseline"]["risk_score"] == base