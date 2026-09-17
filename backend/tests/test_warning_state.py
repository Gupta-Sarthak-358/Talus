"""Warning state machine: every zone gets a state + reasons + officer action."""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)
STATES = ["NORMAL", "WATCH", "ALERT", "CRITICAL", "RESTRICT", "EVACUATE"]


def check_location(loc):
    r = client.get(f"/api/warning/state?location={loc}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["location"] == loc
    assert len(body["states"]) == 4
    assert body["corridor_state"] in STATES
    for s in body["states"]:
        assert s["state"] in STATES
        assert isinstance(s["score"], int)
        assert len(s["reasons"]) >= 1 and s["reasons"][0].startswith("Risk score")
        assert s["action"]["message"] and s["action"]["priority"]
    # corridor rollup = max state present
    assert body["corridor_state"] == max(
        (s["state"] for s in body["states"]), key=STATES.index)


def test_gangtok():
    check_location("gangtok")


def test_lachung():
    check_location("lachung")


def test_darjeeling():
    check_location("darjeeling")


def test_unknown_location_404():
    assert client.get("/api/warning/state?location=atlantis").status_code == 404


def test_state_consistent_with_band_and_escalation():
    # State must equal band level, or up to one higher when reason-stamped
    # (rapid, SWI, wound, forecast, effective rain). Isolation adds RESTRICT/EVACUATE.
    for loc in ("gangtok", "lachung", "darjeeling"):
        zones = {z["zone_id"]: z for z in
                 client.get(f"/api/zones?location={loc}").json()["zones"]}
        body = client.get(f"/api/warning/state?location={loc}").json()
        for s in body["states"]:
            z = zones[s["zone_id"]]
            base = {"Very Low": 0, "Low": 0, "Moderate": 1,
                    "High": 2, "Critical": 3}[z["risk_band"]]
            lvl = STATES.index(s["state"])
            # Non-isolated zones: at most +1 for reason stamps; isolated may go to 5
            if s["state"] in ("RESTRICT", "EVACUATE"):
                assert "ISOLATED" in s["reasons"][-1] or "RESTRICT" in s["reasons"][-1] or "May isolate" in " ".join(s["reasons"])
            else:
                assert lvl in (base, min(3, base + 1), 4, 5) or lvl == base, (loc, s)
            assert s["reasons"][0] == f"Risk score {s['score']} ({s['band']})"
            if lvl == base + 1 and s["state"] not in ("RESTRICT","EVACUATE"):
                assert any(k in " ".join(s["reasons"]) for k in ["rapidly rising","SWI","wound","Forecast","Effective rain"]), s["reasons"]
