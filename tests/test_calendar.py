"""Tests for calendar.py — offer-to-event conversion and entity behaviour."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from custom_components.free_games.calendar import FreeGamesCalendar, _offer_to_event


def _make_offer(**overrides: object) -> dict:
    base = {
        "id": "offer-1",
        "title": "Steam (Game, PC) - Tell Me Why",
        "description": "A narrative adventure game.",
        "offer_from": "2026-06-20",
        "offer_to": "2026-06-30",
        "published": "2026-06-19T12:00:00+00:00",
    }
    base.update(overrides)
    return base


@pytest.mark.regression
def test_offer_to_event_normal_case_has_exclusive_end_date() -> None:
    event = _offer_to_event(_make_offer())
    assert event is not None
    assert event.summary == "Steam (Game, PC) - Tell Me Why"
    assert event.description == "A narrative adventure game."
    assert event.uid == "offer-1"
    assert event.start == date(2026, 6, 20)
    # offer_to is inclusive in the feed; CalendarEvent end is exclusive.
    assert event.end == date(2026, 7, 1)


@pytest.mark.regression
def test_offer_to_event_skipped_when_offer_to_missing() -> None:
    assert _offer_to_event(_make_offer(offer_to="")) is None


@pytest.mark.regression
def test_offer_to_event_falls_back_to_published_when_offer_from_missing() -> None:
    event = _offer_to_event(_make_offer(offer_from=""))
    assert event is not None
    assert event.start == date(2026, 6, 19)


@pytest.mark.regression
def test_offer_to_event_skipped_when_offer_from_and_published_unparseable() -> None:
    assert (
        _offer_to_event(_make_offer(offer_from="", published="not-a-date")) is None
    )


@pytest.mark.regression
def test_offer_to_event_skipped_when_offer_to_unparseable() -> None:
    assert _offer_to_event(_make_offer(offer_to="not-a-date")) is None


@pytest.mark.regression
def test_offer_to_event_skipped_when_dates_invert() -> None:
    assert (
        _offer_to_event(
            _make_offer(offer_from="2026-06-30", offer_to="2026-06-20")
        )
        is None
    )


def _make_coordinator(offers: list[dict]) -> MagicMock:
    coordinator = MagicMock()
    coordinator.data = {"offers": offers, "metadata": {}, "platform_offers": {}}
    coordinator.last_update_success = True
    return coordinator


@pytest.mark.regression
async def test_calendar_event_property_none_when_no_offers() -> None:
    entity = FreeGamesCalendar(_make_coordinator([]))
    assert entity.event is None


@pytest.mark.regression
async def test_calendar_event_property_returns_soonest_ending_active_offer(
    freezer,
) -> None:
    freezer.move_to("2026-06-25T12:00:00+00:00")
    offers = [
        _make_offer(id="ends-later", offer_from="2026-06-20", offer_to="2026-07-10"),
        _make_offer(id="ends-sooner", offer_from="2026-06-20", offer_to="2026-06-28"),
    ]
    entity = FreeGamesCalendar(_make_coordinator(offers))
    event = entity.event
    assert event is not None
    assert event.uid == "ends-sooner"


@pytest.mark.regression
async def test_calendar_event_property_returns_soonest_upcoming_when_none_active(
    freezer,
) -> None:
    freezer.move_to("2026-06-01T12:00:00+00:00")
    offers = [
        _make_offer(id="starts-later", offer_from="2026-06-20", offer_to="2026-06-30"),
        _make_offer(id="starts-sooner", offer_from="2026-06-10", offer_to="2026-06-15"),
    ]
    entity = FreeGamesCalendar(_make_coordinator(offers))
    event = entity.event
    assert event is not None
    assert event.uid == "starts-sooner"


@pytest.mark.regression
async def test_calendar_event_property_none_when_data_not_ready() -> None:
    coordinator = _make_coordinator([])
    coordinator.data = None
    entity = FreeGamesCalendar(coordinator)
    assert entity.event is None


@pytest.mark.regression
async def test_calendar_async_get_events_returns_overlapping_only(hass) -> None:
    offers = [
        _make_offer(id="in-range", offer_from="2026-06-20", offer_to="2026-06-25"),
        _make_offer(id="out-of-range", offer_from="2026-08-01", offer_to="2026-08-05"),
    ]
    entity = FreeGamesCalendar(_make_coordinator(offers))
    events = await entity.async_get_events(
        hass,
        datetime(2026, 6, 1, tzinfo=UTC),
        datetime(2026, 6, 30, tzinfo=UTC),
    )
    assert {e.uid for e in events} == {"in-range"}


@pytest.mark.regression
async def test_calendar_async_get_events_empty_when_data_not_ready(hass) -> None:
    coordinator = _make_coordinator([])
    coordinator.data = None
    entity = FreeGamesCalendar(coordinator)
    events = await entity.async_get_events(
        hass,
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, tzinfo=UTC),
    )
    assert events == []


@pytest.mark.regression
def test_calendar_shares_device_with_sensors() -> None:
    from custom_components.free_games.entity import make_device_info

    entity = FreeGamesCalendar(_make_coordinator([]))
    assert entity._attr_device_info == make_device_info()
