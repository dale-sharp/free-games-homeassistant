"""Tests for const.py — build_feed_url and the path-based feed constants."""

from __future__ import annotations

import pytest

from custom_components.free_games.const import (
    CONSOLIDATED_FEED_PATH,
    DEFAULT_BASE_URL,
    PLATFORM_FEED_PATHS,
    build_feed_url,
)

# The exact URLs PLATFORM_FEEDS/CONSOLIDATED_FEED_URL hardcoded before this refactor —
# kept here as the regression baseline the new base-URL + path construction must reproduce.
_LEGACY_PLATFORM_URLS = {
    "steam_game": "https://feed.eikowagenknecht.com/lootscraper_steam_game.xml",
    "epic_game": "https://feed.eikowagenknecht.com/lootscraper_epic_game.xml",
    "gog_game": "https://feed.eikowagenknecht.com/lootscraper_gog_game.xml",
    "humble_game": "https://feed.eikowagenknecht.com/lootscraper_humble_game.xml",
    "itch_game": "https://feed.eikowagenknecht.com/lootscraper_itch_game.xml",
    "amazon_game": "https://feed.eikowagenknecht.com/lootscraper_amazon_game.xml",
    "amazon_loot": "https://feed.eikowagenknecht.com/lootscraper_amazon_loot.xml",
    "steam_loot": "https://feed.eikowagenknecht.com/lootscraper_steam_loot.xml",
    "epic_android": "https://feed.eikowagenknecht.com/lootscraper_epic_game_android.xml",
    "epic_ios": "https://feed.eikowagenknecht.com/lootscraper_epic_game_ios.xml",
    "apple_game": "https://feed.eikowagenknecht.com/lootscraper_apple_game.xml",
    "google_game": "https://feed.eikowagenknecht.com/lootscraper_google_game.xml",
}
_LEGACY_CONSOLIDATED_URL = "https://feed.eikowagenknecht.com/lootscraper.xml"


@pytest.mark.phase3
def test_build_feed_url_joins_base_and_path() -> None:
    assert (
        build_feed_url("https://feed.eikowagenknecht.com", "lootscraper.xml")
        == _LEGACY_CONSOLIDATED_URL
    )


@pytest.mark.phase3
def test_build_feed_url_strips_trailing_slash_on_base() -> None:
    assert (
        build_feed_url("https://feed.eikowagenknecht.com/", "lootscraper.xml")
        == _LEGACY_CONSOLIDATED_URL
    )


@pytest.mark.phase3
@pytest.mark.parametrize("key", sorted(_LEGACY_PLATFORM_URLS))
def test_default_platform_url_matches_legacy_url(key: str) -> None:
    assert (
        build_feed_url(DEFAULT_BASE_URL, PLATFORM_FEED_PATHS[key])
        == _LEGACY_PLATFORM_URLS[key]
    )


@pytest.mark.phase3
def test_default_consolidated_url_matches_legacy_url() -> None:
    assert (
        build_feed_url(DEFAULT_BASE_URL, CONSOLIDATED_FEED_PATH)
        == _LEGACY_CONSOLIDATED_URL
    )
