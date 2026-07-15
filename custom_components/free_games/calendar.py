"""Calendar entity showing offer expiry windows for the Free Games integration."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import LootScraperDataUpdateCoordinator
from .entity import make_device_info

_LOGGER = logging.getLogger(__package__)


def _parse_date(value: str) -> date | None:
    """Parse a YYYY-MM-DD or ISO-8601 datetime string's date component."""
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _offer_to_event(offer: dict[str, Any]) -> CalendarEvent | None:
    """Convert an offer dict into a CalendarEvent, or None if it can't be represented.

    Skips offers with no usable end date (offer_to), or where the resulting
    start would not be strictly before the end.
    """
    end_date = _parse_date(offer.get("offer_to", ""))
    if end_date is None:
        return None

    start_date = _parse_date(offer.get("offer_from", ""))
    if start_date is None:
        start_date = _parse_date(offer.get("published", ""))
    if start_date is None:
        return None

    # CalendarEvent end is exclusive; the feed's offer_to is inclusive.
    end_date = end_date + timedelta(days=1)

    if start_date >= end_date:
        return None

    return CalendarEvent(
        start=start_date,
        end=end_date,
        summary=offer.get("title", ""),
        description=offer.get("description", ""),
        uid=offer.get("id", ""),
    )


class FreeGamesCalendar(
    CoordinatorEntity[LootScraperDataUpdateCoordinator], CalendarEntity
):
    """Calendar entity showing offer expiry windows across all selected platforms."""

    _attr_has_entity_name = True
    _attr_translation_key = "free_games"

    def __init__(self, coordinator: LootScraperDataUpdateCoordinator) -> None:
        """Initialise the calendar entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_calendar"
        self._attr_device_info = make_device_info()

    def _all_events(self) -> list[CalendarEvent]:
        """Build every representable CalendarEvent from current coordinator data."""
        data = self.coordinator.data
        if not isinstance(data, dict):
            return []
        events = (_offer_to_event(offer) for offer in data.get("offers", []))
        return [event for event in events if event is not None]

    @property
    def event(self) -> CalendarEvent | None:
        """Return the most relevant event: soonest-ending if active, else soonest-upcoming."""
        now = dt_util.now()
        active: list[CalendarEvent] = []
        upcoming: list[CalendarEvent] = []
        for candidate in self._all_events():
            if candidate.start_datetime_local <= now < candidate.end_datetime_local:
                active.append(candidate)
            elif candidate.start_datetime_local > now:
                upcoming.append(candidate)

        if active:
            return min(active, key=lambda e: e.end_datetime_local)
        if upcoming:
            return min(upcoming, key=lambda e: e.start_datetime_local)
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return events overlapping the requested [start_date, end_date) window."""
        return [
            candidate
            for candidate in self._all_events()
            if candidate.start_datetime_local < end_date
            and candidate.end_datetime_local > start_date
        ]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar entity from a config entry."""
    coordinator: LootScraperDataUpdateCoordinator = config_entry.runtime_data
    async_add_entities([FreeGamesCalendar(coordinator)])
