"""Tests for calendar.py — offer-to-event conversion and entity behaviour."""

from __future__ import annotations

from datetime import date

import pytest

from custom_components.free_games.calendar import _offer_to_event


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
