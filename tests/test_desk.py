from __future__ import annotations

from fastapi.testclient import TestClient

from narrativeradar.config import Config
from narrativeradar.desk import create_app


def test_health_and_brief_endpoints(mock_config: Config) -> None:
    client = TestClient(create_app(mock_config))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert health.json()["mock"] is True

    home = client.get("/")
    assert home.status_code == 200
    assert "NarrativeRadar" in home.text

    brief = client.get("/api/brief")
    assert brief.status_code == 200
    payload = brief.json()
    assert payload["cards"]
    card_id = payload["cards"][0]["id"]

    card = client.get(f"/api/cards/{card_id}")
    assert card.status_code == 200
    assert card.json()["id"] == card_id

    explain = client.get(f"/api/explain/{card_id}")
    assert explain.status_code == 200
    body = explain.json()
    assert body["receipts"]
    assert "why" in body

    missing = client.get("/api/explain/nr-missing")
    assert missing.status_code == 404
