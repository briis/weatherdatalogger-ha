"""Tests for the WeatherDataLogger config flow."""

from unittest.mock import patch

import pymysql
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weatherdatalogger.const import DOMAIN
from custom_components.weatherdatalogger.db import WeatherDataLoggerSnapshot

CONNECTION_INPUT = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "weatherdatalogger",
    "username": "weatherdatalogger_ha",
    "password": "secret",
}
LOCATION_INPUT = {"location": "home"}
PROVIDER_INPUT = {"provider": "visualcrossing"}
USER_INPUT = {**CONNECTION_INPUT, **LOCATION_INPUT, **PROVIDER_INPUT}

_CLIENT_TEST_CONNECTION = (
    "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.test_connection"
)
_CLIENT_LIST_LOCATIONS = (
    "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.list_locations"
)
_CLIENT_LIST_PROVIDERS = (
    "custom_components.weatherdatalogger.config_flow.WeatherDataLoggerClient.list_providers"
)


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """A valid connection, then picking a location and a provider, creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "location"

    with patch(_CLIENT_LIST_PROVIDERS, return_value=["visualcrossing"]):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LOCATION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provider"

    # Config entry creation triggers a real async_setup_entry, which
    # would otherwise open a real DB connection via the coordinator's
    # first refresh — out of scope for a config_flow test.
    with patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], PROVIDER_INPUT)
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WeatherDataLogger (home)"
    assert result["data"] == USER_INPUT


async def test_user_flow_location_step_offers_discovered_locations(hass: HomeAssistant) -> None:
    """The location step's dropdown lists whatever locations were found in the database."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["office", "home"]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "location"
    schema = result["data_schema"].schema
    (location_key,) = [key for key in schema if key.schema == "location"]
    assert location_key.default() == "home"
    assert schema[location_key].config["options"] == ["office", "home"]


async def test_user_flow_location_step_falls_back_to_default_when_none_found(
    hass: HomeAssistant,
) -> None:
    """If the database has no forecast rows yet, the dropdown still offers the default."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=[]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "location"
    schema = result["data_schema"].schema
    (location_key,) = [key for key in schema if key.schema == "location"]
    assert schema[location_key].config["options"] == ["home"]


async def test_user_flow_provider_step_offers_discovered_providers(hass: HomeAssistant) -> None:
    """The provider step's dropdown lists whatever providers were found for the location."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    with patch(_CLIENT_LIST_PROVIDERS, return_value=["pirateweather", "visualcrossing"]):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LOCATION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provider"
    schema = result["data_schema"].schema
    (provider_key,) = [key for key in schema if key.schema == "provider"]
    assert provider_key.default() == "visualcrossing"
    assert schema[provider_key].config["options"] == ["pirateweather", "visualcrossing"]


async def test_user_flow_provider_step_falls_back_to_default_when_none_found(
    hass: HomeAssistant,
) -> None:
    """If the location has no forecast rows yet, the dropdown still offers the default."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    with patch(_CLIENT_LIST_PROVIDERS, return_value=[]):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LOCATION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provider"
    schema = result["data_schema"].schema
    (provider_key,) = [key for key in schema if key.schema == "provider"]
    assert schema[provider_key].config["options"] == ["visualcrossing"]


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """A connection error is surfaced as a form error, not an exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        _CLIENT_TEST_CONNECTION,
        side_effect=pymysql.err.OperationalError(2003, "Can't connect to MySQL server"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_invalid_auth(hass: HomeAssistant) -> None:
    """A MariaDB access-denied error (1045) maps to invalid_auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        _CLIENT_TEST_CONNECTION,
        side_effect=pymysql.err.OperationalError(1045, "Access denied"),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


async def _setup_entry(hass: HomeAssistant) -> config_entries.ConfigEntry:
    """Create a real, loaded config entry via the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    with patch(_CLIENT_LIST_PROVIDERS, return_value=["visualcrossing"]):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LOCATION_INPUT)

    with patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], PROVIDER_INPUT)
        await hass.async_block_till_done()

    return hass.config_entries.async_entries(DOMAIN)[0]


