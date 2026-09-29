from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_simulation_start_and_state():
    with TestClient(app) as client:
        response = client.post("/simulation/start")
        assert response.status_code == 200
        assert response.json()["status"] == "running"

        state = client.get("/simulation/state")
        assert state.status_code == 200
        assert state.json()["running"] is True

        response = client.post("/simulation/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"
