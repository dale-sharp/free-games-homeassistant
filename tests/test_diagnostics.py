"""Tests for diagnostics.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.free_games.const import (
    DEFAULT_BASE_URL,
    DOMAIN,
    OPTION_BASE_URL,
    OPTION_PLATFORMS,
    OPTION_SCAN_INTERVAL_MINUTES,
)
from custom_components.free_games.diagnostics import (
    async_get_config_entry_diagnostics,
)


def _make_entry(**options: object) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, options=options, unique_id="lootscraper_feed"
    )
    entry.runtime_data = MagicMock()
    entry.runtime_data.data = {"platform_offers": {}}
    entry.runtime_data.last_update_success = True
    entry.runtime_data.last_exception = None
    return entry


@pytest.mark.phase1
async def test_default_base_url_is_not_redacted(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["options"][OPTION_BASE_URL] == DEFAULT_BASE_URL


@pytest.mark.phase1
async def test_custom_base_url_is_redacted(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: "https://self-hosted.example.com",
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["options"][OPTION_BASE_URL] == "**REDACTED**"


@pytest.mark.phase1
async def test_offer_counts_reflect_lengths_not_full_payloads(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    entry.runtime_data.data = {
        "platform_offers": {
            "steam_game": [{"id": "1"}, {"id": "2"}],
            "epic_game": [{"id": "3"}],
        }
    }
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator"]["offer_counts_by_platform"] == {
        "steam_game": 2,
        "epic_game": 1,
    }


@pytest.mark.phase1
async def test_sample_offers_capped_at_10(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    offers = [{"id": str(i), "title": f"Game {i}"} for i in range(15)]
    entry.runtime_data.data = {"offers": offers, "platform_offers": {}}
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert len(result["coordinator"]["sample_offers"]) <= 10


@pytest.mark.phase1
async def test_sample_offers_reflect_actual_offer_data(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    offer = {
        "id": "abc123",
        "title": "Steam (Game) - Some Title",
        "game_name": "Some Title",
        "store": "Steam",
        "platform": "PC",
        "type": "Game",
        "claim_url": "https://store.steampowered.com/app/123",
        "published": "2026-01-01T00:00:00Z",
        "updated": "",
        "image_url": "https://example.com/image.jpg",
        "description": "A great game",
        "genres": ["Action", "Indie"],
        "recommended_price": "9.99 EUR",
        "offer_from": "2026-01-01",
        "offer_to": "2026-01-08",
        "platform_key": "steam_game",
    }
    entry.runtime_data.data = {"offers": [offer], "platform_offers": {}}
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator"]["sample_offers"] == [offer]


@pytest.mark.phase1
async def test_last_exception_none_when_absent(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator"]["last_exception"] is None


@pytest.mark.phase1
async def test_last_exception_rendered_as_string_when_present(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    entry.runtime_data.last_exception = ValueError("boom")
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator"]["last_exception"] == "boom"


@pytest.mark.phase1
async def test_last_update_success_passes_through(hass) -> None:
    entry = _make_entry(
        **{
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        }
    )
    entry.runtime_data.last_update_success = False
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator"]["last_update_success"] is False
