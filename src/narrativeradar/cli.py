"""CLI: narrativeradar brief | watch | serve."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from narrativeradar import __version__
from narrativeradar.config import Config
from narrativeradar.export import render_json, render_telegram, write_brief
from narrativeradar.ingest import IngestError
from narrativeradar.pipeline import run_brief


def _add_shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--hours", type=float, default=None, help="Lookback window in hours (default 24)")
    parser.add_argument("--min-score", type=float, default=None, dest="min_score", help="Minimum spike score")
    parser.add_argument("--fixture", type=Path, default=None, help="Override mock fixture JSON")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use live X recent-search (requires a bearer token). Default is MOCK=1.",
    )
    parser.add_argument("--query", default=None, help="Override live X search query")


def _config_from_args(args: argparse.Namespace) -> Config:
    mock = False if getattr(args, "live", False) else None
    return Config.from_env(
        mock=mock,
        hours=args.hours,
        min_score=args.min_score,
        fixture_path=args.fixture,
        query=args.query,
    )


def _parse_formats(raw: str) -> set[str]:
    parts = {part.strip().lower() for part in raw.split(",") if part.strip()}
    allowed = {"json", "md", "csv", "all"}
    unknown = parts - allowed
    if unknown:
        raise ValueError(f"Unknown format(s): {', '.join(sorted(unknown))}")
    return parts or {"md"}


def cmd_brief(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args)
    try:
        brief = run_brief(cfg)
    except IngestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    formats = _parse_formats(args.format)
    if args.out:
        written = write_brief(brief, args.out, formats)
        if not args.quiet:
            for path in written:
                print(path)
    if args.quiet:
        return 0
    if args.out and "json" not in formats and "md" not in formats:
        return 0
    if "json" in formats and "md" not in formats and "all" not in formats:
        sys.stdout.write(render_json(brief))
    elif not args.out:
        if "json" in formats and "md" not in formats:
            sys.stdout.write(render_json(brief))
        else:
            sys.stdout.write(render_telegram(brief))
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args)
    state_path: Path = args.state
    seen: set[str] = set()
    if state_path.exists():
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            seen = set(payload.get("card_ids") or [])
        except (OSError, json.JSONDecodeError):
            seen = set()

    cycles = 0
    max_cycles = 1 if args.once else args.max_cycles
    while True:
        try:
            brief = run_brief(cfg)
        except IngestError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        fresh = [card for card in brief.cards if card.id not in seen]
        if fresh:
            print(f"{len(fresh)} new card(s) · source {brief.source} · score floor {cfg.min_score:g}")
            for card in fresh:
                tickers = " ".join(f"${item}" for item in card.tickers) or "—"
                print(f"- [{card.spike_score:.0f}] {card.theme} · {tickers}")
                if card.receipts:
                    top = card.receipts[0]
                    print(f"  receipt {top.post_id} {top.url}")
                seen.add(card.id)
        else:
            print(f"no new spikes · {brief.card_count} card(s) already seen")
        state_path.write_text(json.dumps({"card_ids": sorted(seen)}, indent=2) + "\n", encoding="utf-8")
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            return 0
        time.sleep(max(args.interval, 1))


def cmd_serve(args: argparse.Namespace) -> int:
    cfg = _config_from_args(args)
    try:
        import uvicorn
    except ImportError:
        print("error: uvicorn is required for serve. Reinstall with: pip install -e .", file=sys.stderr)
        return 1
    from narrativeradar.desk import create_app

    app = create_app(cfg)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="narrativeradar",
        description="CT social-arb narrative spike detector → scored opportunity cards with receipts.",
    )
    parser.add_argument("--version", action="version", version=f"narrativeradar {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    brief = sub.add_parser("brief", help="Score the current window and print/export cards")
    _add_shared(brief)
    brief.add_argument(
        "--format",
        default="md",
        help="json, md, csv, all, or a comma list (default md)",
    )
    brief.add_argument("--out", type=Path, default=None, help="Write artifacts to this directory")
    brief.add_argument("--quiet", action="store_true", help="Write files only, no stdout brief")
    brief.set_defaults(func=cmd_brief)

    watch = sub.add_parser("watch", help="Re-run the brief and print newly seen cards")
    _add_shared(watch)
    watch.add_argument("--interval", type=float, default=60.0, help="Seconds between cycles")
    watch.add_argument("--once", action="store_true", help="Run a single cycle (useful for CI)")
    watch.add_argument("--max-cycles", type=int, default=None, dest="max_cycles")
    watch.add_argument(
        "--state",
        type=Path,
        default=Path(".narrativeradar-state.json"),
        help="Seen-card state file",
    )
    watch.set_defaults(func=cmd_watch)

    serve = sub.add_parser("serve", help="Local FastAPI desk (HTML + JSON)")
    _add_shared(serve)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
