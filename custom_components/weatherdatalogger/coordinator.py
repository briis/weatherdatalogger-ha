"""DataUpdateCoordinator for the WeatherDataLogger integration."""

from __future__ import annotations

import logging
from datetime import timedelta

import pymysql
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .db import WeatherDataLoggerClient, WeatherDataLoggerSnapshot

_LOGGER = logging.getLogger(__name__)


class WeatherDataLoggerCoordinator(DataUpdateCoordinator[WeatherDataLoggerSnapshot]):
    """Polls the weatherdatalogger MariaDB database on a fixed interval."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: WeatherDataLoggerClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="weatherdatalogger",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client

    async def _async_update_data(self) -> WeatherDataLoggerSnapshot:
        try:
            return await self.hass.async_add_executor_job(self._client.fetch_all)
        except pymysql.MySQLError as err:
            raise UpdateFailed(f"Error communicating with weatherdatalogger DB: {err}") from err
