"""Build and filter opportunity cards from clusters."""

from __future__ import annotations

from datetime import datetime

from narrativeradar.config import Config
from narrativeradar.models import Cluster, OpportunityCard
from narrativeradar.score import score_cluster


def build_cards(clusters: list[Cluster], cfg: Config, as_of: datetime) -> list[OpportunityCard]:
    cards = [score_cluster(cluster, cfg, as_of) for cluster in clusters]
    cards = [card for card in cards if card.spike_score >= cfg.min_score]
    cards.sort(key=lambda card: (-card.spike_score, card.theme_id))
    return cards
