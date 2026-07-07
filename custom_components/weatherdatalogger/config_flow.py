"""Config flow for the WeatherDataLogger integration."""

from __future__ import annotations

import logging
from typing import Any

import pymysql
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LOCATION,
    DEFAULT_DATABASE,
    DEFAULT_LOCATION,
    DEFAULT_PORT,
    DOMAIN,
)
from .db import WeatherDataLoggerClient, WeatherDataLoggerConfig

_LOGGER = logging.getLogger(__name__)

CONF_DATABASE = "database"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_DATABASE, default=DEFAULT_DATABASE): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_LOCATION, default=DEFAULT_LOCATION): str,
    }
)


async def _async_validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Raise CannotConnect/InvalidAuth if the given settings don't work."""
    client = WeatherDataLoggerClient(
        WeatherDataLoggerConfig(
            host=data[CONF_HOST],
            port=data[CONF_PORT],
            database=data[CONF_DATABASE],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            location=data[CONF_LOCATION],
        )
    )
    try:
        await hass.async_add_executor_job(client.test_connection)
    except pymysql.err.OperationalError as err:
        # PyMySQL's access-denied error code is 1045.
        if err.args and err.args[0] == 1045:
            raise InvalidAuth from err
        raise CannotConnect from err


class WeatherDataLoggerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeatherDataLogger."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                f"/{user_input[CONF_DATABASE]}/{user_input[CONF_LOCATION]}"
            )
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during WeatherDataLogger setup")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"WeatherDataLogger ({user_input[CONF_LOCATION]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(Exception):
    """Error to indicate we cannot reach the database host."""


class InvalidAuth(Exception):
    """Error to indicate the given DB credentials were rejected."""
