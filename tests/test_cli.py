from __future__ import annotations

import json
from pathlib import Path

from narrativeradar.cli import main


def test_brief_markdown_stdout(capsys, mock_config, monkeypatch) -> None:
    monkeypatch.setenv("NARRATIVERADAR_MOCK", "1")
    code = main(["brief", "--format", "md", "--hours", "24"])
    captured = capsys.readouterr()
    assert code == 0
    assert "NarrativeRadar" in captured.out
    assert "Receipts:" in captured.out


def test_brief_json_and_out_dir(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setenv("NARRATIVERADAR_MOCK", "1")
    out = tmp_path / "out"
    code = main(["brief", "--format", "all", "--out", str(out), "--quiet"])
    assert code == 0
    payload = json.loads((out / "brief.json").read_text(encoding="utf-8"))
    assert payload["source"] == "mock"
    assert payload["cards"][0]["receipts"][0]["post_id"]
    assert capsys.readouterr().out == ""


def test_watch_once_writes_state(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setenv("NARRATIVERADAR_MOCK", "1")
    state = tmp_path / "state.json"
    assert main(["watch", "--once", "--state", str(state)]) == 0
    first = capsys.readouterr().out
    assert "new card" in first
    assert state.exists()
    assert main(["watch", "--once", "--state", str(state)]) == 0
    second = capsys.readouterr().out
    assert "already seen" in second


def test_live_without_token_exits_1(monkeypatch, capsys) -> None:
    monkeypatch.setenv("NARRATIVERADAR_MOCK", "0")
    monkeypatch.delenv("NARRATIVERADAR_X_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)
    code = main(["brief", "--live"])
    assert code == 1
    assert "bearer" in capsys.readouterr().err.lower()  # token name in error


def test_unknown_format_exits_2(monkeypatch, capsys) -> None:
    monkeypatch.setenv("NARRATIVERADAR_MOCK", "1")
    assert main(["brief", "--format", "pdf"]) == 2
    assert "Unknown format" in capsys.readouterr().err
