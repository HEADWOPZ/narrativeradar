"""JSON, Telegram-friendly markdown, and CSV watchlist export."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from narrativeradar.models import Brief, OpportunityCard

TELEGRAM_SPECIAL = re.compile(r"([_*`\[])")


def escape_telegram(text: str) -> str:
    """Escape Telegram legacy-Markdown metacharacters in untrusted snippets."""

    return TELEGRAM_SPECIAL.sub(r"\\\1", text)


def render_card_markdown(card: OpportunityCard, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    tickers = " ".join(f"${item}" for item in card.tickers) or "—"
    kols = ", ".join(f"@{name}" for name in card.kols) or "—"
    lines = [
        f"*{prefix}{escape_telegram(card.theme)}*",
        f"score `{card.spike_score:.0f}` · {card.post_count} posts · {escape_telegram(tickers)}",
        f"*KOLs:* {escape_telegram(kols)}",
        f"*Why:* {escape_telegram(card.why)}",
        "*Receipts:*",
    ]
    for receipt in card.receipts:
        author = escape_telegram(receipt.author)
        excerpt = escape_telegram(receipt.excerpt)
        lines.append(f"• [{author}]({receipt.url}) `{receipt.post_id}`")
        lines.append(f"  _{excerpt}_")
    return "\n".join(lines)


def render_telegram(brief: Brief) -> str:
    lines = [
        "📡 *NarrativeRadar*",
        (
            f"source `{escape_telegram(brief.source)}` · {brief.card_count} cards · "
            f"{brief.window_hours:g}h · {brief.post_count} posts"
        ),
        "",
    ]
    if not brief.cards:
        lines.append("_No narrative spikes above the score floor._")
    else:
        for index, card in enumerate(brief.cards, start=1):
            lines.append(render_card_markdown(card, index=index))
            lines.append("")
    lines.append(f"_{escape_telegram(brief.disclaimer)}_")
    return "\n".join(lines).rstrip() + "\n"


def render_json(brief: Brief) -> str:
    return json.dumps(brief.to_dict(), indent=2, ensure_ascii=True) + "\n"


def write_watchlist_csv(path: Path, brief: Brief) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "card_id",
        "theme",
        "spike_score",
        "tickers",
        "kols",
        "post_count",
        "top_receipt_id",
        "top_receipt_url",
        "why",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for card in brief.cards:
            top = card.receipts[0] if card.receipts else None
            writer.writerow(
                {
                    "card_id": card.id,
                    "theme": card.theme,
                    "spike_score": f"{card.spike_score:.1f}",
                    "tickers": " ".join(card.tickers),
                    "kols": " ".join(card.kols),
                    "post_count": card.post_count,
                    "top_receipt_id": top.post_id if top else "",
                    "top_receipt_url": top.url if top else "",
                    "why": card.why,
                }
            )


def write_brief(brief: Brief, out_dir: Path, formats: set[str]) -> list[Path]:
    """Write selected artifacts. `all` expands to json/md/csv."""

    out_dir.mkdir(parents=True, exist_ok=True)
    if "all" in formats:
        formats = {"json", "md", "csv"}
    written: list[Path] = []
    if "json" in formats:
        path = out_dir / "brief.json"
        path.write_text(render_json(brief), encoding="utf-8")
        written.append(path)
    if "md" in formats:
        path = out_dir / "brief.md"
        path.write_text(render_telegram(brief), encoding="utf-8")
        written.append(path)
    if "csv" in formats:
        path = out_dir / "watchlist.csv"
        write_watchlist_csv(path, brief)
        written.append(path)
    return written
