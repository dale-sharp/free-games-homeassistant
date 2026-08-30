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


def _combine_feed_metadata(feed_metadatas: list[dict]) -> dict:
    """Combine metadata from one or more successful feed fetches.

    A single-feed fetch (the consolidated path) passes its real metadata
    through unchanged. Multiple per-platform fetches have no single feed
    title/updated timestamp, so this takes the first non-empty title and
    the latest (lexicographically greatest ISO 8601) updated timestamp.
    """
    titles = [
        metadata["feed_title"]
        for metadata in feed_metadatas
        if metadata.get("feed_title")
    ]
    updates = [
        metadata["feed_updated"]
        for metadata in feed_metadatas
        if metadata.get("feed_updated")
    ]
    return {
        "feed_title": titles[0] if titles else "LootScraper",
        "feed_updated": max(updates) if updates else "",
    }


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
        self._known_offer_ids: set[str] | None = None

    async def _fetch_per_platform(
        self, platforms: set[str]
    ) -> tuple[dict[str, list[dict]], bool, set[str], list[dict]]:
        """Fetch each of the given platforms' individual feeds in parallel."""

        async def _fetch_platform(
            key: str, url: str
        ) -> tuple[str, list[dict], bool, dict]:
            try:
                offers, metadata = await fetch_feed_data(self._session, url)
                for offer in offers:
                    offer["platform_key"] = key
                return key, offers, True, metadata
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Failed to fetch platform feed %s", url)
                return key, [], False, {}

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
            key: offers for key, offers, _, _ in results
        }
        failed_platforms = {key for key, _, ok, _ in results if not ok}
        any_succeeded = any(ok for _, _, ok, _ in results)
        feed_metadatas = [metadata for _, _, ok, metadata in results if ok]
        return platform_offers, any_succeeded, failed_platforms, feed_metadatas

    async def _fetch_consolidated(
        self, platforms: set[str]
    ) -> tuple[dict[str, list[dict]], bool, set[str], list[dict]]:
        """Fetch the consolidated feed once and bucket entries by platform_key.

        The returned bool reflects whether the fetch itself succeeded, not
        whether any offers matched the given platforms.
        """
        consolidated_url = build_feed_url(self._base_url, CONSOLIDATED_FEED_PATH)
        try:
            offers, metadata = await fetch_feed_data(self._session, consolidated_url)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Failed to fetch consolidated feed %s", consolidated_url)
            return {}, False, set(), []

        platform_offers: dict[str, list[dict]] = {key: [] for key in platforms}
        for offer in offers:
            key = offer.get("platform_key", "")
            if key in platform_offers:
                platform_offers[key].append(offer)

        return platform_offers, True, set(), [metadata]

    async def _async_update_data(self) -> dict:
        """Fetch data from the selected LootScraper Atom XML feeds."""
        try:
            if len(self._platforms) > 1:
                (
                    platform_offers,
                    any_succeeded,
                    failed_platforms,
                    feed_metadatas,
                ) = await self._fetch_consolidated(self._platforms)
                if not any_succeeded:
                    _LOGGER.debug(
                        "Consolidated feed fetch failed, falling back to "
                        "per-platform feeds"
                    )
                    (
                        platform_offers,
                        any_succeeded,
                        failed_platforms,
                        feed_metadatas,
                    ) = await self._fetch_per_platform(self._platforms)
            else:
                (
                    platform_offers,
                    any_succeeded,
                    failed_platforms,
                    feed_metadatas,
                ) = await self._fetch_per_platform(self._platforms)

            if self._platforms and not any_succeeded:
                raise UpdateFailed("All platform feeds failed to fetch")

            all_offers = [
                offer for offers in platform_offers.values() for offer in offers
            ]

            current_ids = {offer["id"] for offer in all_offers}
            if self._known_offer_ids is None:
                new_offers: list[dict] = []
            else:
                new_ids = current_ids - self._known_offer_ids
                new_offers = [offer for offer in all_offers if offer["id"] in new_ids]
            self._known_offer_ids = current_ids

            metadata = _combine_feed_metadata(feed_metadatas)
            metadata["total_offer_count"] = len(all_offers)

            if self.consecutive_failure_count > 0:
                ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PERSISTENT_FETCH_FAILURE)
                self.consecutive_failure_count = 0

            return {
                "offers": all_offers,
                "metadata": metadata,
                "platform_offers": platform_offers,
                "failed_platforms": failed_platforms,
                "new_offers": new_offers,
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
            _LOGGER.debug("Error fetching LootScraper feed data", exc_info=True)
            raise UpdateFailed(f"Error fetching feed: {err}") from err
