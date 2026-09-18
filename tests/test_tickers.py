from __future__ import annotations

from datetime import datetime, timezone

from narrativeradar.models import Post
from narrativeradar.tickers import extract_tickers, extract_tickers_from_posts


def test_cashtag_and_alias_only_when_evidenced() -> None:
    text = "TikToks talking $BONK and solana tonight"
    assert extract_tickers(text) == ["BONK", "SOL"]


def test_no_invented_ticker() -> None:
    assert extract_tickers("grabbing tacos in austin, nothing about markets") == []


def test_mint_like_string_is_linked() -> None:
    mint = "So11111111111111111111111111111111111111112"
    assert mint in extract_tickers(f"pool {mint} printed")


def test_union_preserves_first_seen_order() -> None:
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    posts = [
        Post(id="1", url="u", author="a", text="only $WIF here", created_at=now),
        Post(id="2", url="u", author="b", text="$BONK and $WIF", created_at=now),
    ]
    assert extract_tickers_from_posts(posts) == ["WIF", "BONK"]
