"""Tests for config_flow.py — all phase1 except base-URL tests (phase3)."""

from __future__ import annotations

from unittest.mock import ANY, AsyncMock, patch

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.free_games.const import (
    DEFAULT_BASE_URL,
    DOMAIN,
    OPTION_BASE_URL,
    OPTION_PLATFORMS,
    PLATFORM_FEED_PATHS,
)


@pytest.fixture(autouse=True)
def mock_client_session():
    """Avoid constructing a real aiohttp session during base URL validation.

    async_get_clientsession(hass) builds a real ClientSession whose default
    resolver needs a SelectorEventLoop; pytest-homeassistant-custom-component
    runs tests on a ProactorEventLoop on Windows, so a real session blows up
    before fetch_feed_data (already mocked per-test) is ever reached.
    """
    with patch(
        "custom_components.free_games.config_flow.async_get_clientsession",
        return_value=AsyncMock(),
    ):
        yield


@pytest.mark.phase1
async def test_initial_setup_creates_entry(hass) -> None:
    with (
        patch("custom_components.free_games.async_setup_entry", return_value=True),
        patch(
            "custom_components.free_games.config_flow.fetch_feed_data",
            return_value=([], {}),
        ),
    ):
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

    with patch(
        "custom_components.free_games.config_flow.fetch_feed_data",
        return_value=([], {}),
    ):
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


@pytest.mark.phase3
async def test_initial_setup_uses_default_base_url_when_unset(hass) -> None:
    with (
        patch("custom_components.free_games.async_setup_entry", return_value=True),
        patch(
            "custom_components.free_games.config_flow.fetch_feed_data",
            return_value=([], {}),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={OPTION_PLATFORMS: ["steam_game"]},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][OPTION_BASE_URL] == DEFAULT_BASE_URL


@pytest.mark.phase3
async def test_initial_setup_stores_custom_reachable_base_url(hass) -> None:
    with (
        patch("custom_components.free_games.async_setup_entry", return_value=True),
        patch(
            "custom_components.free_games.config_flow.fetch_feed_data",
            return_value=([], {}),
        ) as mock_fetch,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                OPTION_PLATFORMS: ["steam_game"],
                OPTION_BASE_URL: "https://self-hosted.example.com/",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][OPTION_BASE_URL] == "https://self-hosted.example.com"
    mock_fetch.assert_called_once_with(
        ANY, "https://self-hosted.example.com/lootscraper.xml"
    )


@pytest.mark.phase3
async def test_initial_setup_rejects_unreachable_base_url(hass) -> None:
    with patch(
        "custom_components.free_games.config_flow.fetch_feed_data",
        side_effect=aiohttp.ClientError("boom"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                OPTION_PLATFORMS: ["steam_game"],
                OPTION_BASE_URL: "https://unreachable.example.com",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base_url": "cannot_connect"}


@pytest.mark.phase3
async def test_options_flow_prefills_existing_base_url(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            OPTION_PLATFORMS: list(PLATFORM_FEED_PATHS.keys()),
            OPTION_BASE_URL: "https://self-hosted.example.com",
        },
        unique_id="lootscraper_feed",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert (
        result["data_schema"]({})[OPTION_BASE_URL] == "https://self-hosted.example.com"
    )


@pytest.mark.phase3
async def test_options_flow_prefills_default_for_legacy_entry(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={OPTION_PLATFORMS: list(PLATFORM_FEED_PATHS.keys())},
        unique_id="lootscraper_feed",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["data_schema"]({})[OPTION_BASE_URL] == DEFAULT_BASE_URL


@pytest.mark.phase3
async def test_options_flow_updates_base_url(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            OPTION_PLATFORMS: list(PLATFORM_FEED_PATHS.keys()),
            OPTION_BASE_URL: DEFAULT_BASE_URL,
        },
        unique_id="lootscraper_feed",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.free_games.config_flow.fetch_feed_data",
        return_value=([], {}),
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                OPTION_PLATFORMS: ["steam_game"],
                OPTION_BASE_URL: "https://self-hosted.example.com",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[OPTION_BASE_URL] == "https://self-hosted.example.com"
