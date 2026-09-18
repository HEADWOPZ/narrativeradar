from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "narrative-brief" / "SKILL.md"


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    _, block, body = text.split("---", 2)
    assert body.strip(), "SKILL.md needs a non-empty body"
    data: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def test_narrative_brief_skill_frontmatter() -> None:
    text = SKILL.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    assert meta["name"] == "narrative-brief"
    description = meta["description"].strip().strip('"')
    assert description.endswith(".")
    assert len(description) <= 60
    assert "MIT" in meta["license"]
    assert "Kevin Lance Murray" in meta["author"]
    assert "narrativeradar brief" in text
    assert "TrenchDesk" in text
