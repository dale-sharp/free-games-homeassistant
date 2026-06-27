"""DataUpdateCoordinator for polling LootScraper Atom XML feeds."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import fetch_feed_data
from .const import FEED_URL_MERGED, PLATFORM_FEEDS, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__package__)


class LootScraperDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching LootScraper feed data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="free_games",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self._session = session

    async def _async_update_data(self) -> dict:
        """Fetch data from all LootScraper Atom XML feeds."""
        try:
            # Fetch merged feed for total count + metadata
            merged_offers, metadata = await fetch_feed_data(
                self._session, FEED_URL_MERGED
            )

            # Deduplicate merged offers by ID for total count sensor
            seen_ids: set[str] = set()
            unique_offers: list[dict] = []
            for offer in merged_offers:
                oid = offer.get("id", "") or ""
                if oid not in seen_ids:
                    seen_ids.add(oid)
                    unique_offers.append(offer)

            metadata["unique_offer_count"] = len(unique_offers)

            # Fetch each platform feed in parallel, tag offers with platform_key
            async def _fetch_platform(key: str, url: str) -> tuple[str, list[dict]]:
                try:
                    offers, _ = await fetch_feed_data(self._session, url)
                    for offer in offers:
                        offer["platform_key"] = key
                    return key, offers
                except Exception:  # noqa: BLE001
                    _LOGGER.debug("Failed to fetch platform feed %s", url)
                    return key, []

            results = await asyncio.gather(
                *[_fetch_platform(key, url) for key, url in PLATFORM_FEEDS.items()]
            )

            platform_offers: dict[str, list[dict]] = {
                key: offers for key, offers in results
            }

            return {
                "offers": unique_offers,
                "metadata": metadata,
                "platform_offers": platform_offers,
            }

        except Exception as err:
            _LOGGER.exception("Error fetching LootScraper feed data")
            raise UpdateFailed(f"Error fetching feed: {err}") from err
