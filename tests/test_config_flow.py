"""Tests for config_flow.py — all phase1."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.free_games.const import (
    DOMAIN,
    OPTION_PLATFORMS,
    PLATFORM_FEED_PATHS,
)


@pytest.mark.phase1
async def test_initial_setup_creates_entry(hass) -> None:
    with patch("custom_components.free_games.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={OPTION_PLATFORMS: ["steam_game", "epic_game"]},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][OPTION_PLATFORMS] == ["steam_game", "epic_game"]


@pytest.mark.phase1
async def test_options_flow_updates_platforms(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={OPTION_PLATFORMS: list(PLATFORM_FEED_PATHS.keys())},
        unique_id="lootscraper_feed",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={OPTION_PLATFORMS: ["steam_game"]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[OPTION_PLATFORMS] == ["steam_game"]


@pytest.mark.phase1
async def test_duplicate_setup_aborted(hass) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="lootscraper_feed")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
