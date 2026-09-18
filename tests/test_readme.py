from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_says_what_it_is_and_is_not() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "what it is" in lowered
    assert "what it isn’t" in lowered or "what it isn't" in lowered
    assert "TrenchDesk" in text
    assert "auto-trad" in lowered
    assert "NARRATIVERADAR_MOCK" in text
    assert "narrativeradar brief" in text
    assert "MIT" in text


def test_license_is_mit_headwopz() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert text.startswith("MIT License")
    assert "Kevin Lance Murray" in text
    assert "HEADWOPZ" in text
