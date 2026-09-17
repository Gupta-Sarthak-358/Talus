"""Runout/exposure bundle: 12 zones, honest screening numbers."""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)


def test_runout_shape():
    r = client.get("/api/runout/exposure")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "screening" in body["method"] and len(body["zones"]) == 12
    for zid, z in body["zones"].items():
        assert set(z) >= {"path", "length_m", "buildings_n", "buildings_seen",
                          "road_m", "nearest_road_seg", "nearest_road_m"}
        assert isinstance(z["buildings_n"], int) and z["buildings_n"] <= z["buildings_seen"]
        assert isinstance(z["road_m"], dict)
