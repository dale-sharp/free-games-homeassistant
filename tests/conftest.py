"""Pytest configuration, phase markers, and shared fixtures."""

from __future__ import annotations

import contextlib
import logging
import pathlib
import socket as _socket_module
import sys
from collections.abc import Generator

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


# ---------------------------------------------------------------------------
# Log noise suppression
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def suppress_expected_log_noise() -> Generator:
    """Raise log levels for loggers that produce expected noise during tests.

    - homeassistant.loader: emits INFO/WARNING for every custom integration
      it loads — expected in all tests, not actionable.
    - homeassistant.setup: emits INFO on every setup call — expected, not actionable.
    - custom_components.free_games: WARNING emitted when malformed XML is parsed
      without a <feed> root; that path is tested structurally, not by log assertion.
    """
    loggers = [
        logging.getLogger("homeassistant.loader"),
        logging.getLogger("homeassistant.setup"),
        logging.getLogger("custom_components.free_games"),
    ]
    original_levels = [(lg, lg.level) for lg in loggers]
    for lg in loggers:
        lg.setLevel(logging.CRITICAL)
    yield
    for lg, level in original_levels:
        lg.setLevel(level)


@contextlib.contextmanager
def capture_logs_without_propagation(
    caplog_fixture: pytest.LogCaptureFixture,
    logger_name: str,
    level: int = logging.ERROR,
) -> Generator:
    """Capture log records from ``logger_name`` for assertion without live output.

    Sets propagate=False so records never reach root-logger handlers, then
    attaches caplog's handler directly for assertion via caplog.text.
    """
    logger = logging.getLogger(logger_name)
    original_propagate = logger.propagate
    original_level = logger.level
    logger.propagate = False
    logger.setLevel(level)
    logger.addHandler(caplog_fixture.handler)
    try:
        yield
    finally:
        logger.removeHandler(caplog_fixture.handler)
        logger.propagate = original_propagate
        logger.setLevel(original_level)


@pytest.fixture
def sample_game_feed_xml() -> str:
    return (FIXTURES_DIR / "sample_game_feed.xml").read_text(encoding="utf-8")


@pytest.fixture
def sample_loot_feed_xml() -> str:
    return (FIXTURES_DIR / "sample_loot_feed.xml").read_text(encoding="utf-8")


@pytest.fixture
def malformed_xml() -> str:
    return (FIXTURES_DIR / "malformed.xml").read_text(encoding="utf-8")
