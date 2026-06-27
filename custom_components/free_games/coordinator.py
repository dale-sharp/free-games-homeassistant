"""DataUpdateCoordinator for polling LootScraper Atom XML feeds."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import fetch_feed_data
from .const import PLATFORM_FEEDS, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__package__)


class LootScraperDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching LootScraper feed data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        platforms: set[str],
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="free_games",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self._session = session
        self._platforms = platforms

    async def _async_update_data(self) -> dict:
        """Fetch data from the selected LootScraper Atom XML feeds."""
        try:

            async def _fetch_platform(
                key: str, url: str
            ) -> tuple[str, list[dict], bool]:
                try:
                    offers, _ = await fetch_feed_data(self._session, url)
                    for offer in offers:
                        offer["platform_key"] = key
                    return key, offers, True
                except Exception:  # noqa: BLE001
                    _LOGGER.debug("Failed to fetch platform feed %s", url)
                    return key, [], False

            results = await asyncio.gather(
                *[
                    _fetch_platform(key, PLATFORM_FEEDS[key])
                    for key in self._platforms
                    if key in PLATFORM_FEEDS
                ]
            )

            platform_offers: dict[str, list[dict]] = {
                key: offers for key, offers, _ in results
            }
            any_succeeded = any(ok for _, _, ok in results)

            if self._platforms and not any_succeeded:
                raise UpdateFailed("All platform feeds failed to fetch")
            all_offers = [
                offer for offers in platform_offers.values() for offer in offers
            ]

            metadata: dict = {
                "feed_title": "LootScraper",
                "feed_updated": "",
                "total_offer_count": len(all_offers),
            }

            return {
                "offers": all_offers,
                "metadata": metadata,
                "platform_offers": platform_offers,
            }

        except Exception as err:
            _LOGGER.exception("Error fetching LootScraper feed data")
            raise UpdateFailed(f"Error fetching feed: {err}") from err
