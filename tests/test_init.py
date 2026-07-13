"""Tests for __init__.py — entry setup and options-update reload behaviour."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.free_games.const import (
    DOMAIN,
    OPTION_PLATFORMS,
    PLATFORM_FEED_PATHS,
)


@pytest.mark.phase4
async def test_updating_options_reloads_the_entry(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={OPTION_PLATFORMS: list(PLATFORM_FEED_PATHS.keys())},
        unique_id="lootscraper_feed",
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.free_games.async_get_clientsession",
            return_value=AsyncMock(),
        ),
        patch(
            "custom_components.free_games.coordinator.fetch_feed_data",
            return_value=([], {}),
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED

        with patch(
            "homeassistant.config_entries.ConfigEntries.async_reload",
            wraps=hass.config_entries.async_reload,
        ) as mock_reload:
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, OPTION_PLATFORMS: ["steam_game"]}
            )
            await hass.async_block_till_done()

    mock_reload.assert_called_once_with(entry.entry_id)
