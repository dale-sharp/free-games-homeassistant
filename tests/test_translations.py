"""Structural tests for translation and icon JSON files."""

from __future__ import annotations

import json
import pathlib

from custom_components.free_games.config_flow import PLATFORM_LABELS

COMPONENT_DIR = pathlib.Path(__file__).parent.parent / "custom_components" / "free_games"


def test_strings_and_translations_en_are_identical() -> None:
    strings = json.loads((COMPONENT_DIR / "strings.json").read_text(encoding="utf-8"))
    translations_en = json.loads(
        (COMPONENT_DIR / "translations" / "en.json").read_text(encoding="utf-8")
    )
    assert strings == translations_en


def test_icons_json_covers_every_sensor_entity() -> None:
    icons = json.loads((COMPONENT_DIR / "icons.json").read_text(encoding="utf-8"))
    sensor_icons = icons["entity"]["sensor"]

    expected_keys = {"active_free_games", *PLATFORM_LABELS.keys()}
    assert set(sensor_icons.keys()) == expected_keys
    for key, entry in sensor_icons.items():
        assert "default" in entry, f"{key} is missing a default icon"
