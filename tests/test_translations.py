"""Structural tests for translation and icon JSON files."""

from __future__ import annotations

import json
import pathlib

COMPONENT_DIR = pathlib.Path(__file__).parent.parent / "custom_components" / "free_games"


def test_strings_and_translations_en_are_identical() -> None:
    strings = json.loads((COMPONENT_DIR / "strings.json").read_text(encoding="utf-8"))
    translations_en = json.loads(
        (COMPONENT_DIR / "translations" / "en.json").read_text(encoding="utf-8")
    )
    assert strings == translations_en
