"""DataUpdateCoordinator for polling LootScraper Atom XML feeds."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import FEED_URL_MERGED, SCAN_INTERVAL_SECONDS
from .api import fetch_feed_data

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
        """Fetch data from LootScraper Atom XML feed."""
        try:
            offers, metadata = await fetch_feed_data(self._session, FEED_URL_MERGED)

            # Deduplicate by offer ID (some games appear in multiple feeds)
            seen_ids: set[str] = set()
            unique_offers: list[dict] = []
            for offer in offers:
                oid = offer.get("id", "") or ""
                if oid not in seen_ids:
                    seen_ids.add(oid)
                    unique_offers.append(offer)

            metadata["unique_offer_count"] = len(unique_offers)
            return {"offers": unique_offers, "metadata": metadata}

        except Exception as err:
            raise UpdateFailed(f"Error fetching feed: {err}") from err
