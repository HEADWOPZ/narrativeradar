from __future__ import annotations

import os
from pathlib import Path

import pytest

from narrativeradar.config import Config
from narrativeradar.ingest import default_fixture_path

os.environ.setdefault("NARRATIVERADAR_MOCK", "1")


@pytest.fixture
def fixture_path() -> Path:
    return default_fixture_path()


@pytest.fixture
def mock_config(fixture_path: Path) -> Config:
    return Config(mock=True, fixture_path=fixture_path, hours=24.0, min_score=35.0)
