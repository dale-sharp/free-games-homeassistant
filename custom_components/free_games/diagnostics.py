"""Diagnostics support for the Free Games integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant

from . import FreeGamesConfigEntry
from .const import (
    DEFAULT_BASE_URL,
    OPTION_BASE_URL,
    OPTION_PLATFORMS,
    OPTION_SCAN_INTERVAL_MINUTES,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FreeGamesConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    base_url = entry.options.get(OPTION_BASE_URL, DEFAULT_BASE_URL)

    return {
        "options": {
            OPTION_PLATFORMS: entry.options.get(OPTION_PLATFORMS, []),
            OPTION_BASE_URL: base_url if base_url == DEFAULT_BASE_URL else REDACTED,
            OPTION_SCAN_INTERVAL_MINUTES: entry.options.get(
                OPTION_SCAN_INTERVAL_MINUTES
            ),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": str(coordinator.last_exception)
            if coordinator.last_exception
            else None,
            "offer_counts_by_platform": {
                key: len(offers)
                for key, offers in coordinator.data.get("platform_offers", {}).items()
            },
            # Every GameOffer field is public promotional metadata from the feed
            # (title, store, URLs, description, genres, price, dates) - nothing
            # personally identifiable, unlike e.g. a fuel-price integration's
            # station coordinates. Reviewed field-by-field; no redaction needed.
            "sample_offers": coordinator.data.get("offers", [])[:10],
        },
    }
