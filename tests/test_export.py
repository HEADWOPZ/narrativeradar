from __future__ import annotations

import json
from pathlib import Path

from narrativeradar.config import Config
from narrativeradar.export import escape_telegram, render_telegram, write_brief
from narrativeradar.pipeline import run_brief


def test_telegram_markdown_cites_receipts(mock_config: Config) -> None:
    brief = run_brief(mock_config)
    md = render_telegram(brief)
    assert md.startswith("📡 *NarrativeRadar*")
    assert "Receipts:" in md
    assert "2073450447105401190" in md
    assert "https://x.com/" in md
    assert "does not auto-trade" in md


def test_escape_telegram_metacharacters() -> None:
    assert escape_telegram("why_this *fires*") == r"why\_this \*fires\*"


def test_write_all_artifacts(mock_config: Config, tmp_path: Path) -> None:
    brief = run_brief(mock_config)
    written = write_brief(brief, tmp_path, {"all"})
    names = {path.name for path in written}
    assert names == {"brief.json", "brief.md", "watchlist.csv"}
    payload = json.loads((tmp_path / "brief.json").read_text(encoding="utf-8"))
    assert payload["cards"]
    csv_text = (tmp_path / "watchlist.csv").read_text(encoding="utf-8")
    assert "card_id" in csv_text
    assert "top_receipt_url" in csv_text
