"""Link tickers and mint-like strings only when they appear in text."""

from __future__ import annotations

import re
from collections.abc import Iterable

from narrativeradar.models import Post

CASHTAG_RE = re.compile(r"(?<![A-Za-z0-9])\$([A-Za-z]{2,10})\b")
MINT_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
WORD_RE = re.compile(r"[A-Za-z]{3,}")

# Whole-word aliases only. Never invent a ticker that is not evidenced in text.
WORD_TICKERS = {
    "solana": "SOL",
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "dogwifhat": "WIF",
    "bonk": "BONK",
}


def extract_tickers(text: str) -> list[str]:
    """Return unique tickers/mints evidenced in `text`, cashtags first."""

    found: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        key = token.upper() if token.isascii() and token.isalpha() else token
        if key not in seen:
            seen.add(key)
            found.append(key)

    for match in CASHTAG_RE.finditer(text):
        add(match.group(1).upper())

    lowered = text.lower()
    for word in WORD_RE.findall(lowered):
        mapped = WORD_TICKERS.get(word)
        if mapped:
            add(mapped)

    for match in MINT_RE.finditer(text):
        raw = match.group(0)
        if raw.isdigit():
            continue
        add(raw)

    return found


def extract_tickers_from_posts(posts: Iterable[Post]) -> list[str]:
    """Union of tickers evidenced in any post, stable order by first appearance."""

    found: list[str] = []
    seen: set[str] = set()
    for post in posts:
        for ticker in extract_tickers(post.text):
            if ticker not in seen:
                seen.add(ticker)
                found.append(ticker)
    return found
