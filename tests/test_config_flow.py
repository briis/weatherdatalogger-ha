"""Tests for the WeatherDataLogger config flow."""

from unittest.mock import patch

import pymysql
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.weatherdatalogger.const import DOMAIN

USER_INPUT = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "weatherdatalogger",
    "username": "weatherdatalogger_ha",
    "password": "secret",
    "location": "home",
}


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """A valid connection creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with (
        patch(
            "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.test_connection"
        ),
        # Config entry creation triggers a real async_setup_entry, which
        # would otherwise open a real DB connection via the coordinator's
        # first refresh — out of scope for a config_flow test.
        patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WeatherDataLogger (home)"
    assert result["data"] == USER_INPUT


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """A connection error is surfaced as a form error, not an exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.test_connection",
        side_effect=pymysql.err.OperationalError(2003, "Can't connect to MySQL server"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_invalid_auth(hass: HomeAssistant) -> None:
    """A MariaDB access-denied error (1045) maps to invalid_auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.test_connection",
        side_effect=pymysql.err.OperationalError(1045, "Access denied"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def _setup_entry(hass: HomeAssistant) -> config_entries.ConfigEntry:
    """Create a real, loaded config entry via the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(
            "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.test_connection"
        ),
        patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
        await hass.async_block_till_done()

    return hass.config_entries.async_entries(DOMAIN)[0]


async def test_reconfigure_flow_prefills_current_values(hass: HomeAssistant) -> None:
    """The reconfigure form is pre-filled with the existing entry's data."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    schema = result["data_schema"].schema
    suggested = {
        key.schema: key.description["suggested_value"]
        for key in schema
        if isinstance(key.description, dict) and "suggested_value" in key.description
    }
    assert suggested["host"] == USER_INPUT["host"]
    assert suggested["location"] == USER_INPUT["location"]


async def test_reconfigure_flow_success_updates_entry(hass: HomeAssistant) -> None:
    """Submitting new values on reconfigure updates the existing entry in place."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    new_input = {**USER_INPUT, "host": "192.168.1.50"}
    with (
        patch(
            "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.test_connection"
        ),
        patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], new_input)
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].entry_id == entry.entry_id
    assert entries[0].data["host"] == "192.168.1.50"
