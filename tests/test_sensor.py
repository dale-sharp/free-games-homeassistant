"""Tests for sensor.py — phase1 (properties) and phase2 (setup filtering)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorStateClass

from custom_components.free_games.const import OPTION_PLATFORMS
from custom_components.free_games.sensor import (
    FreeGamesCountSensor,
    PerPlatformFreeGamesSensor,
    async_setup_entry,
)


def _make_coordinator(
    data: dict | None, last_update_success: bool = True
) -> MagicMock:
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = last_update_success
    return coordinator


def _make_offers(n: int) -> list[dict]:
    return [
        {
            "id": str(i),
            "title": f"Game {i}",
            "platform": "Steam",
            "type": "Game",
            "claim_url": f"https://example.com/{i}",
            "published": "2026-06-20T00:00:00Z",
        }
        for i in range(n)
    ]


@pytest.mark.phase1
def test_total_sensor_state_is_int() -> None:
    data = {"offers": _make_offers(5), "metadata": {}, "platform_offers": {}}
    sensor = FreeGamesCountSensor(_make_coordinator(data))
    assert isinstance(sensor.native_value, int)
    assert sensor.native_value == 5


@pytest.mark.phase1
def test_total_sensor_no_unit() -> None:
    data = {"offers": [], "metadata": {}, "platform_offers": {}}
    sensor = FreeGamesCountSensor(_make_coordinator(data))
    assert sensor.native_unit_of_measurement is None


@pytest.mark.phase1
def test_total_sensor_state_class() -> None:
    data = {"offers": [], "metadata": {}, "platform_offers": {}}
    sensor = FreeGamesCountSensor(_make_coordinator(data))
    assert sensor.state_class == SensorStateClass.MEASUREMENT


@pytest.mark.phase1
def test_total_sensor_excludes_offers_from_recorder() -> None:
    data = {"offers": [], "metadata": {}, "platform_offers": {}}
    sensor = FreeGamesCountSensor(_make_coordinator(data))
    assert "offers" in sensor._unrecorded_attributes


@pytest.mark.phase1
def test_total_sensor_native_value_defaults_to_zero_when_data_not_ready() -> None:
    sensor = FreeGamesCountSensor(_make_coordinator(None))
    assert sensor.native_value == 0


@pytest.mark.phase1
def test_total_sensor_attributes_default_to_empty_when_data_not_ready() -> None:
    sensor = FreeGamesCountSensor(_make_coordinator(None))
    assert sensor.extra_state_attributes == {}


@pytest.mark.phase1
def test_platform_sensor_attributes_capped_at_20() -> None:
    platform_offers = {"steam_game": _make_offers(25)}
    data = {"offers": [], "metadata": {}, "platform_offers": platform_offers}
    sensor = PerPlatformFreeGamesSensor(_make_coordinator(data), "steam_game")
    assert len(sensor.extra_state_attributes["offers"]) == 20


@pytest.mark.phase1
def test_platform_sensor_excludes_offers_from_recorder() -> None:
    data = {"offers": [], "metadata": {}, "platform_offers": {}}
    sensor = PerPlatformFreeGamesSensor(_make_coordinator(data), "steam_game")
    assert "offers" in sensor._unrecorded_attributes


@pytest.mark.phase1
def test_platform_sensor_defaults_to_empty_when_data_not_ready() -> None:
    sensor = PerPlatformFreeGamesSensor(_make_coordinator(None), "steam_game")
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {"offers": []}


@pytest.mark.regression
def test_platform_sensor_unavailable_when_platform_failed() -> None:
    data = {
        "offers": [],
        "metadata": {},
        "platform_offers": {},
        "failed_platforms": {"steam_game"},
    }
    sensor = PerPlatformFreeGamesSensor(_make_coordinator(data), "steam_game")
    assert sensor.available is False


@pytest.mark.regression
def test_platform_sensor_available_when_platform_not_failed() -> None:
    data = {
        "offers": [],
        "metadata": {},
        "platform_offers": {},
        "failed_platforms": {"steam_game"},
    }
    sensor = PerPlatformFreeGamesSensor(_make_coordinator(data), "epic_game")
    assert sensor.available is True


@pytest.mark.regression
def test_platform_sensor_unavailable_when_coordinator_down() -> None:
    data = {
        "offers": [],
        "metadata": {},
        "platform_offers": {},
        "failed_platforms": set(),
    }
    sensor = PerPlatformFreeGamesSensor(
        _make_coordinator(data, last_update_success=False), "steam_game"
    )
    assert sensor.available is False


@pytest.mark.regression
def test_platform_sensor_available_before_first_refresh() -> None:
    sensor = PerPlatformFreeGamesSensor(
        _make_coordinator(None, last_update_success=True), "steam_game"
    )
    assert sensor.available is True


@pytest.mark.phase2
async def test_only_enabled_platform_sensors_created() -> None:
    coordinator = _make_coordinator(
        {"offers": [], "metadata": {}, "platform_offers": {}}
    )
    entry = MagicMock()
    entry.runtime_data = coordinator
    entry.options = {OPTION_PLATFORMS: ["steam_game", "epic_game"]}

    added: list = []
    async_add = MagicMock(side_effect=lambda entities: added.extend(entities))

    await async_setup_entry(MagicMock(), entry, async_add)

    # 1 total sensor + 2 platform sensors
    assert len(added) == 3
    platform_keys = {e._platform_key for e in added if hasattr(e, "_platform_key")}
    assert platform_keys == {"steam_game", "epic_game"}
