"""Tests guarding that every platform key is registered consistently everywhere."""

from __future__ import annotations

import pytest

from custom_components.free_games.config_flow import PLATFORM_LABELS
from custom_components.free_games.const import (
    PLATFORM_FEED_PATHS,
    PLATFORM_KEY_CATEGORIES,
)


@pytest.mark.phase5
def test_platform_feed_paths_and_categories_have_same_keys() -> None:
    assert set(PLATFORM_FEED_PATHS) == set(PLATFORM_KEY_CATEGORIES)


@pytest.mark.phase5
def test_platform_feed_paths_and_labels_have_same_keys() -> None:
    assert set(PLATFORM_FEED_PATHS) == set(PLATFORM_LABELS)
