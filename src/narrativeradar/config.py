"""Environment and CLI configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

TRUE_VALUES = {"1", "true", "yes", "on"}

DEFAULT_KOLS = (
    "ansem",
    "camillo",
    "cobie",
    "hsaka",
    "pag",
    "solanafloor",
)

DEFAULT_QUERY = (
    '(crypto OR solana OR bitcoin OR meme OR narrative OR "social arb" '
    "OR polymarket OR tiktok) lang:en -is:retweet"
)


def _parse_bool(raw: str | None, default: bool = True) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip().replace("Z", "+00:00")
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass
class Config:
    """Runtime knobs. Mock stays on unless the operator opts into live X."""

    mock: bool = True
    hours: float = 24.0
    min_score: float = 35.0
    query: str = DEFAULT_QUERY
    bearer_token: str | None = None
    fixture_path: Path | None = None
    as_of: datetime | None = None
    kol_usernames: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_KOLS))
    x_api_base: str = "https://api.x.com/2"
    max_receipts: int = 5
    max_posts: int = 100

    @property
    def source(self) -> str:
        return "mock" if self.mock else "x-search"

    @classmethod
    def from_env(cls, **overrides: object) -> Config:
        mock = _parse_bool(os.environ.get("NARRATIVERADAR_MOCK"), default=True)
        hours = float(os.environ.get("NARRATIVERADAR_HOURS", "24"))
        min_score = float(os.environ.get("NARRATIVERADAR_MIN_SCORE", "35"))
        query = os.environ.get("NARRATIVERADAR_QUERY", DEFAULT_QUERY)
        token = (
            os.environ.get("NARRATIVERADAR_X_BEARER_TOKEN")
            or os.environ.get("X_BEARER_TOKEN")
            or os.environ.get("TWITTER_BEARER_TOKEN")
        )
        fixture = os.environ.get("NARRATIVERADAR_FIXTURE")
        kols_raw = os.environ.get("NARRATIVERADAR_KOL_LIST")
        if kols_raw:
            kol_usernames = frozenset(
                part.strip().lstrip("@").lower() for part in kols_raw.split(",") if part.strip()
            )
        else:
            kol_usernames = frozenset(DEFAULT_KOLS)
        cfg = cls(
            mock=mock,
            hours=hours,
            min_score=min_score,
            query=query,
            bearer_token=token,
            fixture_path=Path(fixture) if fixture else None,
            as_of=_parse_datetime(os.environ.get("NARRATIVERADAR_AS_OF")),
            kol_usernames=kol_usernames,
        )
        for key, value in overrides.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)
        return cfg
