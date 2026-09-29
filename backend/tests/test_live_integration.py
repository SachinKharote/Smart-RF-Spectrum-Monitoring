from fastapi.testclient import TestClient

from app.main import app


def test_strategy_configuration_and_websocket_live_event():
    with TestClient(app) as client:
        client.post("/simulation/stop")
        response = client.post("/simulation/strategy", json={"strategy": "Smart"})
        assert response.status_code == 200

        with client.websocket_connect("/ws") as websocket:
            started = client.post("/simulation/start")
            assert started.status_code == 200
            event = websocket.receive_json()
            assert event["type"] == "scan_update"
            assert event["strategy"] == "Smart"
            assert "predicted_band" in event
            assert "prediction_confidence" in event
            assert "reason" in event
            client.post("/simulation/stop")
