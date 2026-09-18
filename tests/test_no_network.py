from __future__ import annotations

import urllib.request

import pytest

from narrativeradar.config import Config
from narrativeradar.pipeline import run_brief


def test_mock_brief_never_opens_sockets(mock_config: Config, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args, **_kwargs):  # pragma: no cover - fail path
        raise AssertionError("mock path must not call urlopen")

    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    brief = run_brief(mock_config)
    assert brief.source == "mock"
    assert brief.cards
