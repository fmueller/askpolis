from fastapi.testclient import TestClient

from askpolis.main import app

client = TestClient(app)


def test_liveness_probe() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"healthy": True}


def test_readiness_probe() -> None:
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"healthy": True}
