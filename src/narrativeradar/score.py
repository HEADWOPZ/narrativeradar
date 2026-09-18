"""Transparent spike scoring and receipt-backed opportunity cards."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta

from narrativeradar.config import Config
from narrativeradar.models import Cluster, OpportunityCard, Post, Receipt, isoformat_z
from narrativeradar.tickers import extract_tickers_from_posts


def _card_id(theme_id: str, posts: list[Post]) -> str:
    joined = ",".join(sorted(post.id for post in posts))
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:10]
    return f"nr-{theme_id}-{digest}"


def _receipts(posts: list[Post], limit: int) -> list[Receipt]:
    ranked = sorted(posts, key=lambda post: (-post.engagement, -post.created_at.timestamp(), post.id))
    receipts: list[Receipt] = []
    for post in ranked[:limit]:
        receipts.append(
            Receipt(
                post_id=post.id,
                url=post.url,
                author=post.author,
                excerpt=post.excerpt(),
                created_at=isoformat_z(post.created_at),
                engagement=post.engagement,
                is_kol=post.is_kol,
            )
        )
    return receipts


def _summary(cluster: Cluster, tickers: list[str], hours: float) -> str:
    ticker_bit = ""
    if tickers:
        ticker_bit = " · linked " + ", ".join(f"${item}" for item in tickers)
    return f"{cluster.theme} — {len(cluster.posts)} posts in {hours:g}h{ticker_bit}"


def _why(
    cluster: Cluster,
    *,
    score: float,
    components: dict[str, float],
    tickers: list[str],
    kols: list[str],
    recent_count: int,
    window_hours: float,
) -> str:
    ticker_clause = (
        f" Linked tickers {', '.join('$' + item for item in tickers)} appear in-cluster text."
        if tickers
        else " No cashtag/alias/mint was evidenced in-cluster text, so no ticker was attached."
    )
    kol_clause = f" KOLs: {', '.join('@' + name for name in kols)}." if kols else " No configured KOL in the cluster."
    return (
        f"This card fired because {len(cluster.posts)} posts clustered on "
        f"“{cluster.theme}” via {cluster.method} matching. "
        f"{recent_count} of them landed in the most recent quarter of the {window_hours:g}h window. "
        f"Score {score:.0f}/100 = volume {components['volume']:.0f} + engagement {components['engagement']:.0f} "
        f"+ kol {components['kol']:.0f} + velocity {components['velocity']:.0f} "
        f"+ ticker {components['ticker']:.0f}."
        f"{kol_clause}{ticker_clause} Receipts cite the highest-engagement posts."
    )


def score_cluster(cluster: Cluster, cfg: Config, as_of: datetime) -> OpportunityCard:
    posts = cluster.posts
    hours = cfg.hours
    engagement_total = sum(post.engagement for post in posts)
    kols = sorted({post.author for post in posts if post.is_kol})
    kol_weight = sum(post.kol_weight for post in posts if post.is_kol)
    tickers = extract_tickers_from_posts(posts)

    volume = min(30.0, len(posts) * 4.5)
    engagement = min(30.0, math.log1p(engagement_total) * 2.55)
    kol = min(20.0, kol_weight * 6.5)
    recent_cut = as_of - timedelta(hours=max(hours * 0.25, 1.0))
    recent = [post for post in posts if post.created_at >= recent_cut]
    velocity = min(15.0, (len(recent) / max(hours * 0.25, 1.0)) * 10.0)
    ticker_pts = 5.0 if tickers else 0.0
    components = {
        "volume": round(volume, 2),
        "engagement": round(engagement, 2),
        "kol": round(kol, 2),
        "velocity": round(velocity, 2),
        "ticker": ticker_pts,
    }
    score = round(min(100.0, sum(components.values())), 1)

    first_seen = min(post.created_at for post in posts)
    last_seen = max(post.created_at for post in posts)
    return OpportunityCard(
        id=_card_id(cluster.theme_id, posts),
        theme=cluster.theme,
        theme_id=cluster.theme_id,
        summary=_summary(cluster, tickers, hours),
        spike_score=score,
        window_hours=hours,
        tickers=tickers,
        kols=kols,
        post_count=len(posts),
        engagement_total=engagement_total,
        why=_why(
            cluster,
            score=score,
            components=components,
            tickers=tickers,
            kols=kols,
            recent_count=len(recent),
            window_hours=hours,
        ),
        receipts=_receipts(posts, cfg.max_receipts),
        first_seen=isoformat_z(first_seen),
        last_seen=isoformat_z(last_seen),
        keywords=cluster.keywords,
        components=components,
    )
