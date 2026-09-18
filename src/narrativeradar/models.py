"""Shared dataclasses for posts, clusters, and opportunity cards."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat() + "Z"
    return value.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Post:
    """A single ingested social post (fixture or live X)."""

    id: str
    url: str
    author: str
    text: str
    created_at: datetime
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    quotes: int = 0
    source: str = "fixture"
    author_id: str | None = None
    is_kol: bool = False
    kol_weight: float = 1.0

    @property
    def engagement(self) -> int:
        return self.likes + self.reposts + self.quotes + self.replies

    def excerpt(self, limit: int = 180) -> str:
        text = " ".join(self.text.split())
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"


@dataclass(frozen=True)
class Receipt:
    """Cited post that explains why a card fired."""

    post_id: str
    url: str
    author: str
    excerpt: str
    created_at: str
    engagement: int
    is_kol: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Cluster:
    """Theme-grouped posts before scoring."""

    theme_id: str
    theme: str
    posts: list[Post]
    keywords: list[str]
    method: str


@dataclass
class OpportunityCard:
    """Scored narrative opportunity with receipts."""

    id: str
    theme: str
    theme_id: str
    summary: str
    spike_score: float
    window_hours: float
    tickers: list[str]
    kols: list[str]
    post_count: int
    engagement_total: int
    why: str
    receipts: list[Receipt]
    first_seen: str
    last_seen: str
    keywords: list[str]
    components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["receipts"] = [r.to_dict() if isinstance(r, Receipt) else r for r in self.receipts]
        return payload


@dataclass
class Brief:
    """A scored batch of opportunity cards."""

    generated_at: str
    source: str
    window_hours: float
    post_count: int
    card_count: int
    cards: list[OpportunityCard]
    disclaimer: str = (
        "Research only. Not a trade signal. NarrativeRadar does not auto-trade, "
        "route orders, or take custody."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "source": self.source,
            "window_hours": self.window_hours,
            "post_count": self.post_count,
            "card_count": self.card_count,
            "disclaimer": self.disclaimer,
            "cards": [card.to_dict() for card in self.cards],
        }

    def card_by_id(self, card_id: str) -> OpportunityCard | None:
        for card in self.cards:
            if card.id == card_id:
                return card
        return None


def isoformat_z(value: datetime) -> str:
    """UTC timestamp as `...Z`."""

    return _iso(value)
