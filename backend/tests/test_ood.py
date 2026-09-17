"""OOD guard tests (E16d): validated terrain-support rule, shipped cautions."""
import pytest
from fastapi.testclient import TestClient

from backend.app import support
from backend.app.main import app as talus_app

client = TestClient(talus_app)

# Typical in-domain NGEN row shape (training medians): inside support bands
IN_DOMAIN = {"slope_angle": 25.0, "elevation": 1300.0, "aspect": 180.0,
             "curvature": 0.005, "twi": 5.5, "spi": 100.0,
             "distance_to_road": 300.0, "distance_to_river": 400.0,
             "drain_density": 1.0}
# S1 road-cut shape: road=4m sits below training-positive p1 (29m) — truthful
# caveat (extreme road-cut), warning still fires; only confidence is downgraded.
S1_ROADCUT = {"slope_angle": 28.5, "elevation": 1290.0, "aspect": 289.0,
              "curvature": 0.0111, "twi": 5.99, "spi": 120.9,
              "distance_to_road": 4.0, "distance_to_river": 226.0,
              "drain_density": 0.0}
# Plains-like held-out row (H008 shape): elevation + road far outside support
PLAINS = {"slope_angle": 37.9, "elevation": 226.1, "aspect": 163.0,
          "curvature": 0.004, "twi": 3.57, "spi": 21.5,
          "distance_to_road": 83.0, "distance_to_river": 400.0,
          "drain_density": 2.564}


def test_bands_file_loads():
    assert support._load(), "feature_support.json bands missing"
    assert "elevation" in support._load()


def test_in_domain_not_ood():
    r = support.check(IN_DOMAIN)
    assert r["ood"] is False and r["ood_reasons"] == []


def test_s1_roadcut_flags_caveat_only():
    # extreme road-cut is outside road support: caveat fires, but the row is
    # NOT suppressed — warnings still driven by score, only confidence downgraded
    r = support.check(S1_ROADCUT)
    assert r["ood"] is True
    assert any("distance_to_road" in x for x in r["ood_reasons"])


def test_plains_row_is_ood_with_reasons():
    r = support.check(PLAINS)
    assert r["ood"] is True
    assert any("elevation" in x for x in r["ood_reasons"])


def test_dynamic_extremes_never_trigger():
    # extreme monsoon on in-domain terrain must NOT abstain (warnings matter most then)
    row = dict(IN_DOMAIN, rainfall_24h_mm=300.0, rainfall_7d_mm=900.0)
    assert support.check(row)["ood"] is False


def test_missing_terrain_is_ood():
    r = support.check({})
    assert r["ood"] is True


def test_score_row_carries_ood_keys():
    from backend.app import sih26001_model
    live = sih26001_model.get_live()
    if live is None:
        pytest.skip("weights absent (fresh clone) — guard unit tests above still hold")
    row = dict(IN_DOMAIN, zone_id="S1", rainfall_24h_mm=14.0, rainfall_7d_mm=327.3,
               rainfall_30d_mm=712.2, soil_moisture=0.271, ndvi=0.718, lulc="FOREST",
               seismic_dist_km=35.0, seismic_n50_rate=0.08, seismic_years_since=13.0)
    out = live.score_row(row)
    assert out is not None and "ood" in out and "probability_status" in out


def test_warning_state_has_ood_keys():
    r = client.get("/api/warning/state?location=gangtok")
    assert r.status_code == 200
    s = r.json()["states"][0]
    for k in ("ood", "ood_reasons", "probability_status", "confidence"):
        assert k in s, f"missing {k}"
    assert s["probability_status"] in ("calibrated", "uncalibrated-ood")
