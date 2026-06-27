"""Pytest configuration, phase markers, and shared fixtures."""
from __future__ import annotations

import pathlib

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "phase1: HA compliance and dead code fixes")
    config.addinivalue_line("markers", "phase2: efficiency changes")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test in the suite."""
    yield


@pytest.fixture
def sample_game_feed_xml() -> str:
    return (FIXTURES_DIR / "sample_game_feed.xml").read_text(encoding="utf-8")


@pytest.fixture
def sample_loot_feed_xml() -> str:
    return (FIXTURES_DIR / "sample_loot_feed.xml").read_text(encoding="utf-8")


@pytest.fixture
def malformed_xml() -> str:
    return (FIXTURES_DIR / "malformed.xml").read_text(encoding="utf-8")
