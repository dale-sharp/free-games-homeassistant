"""Config flow and options flow for Free Games integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import fetch_feed_data
from .const import (
    CONSOLIDATED_FEED_PATH,
    DEFAULT_BASE_URL,
    DOMAIN,
    OPTION_BASE_URL,
    OPTION_PLATFORMS,
    PLATFORM_FEED_PATHS,
    build_feed_url,
)

# Single static unique ID - only one instance of this integration makes sense
# since it polls a single public feed with no per-user credentials.
_UNIQUE_ID = "lootscraper_feed"

# Human-readable labels for each platform key - used in both config and options flows
PLATFORM_LABELS: dict[str, str] = {
    "steam_game": "Steam Games",
    "epic_game": "Epic Games",
    "gog_game": "GOG Games",
    "humble_game": "Humble Games",
    "itch_game": "Itch.io Games",
    "amazon_game": "Amazon Games",
    "amazon_loot": "Amazon In-Game Loot",
    "steam_loot": "Steam In-Game Loot",
    "epic_android": "Epic (Android)",
    "epic_ios": "Epic (iOS)",
    "apple_game": "Apple App Store",
    "google_game": "Google Play",
}


def _config_schema(current_platforms: list[str], current_base_url: str) -> vol.Schema:
    """Return a schema with the platform multi-select and base URL fields."""
    options = [
        SelectOptionDict(value=key, label=label)
        for key, label in PLATFORM_LABELS.items()
    ]
    return vol.Schema(
        {
            vol.Required(OPTION_PLATFORMS, default=current_platforms): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
            vol.Required(OPTION_BASE_URL, default=current_base_url): TextSelector(
                TextSelectorConfig(type=TextSelectorType.URL)
            ),
        }
    )


async def _async_validate_base_url(hass: HomeAssistant, base_url: str) -> str | None:
    """Check that base_url serves a reachable LootScraper consolidated feed.

    Returns an error code for async_show_form's errors dict, or None if reachable.
    """
    session = async_get_clientsession(hass)
    try:
        await fetch_feed_data(session, build_feed_url(base_url, CONSOLIDATED_FEED_PATH))
    except (aiohttp.ClientError, ValueError):
        return "cannot_connect"
    return None


class FreeGamesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Free Games."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user step."""
        await self.async_set_unique_id(_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[OPTION_BASE_URL].rstrip("/")
            error = await _async_validate_base_url(self.hass, base_url)
            if error is None:
                return self.async_create_entry(
                    title="Free Games",
                    data={},
                    options={
                        OPTION_PLATFORMS: user_input[OPTION_PLATFORMS],
                        OPTION_BASE_URL: base_url,
                    },
                )
            errors["base_url"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=_config_schema(
                list(PLATFORM_FEED_PATHS.keys()), DEFAULT_BASE_URL
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> FreeGamesOptionsFlow:
        """Create the options flow."""
        return FreeGamesOptionsFlow()


class FreeGamesOptionsFlow(OptionsFlow):
    """Handle options for the Free Games integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        config_entry = self.hass.config_entries.async_get_entry(self.handler)
        current_platforms: list[str] = (
            config_entry.options.get(OPTION_PLATFORMS, list(PLATFORM_FEED_PATHS.keys()))
            if config_entry is not None
            else list(PLATFORM_FEED_PATHS.keys())
        )
        current_base_url: str = (
            config_entry.options.get(OPTION_BASE_URL, DEFAULT_BASE_URL)
            if config_entry is not None
            else DEFAULT_BASE_URL
        )

        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[OPTION_BASE_URL].rstrip("/")
            error = await _async_validate_base_url(self.hass, base_url)
            if error is None:
                return self.async_create_entry(
                    data={
                        OPTION_PLATFORMS: user_input[OPTION_PLATFORMS],
                        OPTION_BASE_URL: base_url,
                    }
                )
            errors["base_url"] = error

        return self.async_show_form(
            step_id="init",
            data_schema=_config_schema(current_platforms, current_base_url),
            errors=errors,
        )
