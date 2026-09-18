from __future__ import annotations

from narrativeradar.config import Config
from narrativeradar.pipeline import run_brief


def test_empty_fixture_yields_empty_brief(tmp_path, mock_config: Config) -> None:
    empty = tmp_path / "empty.json"
    empty.write_text('{"posts": []}\n', encoding="utf-8")
    cfg = Config(mock=True, fixture_path=empty, hours=24.0, min_score=35.0)
    brief = run_brief(cfg)
    assert brief.post_count == 0
    assert brief.cards == []
    assert brief.card_count == 0


def test_brief_disclaimer_forbids_auto_trade(mock_config: Config) -> None:
    brief = run_brief(mock_config)
    assert "auto-trade" in brief.disclaimer.lower()
    assert brief.to_dict()["card_count"] == len(brief.cards)
