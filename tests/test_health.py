# Minimal API smoke test so CI can validate the FastAPI app boots correctly.
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
