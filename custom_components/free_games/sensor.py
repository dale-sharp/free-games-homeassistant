"""Home Assistant sensors for LootScraper free game offers."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OPTION_PLATFORMS, PLATFORM_FEED_PATHS
from .coordinator import LootScraperDataUpdateCoordinator
from .entity import make_device_info

_LOGGER = logging.getLogger(__package__)

PARALLEL_UPDATES = 0

_UNRECORDED_OFFER_ATTRS: Final = frozenset({"offers"})


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: LootScraperDataUpdateCoordinator = config_entry.runtime_data

    entities: list[SensorEntity] = [FreeGamesCountSensor(coordinator)]

    selected_platforms: set[str] = set(
        config_entry.options.get(OPTION_PLATFORMS, list(PLATFORM_FEED_PATHS.keys()))
    )
    for platform_key in sorted(selected_platforms):
        if platform_key in PLATFORM_FEED_PATHS:
            entities.append(PerPlatformFreeGamesSensor(coordinator, platform_key))

    async_add_entities(entities)


class FreeGamesCountSensor(
    CoordinatorEntity[LootScraperDataUpdateCoordinator], SensorEntity
):
    """Displays total count of active free game offers across all platforms."""

    _attr_has_entity_name = True
    _attr_translation_key = "active_free_games"
    _attr_native_unit_of_measurement = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = _UNRECORDED_OFFER_ATTRS

    def __init__(self, coordinator: LootScraperDataUpdateCoordinator) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_active_count"
        self._attr_device_info = make_device_info()

    @property
    def native_value(self) -> int:
        """Return the total number of active offers."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return 0
        return len(data.get("offers", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return feed metadata and offer list as extra attributes."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return {}
        metadata: dict[str, Any] = data.get("metadata", {})
        offers: list[dict[str, Any]] = data.get("offers", [])
        return {
            "feed_title": metadata.get("feed_title", ""),
            "feed_updated": metadata.get("feed_updated", ""),
            "total_offer_count": metadata.get("total_offer_count", 0),
            "offers": offers[:20],
        }


class PerPlatformFreeGamesSensor(
    CoordinatorEntity[LootScraperDataUpdateCoordinator], SensorEntity
):
    """Displays count of active free game offers for a specific platform."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = _UNRECORDED_OFFER_ATTRS

    def __init__(
        self,
        coordinator: LootScraperDataUpdateCoordinator,
        platform_key: str,
    ) -> None:
        """Initialise the per-platform sensor."""
        super().__init__(coordinator)
        self._platform_key = platform_key
        self._attr_unique_id = f"{DOMAIN}_active_count_{platform_key}"
        self._attr_translation_key = platform_key
        self._attr_device_info = make_device_info()

    @property
    def available(self) -> bool:
        """Return False if the coordinator is down, or this platform's fetch failed."""
        if not super().available:
            return False
        data = self.coordinator.data
        if not isinstance(data, dict):
            return True
        failed_platforms: set[str] = data.get("failed_platforms", set())
        return self._platform_key not in failed_platforms

    def _get_platform_offers(self) -> list[dict[str, Any]]:
        """Return offers for this platform from the coordinator."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return []
        platform_offers: dict[str, list[dict[str, Any]]] = data.get(
            "platform_offers", {}
        )
        return platform_offers.get(self._platform_key, [])

    @property
    def native_value(self) -> int:
        """Return the count of active offers for this platform."""
        return len(self._get_platform_offers())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the list of current offers for this platform as attributes."""
        return {"offers": self._get_platform_offers()[:20]}
