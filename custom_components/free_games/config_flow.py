"""Config flow and options flow for Free Games integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN, OPTION_PLATFORMS, PLATFORM_FEED_PATHS

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


def _platforms_schema(current: list[str]) -> vol.Schema:
    """Return a schema with a multi-select for platform keys."""
    options = [
        SelectOptionDict(value=key, label=label)
        for key, label in PLATFORM_LABELS.items()
    ]
    return vol.Schema(
        {
            vol.Required(OPTION_PLATFORMS, default=current): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


class FreeGamesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Free Games."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user step."""
        await self.async_set_unique_id(_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Free Games",
                data={},
                options={OPTION_PLATFORMS: user_input[OPTION_PLATFORMS]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_platforms_schema(list(PLATFORM_FEED_PATHS.keys())),
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
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        config_entry = self.hass.config_entries.async_get_entry(self.handler)
        current: list[str] = (
            config_entry.options.get(OPTION_PLATFORMS, list(PLATFORM_FEED_PATHS.keys()))
            if config_entry is not None
            else list(PLATFORM_FEED_PATHS.keys())
        )

        return self.async_show_form(
            step_id="init",
            data_schema=_platforms_schema(current),
        )
