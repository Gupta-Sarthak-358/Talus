"""Wound bundle: review queue with provenance, per corridor."""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)


def test_wounds_shape():
    r = client.get("/api/wounds")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "REVIEW QUEUE" in body["method"]
    assert set(body["corridors"]) == {"gangtok", "lachung", "darjeeling"}
    for loc, corr in body["corridors"].items():
        assert corr["status"] in ("ok", "no-scene-pair") or corr["status"].startswith("error")
        for c in corr.get("candidates", []):
            assert set(c) >= {"lat", "lon", "seg", "ndvi_pre", "ndvi_post", "drop"}
            assert c["ndvi_pre"] >= 0.4 and c["drop"] >= 0.3 and c["ndvi_post"] < 0.45
