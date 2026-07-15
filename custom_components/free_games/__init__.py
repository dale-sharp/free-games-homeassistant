"""Home Assistant custom component integration for LootScraper free games feed."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    OPTION_BASE_URL,
    OPTION_PLATFORMS,
    OPTION_SCAN_INTERVAL_MINUTES,
    PLATFORM_FEED_PATHS,
)
from .coordinator import LootScraperDataUpdateCoordinator

_LOGGER = logging.getLogger(__package__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]

type FreeGamesConfigEntry = ConfigEntry[LootScraperDataUpdateCoordinator]


async def _async_update_options(
    hass: HomeAssistant, entry: FreeGamesConfigEntry
) -> None:
    """Reload the config entry so updated options take effect immediately."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: FreeGamesConfigEntry) -> bool:
    """Set up Free Games from a config entry."""
    session = async_get_clientsession(hass)
    selected_platforms = set(
        entry.options.get(OPTION_PLATFORMS, list(PLATFORM_FEED_PATHS.keys()))
    )
    base_url = entry.options.get(OPTION_BASE_URL, DEFAULT_BASE_URL)
    scan_interval_minutes = entry.options.get(
        OPTION_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES
    )
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass,
        session=session,
        platforms=selected_platforms,
        base_url=base_url,
        scan_interval_minutes=scan_interval_minutes,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FreeGamesConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
