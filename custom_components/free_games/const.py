"""Constants for the Free Games Home Assistant integration."""

from __future__ import annotations

from typing import Final

DOMAIN = "free_games"
MANUFACTURER = "LootScraper / Eiko Wagenknecht"
DEFAULT_NAME = "Free Games"

SCAN_INTERVAL_SECONDS: Final[int] = 900

PLATFORM_FEEDS: dict[str, str] = {
    "steam_game": "https://feed.eikowagenknecht.com/lootscraper_steam_game.xml",
    "epic_game": "https://feed.eikowagenknecht.com/lootscraper_epic_game.xml",
    "gog_game": "https://feed.eikowagenknecht.com/lootscraper_gog_game.xml",
    "humble_game": "https://feed.eikowagenknecht.com/lootscraper_humble_game.xml",
    "itch_game": "https://feed.eikowagenknecht.com/lootscraper_itch_game.xml",
    "amazon_game": "https://feed.eikowagenknecht.com/lootscraper_amazon_game.xml",
    "amazon_loot": "https://feed.eikowagenknecht.com/lootscraper_amazon_loot.xml",
    "steam_loot": "https://feed.eikowagenknecht.com/lootscraper_steam_loot.xml",
    "epic_android": "https://feed.eikowagenknecht.com/lootscraper_epic_game_android.xml",
    "epic_ios": "https://feed.eikowagenknecht.com/lootscraper_epic_game_ios.xml",
    "apple_game": "https://feed.eikowagenknecht.com/lootscraper_apple_game.xml",
    "google_game": "https://feed.eikowagenknecht.com/lootscraper_google_game.xml",
}

OPTION_PLATFORMS = "platforms"
