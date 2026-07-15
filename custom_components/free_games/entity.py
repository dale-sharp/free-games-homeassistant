"""Shared entity helpers for the Free Games integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN, MANUFACTURER


def make_device_info() -> DeviceInfo:
    """Return a shared DeviceInfo for all Free Games entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, "lootscraper_feed")},
        name="Free Games",
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
    )
