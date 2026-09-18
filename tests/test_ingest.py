from __future__ import annotations

from datetime import datetime, timezone

import pytest

from narrativeradar.config import Config
from narrativeradar.ingest import IngestError, ingest, posts_from_x_payload, search_x


def test_mock_filters_stale_fixture_posts(mock_config: Config) -> None:
    posts, as_of = ingest(mock_config)
    ids = {post.id for post in posts}
    assert "1000000000000000001" not in ids
    assert as_of.tzinfo is not None
    assert any(post.author == "ansem" for post in posts)


def test_live_without_token_fails_closed() -> None:
    cfg = Config(mock=False, bearer_token=None)
    with pytest.raises(IngestError, match="(?i)bearer"):
        ingest(cfg)


def test_x_payload_maps_metrics_and_urls() -> None:
    cfg = Config(mock=False, bearer_token="x", kol_usernames=frozenset({"ansem"}))
    payload = {
        "data": [
            {
                "id": "99",
                "author_id": "7",
                "text": "hello $SOL",
                "created_at": "2026-09-18T00:00:00.000Z",
                "public_metrics": {
                    "like_count": 3,
                    "retweet_count": 1,
                    "reply_count": 0,
                    "quote_count": 0,
                },
            }
        ],
        "includes": {"users": [{"id": "7", "username": "ansem"}]},
    }
    posts = posts_from_x_payload(payload, cfg)
    assert len(posts) == 1
    assert posts[0].author == "ansem"
    assert posts[0].is_kol is True
    assert posts[0].likes == 3
    assert posts[0].url.endswith("/status/99")


def test_search_x_uses_injected_fetch_not_network() -> None:
    seen: dict[str, str] = {}

    def fake_fetch(url: str, headers: dict[str, str]) -> dict:
        seen["url"] = url
        seen["auth"] = headers.get("Authorization", "")
        return {
            "data": [
                {
                    "id": "1",
                    "author_id": "2",
                    "text": "prediction market chatter",
                    "created_at": "2026-09-18T00:00:00Z",
                    "public_metrics": {},
                }
            ],
            "includes": {"users": [{"id": "2", "username": "polywatcher"}]},
        }

    cfg = Config(
        mock=False,
        bearer_token="secret-token",
        hours=6,
        as_of=datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc),
        query="crypto",
    )
    posts, _ = search_x(cfg, fetch=fake_fetch)
    assert seen["auth"] == "Bearer secret-token"
    assert "tweets/search/recent" in seen["url"]
    assert posts[0].source == "x-search"
