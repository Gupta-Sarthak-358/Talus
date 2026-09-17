"""Alert acknowledgements are recorded server-side (no fake local acks)."""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)


def test_ack_roundtrip():
    r = client.post("/api/alerts/ack", json={"alert_id": "zone-S1-critical"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["alert_id"] == "zone-S1-critical"
    assert body["acknowledged"] is True and body["synced"] is True
    assert body["acknowledged_at"]
    g = client.get("/api/alerts/ack")
    assert g.status_code == 200
    assert "zone-S1-critical" in [a["alert_id"] for a in g.json()["acks"]]


def test_ack_rejects_empty():
    assert client.post("/api/alerts/ack", json={}).status_code == 422
    assert client.post("/api/alerts/ack", json={"alert_id": ""}).status_code == 422
