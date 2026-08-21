"""Tests for the causal physics What-If endpoints (Scenario Engine v1.5)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_templates_list_provenance():
    r = client.get("/api/simulation/templates")
    assert r.status_code == 200
    tpls = {t["template_id"]: t for t in r.json()["templates"]}
    assert "dec_1902" in tpls
    assert tpls["dec_1902"]["window_total_mm"] > 1000
    assert tpls["dec_1902"]["imd_window"] == ["1902-12-01", "1902-12-31"]


def test_causal_storm_returns_trajectory():
    body = {"zone_id": "C", "kind": "rainfall_storm", "start_day": 200,
            "duration_days": 7, "params": {"peak_mm": 100}}
    r = client.post("/api/simulation/causal-what-if", json=body)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "causal_physics"
    assert len(body["trajectory"]) > 50
    s = body["summary"]
    assert 0 <= s["scenario_min_fos"] <= 5
    assert s["scenario_peak_instability"] >= 0
    assert body["trajectory"][0]["day"] == 0


def test_causal_determinism_same_request_same_summary():
    req = {"zone_id": "B", "kind": "combined", "start_day": 180, "duration_days": 10,
           "params": {"peak_mm": 80, "ppv_mult": 2.0, "extra_event_prob": 0.3},
           "horizon_days": 365}
    a = client.post("/api/simulation/causal-what-if", json=req).json()
    b = client.post("/api/simulation/causal-what-if", json=req).json()
    assert a["summary"] == b["summary"]
    assert a["trajectory"] == b["trajectory"]


def test_causal_historical_template_has_provenance():
    body = {"zone_id": "C", "kind": "historical_rain", "start_day": 200,
            "duration_days": 31, "params": {"template_id": "dec_1902"}}
    r = client.post("/api/simulation/causal-what-if", json=body)
    assert r.status_code == 200
    prov = r.json()["provenance"]
    assert prov["template_id"] == "dec_1902"
    assert prov["window_total_mm"] > 1000


def test_causal_blast_surge_nonblast_zone_is_noop():
    req = {"zone_id": "D", "kind": "blast_surge", "start_day": 200, "duration_days": 30,
           "params": {"ppv_mult": 3.0, "extra_event_prob": 0.9}, "horizon_days": 365}
    r = client.post("/api/simulation/causal-what-if", json=req)
    assert r.status_code == 200
    traj = r.json()["trajectory"]
    assert all(p["fos"] == p["baseline_fos"] for p in traj)


def test_causal_multiyear_can_fire_open_crack_branch():
    body = {"zone_id": "C", "kind": "historical_rain", "start_day": 550,
            "duration_days": 31, "params": {"template_id": "dec_1902"},
            "horizon_days": 1095}
    r = client.post("/api/simulation/causal-what-if", json=body)
    assert r.status_code == 200
    s = r.json()["summary"]
    assert s["open_crack_branch_fired"] is True
    assert s["delta_min_fos"] < 0 or s["scenario_days_high_or_critical"] >= 0


def test_causal_unknown_kind_rejected():
    body = {"zone_id": "C", "kind": "meteor_shower"}
    assert client.post("/api/simulation/causal-what-if", json=body).status_code == 422


def test_causal_unknown_zone_rejected():
    body = {"zone_id": "Z", "kind": "rainfall_storm"}
    assert client.post("/api/simulation/causal-what-if", json=body).status_code == 422