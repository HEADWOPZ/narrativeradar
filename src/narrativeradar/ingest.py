"""Ingest mock fixtures or optional live X recent-search."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from narrativeradar.config import Config
from narrativeradar.models import Post, isoformat_z

FetchFn = Callable[[str, dict[str, str]], dict[str, Any]]

PACKAGED_FIXTURE = Path(__file__).resolve().parent / "data" / "posts.json"


class IngestError(RuntimeError):
    """Raised when live ingest is misconfigured or the remote call fails."""


def default_fixture_path() -> Path:
    return PACKAGED_FIXTURE


def parse_datetime(raw: str) -> datetime:
    text = raw.strip().replace("Z", "+00:00")
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def post_url(post_id: str, author: str | None = None) -> str:
    if author:
        return f"https://x.com/{author}/status/{post_id}"
    return f"https://x.com/i/web/status/{post_id}"


def _kol_flag(author: str, cfg: Config, explicit: bool | None) -> tuple[bool, float]:
    if explicit is True:
        return True, 1.2
    if explicit is False:
        return False, 1.0
    handle = author.lstrip("@").lower()
    if handle in cfg.kol_usernames:
        return True, 1.2
    return False, 1.0


def row_to_post(row: dict[str, Any], cfg: Config, source: str) -> Post:
    post_id = str(row["id"])
    author = str(row.get("author") or row.get("username") or "unknown")
    created = parse_datetime(str(row["created_at"]))
    explicit_kol = row.get("is_kol")
    if explicit_kol is not None:
        explicit_kol = bool(explicit_kol)
    is_kol, default_weight = _kol_flag(author, cfg, explicit_kol)
    weight = float(row.get("kol_weight") or (default_weight if is_kol else 1.0))
    url = str(row.get("url") or post_url(post_id, author))
    return Post(
        id=post_id,
        url=url,
        author=author.lstrip("@"),
        text=str(row.get("text") or ""),
        created_at=created,
        likes=int(row.get("likes") or 0),
        reposts=int(row.get("reposts") or 0),
        replies=int(row.get("replies") or 0),
        quotes=int(row.get("quotes") or 0),
        source=source,
        author_id=str(row["author_id"]) if row.get("author_id") else None,
        is_kol=is_kol,
        kol_weight=weight,
    )


def load_fixture_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    posts = payload.get("posts")
    if not isinstance(posts, list):
        raise IngestError(f"Fixture {path} must be a list or an object with a posts array")
    return posts


def filter_window(posts: list[Post], hours: float, as_of: datetime) -> list[Post]:
    cutoff = as_of - timedelta(hours=hours)
    return [post for post in posts if cutoff <= post.created_at <= as_of]


def resolve_as_of(posts: list[Post], cfg: Config) -> datetime:
    if cfg.as_of is not None:
        return cfg.as_of
    if cfg.mock and posts:
        # Anchor mock windows to the fixture timeline so CI stays green.
        return max(post.created_at for post in posts)
    return datetime.now(timezone.utc)


def load_mock_posts(cfg: Config) -> tuple[list[Post], datetime]:
    path = cfg.fixture_path or default_fixture_path()
    rows = load_fixture_rows(path)
    posts = [row_to_post(row, cfg, source="fixture") for row in rows]
    as_of = resolve_as_of(posts, cfg)
    return filter_window(posts, cfg.hours, as_of), as_of


def posts_from_x_payload(payload: dict[str, Any], cfg: Config) -> list[Post]:
    users = {str(user["id"]): user for user in payload.get("includes", {}).get("users", [])}
    posts: list[Post] = []
    for item in payload.get("data") or []:
        author_id = str(item.get("author_id") or "")
        user = users.get(author_id, {})
        username = str(user.get("username") or item.get("username") or "unknown")
        metrics = item.get("public_metrics") or {}
        row = {
            "id": item.get("id"),
            "author": username,
            "author_id": author_id or None,
            "text": item.get("text") or "",
            "created_at": item.get("created_at"),
            "likes": metrics.get("like_count") or 0,
            "reposts": metrics.get("retweet_count") or 0,
            "replies": metrics.get("reply_count") or 0,
            "quotes": metrics.get("quote_count") or 0,
            "url": post_url(str(item.get("id")), username),
        }
        posts.append(row_to_post(row, cfg, source="x-search"))
    return posts


def http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise IngestError(f"X search failed ({exc.code}): {detail[:400]}") from exc
    except urllib.error.URLError as exc:
        raise IngestError(f"X search unreachable: {exc.reason}") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise IngestError("X search returned non-JSON") from exc
    if not isinstance(payload, dict):
        raise IngestError("X search returned an unexpected payload")
    return payload


def search_x(cfg: Config, fetch: FetchFn | None = None) -> tuple[list[Post], datetime]:
    if not cfg.bearer_token:
        raise IngestError(
            "Live X search requires NARRATIVERADAR_X_BEARER_TOKEN (or X_BEARER_TOKEN). "
            "Keep NARRATIVERADAR_MOCK=1 for the offline fixture path."
        )
    as_of = cfg.as_of or datetime.now(timezone.utc)
    start = as_of - timedelta(hours=cfg.hours)
    params = {
        "query": cfg.query,
        "max_results": str(min(max(cfg.max_posts, 10), 100)),
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "username,name",
        "start_time": isoformat_z(start),
    }
    url = f"{cfg.x_api_base.rstrip('/')}/tweets/search/recent?{urllib.parse.urlencode(params)}"
    headers = {
        "Authorization": f"Bearer {cfg.bearer_token}",
        "User-Agent": "NarrativeRadar/0.1 (+https://github.com/HEADWOPZ/narrativeradar)",
    }
    client = fetch or http_get_json
    payload = client(url, headers)
    posts = posts_from_x_payload(payload, cfg)
    return filter_window(posts, cfg.hours, as_of), as_of


def ingest(cfg: Config, fetch: FetchFn | None = None) -> tuple[list[Post], datetime]:
    """Return (posts, as_of). Mock never touches the network."""

    if cfg.mock:
        return load_mock_posts(cfg)
    return search_x(cfg, fetch=fetch)
