"""Tests for event.py — per-platform new-offer event entity."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.free_games.const import (
    DEFAULT_BASE_URL,
    DOMAIN,
    OPTION_BASE_URL,
    OPTION_PLATFORMS,
    OPTION_SCAN_INTERVAL_MINUTES,
)
from custom_components.free_games.event import PlatformNewOfferEvent, async_setup_entry


def _make_offer(offer_id: str, platform_key: str) -> dict:
    return {
        "id": offer_id,
        "title": f"Game {offer_id}",
        "game_name": f"Game {offer_id}",
        "store": "Steam",
        "claim_url": f"https://example.com/{offer_id}",
        "offer_to": "2026-06-30",
        "platform_key": platform_key,
    }


def _make_coordinator(new_offers: list[dict]) -> MagicMock:
    coordinator = MagicMock()
    coordinator.data = {"new_offers": new_offers}
    coordinator.last_update_success = True
    return coordinator


@pytest.mark.regression
def test_platform_new_offer_event_shares_device_with_sensors() -> None:
    from custom_components.free_games.entity import make_device_info

    entity = PlatformNewOfferEvent(_make_coordinator([]), "steam_game")
    assert entity._attr_device_info == make_device_info()


@pytest.mark.regression
async def test_only_selected_platforms_get_event_entities() -> None:
    coordinator = _make_coordinator([])
    entry = MagicMock()
    entry.runtime_data = coordinator
    entry.options = {OPTION_PLATFORMS: ["steam_game", "epic_game"]}

    added: list = []
    async_add = MagicMock(side_effect=lambda entities: added.extend(entities))

    await async_setup_entry(MagicMock(), entry, async_add)

    assert len(added) == 2
    platform_keys = {e._platform_key for e in added}
    assert platform_keys == {"steam_game", "epic_game"}


@pytest.mark.regression
async def test_new_offer_fires_once_per_offer_on_matching_platform(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            OPTION_PLATFORMS: ["steam_game", "epic_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        },
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
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    coordinator = entry.runtime_data

    events = async_capture_events(hass, "state_changed")

    offers = [
        _make_offer("1", "steam_game"),
        _make_offer("2", "steam_game"),
        _make_offer("3", "epic_game"),
    ]
    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        return_value=(offers, {}),
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    steam_events = [
        e
        for e in events
        if e.data.get("entity_id") == "event.free_games_steam_games_new_offer"
    ]
    epic_events = [
        e
        for e in events
        if e.data.get("entity_id") == "event.free_games_epic_games_new_offer"
    ]

    assert len(steam_events) == 2
    assert len(epic_events) == 1
    fired_ids = {e.data["new_state"].attributes["id"] for e in steam_events}
    assert fired_ids == {"1", "2"}
    assert epic_events[0].data["new_state"].attributes["id"] == "3"
    assert epic_events[0].data["new_state"].attributes["claim_url"] == (
        "https://example.com/3"
    )


@pytest.mark.regression
async def test_no_new_offers_produces_no_state_changed_event(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            OPTION_PLATFORMS: ["steam_game"],
            OPTION_BASE_URL: DEFAULT_BASE_URL,
            OPTION_SCAN_INTERVAL_MINUTES: 60,
        },
        unique_id="lootscraper_feed",
    )
    entry.add_to_hass(hass)

    offer = _make_offer("1", "steam_game")

    with (
        patch(
            "custom_components.free_games.async_get_clientsession",
            return_value=AsyncMock(),
        ),
        patch(
            "custom_components.free_games.coordinator.fetch_feed_data",
            return_value=([offer], {}),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    coordinator = entry.runtime_data
    events = async_capture_events(hass, "state_changed")

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        return_value=([offer], {}),
    ):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    steam_events = [
        e
        for e in events
        if e.data.get("entity_id") == "event.free_games_steam_games_new_offer"
    ]
    assert steam_events == []
