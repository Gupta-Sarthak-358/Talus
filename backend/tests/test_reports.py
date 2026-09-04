import pytest
from fastapi.testclient import TestClient

from backend.app.main import _REPORTS
from backend.app.main import app as talus_app
from backend.app import data as data_mod

client = TestClient(talus_app)

VALID_REPORT = {
    "zone_id": "S2",
    "type": "crack",
    "text": "Fresh crack above Chandmari road-cut, about 5 meters long, widening.",
    "lat": 27.3381,
    "lon": 88.6121,
    "captured_at": "2026-09-04T09:30:00+05:30",
    "reporter_role": "field_officer",
    "photo": {
        "filename": "crack_S2.jpg",
        "mime": "image/jpeg",
        "size_bytes": 12345,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "exif_lat": 27.3381,
        "exif_lon": 88.6121,
    },
    "consent": True,
}


@pytest.fixture(autouse=True)
def reset_reports():
    # Snapshot length; we reset by truncating to seed size (1) between tests.
    # _REPORTS is in-memory per contract; tests isolate by trimming extras.
    seed_len = 1  # REP-001 from fixtures/reports.json after normalization
    yield
    # Trim any reports created during the test
    while len(_REPORTS) > seed_len:
        _REPORTS.pop()
    # Reset any mutated seed status
    if _REPORTS:
        _REPORTS[0]["status"] = "queued"
        _REPORTS[0].pop("reviewer_role", None)
        _REPORTS[0].pop("flagged_reason", None)
        _REPORTS[0]["flagged_reason"] = None


def test_reports_fixture_seeded():
    r = client.get("/api/reports/queue")
    assert r.status_code == 200
    assert any(rep["id"] == "REP-001" for rep in r.json()["reports"])
    rep = next(rep for rep in r.json()["reports"] if rep["id"] == "REP-001")
    assert rep["lat"] and rep["lon"]
    assert rep["consent"] is True
    assert rep["photo"]["sha256"]
    assert rep["status"] in {"queued", "verified", "dismissed", "flagged"}


def test_post_valid_report_queued():
    r = client.post("/api/reports", json=VALID_REPORT)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"].startswith("REP-")
    assert body["status"] == "queued"
    assert body["zone_id"] == "S2"
    assert body["consent"] is True


def test_post_exif_mismatch_flagged():
    payload = dict(VALID_REPORT)
    payload["photo"] = dict(VALID_REPORT["photo"])
    # ~2km mismatch (>200m threshold)
    payload["photo"]["exif_lat"] = 27.36
    payload["photo"]["exif_lon"] = 88.63
    r = client.post("/api/reports", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "flagged"
    assert "EXIF GPS" in (r.json().get("flagged_reason") or "")


def test_post_rejects_missing_consent():
    payload = dict(VALID_REPORT)
    payload["consent"] = False
    r = client.post("/api/reports", json=payload)
    # Pydantic allows bool false but business rule rejects; we raise 422
    assert r.status_code == 422


def test_post_rejects_bad_zone():
    payload = dict(VALID_REPORT)
    payload["zone_id"] = "ZZZ"
    r = client.post("/api/reports", json=payload)
    assert r.status_code == 422


def test_post_rejects_out_of_bbox():
    payload = dict(VALID_REPORT)
    payload["lat"] = 28.5  # outside 27.20-27.40
    r = client.post("/api/reports", json=payload)
    assert r.status_code == 422


def test_post_rejects_short_text():
    payload = dict(VALID_REPORT)
    payload["text"] = "hi"
    r = client.post("/api/reports", json=payload)
    assert r.status_code == 422


def test_post_rejects_bad_mime_flagged_or_422():
    payload = dict(VALID_REPORT)
    payload["photo"] = dict(VALID_REPORT["photo"])
    payload["photo"]["mime"] = "application/octet-stream"
    r = client.post("/api/reports", json=payload)
    # flagged via mime whitelist check: still 200 but flagged, or 422 if schema
    assert r.status_code in {200, 422}
    if r.status_code == 200:
        assert r.json()["status"] == "flagged"


def test_queue_filter_by_status():
    # Create one flagged
    payload = dict(VALID_REPORT)
    payload["photo"] = dict(VALID_REPORT["photo"])
    payload["photo"]["exif_lat"] = 27.50
    payload["photo"]["exif_lon"] = 88.80
    r1 = client.post("/api/reports", json=payload)
    assert r1.json()["status"] == "flagged"
    r = client.get("/api/reports/queue", params={"status": "flagged"})
    assert r.status_code == 200
    assert all(rep["status"] == "flagged" for rep in r.json()["reports"])
    r2 = client.get("/api/reports/queue", params={"status": "queued"})
    assert all(rep["status"] == "queued" for rep in r2.json()["reports"])


def test_review_transition_queued_to_verified():
    r = client.post("/api/reports", json=VALID_REPORT)
    rid = r.json()["id"]
    rev = client.patch(f"/api/reports/{rid}", json={"status": "verified", "reviewer_role": "district_officer"})
    assert rev.status_code == 200
    assert rev.json()["status"] == "verified"
    # Verify queue filter sees it
    q = client.get("/api/reports/queue", params={"status": "verified"})
    assert any(rep["id"] == rid for rep in q.json()["reports"])


def test_review_rejects_transition_from_verified():
    r = client.post("/api/reports", json=VALID_REPORT)
    rid = r.json()["id"]
    client.patch(f"/api/reports/{rid}", json={"status": "verified"})
    # Second transition should 409
    r2 = client.patch(f"/api/reports/{rid}", json={"status": "dismissed"})
    assert r2.status_code == 409


def test_review_404():
    r = client.patch("/api/reports/REP-999", json={"status": "verified"})
    assert r.status_code == 404


def test_report_appears_in_queue_after_post():
    r = client.post("/api/reports", json=VALID_REPORT)
    rid = r.json()["id"]
    q = client.get("/api/reports/queue")
    assert any(rep["id"] == rid for rep in q.json()["reports"])


def test_post_without_photo_allowed():
    payload = dict(VALID_REPORT)
    payload.pop("photo", None)
    # set text to valid
    r = client.post("/api/reports", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "queued"


def test_post_rejects_future_captured_at_far_future():
    payload = dict(VALID_REPORT)
    payload["captured_at"] = "2099-01-01T00:00:00+05:30"
    r = client.post("/api/reports", json=payload)
    assert r.status_code == 422
