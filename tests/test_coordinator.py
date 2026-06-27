"""Tests for LootScraperDataUpdateCoordinator efficiency behaviour — all phase2."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.free_games.const import PLATFORM_FEEDS
from custom_components.free_games.coordinator import LootScraperDataUpdateCoordinator


def _make_offer(offer_id: str) -> dict:
    return {
        "id": offer_id,
        "title": f"Game {offer_id}",
        "platform": "Steam",
        "type": "Game",
        "claim_url": f"https://example.com/{offer_id}",
        "published": "2026-06-20T00:00:00Z",
    }


@pytest.mark.phase2
async def test_only_selected_platforms_fetched(hass) -> None:
    selected = {"steam_game", "epic_game", "gog_game"}
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

    called_urls = {c.args[1] for c in mock_fn.call_args_list}
    expected_urls = {PLATFORM_FEEDS[k] for k in selected}
    assert called_urls == expected_urls


@pytest.mark.phase2
async def test_total_derived_from_platform_data(hass) -> None:
    selected = {"steam_game", "epic_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )

    async def mock_fetch(session, url):  # noqa: ANN001
        return [_make_offer(f"{url}-1"), _make_offer(f"{url}-2")], {}

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ) as mock_fn:
        data = await coordinator._async_update_data()

    # 2 platforms × 2 offers = 4 total; exactly 2 fetches (no merged feed)
    assert mock_fn.call_count == len(selected)
    assert len(data["offers"]) == 4


@pytest.mark.phase2
async def test_failed_platform_returns_empty_list(hass) -> None:
    selected = {"steam_game", "epic_game", "gog_game"}
    session = AsyncMock()
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected
    )
    epic_url = PLATFORM_FEEDS["epic_game"]

    async def mock_fetch(session, url):  # noqa: ANN001
        if url == epic_url:
            raise ValueError("Network error")
        return [_make_offer("1")], {}

    with patch(
        "custom_components.free_games.coordinator.fetch_feed_data",
        side_effect=mock_fetch,
    ):
        data = await coordinator._async_update_data()

    # epic failed → empty; steam + gog each have 1 → 2 total
    assert len(data["offers"]) == 2
    assert data["platform_offers"]["epic_game"] == []
    assert len(data["platform_offers"]["steam_game"]) == 1
