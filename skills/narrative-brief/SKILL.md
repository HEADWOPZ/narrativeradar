---
name: narrative-brief
description: Score CT narrative spikes into cards with receipts.
version: 0.1.0
author: Kevin Lance Murray (HEADWOPZ)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Crypto, Narrative, Social, Brief, CT]
    related_skills: []
    blueprint:
      schedule: "0 13 * * *"
      deliver: origin
      prompt: "Run a NarrativeRadar brief (mock unless the user opted into live X) and summarize the top opportunity cards with cited receipts."
required_environment_variables:
  - name: NARRATIVERADAR_MOCK
    prompt: Keep mock ingest on unless live X is requested
    help: Default 1. Offline fixtures. Set 0 only when a bearer token is configured.
    required_for: "Offline-safe default"
  - name: NARRATIVERADAR_X_BEARER_TOKEN
    prompt: X API bearer token
    help: Optional. Only used when NARRATIVERADAR_MOCK=0.
    required_for: "Live X recent-search"
---

# Narrative brief

Turn Crypto Twitter (or packaged fixtures) into scored **opportunity cards** with cited post ids/urls. This is inbound social-arb radar, not an on-chain trench desk.

## When to Use

- The user asks for a narrative brief, CT spike check, social-arb cards, or “why did this fire?”
- They want Telegram-ready markdown or a JSON/CSV watchlist
- They want receipts (post ids + urls), not vibes

Don't use for:

- On-chain new-pair / rug / Dexscreener work (that is TrenchDesk)
- Drafting or scheduling Kevin’s own posts (that is AlgoDesk)
- Placing trades, sizing, or routing orders — NarrativeRadar never auto-trades

## Prerequisites

- Python 3.11+
- Package installed: `pip install -e .` from the repo root (or `pip install narrativeradar` when published)
- Default env: `NARRATIVERADAR_MOCK=1` so CI and local demos stay offline
- Live path only: `NARRATIVERADAR_MOCK=0` plus `NARRATIVERADAR_X_BEARER_TOKEN` (or `X_BEARER_TOKEN`)

## How to Use

Canonical invocation through the `terminal` tool. Prefer mock unless the user explicitly asks for live X.

```bash
export NARRATIVERADAR_MOCK=1
narrativeradar brief --format md
narrativeradar brief --format json --out ./out
narrativeradar watch --once
```

If they ask “why did this fire?”, run a JSON brief and read `cards[].why` plus `cards[].receipts`.

## Quick Reference

| Task | Command |
| --- | --- |
| Markdown brief to stdout | `narrativeradar brief --format md` |
| JSON + md + CSV | `narrativeradar brief --format all --out ./out` |
| One watch cycle | `narrativeradar watch --once` |
| Local desk | `narrativeradar serve --port 8765` |
| Live X (opt-in) | `NARRATIVERADAR_MOCK=0 narrativeradar brief --live` |

## Procedure

1. Confirm mock vs live. If unset, keep `NARRATIVERADAR_MOCK=1`.
2. Run `narrativeradar brief --format json --out ./out`.
3. Check `./out/brief.json` for `cards` sorted by `spike_score`.
4. For each card, quote `theme`, `spike_score`, `tickers` (only if present), `why`, and at least one receipt `post_id` + `url`.
5. If they want Telegram copy, also emit `./out/brief.md` (or `--format md`).
6. Remind them this is research only — no auto-trading.

## Pitfalls

- Tickers are linked only when a cashtag, known alias, or mint-like string appears in post text. Do not invent a ticker.
- Live mode without a bearer token fails closed. Fall back to mock; do not scrape.
- Mock windows are anchored to the fixture timeline so offline CI does not depend on wall-clock date.
- Score components are heuristic and transparent (`volume`, `engagement`, `kol`, `velocity`, `ticker`). They are not a price forecast.

## Verification

- `NARRATIVERADAR_MOCK=1 narrativeradar brief --format json` exits 0
- Output cards include `receipts[].post_id` and `receipts[].url`
- `pytest` in the repo is fully offline (fixtures only)
