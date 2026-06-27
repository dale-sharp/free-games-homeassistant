"""Home Assistant custom component integration for LootScraper free games feed."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import OPTION_PLATFORMS, PLATFORM_FEEDS
from .coordinator import LootScraperDataUpdateCoordinator

_LOGGER = logging.getLogger(__package__)

PLATFORMS = [Platform.SENSOR]

type FreeGamesConfigEntry = ConfigEntry[LootScraperDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FreeGamesConfigEntry) -> bool:
    """Set up Free Games from a config entry."""
    session = async_get_clientsession(hass)
    selected_platforms = set(
        entry.options.get(OPTION_PLATFORMS, list(PLATFORM_FEEDS.keys()))
    )
    coordinator = LootScraperDataUpdateCoordinator(
        hass=hass, session=session, platforms=selected_platforms
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FreeGamesConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