async def test_user_flow_aborts_on_duplicate_host_location_provider(hass: HomeAssistant) -> None:
    """Adding the same host/database/location/provider a second time is rejected."""
    await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONNECTION_INPUT
        )

    with patch(_CLIENT_LIST_PROVIDERS, return_value=["visualcrossing"]):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCATION_INPUT
        )

    result = await hass.config_entries.flow.async_configure(result["flow_id"], PROVIDER_INPUT)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_user_flow_allows_same_host_with_different_location(hass: HomeAssistant) -> None:
    """A second location on the same database/host is a legitimate, separate entry."""
    await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home", "cabin"]),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONNECTION_INPUT
        )

    with patch(_CLIENT_LIST_PROVIDERS, return_value=["visualcrossing"]):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"location": "cabin"}
        )

    with patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], PROVIDER_INPUT)
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2


async def test_reconfigure_flow_prefills_current_values(hass: HomeAssistant) -> None:
    """The reconfigure form is pre-filled with the existing entry's connection details."""
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


async def test_reconfigure_flow_location_step_defaults_to_current_location(
    hass: HomeAssistant,
) -> None:
    """The location step defaults to the entry's existing location, even if not rediscovered."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=[]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "location"
    schema = result["data_schema"].schema
    (location_key,) = [key for key in schema if key.schema == "location"]
    assert location_key.default() == "home"
    assert schema[location_key].config["options"] == ["home"]


async def test_reconfigure_flow_provider_step_defaults_to_current_provider(
    hass: HomeAssistant,
) -> None:
    """The provider step defaults to the entry's existing provider, even if not rediscovered."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    with patch(_CLIENT_LIST_PROVIDERS, return_value=[]):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LOCATION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provider"
    schema = result["data_schema"].schema
    (provider_key,) = [key for key in schema if key.schema == "provider"]
    assert provider_key.default() == "visualcrossing"
    assert schema[provider_key].config["options"] == ["visualcrossing"]


async def test_reconfigure_flow_success_updates_entry(hass: HomeAssistant) -> None:
    """Submitting new values on reconfigure updates the existing entry in place."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    new_connection_input = {**CONNECTION_INPUT, "host": "192.168.1.50"}
    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch(_CLIENT_LIST_LOCATIONS, return_value=["home"]),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], new_connection_input
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "location"

    with patch(_CLIENT_LIST_PROVIDERS, return_value=["visualcrossing"]):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], LOCATION_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provider"

    with patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], PROVIDER_INPUT)
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].entry_id == entry.entry_id
    assert entries[0].data["host"] == "192.168.1.50"


async def test_options_flow_defaults_to_current_scan_interval(hass: HomeAssistant) -> None:
    """The options form defaults to the current polling interval."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    (scan_interval_key,) = [key for key in schema if key.schema == "scan_interval"]
    assert scan_interval_key.default() == 60


async def test_options_flow_updates_scan_interval_and_reloads(hass: HomeAssistant) -> None:
    """Submitting a new interval updates entry.options and reloads the entry."""
    entry = await _setup_entry(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with (
        patch(_CLIENT_TEST_CONNECTION),
        patch("custom_components.weatherdatalogger.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"scan_interval": 15}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["scan_interval"] == 15


async def test_migrate_v1_entry_adds_default_provider(hass: HomeAssistant) -> None:
    """A pre-provider (version 1) entry gets backfilled with the default provider."""
    v1_data = {**CONNECTION_INPUT, **LOCATION_INPUT}
    entry = MockConfigEntry(domain=DOMAIN, data=v1_data, version=1)
    entry.add_to_hass(hass)

    empty_snapshot = WeatherDataLoggerSnapshot(
        realtime={},
        realtime_stats={},
        forecast_current={},
        forecast_hourly=[],
        forecast_daily=[],
    )
    with patch(
        "custom_components.weatherdatalogger.WeatherDataLoggerClient.fetch_all",
        return_value=empty_snapshot,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.version == 2
    assert entry.data["provider"] == "visualcrossing"
