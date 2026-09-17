"""Live simulator lane: /api/live/feed + /api/live/audit.

Honest fallback chain: runs/live_feed.json (simulator) ->
data/sih26001/fixtures/live_feed.sample.json (committed SIMULATED sample).
Scores/bands/roles/fixtures must be untouched by this lane.
"""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)

ZONES_12 = {"S1", "S2", "S3", "S4", "N1", "N2", "N3", "N4", "D1", "D2", "D3", "D4"}


def test_live_feed_shape():
    r = client.get("/api/live/feed")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["served_from"] in {"simulator", "sample"}
    feed = body["feed"]
    assert feed["mode"] == "simulated", "feed must be labeled simulated, never real"
    assert set(feed["zones"]) == ZONES_12
    for zid, z in feed["zones"].items():
        assert set(z) >= {"rain_1h_mm", "soil_delta", "battery_pct", "rssi_dbm", "status"}, zid
        assert z["status"] in {"ok", "stale", "low-batt"}, zid


def test_live_audit_shape():
    r = client.get("/api/live/audit?limit=5")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] in {"simulator", "empty"}
    assert isinstance(body["events"], list)
    for ev in body["events"]:
        assert set(ev) >= {"tick", "issued_at", "event", "detail"}


def test_replay_series_shape_and_causality():
    r = client.get("/api/replay/series")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "causality" in body and len(body["cases"]) == 5 and len(body["ledger"]) == 5
    for case in body["cases"]:
        dates = [row["date"] for row in case["series"]]
        assert dates == sorted(dates), case["id"]
        assert max(dates) <= case["event_date"], f"{case['id']} leaks past event"
        for row in case["series"]:
            assert set(row) >= {"date", "score", "band", "rain_24h", "rain_7d",
                                "rain_30d", "soil_moisture", "ndvi", "drivers"}
    for entry in body["ledger"]:
        assert set(entry) >= {"id", "event_date", "first_high", "lead_high_days",
                              "early_hot_episodes"}
