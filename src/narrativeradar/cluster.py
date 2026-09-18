"""Cluster posts into narrative themes (lexicon + Jaccard leftovers)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from narrativeradar.models import Cluster, Post
from narrativeradar.tickers import extract_tickers

TOKEN_RE = re.compile(r"[a-z0-9$]{3,}")

STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "you",
        "this",
        "that",
        "with",
        "from",
        "are",
        "was",
        "were",
        "have",
        "has",
        "not",
        "but",
        "just",
        "all",
        "out",
        "about",
        "into",
        "your",
        "our",
        "their",
        "what",
        "when",
        "where",
        "who",
        "why",
        "how",
        "than",
        "then",
        "too",
        "very",
        "can",
        "could",
        "should",
        "would",
        "still",
        "again",
        "over",
        "after",
        "before",
        "another",
        "page",
        "today",
        "tonight",
        "week",
        "year",
        "nothing",
        "else",
    }
)

JACCARD_THRESHOLD = 0.22
MIN_CLUSTER_SIZE = 2


@dataclass(frozen=True)
class ThemeSeed:
    theme_id: str
    theme: str
    phrases: tuple[str, ...]


THEME_SEEDS: tuple[ThemeSeed, ...] = (
    ThemeSeed(
        theme_id="social_arb",
        theme="Social arb / attention premium",
        phrases=(
            "social arb",
            "narrative arb",
            "attention premium",
            "attention is clustering",
            "why anyone cares",
        ),
    ),
    ThemeSeed(
        theme_id="tiktok_attention",
        theme="Short-form / TikTok attention",
        phrases=(
            "tiktok",
            "short-form",
            "short form",
            "for you page",
            "slideshow",
        ),
    ),
    ThemeSeed(
        theme_id="prediction_markets",
        theme="Prediction markets",
        phrases=("polymarket", "prediction market", "kalshi", "election odds"),
    ),
    ThemeSeed(
        theme_id="explainable_discovery",
        theme="Explainable discovery",
        phrases=("receipts", "explainability", "scam-group", "scam group", "cite post"),
    ),
)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def tokens(text: str) -> set[str]:
    found = set(TOKEN_RE.findall(text.lower()))
    return {token for token in found if token not in STOPWORDS}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def match_seed(text: str) -> ThemeSeed | None:
    haystack = normalize(text)
    for seed in THEME_SEEDS:
        if any(phrase in haystack for phrase in seed.phrases):
            return seed
    return None


def _keywords(posts: list[Post], limit: int = 6) -> list[str]:
    counts: dict[str, int] = {}
    for post in posts:
        for token in tokens(post.text):
            if token.startswith("$"):
                continue
            counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:limit]]


def _cluster_from_posts(theme_id: str, theme: str, posts: list[Post], method: str) -> Cluster:
    keywords = _keywords(posts)
    tickers = extract_tickers(" ".join(post.text for post in posts))
    extra = [f"${ticker}" for ticker in tickers[:4]]
    merged = list(dict.fromkeys(keywords + extra))
    return Cluster(theme_id=theme_id, theme=theme, posts=posts, keywords=merged, method=method)


def _label_leftover(posts: list[Post], index: int) -> tuple[str, str]:
    words = _keywords(posts, limit=3)
    if words:
        theme = " / ".join(words)
        slug = "-".join(words)[:40]
        return f"adhoc-{slug}", theme
    return f"adhoc-{index}", f"Unlabeled cluster {index}"


def cluster_leftovers(posts: list[Post]) -> list[Cluster]:
    if not posts:
        return []
    groups: list[list[int]] = [[index] for index in range(len(posts))]
    token_sets = [tokens(post.text) for post in posts]

    merged = True
    while merged:
        merged = False
        best = 0.0
        pair: tuple[int, int] | None = None
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                score = 0.0
                count = 0
                for left in groups[i]:
                    for right in groups[j]:
                        score += jaccard(token_sets[left], token_sets[right])
                        count += 1
                avg = score / count if count else 0.0
                if avg > best:
                    best = avg
                    pair = (i, j)
        if pair and best >= JACCARD_THRESHOLD:
            i, j = pair
            groups[i] = groups[i] + groups[j]
            del groups[j]
            merged = True

    clusters: list[Cluster] = []
    for index, members in enumerate(groups, start=1):
        grouped = [posts[i] for i in members]
        if len(grouped) < MIN_CLUSTER_SIZE:
            continue
        theme_id, theme = _label_leftover(grouped, index)
        clusters.append(_cluster_from_posts(theme_id, theme, grouped, method="jaccard"))
    return clusters


def cluster_posts(posts: list[Post]) -> list[Cluster]:
    """Assign lexicon themes first, then Jaccard-cluster leftovers."""

    buckets: dict[str, list[Post]] = {seed.theme_id: [] for seed in THEME_SEEDS}
    leftovers: list[Post] = []
    seed_by_id = {seed.theme_id: seed for seed in THEME_SEEDS}

    for post in posts:
        seed = match_seed(post.text)
        if seed:
            buckets[seed.theme_id].append(post)
        else:
            leftovers.append(post)

    clusters: list[Cluster] = []
    for theme_id, grouped in buckets.items():
        if len(grouped) < MIN_CLUSTER_SIZE:
            leftovers.extend(grouped)
            continue
        seed = seed_by_id[theme_id]
        clusters.append(_cluster_from_posts(seed.theme_id, seed.theme, grouped, method="lexicon"))

    clusters.extend(cluster_leftovers(leftovers))
    clusters.sort(key=lambda cluster: (-len(cluster.posts), cluster.theme_id))
    return clusters
