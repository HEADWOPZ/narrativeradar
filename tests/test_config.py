from __future__ import annotations

from narrativeradar.config import Config


def test_from_env_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("NARRATIVERADAR_MOCK", raising=False)
    monkeypatch.delenv("NARRATIVERADAR_X_BEARER_TOKEN", raising=False)
    cfg = Config.from_env()
    assert cfg.mock is True
    assert cfg.source == "mock"
    assert cfg.hours == 24.0


def test_from_env_live_override(monkeypatch) -> None:
    monkeypatch.setenv("NARRATIVERADAR_MOCK", "0")
    monkeypatch.setenv("NARRATIVERADAR_X_BEARER_TOKEN", "tok")
    monkeypatch.setenv("NARRATIVERADAR_KOL_LIST", "@Ansem, camillo")
    cfg = Config.from_env()
    assert cfg.mock is False
    assert cfg.bearer_token == "tok"
    assert cfg.kol_usernames == frozenset({"ansem", "camillo"})
