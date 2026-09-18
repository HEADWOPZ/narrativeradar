"""Optional local FastAPI desk for opportunity cards."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from narrativeradar import __version__
from narrativeradar.config import Config
from narrativeradar.pipeline import run_brief

DESK_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>NarrativeRadar</title>
  <style>
    :root {
      --bg: #0b0d10;
      --panel: #14181e;
      --ink: #e8eef4;
      --muted: #8b98a5;
      --cyan: #3ee0c5;
      --gold: #e4b84a;
      --line: #232a33;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 15px/1.5 ui-sans-serif, system-ui, sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #16302b 0%, var(--bg) 45%);
      color: var(--ink);
    }
    header, main { max-width: 1080px; margin: 0 auto; padding: 24px; }
    header { padding-bottom: 0; }
    .kicker { color: var(--cyan); letter-spacing: 0.12em; font-size: 12px; text-transform: uppercase; }
    h1 { margin: 6px 0 8px; font-size: 28px; }
    .sub { color: var(--muted); max-width: 720px; }
    .meta { margin-top: 16px; color: var(--muted); font-size: 13px; }
    .grid { display: grid; gap: 16px; }
    @media (min-width: 860px) { .grid { grid-template-columns: 1fr 1fr; } }
    article {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px 18px;
    }
    .score {
      display: inline-block;
      background: #10241f;
      color: var(--cyan);
      border: 1px solid #1e4d43;
      border-radius: 999px;
      padding: 2px 10px;
      font-variant-numeric: tabular-nums;
    }
    .tickers { color: var(--gold); }
    .why { color: var(--muted); font-size: 13px; }
    ul { padding-left: 18px; margin: 8px 0 0; }
    a { color: var(--cyan); }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      color: var(--cyan);
      background: #10241f;
      padding: 1px 6px;
      border-radius: 6px;
    }
    .receipt-meta { color: var(--muted); font-size: 12px; }
    footer { max-width: 1080px; margin: 0 auto; padding: 0 24px 32px; color: var(--muted); font-size: 12px; }
  </style>
</head>
<body>
  <header>
    <div class="kicker">HEADWOPZ · social arb</div>
    <h1>NarrativeRadar</h1>
    <p class="sub">CT narrative spikes scored into opportunity cards with receipts. Not an on-chain trench desk. Not a trading bot.</p>
    <p class="meta" id="meta">Loading brief…</p>
  </header>
  <main>
    <div class="grid" id="cards"></div>
  </main>
  <footer id="foot"></footer>
  <script>
    function el(html) {
      const t = document.createElement("template");
      t.innerHTML = html.trim();
      return t.content.firstElementChild;
    }
    fetch("/api/brief").then(r => r.json()).then(brief => {
      document.getElementById("meta").textContent =
        `${brief.source} · ${brief.card_count} cards · ${brief.window_hours}h · ${brief.post_count} posts`;
      document.getElementById("foot").textContent = brief.disclaimer;
      const root = document.getElementById("cards");
      if (!brief.cards.length) {
        root.appendChild(el("<article><p>No narrative spikes above the score floor.</p></article>"));
        return;
      }
      for (const card of brief.cards) {
        const tickers = card.tickers.length ? card.tickers.map(t => "$" + t).join(" ") : "—";
        const receipts = card.receipts.map(r =>
          `<li><a href="${r.url}">@${r.author}</a> <span class="receipt-meta">·</span> <code>${r.post_id}</code><div class="why">${r.excerpt}</div></li>`
        ).join("");
        root.appendChild(el(`
          <article>
            <div><span class="score">${Math.round(card.spike_score)}</span></div>
            <h2>${card.theme}</h2>
            <p class="tickers">${tickers}</p>
            <p class="why">${card.why}</p>
            <ul>${receipts}</ul>
          </article>
        `));
      }
    }).catch(err => {
      document.getElementById("meta").textContent = "Failed to load /api/brief";
      document.getElementById("cards").textContent = String(err);
    });
  </script>
</body>
</html>
"""


def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config.from_env()
    app = FastAPI(
        title="NarrativeRadar",
        version=__version__,
        description="CT social-arb narrative spike detector. Research only — no auto-trading.",
    )

    def _brief():
        return run_brief(cfg)

    @app.get("/", response_class=HTMLResponse)
    def desk() -> str:
        return DESK_HTML

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True, "version": __version__, "mock": cfg.mock, "source": cfg.source}

    @app.get("/api/brief")
    def api_brief() -> dict[str, object]:
        return _brief().to_dict()

    @app.get("/api/cards")
    def api_cards() -> dict[str, object]:
        brief = _brief()
        return {"cards": [card.to_dict() for card in brief.cards]}

    @app.get("/api/cards/{card_id}")
    def api_card(card_id: str) -> dict[str, object]:
        card = _brief().card_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Unknown card id")
        return card.to_dict()

    @app.get("/api/explain/{card_id}")
    def api_explain(card_id: str) -> dict[str, object]:
        card = _brief().card_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Unknown card id")
        return {
            "id": card.id,
            "theme": card.theme,
            "why": card.why,
            "components": card.components,
            "receipts": [receipt.to_dict() for receipt in card.receipts],
            "tickers": card.tickers,
        }

    return app
