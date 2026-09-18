from __future__ import annotations

from narrativeradar.config import Config
from narrativeradar.pipeline import run_brief


def test_cards_have_receipts_with_ids_and_urls(mock_config: Config) -> None:
    brief = run_brief(mock_config)
    assert brief.card_count >= 3
    assert brief.source == "mock"
    for card in brief.cards:
        assert card.receipts, f"{card.theme} missing receipts"
        for receipt in card.receipts:
            assert receipt.post_id
            assert receipt.url.startswith("https://x.com/")
            assert receipt.excerpt
        assert "receipt" in card.why.lower()


def test_tiktok_card_links_only_evidenced_tickers(mock_config: Config) -> None:
    brief = run_brief(mock_config)
    tiktok = next(card for card in brief.cards if card.theme_id == "tiktok_attention")
    assert "BONK" in tiktok.tickers
    assert "WIF" in tiktok.tickers
    assert "BTC" not in tiktok.tickers


def test_prediction_card_has_no_invented_ticker(mock_config: Config) -> None:
    brief = run_brief(mock_config)
    pred = next(card for card in brief.cards if card.theme_id == "prediction_markets")
    assert pred.tickers == []
    assert "no ticker" in pred.why.lower() or "no cashtag" in pred.why.lower()
