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
