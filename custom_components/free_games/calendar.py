"""Calendar entity showing offer expiry windows for the Free Games integration."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEvent

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
