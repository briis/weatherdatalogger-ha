"""Config flow for the WeatherDataLogger integration."""

from __future__ import annotations

import logging
from typing import Any

import pymysql
import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_LOCATION,
    CONF_PROVIDER,
    DEFAULT_DATABASE,
    DEFAULT_LOCATION,
    DEFAULT_PORT,
    DEFAULT_PROVIDER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
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
    }
)


def _select_schema(key: str, options: list[str], default: str) -> vol.Schema:
    """Build a single-field dropdown schema, adding `default` to `options` if it's missing."""
    if default not in options:
        options = [*options, default]
    return vol.Schema(
        {
            vol.Required(key, default=default): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    mode=SelectSelectorMode.DROPDOWN,
                    custom_value=True,
                )
            ),
        }
    )


async def _async_validate_and_discover_locations(
    hass: HomeAssistant, data: dict[str, Any]
) -> list[str]:
    """Raise CannotConnect/InvalidAuth if the given settings don't work.

    Otherwise return the distinct forecast locations already configured in
    the database (empty if none have written any forecast rows yet).
    """
    client = WeatherDataLoggerClient(
        WeatherDataLoggerConfig(
            host=data[CONF_HOST],
            port=data[CONF_PORT],
            database=data[CONF_DATABASE],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
        )
    )
    try:
        await hass.async_add_executor_job(client.test_connection)
        return await hass.async_add_executor_job(client.list_locations)
    except pymysql.err.OperationalError as err:
        # PyMySQL's access-denied error code is 1045.
        if err.args and err.args[0] == 1045:
            raise InvalidAuth from err
        raise CannotConnect from err


async def _async_discover_providers(
    hass: HomeAssistant, connection_data: dict[str, Any], location: str
) -> list[str]:
    """Raise CannotConnect/InvalidAuth if the connection fails.

    Otherwise return the distinct forecast providers already configured for
    `location` (empty if none have written any forecast rows yet).
    """
    client = WeatherDataLoggerClient(
        WeatherDataLoggerConfig(
            host=connection_data[CONF_HOST],
            port=connection_data[CONF_PORT],
            database=connection_data[CONF_DATABASE],
            username=connection_data[CONF_USERNAME],
            password=connection_data[CONF_PASSWORD],
            location=location,
        )
    )
    try:
        return await hass.async_add_executor_job(client.list_providers)
    except pymysql.err.OperationalError as err:
        # PyMySQL's access-denied error code is 1045.
        if err.args and err.args[0] == 1045:
            raise InvalidAuth from err
        raise CannotConnect from err


class WeatherDataLoggerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeatherDataLogger."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize flow-instance state carried across the connection/location/provider steps."""
        self._connection_data: dict[str, Any] = {}
        self._location_data: dict[str, Any] = {}
        self._discovered_locations: list[str] = []
        self._discovered_providers: list[str] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> WeatherDataLoggerOptionsFlow:
        """Return the options flow for changing the polling interval."""
        return WeatherDataLoggerOptionsFlow()

    def _reconfigure_entry(self) -> ConfigEntry | None:
        return self._get_reconfigure_entry() if self.source == SOURCE_RECONFIGURE else None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        return await self._async_handle_connection_step(user_input, step_id="user")

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-running setup for an existing entry (e.g. host details changed)."""
        return await self._async_handle_connection_step(user_input, step_id="reconfigure")

    async def _async_handle_connection_step(
        self, user_input: dict[str, Any] | None, *, step_id: str
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reconfigure_entry = self._reconfigure_entry()

        if user_input is not None:
            try:
                locations = await _async_validate_and_discover_locations(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during WeatherDataLogger setup")
                errors["base"] = "unknown"
            else:
                self._connection_data = user_input
                self._discovered_locations = locations
                return await self.async_step_location()

        # Pre-fill with whatever the user just submitted (on a validation
        # error) or, failing that, the current entry's values (on reconfigure).
        suggested_values = user_input or (reconfigure_entry.data if reconfigure_entry else None)
        data_schema = self.add_suggested_values_to_schema(STEP_USER_DATA_SCHEMA, suggested_values)

        return self.async_show_form(step_id=step_id, data_schema=data_schema, errors=errors)

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a forecast location from the ones found in the database."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._reconfigure_entry()

        if user_input is not None:
            try:
                providers = await _async_discover_providers(
                    self.hass, self._connection_data, user_input[CONF_LOCATION]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during WeatherDataLogger setup")
                errors["base"] = "unknown"
            else:
                self._location_data = user_input
                self._discovered_providers = providers
                return await self.async_step_provider()

        current_location = (
            reconfigure_entry.data.get(CONF_LOCATION, DEFAULT_LOCATION)
            if reconfigure_entry
            else DEFAULT_LOCATION
        )
        options = self._discovered_locations or [DEFAULT_LOCATION]
        data_schema = _select_schema(CONF_LOCATION, options, current_location)

        return self.async_show_form(step_id="location", data_schema=data_schema, errors=errors)

    async def async_step_provider(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a forecast provider from the ones found for this location."""
        reconfigure_entry = self._reconfigure_entry()

        if user_input is not None:
            data = {**self._connection_data, **self._location_data, **user_input}
            unique_id = (
                f"{data[CONF_HOST]}:{data[CONF_PORT]}"
                f"/{data[CONF_DATABASE]}/{data[CONF_LOCATION]}/{data[CONF_PROVIDER]}"
            )
            await self.async_set_unique_id(unique_id)
            # Only enforce the collision check against *other* entries — a
            # reconfigure that leaves the unique ID unchanged would otherwise
            # collide with the entry being reconfigured itself.
            if reconfigure_entry is None or reconfigure_entry.unique_id != unique_id:
                self._abort_if_unique_id_configured()

            title = f"WeatherDataLogger ({data[CONF_LOCATION]})"
            if reconfigure_entry is None:
                return self.async_create_entry(title=title, data=data)
            return self.async_update_reload_and_abort(
                reconfigure_entry,
                unique_id=unique_id,
                title=title,
                data=data,
            )

        current_provider = (
            reconfigure_entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
            if reconfigure_entry
            else DEFAULT_PROVIDER
        )
        options = self._discovered_providers or [DEFAULT_PROVIDER]
        data_schema = _select_schema(CONF_PROVIDER, options, current_provider)

        return self.async_show_form(step_id="provider", data_schema=data_schema)


class WeatherDataLoggerOptionsFlow(OptionsFlowWithReload):
    """Handle options for an existing WeatherDataLogger entry (polling interval)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the polling interval option."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement=UnitOfTime.SECONDS,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)


class CannotConnect(Exception):
    """Error to indicate we cannot reach the database host."""


class InvalidAuth(Exception):
    """Error to indicate the given DB credentials were rejected."""
