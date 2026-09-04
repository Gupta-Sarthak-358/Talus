import pytest
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app
from backend.app import data as data_mod

client = TestClient(talus_app)


@pytest.fixture(autouse=True)
def reset_stores():
    for store in data_mod.stores.values():
        store.reset()
    yield
    for store in data_mod.stores.values():
        store.reset()


def _route(start, end):
    return client.post("/api/routes/safe", json={"start": start, "end": end})


def test_gangtok_route_unchanged():
    r = _route(
        {"zone_id": "S1", "lat": 27.3450, "lng": 88.6000},
        {"zone_id": "S4", "lat": 27.3150, "lng": 88.5950},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "gangtok"
    aware = body["risk_aware_route"]["path"]
    short = body["shortest_route"]["path"]
    assert len(aware) >= 2 and len(short) >= 2
    for pt in aware + short:
        assert set(pt) == {"lat", "lng"}
        assert 27.20 <= pt["lat"] <= 27.40 and 88.40 <= pt["lng"] <= 88.70
    assert body["risk_aware_route"]["max_risk_exposed"] <= body["shortest_route"]["max_risk_exposed"]


def test_lachung_route_stays_on_corridor():
    r = _route(
        {"zone_id": "N1", "lat": 27.6965, "lng": 88.7355},
        {"zone_id": "N4", "lat": 27.6680, "lng": 88.7305},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "lachung"
    pts = body["risk_aware_route"]["path"] + body["shortest_route"]["path"]
    assert len(pts) >= 4
    for pt in pts:
        assert 27.60 <= pt["lat"] <= 27.75 and 88.65 <= pt["lng"] <= 88.80
    assert all(z.startswith("N") for z in body["avoided_zones"])


def test_darjeeling_route_stays_on_corridor():
    r = _route(
        {"zone_id": "D1", "lat": 27.0485, "lng": 88.2585},
        {"zone_id": "D4", "lat": 27.0220, "lng": 88.2505},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "darjeeling"
    pts = body["risk_aware_route"]["path"] + body["shortest_route"]["path"]
    assert len(pts) >= 4
    for pt in pts:
        assert 26.95 <= pt["lat"] <= 27.10 and 88.15 <= pt["lng"] <= 88.35
    assert all(z.startswith("D") for z in body["avoided_zones"])


def test_v1_single_letter_zones_still_gangtok():
    # v1 compat: single-letter A/D must NOT resolve to darjeeling (strict N[1-4]/D[1-4] rule)
    r = _route(
        {"zone_id": "A", "lat": 20.51, "lng": 80.115},
        {"zone_id": "D", "lat": 20.58, "lng": 80.165},
    )
    assert r.status_code == 200
    assert r.json()["location"] == "gangtok"


def test_roads_default_gangtok():
    r = client.get("/api/roads/status")
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "gangtok" and body["preview"] is False
    segs = {s["id"]: s for s in body["segments"]}
    assert segs["R2"]["status"] == "at-risk"
    assert segs["R1"]["adjacent_slope"] == "S1"
    assert segs["R2"]["coordinates"][0] == [27.3450, 88.6000]


def test_roads_lachung_remapped():
    r = client.get("/api/roads/status?location=lachung")
    assert r.status_code == 200
    body = r.json()
    assert body["location"] == "lachung" and body["preview"] is True
    segs = {s["id"]: s for s in body["segments"]}
    assert segs["R2"]["status"] == "at-risk"
    assert segs["R1"]["adjacent_slope"] == "N1"
    assert segs["R4"]["adjacent_slope"] == "N4"
    lat, lon = segs["R1"]["coordinates"][0]
    assert abs(lat - (27.3450 + 0.35)) < 1e-9 and abs(lon - (88.6000 + 0.135)) < 1e-9


def test_roads_unknown_location_falls_back():
    r = client.get("/api/roads/status?location=bogus")
    assert r.status_code == 200
    assert r.json()["location"] == "gangtok"
