from __future__ import annotations

from narrativeradar.cluster import cluster_posts, match_seed
from narrativeradar.config import Config
from narrativeradar.ingest import load_mock_posts


def test_seed_match_social_arb() -> None:
    seed = match_seed("social arb opportunities everywhere")
    assert seed is not None
    assert seed.theme_id == "social_arb"


def test_fixture_clusters_expected_themes(mock_config: Config) -> None:
    posts, _ = load_mock_posts(mock_config)
    clusters = cluster_posts(posts)
    ids = {cluster.theme_id for cluster in clusters}
    assert {"social_arb", "tiktok_attention", "prediction_markets", "explainable_discovery"} <= ids
    # Lunch/weather noise should not become a scored theme cluster
    assert "adhoc-tacos" not in ids


def test_related_posts_share_a_cluster(mock_config: Config) -> None:
    posts, _ = load_mock_posts(mock_config)
    clusters = cluster_posts(posts)
    tiktok = next(cluster for cluster in clusters if cluster.theme_id == "tiktok_attention")
    authors = {post.author for post in tiktok.posts}
    assert "ansem" in authors
    assert len(tiktok.posts) >= 5
