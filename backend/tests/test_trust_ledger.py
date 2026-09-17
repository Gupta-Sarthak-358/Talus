"""Trust ledger: Warning | Lead | Exposure | Support | Result, incl. OOD row."""
from fastapi.testclient import TestClient

from backend.app.main import app as talus_app

client = TestClient(talus_app)


def test_trust_ledger_shape():
    r = client.get("/api/trust/ledger")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["columns"] == ["Warning", "Lead", "Exposure", "Data support", "Result"]
    assert len(body["ledger"]) >= 5
    for row in body["ledger"]:
        assert set(row) >= {"id", "warning", "lead_days", "exposure",
                            "support", "result"}


def test_trust_ledger_has_ood_row():
    body = client.get("/api/trust/ledger").json()
    ood = [x for x in body["ledger"] if x["support"].startswith("OUT")]
    assert len(ood) == 1, "exactly one out-of-regime row expected"
    assert ood[0]["lead_days"] is None
    assert "Unknown" in ood[0]["result"]
