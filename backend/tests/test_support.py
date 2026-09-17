"""Model-support regime: validated corridors vs operational-inference corridors."""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)


def _ws(loc):
    r = client.get(f"/api/warning/state?location={loc}")
    assert r.status_code == 200, r.text
    return r.json()


def test_validated_regime_gangtok():
    body = _ws("gangtok")
    assert body["model_support"] == "validated-regime"
    assert body["prediction_status"] == "calibrated-validity"
    assert "drain_density (DEM accumulation)" in body["feature_provenance"]["real"]


def test_unvalidated_regime_arunachal():
    body = _ws("arunachal")
    assert body["model_support"] == "outside-validated-regime"
    assert body["prediction_status"] == "operational-inference-unvalidated"
    prov = body["feature_provenance"]
    assert any("drain_density" in p for p in prov["proxy"])
    assert any("lithology" in p for p in prov["proxy"])
    assert len(prov["missing"]) > 0


def test_all_corridors_carry_support():
    for loc in ("gangtok", "lachung", "darjeeling", "arunachal", "assam",
                "manipur", "meghalaya", "mizoram"):
        body = _ws(loc)
        assert set(body) >= {"model_support", "prediction_status",
                             "feature_provenance", "support_note"}
