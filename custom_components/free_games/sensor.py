"""Home Assistant sensors for LootScraper free game offers."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, PLATFORM_FEEDS
from .coordinator import LootScraperDataUpdateCoordinator

_LOGGER = logging.getLogger(__package__)

# Using a coordinator centralises all data updates - no per-entity polling needed
PARALLEL_UPDATES = 0


def _make_device_info() -> DeviceInfo:
    """Return a shared DeviceInfo for all Free Games entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, "lootscraper_feed")},
        name="Free Games",
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: LootScraperDataUpdateCoordinator = config_entry.runtime_data

    entities: list[SensorEntity] = [FreeGamesCountSensor(coordinator)]

    # Per-platform sensors based on user options (default: all platforms)
    selected_platforms: set[str] = set(
        config_entry.options.get("platforms", list(PLATFORM_FEEDS.keys()))
    )
    for platform_key in sorted(selected_platforms):
        if platform_key in PLATFORM_FEEDS:
            entities.append(PerPlatformFreeGamesSensor(coordinator, platform_key))

    async_add_entities(entities)


class FreeGamesCountSensor(
    CoordinatorEntity[LootScraperDataUpdateCoordinator], SensorEntity
):
    """Displays total count of active free game offers across all platforms."""

    _attr_has_entity_name = True
    _attr_translation_key = "active_free_games"
    _attr_native_unit_of_measurement = "games"
    _attr_icon = "mdi:gamepad-variant"

    def __init__(self, coordinator: LootScraperDataUpdateCoordinator) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_active_count"
        self._attr_device_info = _make_device_info()

    @property
    def native_value(self) -> int:
        """Return the total number of active offers."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return 0
        return len(data.get("offers", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return feed metadata as extra attributes."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return {}
        metadata: dict[str, Any] = data.get("metadata", {})
        return {
            "feed_title": metadata.get("feed_title", ""),
            "feed_updated": metadata.get("feed_updated", ""),
            "unique_offer_count": metadata.get("unique_offer_count", 0),
        }


class PerPlatformFreeGamesSensor(
    CoordinatorEntity[LootScraperDataUpdateCoordinator], SensorEntity
):
    """Displays count of active free game offers for a specific platform."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "games"
    _attr_icon = "mdi:gamepad-variant-outline"

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
        self._attr_device_info = _make_device_info()

    @property
    def native_value(self) -> int:
        """Return the count of active offers for this platform."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return 0
        offers: list[dict[str, Any]] = data.get("offers", [])
        platform_lower = self._platform_key.replace("_", " ").lower()
        return sum(
            1
            for o in offers
            if o.get("platform", "").lower() == platform_lower
            or o.get("platform", "") == self._platform_key
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the list of current offers for this platform as attributes."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return {}
        offers: list[dict[str, Any]] = data.get("offers", [])
        platform_lower = self._platform_key.replace("_", " ").lower()
        platform_offers = [
            o
            for o in offers
            if o.get("platform", "").lower() == platform_lower
            or o.get("platform", "") == self._platform_key
        ]
        # Cap at 20 to stay comfortably under the HA state attribute size limit
        return {"offers": platform_offers[:20]}
