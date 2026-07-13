"""Constants for the Free Games Home Assistant integration."""

from __future__ import annotations

from typing import Final

DOMAIN = "free_games"
MANUFACTURER = "LootScraper / Eiko Wagenknecht"
DEFAULT_NAME = "Free Games"

DEFAULT_SCAN_INTERVAL_MINUTES: Final[int] = 60
MIN_SCAN_INTERVAL_MINUTES: Final[int] = 30
MAX_SCAN_INTERVAL_MINUTES: Final[int] = 1440

DEFAULT_BASE_URL: Final[str] = "https://feed.eikowagenknecht.com"

CONSOLIDATED_FEED_PATH: Final[str] = "lootscraper.xml"

PLATFORM_FEED_PATHS: dict[str, str] = {
    "steam_game": "lootscraper_steam_game.xml",
    "epic_game": "lootscraper_epic_game.xml",
    "gog_game": "lootscraper_gog_game.xml",
    "humble_game": "lootscraper_humble_game.xml",
    "itch_game": "lootscraper_itch_game.xml",
    "amazon_game": "lootscraper_amazon_game.xml",
    "amazon_loot": "lootscraper_amazon_loot.xml",
    "steam_loot": "lootscraper_steam_loot.xml",
    "epic_android": "lootscraper_epic_game_android.xml",
    "epic_ios": "lootscraper_epic_game_ios.xml",
    "apple_game": "lootscraper_apple_game.xml",
    "google_game": "lootscraper_google_game.xml",
    "ubisoft_game": "lootscraper_ubisoft_game.xml",
    "fab_asset": "lootscraper_fab_asset.xml",
    "steam_points": "lootscraper_steam_points.xml",
}

OPTION_PLATFORMS = "platforms"
OPTION_BASE_URL = "base_url"
OPTION_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

# platform_key -> (source term, type term, platform term or None = don't care)
PLATFORM_KEY_CATEGORIES: dict[str, tuple[str, str, str | None]] = {
    "steam_game": ("STEAM", "GAME", None),
    "epic_game": ("EPIC", "GAME", "PC"),
    "gog_game": ("GOG", "GAME", None),
    "humble_game": ("HUMBLE", "GAME", None),
    "itch_game": ("ITCH", "GAME", None),
    "amazon_game": ("AMAZON", "GAME", None),
    "amazon_loot": ("AMAZON", "LOOT", None),
    "steam_loot": ("STEAM", "LOOT", None),
    "epic_android": ("EPIC", "GAME", "ANDROID"),
    "epic_ios": ("EPIC", "GAME", "IOS"),
    "apple_game": ("APPLE", "GAME", None),
    "google_game": ("GOOGLE", "GAME", None),
    "ubisoft_game": ("UBISOFT", "GAME", None),
    "fab_asset": ("FAB", "ASSET", None),
    "steam_points": ("STEAM", "POINTS", None),
}


def build_feed_url(base_url: str, path: str) -> str:
    """Join a feed base URL and path, tolerating a trailing slash on base_url."""
    return f"{base_url.rstrip('/')}/{path}"
