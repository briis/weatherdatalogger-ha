"""The WeatherDataLogger integration — reads a weatherdatalogger MariaDB
instance (see https://github.com/briis/WeatherDatalogger) and exposes it as
a weather entity (Visual Crossing forecast) plus a set of station sensors
(live readings merged from whichever hardware station_roles assigns each
role to).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .const import CONF_LOCATION, DEFAULT_SCAN_INTERVAL
from .coordinator import WeatherDataLoggerCoordinator
from .db import WeatherDataLoggerClient, WeatherDataLoggerConfig

PLATFORMS = ["weather", "sensor"]

type WeatherDataLoggerConfigEntry = ConfigEntry[WeatherDataLoggerCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: WeatherDataLoggerConfigEntry) -> bool:
    """Set up WeatherDataLogger from a config entry."""
    client = WeatherDataLoggerClient(
        WeatherDataLoggerConfig(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            database=entry.data["database"],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            location=entry.data[CONF_LOCATION],
        )
    )

    coordinator = WeatherDataLoggerCoordinator(
        hass, entry, client, entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady from err

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: WeatherDataLoggerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """YAML setup is not supported — config entries only."""
    return True
