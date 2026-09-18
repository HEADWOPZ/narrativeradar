from __future__ import annotations

from narrativeradar.cards import build_cards
from narrativeradar.cluster import cluster_posts
from narrativeradar.config import Config
from narrativeradar.ingest import load_mock_posts
from narrativeradar.score import score_cluster


def test_spike_score_is_deterministic(mock_config: Config) -> None:
    posts, as_of = load_mock_posts(mock_config)
    clusters = cluster_posts(posts)
    first = [score_cluster(cluster, mock_config, as_of) for cluster in clusters]
    second = [score_cluster(cluster, mock_config, as_of) for cluster in clusters]
    assert [card.spike_score for card in first] == [card.spike_score for card in second]
    assert [card.id for card in first] == [card.id for card in second]


def test_components_sum_to_score(mock_config: Config) -> None:
    posts, as_of = load_mock_posts(mock_config)
    cluster = cluster_posts(posts)[0]
    card = score_cluster(cluster, mock_config, as_of)
    assert card.spike_score == round(sum(card.components.values()), 1)
    assert 0 <= card.spike_score <= 100


def test_min_score_filters_cards(mock_config: Config) -> None:
    posts, as_of = load_mock_posts(mock_config)
    clusters = cluster_posts(posts)
    strict = Config(**{**mock_config.__dict__, "min_score": 99.0})
    assert build_cards(clusters, strict, as_of) == []
