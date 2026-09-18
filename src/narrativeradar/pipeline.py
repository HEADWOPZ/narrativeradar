"""End-to-end brief pipeline used by CLI, watch, and the desk."""

from __future__ import annotations

from datetime import datetime, timezone

from narrativeradar.cards import build_cards
from narrativeradar.cluster import cluster_posts
from narrativeradar.config import Config
from narrativeradar.ingest import FetchFn, ingest
from narrativeradar.models import Brief, isoformat_z


def run_brief(cfg: Config | None = None, fetch: FetchFn | None = None) -> Brief:
    cfg = cfg or Config.from_env()
    posts, as_of = ingest(cfg, fetch=fetch)
    clusters = cluster_posts(posts)
    cards = build_cards(clusters, cfg, as_of)
    generated = cfg.as_of or datetime.now(timezone.utc)
    return Brief(
        generated_at=isoformat_z(generated),
        source=cfg.source,
        window_hours=cfg.hours,
        post_count=len(posts),
        card_count=len(cards),
        cards=cards,
    )
