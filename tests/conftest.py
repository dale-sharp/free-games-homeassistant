"""Pytest configuration, phase markers, and shared fixtures."""

from __future__ import annotations

import pathlib
import socket as _socket_module
import sys

import pytest

# Windows: socket.socketpair() is emulated via TCP sockets, which pytest-socket
# blocks during event-loop initialisation. Patch socketpair so it temporarily
# restores the real socket class only for the duration of that internal call.
if sys.platform == "win32":
    _real_socket_cls = _socket_module.socket  # captured before pytest-socket patches it
    _orig_socketpair = _socket_module.socketpair

    def _socketpair_allow_real(*args, **kwargs):  # type: ignore[no-untyped-def]
        saved = _socket_module.socket
        _socket_module.socket = _real_socket_cls
        try:
            return _orig_socketpair(*args, **kwargs)
        finally:
            _socket_module.socket = saved

    _socket_module.socketpair = _socketpair_allow_real

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
