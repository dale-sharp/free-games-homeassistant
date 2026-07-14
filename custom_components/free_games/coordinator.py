"""DataUpdateCoordinator for polling LootScraper Atom XML feeds."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import fetch_feed_data
from .const import (
    CONSOLIDATED_FEED_PATH,
    DEFAULT_BASE_URL,
    DOMAIN,
    ISSUE_PERSISTENT_FETCH_FAILURE,
    PERSISTENT_FETCH_FAILURE_THRESHOLD,
    PLATFORM_FEED_PATHS,
    build_feed_url,
)

_LOGGER = logging.getLogger(__package__)


class LootScraperDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching LootScraper feed data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        platforms: set[str],
        base_url: str,
        scan_interval_minutes: int,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="free_games",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )
        self._session = session
        self._platforms = platforms
        self._base_url = base_url
        self.consecutive_failure_count: int = 0

    async def _fetch_per_platform(
        self, platforms: set[str]
    ) -> tuple[dict[str, list[dict]], bool]:
        """Fetch each of the given platforms' individual feeds in parallel."""

        async def _fetch_platform(key: str, url: str) -> tuple[str, list[dict], bool]:
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
                _fetch_platform(
                    key, build_feed_url(self._base_url, PLATFORM_FEED_PATHS[key])
                )
                for key in platforms
                if key in PLATFORM_FEED_PATHS
            ]
        )

        platform_offers: dict[str, list[dict]] = {
            key: offers for key, offers, _ in results
        }
        any_succeeded = any(ok for _, _, ok in results)
        return platform_offers, any_succeeded

    async def _fetch_consolidated(
        self, platforms: set[str]
    ) -> tuple[dict[str, list[dict]], bool]:
        """Fetch the consolidated feed once and bucket entries by platform_key.

        The returned bool reflects whether the fetch itself succeeded, not
        whether any offers matched the given platforms.
        """
        consolidated_url = build_feed_url(self._base_url, CONSOLIDATED_FEED_PATH)
        try:
            offers, _ = await fetch_feed_data(self._session, consolidated_url)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Failed to fetch consolidated feed %s", consolidated_url)
            return {}, False

        platform_offers: dict[str, list[dict]] = {key: [] for key in platforms}
        for offer in offers:
            key = offer.get("platform_key", "")
            if key in platform_offers:
                platform_offers[key].append(offer)

        return platform_offers, True

    async def _async_update_data(self) -> dict:
        """Fetch data from the selected LootScraper Atom XML feeds."""
        try:
            if len(self._platforms) > 1:
                platform_offers, any_succeeded = await self._fetch_consolidated(
                    self._platforms
                )
                if not any_succeeded:
                    _LOGGER.warning(
                        "Consolidated feed fetch failed, falling back to "
                        "per-platform feeds"
                    )
                    platform_offers, any_succeeded = await self._fetch_per_platform(
                        self._platforms
                    )
            else:
                platform_offers, any_succeeded = await self._fetch_per_platform(
                    self._platforms
                )

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

            if self.consecutive_failure_count > 0:
                ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PERSISTENT_FETCH_FAILURE)
                self.consecutive_failure_count = 0

            return {
                "offers": all_offers,
                "metadata": metadata,
                "platform_offers": platform_offers,
            }

        except Exception as err:
            self.consecutive_failure_count += 1
            if self.consecutive_failure_count >= PERSISTENT_FETCH_FAILURE_THRESHOLD:
                translation_key = (
                    "persistent_fetch_failure_default_url"
                    if self._base_url == DEFAULT_BASE_URL
                    else "persistent_fetch_failure_custom_url"
                )
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    ISSUE_PERSISTENT_FETCH_FAILURE,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=translation_key,
                )
            _LOGGER.exception("Error fetching LootScraper feed data")
            raise UpdateFailed(f"Error fetching feed: {err}") from err
