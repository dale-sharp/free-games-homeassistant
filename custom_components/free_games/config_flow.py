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

from .const import DOMAIN, PLATFORM_FEEDS, OPTION_PLATFORMS

# Single static unique ID - only one instance of this integration makes sense
# since it polls a single public feed with no per-user credentials.
_UNIQUE_ID = "lootscraper_feed"


class FreeGamesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Free Games."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user step."""
        # Prevent setting up more than one instance
        await self.async_set_unique_id(_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Free Games", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return FreeGamesOptionsFlow(config_entry)


class FreeGamesOptionsFlow(OptionsFlow):
    """Handle options for the Free Games integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialise options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_platforms: set[str] = set(
            self._config_entry.options.get(
                OPTION_PLATFORMS, list(PLATFORM_FEEDS.keys())
            )
        )

        schema_dict: dict[Any, Any] = {}
        for platform_key in sorted(PLATFORM_FEEDS.keys()):
            schema_dict[
                vol.Optional(
                    platform_key,
                    default=platform_key in current_platforms,
                )
            ] = bool

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
