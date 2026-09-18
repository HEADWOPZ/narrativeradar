# NarrativeRadar

**CT social-arb narrative spike detector → scored opportunity cards with receipts.**

Owner: [Kevin Lance Murray](https://github.com/HEADWOPZ) (HEADWOPZ)  
License: MIT

On-chain tools tell you a pair exists. Social arb tells you *why anyone cares*. NarrativeRadar clusters Crypto Twitter (or offline fixtures) into themes, scores the spike, and ships a card you can explain — with cited post ids and urls.

## What it is

- Inbound **social-arb radar** for CT / short-form narrative spikes
- Theme clustering → **spike score** + **linked tickers only when they appear in text**
- **Opportunity cards** as JSON, Telegram-friendly markdown, and a CSV watchlist
- Explainability: every card carries **receipts** (post id + url + excerpt)
- CLI: `narrativeradar brief`, `narrativeradar watch`, `narrativeradar serve`
- Hermes skill: [`skills/narrative-brief`](skills/narrative-brief/SKILL.md)

## What it isn’t

- **Not TrenchDesk.** No new-pair scanners, no Dexscreener clone, no on-chain rug heuristics
- **Not AlgoDesk.** It does not draft, schedule, or post to anyone’s account
- **Not a trading bot.** No auto-trading, no order routing, no custody, no “printer”
- Not financial advice. Cards are research artifacts, not execution signals

## Privacy

- Default **`NARRATIVERADAR_MOCK=1`** — fixtures only, no network, CI-safe
- Live X recent-search is **opt-in**: `MOCK=0` plus a bearer token you provide
- No telemetry. Tokens stay in your environment
- The desk is local (`127.0.0.1` by default)

## Install

Python 3.11+.

```bash
python -m pip install -e ".[dev]"
```

Copy [`.env.example`](.env.example) if you want local overrides. Leave mock on unless you intend to call X.

## Mock demo (offline)

```bash
export NARRATIVERADAR_MOCK=1
narrativeradar brief --format md
narrativeradar brief --format all --out ./out
narrativeradar watch --once
narrativeradar serve --port 8765
```

Open `http://127.0.0.1:8765` for the small FastAPI desk. JSON lives at `/api/brief`; “why did this fire?” is `/api/explain/{card_id}`.

Packaged fixtures: [`src/narrativeradar/data/posts.json`](src/narrativeradar/data/posts.json). Mock windows are anchored to the fixture timeline so demos and CI do not depend on today’s date.

## Live X (optional)

```bash
export NARRATIVERADAR_MOCK=0
export NARRATIVERADAR_X_BEARER_TOKEN=your_bearer_token
narrativeradar brief --live --query '(crypto OR solana OR narrative) lang:en -is:retweet'
```

Without a token, live mode fails closed and tells you to stay on mock. This repo’s GitHub Actions workflow never sets `MOCK=0`.

## Scoring (transparent)

Each cluster gets a 0–100 spike score from documented parts:

| Component | Cap | Signal |
| --- | --- | --- |
| volume | 30 | post count in-window |
| engagement | 30 | log of likes+reposts+quotes+replies |
| kol | 20 | configured / fixture KOL weight |
| velocity | 15 | share of posts in the most recent quarter-window |
| ticker | 5 | bonus only if a cashtag, alias, or mint-like string is in text |

`why` on each card restates those parts and lists receipts. Tickers are **never invented**.

## Hermes

Install or copy [`skills/narrative-brief/SKILL.md`](skills/narrative-brief/SKILL.md) into your Hermes skills tree. The skill prefers mock ingest and refuses to treat cards as trade tickets.

## Tests / CI

```bash
NARRATIVERADAR_MOCK=1 pytest -q
```

GitHub Actions runs the same offline path on Python 3.11 and 3.12.

## Related (different products)

| Product | Owns |
| --- | --- |
| **NarrativeRadar** | inbound social narrative → cards + receipts |
| TrenchDesk | on-chain meme / new-pair trench discovery |
| AlgoDesk | outbound drafts for Kevin’s own X account |
