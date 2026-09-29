from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_comparison_returns_both_strategies():
    with TestClient(app) as client:
        response = client.get("/dashboard/comparison?scans=20")
        assert response.status_code == 200
        payload = response.json()
        assert payload["scans_per_strategy"] == 20
        assert payload["same_scenario"] is True
        assert set(["Sequential", "Smart"]).issubset(payload)
        assert payload["Sequential"]["strategy"] == "Sequential"
        assert payload["Smart"]["strategy"] == "Smart"
