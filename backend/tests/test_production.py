"""Production-grade coverage for Talus SIH26001 new endpoints (2025-11-15)."""
from fastapi.testclient import TestClient
from backend.app.main import app as talus_app

client = TestClient(talus_app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] in ("ok","degraded")
    assert "store:gangtok" in j["checks"]

def test_db_status():
    r = client.get("/api/db/status")
    assert r.status_code == 200
    j = r.json()
    assert j["mode"] in ("fixture","postgis")
    assert "fallback" in j

def test_warning_kit_and_6state():
    for loc in ("gangtok","lachung","darjeeling"):
        r = client.get(f"/api/warning/state?location={loc}&lang=en")
        assert r.status_code == 200
        body = r.json()
        assert body["location"] == loc
        assert body["corridor_state"] in ["NORMAL","WATCH","ALERT","CRITICAL","RESTRICT","EVACUATE"]
        for s in body["states"]:
            assert "kit" in s
            kit = s["kit"]
            assert "what" in kit and "why" in kit and "shelters" in kit and "phones" in kit
            assert s["state"] in ["NORMAL","WATCH","ALERT","CRITICAL","RESTRICT","EVACUATE"]

def test_isolation_shape():
    for loc in ("gangtok","lachung","darjeeling"):
        r = client.get(f"/api/isolation?location={loc}")
        assert r.status_code == 200
        j = r.json()
        assert j["location"] == loc
        assert "valley_hub" in j and "bottleneck" in j
        assert set(j["bottleneck"].keys()) == {"R1","R2","R3","R4"}
        assert len(j["zones"]) == 4

def test_panchayat_tiles():
    r = client.get("/api/panchayat/tiles")
    assert r.status_code == 200
    j = r.json()
    assert j["count"] == 100
    assert len(j["tiles"]) == 100
    for t in j["tiles"][:2]:
        assert set(t.keys()) >= {"zone_id","lat","lon","risk_score"}
        assert 10 <= t["risk_score"] <= 100

def test_copernicus():
    r = client.get("/api/terrain/copernicus")
    assert r.status_code == 200
    j = r.json()
    assert "dem_sources" in j
    assert "srtm" in j["dem_sources"]["srtm"].lower()
    assert "S1" in j["per_zone_copernicus"]

def test_aws_gauges():
    r = client.get("/api/aws/gauges")
    assert r.status_code == 200
    j = r.json()
    assert j["interval"] == "10min"
    assert len(j["gauges"]) == 12
    assert any(g["location"]=="gangtok" for g in j["gauges"])

def test_soil_swi():
    for loc in ("gangtok","lachung"):
        r = client.get(f"/api/soil/swi?location={loc}")
        assert r.status_code == 200
        j = r.json()
        assert "swi_model" in j
        assert len(j["zones"]) == 4
        for z in j["zones"]:
            assert 0 <= z["swi"] <= 1

def test_road_restrictions():
    r = client.get("/api/roads/restrictions?location=gangtok")
    assert r.status_code == 200
    j = r.json()
    assert "catalogue" in j and "evaluation" in j
    assert len(j["evaluation"]) == 4
    for e in j["evaluation"]:
        assert "restricted" in e and "emergency_route" in e

def test_exposure():
    for zid in ("S1","S2","N1","D1"):
        r = client.get(f"/api/zones/{zid}/exposure")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["zone_id"] == zid
        assert "hazard" in j and "exposure" in j and "operational_risk" in j
        assert 0 <= j["operational_risk"]["score"] <= 100

def test_forecast_imd_live():
    r = client.get("/api/forecast/imd-live?location=gangtok")
    assert r.status_code == 200
    j = r.json()
    assert "location" in j
    # falls back to Open-Meteo when IMD key absent
    assert "daily" in j or "imd_records" in j

def test_cbe_stub():
    r = client.post("/api/alerts/cbe", json={"area":"S1","message":{"en":"test drill"},"severity":"Severe"})
    assert r.status_code == 200
    j = r.json()
    assert j["channel"] == "CB"
    assert j["area"] == "S1"
    assert "simulated" in j
    assert j["broadcast"] in ("simulated","queued","failed")

def test_auto_status_and_trigger():
    r = client.get("/api/alerts/auto/status")
    assert r.status_code == 200
    assert "enabled" in r.json()
    r2 = client.post("/api/alerts/auto/trigger?location=gangtok")
    assert r2.status_code == 200
    assert "would_fire" in r2.json()

def test_unknowns_404():
    assert client.get("/api/isolation?location=atlantis").status_code == 404
    assert client.get("/api/soil/swi?location=atlantis").status_code == 404
    assert client.get("/api/zones/UNKNOWN/exposure").status_code == 404
    assert client.get("/api/terrain/copernicus").status_code == 200  # always ok
