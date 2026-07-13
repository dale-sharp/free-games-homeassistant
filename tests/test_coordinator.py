"""Tests for LootScraperDataUpdateCoordinator fetch-strategy behaviour."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.free_games.const import CONSOLIDATED_FEED_URL, PLATFORM_FEEDS
from custom_components.free_games.coordinator import LootScraperDataUpdateCoordinator


def _make_offer(offer_id: str, platform_key: str = "") -> dict:
    return {
        "id": offer_id,
        "title": f"Game {offer_id}",
        "store": "Steam",
        "platform": "PC",
        "type": "Game",
        "claim_url": f"https://example.com/{offer_id}",
        "published": "2026-06-20T00:00:00Z",
        "platform_key": platform_key,
    }


@pytest.mark.phase2
async def test_single_platform_fetches_individual_feed_only(hass) -> None:
    selected = {"steam_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )

    async def mock_fetch(session, url):  # noqa: ANN001
        return [_make_offer("1")], {}

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ) as mock_fn:
        await coordinator._async_update_data()

    mock_fn.assert_called_once_with(session, PLATFORM_FEEDS["steam_game"])


@pytest.mark.phase2
async def test_multiple_platforms_fetch_consolidated_feed_only(hass) -> None:
    selected = {"steam_game", "epic_game", "gog_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )

    consolidated_offers = [
        _make_offer("1", platform_key="steam_game"),
        _make_offer("2", platform_key="epic_game"),
        _make_offer("3", platform_key="gog_game"),
        _make_offer("4", platform_key="humble_game"),  # not selected, must be excluded
        _make_offer("5", platform_key=""),  # unmapped, must be excluded
    ]

    async def mock_fetch(session, url):  # noqa: ANN001
        assert url == CONSOLIDATED_FEED_URL
        return consolidated_offers, {}

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ) as mock_fn:
        data = await coordinator._async_update_data()

    mock_fn.assert_called_once_with(session, CONSOLIDATED_FEED_URL)
    assert len(data["offers"]) == 3
    assert len(data["platform_offers"]["steam_game"]) == 1
    assert len(data["platform_offers"]["epic_game"]) == 1
    assert len(data["platform_offers"]["gog_game"]) == 1
    assert "humble_game" not in data["platform_offers"]


@pytest.mark.phase2
async def test_consolidated_failure_falls_back_to_per_platform(hass) -> None:
    selected = {"steam_game", "epic_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )
    steam_url = PLATFORM_FEEDS["steam_game"]
    epic_url = PLATFORM_FEEDS["epic_game"]

    async def mock_fetch(session, url):  # noqa: ANN001
        if url == CONSOLIDATED_FEED_URL:
            raise ValueError("Consolidated feed unavailable")
        if url == steam_url:
            return [_make_offer("1")], {}
        if url == epic_url:
            return [_make_offer("2")], {}
        raise AssertionError(f"Unexpected URL fetched: {url}")

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ) as mock_fn:
        data = await coordinator._async_update_data()

    called_urls = [c.args[1] for c in mock_fn.call_args_list]
    assert called_urls[0] == CONSOLIDATED_FEED_URL
    assert set(called_urls[1:]) == {steam_url, epic_url}
    assert len(data["offers"]) == 2
    assert len(data["platform_offers"]["steam_game"]) == 1
    assert len(data["platform_offers"]["epic_game"]) == 1


@pytest.mark.phase2
async def test_partial_fallback_failure_leaves_that_platform_empty(hass) -> None:
    selected = {"steam_game", "epic_game", "gog_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )
    epic_url = PLATFORM_FEEDS["epic_game"]

    async def mock_fetch(session, url):  # noqa: ANN001
        if url == CONSOLIDATED_FEED_URL:
            raise ValueError("Consolidated feed unavailable")
        if url == epic_url:
            raise ValueError("Network error")
        return [_make_offer("1")], {}

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ):
        data = await coordinator._async_update_data()

    assert data["platform_offers"]["epic_game"] == []
    assert len(data["platform_offers"]["steam_game"]) == 1
    assert len(data["platform_offers"]["gog_game"]) == 1
    assert len(data["offers"]) == 2


@pytest.mark.phase2
async def test_total_failure_raises_update_failed(hass) -> None:
    selected = {"steam_game", "epic_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )

    async def mock_fetch(session, url):  # noqa: ANN001
        raise ValueError("Network error")

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
