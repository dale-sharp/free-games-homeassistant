"""Event entities firing once per newly-detected offer, for the Free Games integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OPTION_PLATFORMS, PLATFORM_FEED_PATHS
from .coordinator import LootScraperDataUpdateCoordinator
from .entity import make_device_info

_LOGGER = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up new-offer event entities from a config entry."""
    coordinator: LootScraperDataUpdateCoordinator = config_entry.runtime_data

    selected_platforms: set[str] = set(
        config_entry.options.get(OPTION_PLATFORMS, list(PLATFORM_FEED_PATHS.keys()))
    )
    entities = [
        PlatformNewOfferEvent(coordinator, platform_key)
        for platform_key in sorted(selected_platforms)
        if platform_key in PLATFORM_FEED_PATHS
    ]
    async_add_entities(entities)


class PlatformNewOfferEvent(
    CoordinatorEntity[LootScraperDataUpdateCoordinator], EventEntity
):
    """Fires a new_offer event for each newly-detected offer on one platform."""

    _attr_has_entity_name = True
    _attr_event_types = ["new_offer"]

    def __init__(
        self,
        coordinator: LootScraperDataUpdateCoordinator,
        platform_key: str,
    ) -> None:
        """Initialise the per-platform new-offer event entity."""
        super().__init__(coordinator)
        self._platform_key = platform_key
        self._attr_unique_id = f"{DOMAIN}_new_offer_{platform_key}"
        self._attr_translation_key = platform_key
        self._attr_device_info = make_device_info()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire a new_offer event for each newly-detected offer on this platform."""
        data = self.coordinator.data
        new_offers: list[dict[str, Any]] = (
            data.get("new_offers", []) if isinstance(data, dict) else []
        )
        fired = False
        for offer in new_offers:
            if offer.get("platform_key") == self._platform_key:
                self._trigger_event("new_offer", offer)
                self.async_write_ha_state()
                fired = True
        if not fired:
            self.async_write_ha_state()
