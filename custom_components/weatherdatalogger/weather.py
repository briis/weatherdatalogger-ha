"""Weather platform for WeatherDataLogger — sourced from the Visual Crossing
forecast tables (forecast_current/forecast_hourly/forecast_daily). The
`weather_condition` columns already hold an HA-recognized condition string
(see db_writer.py / migrations/20260707_add_forecast_tables.sql), so no
condition mapping is needed here.
"""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, WEATHER_DEVICE_NAME
from .coordinator import WeatherDataLoggerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the weather entity from a config entry."""
    coordinator: WeatherDataLoggerCoordinator = entry.runtime_data
    async_add_entities([WeatherDataLoggerWeather(coordinator, entry)])


def _row_to_forecast(row: dict, *, daily: bool) -> Forecast:
    forecast: Forecast = {
        "datetime": row["forecast_time"].isoformat(),
        "condition": row.get("weather_condition"),
        "native_wind_speed": row.get("wind_speed_ms"),
        "native_wind_gust_speed": row.get("wind_gust_ms"),
        "wind_bearing": row.get("wind_bearing_deg"),
        "native_pressure": row.get("pressure_mb"),
        "humidity": row.get("humidity_pct"),
        "uv_index": row.get("uv_index"),
        "precipitation_probability": row.get("precipitation_probability_pct"),
        "native_precipitation": row.get("precipitation_mm"),
        "cloud_coverage": row.get("cloud_cover_pct"),
    }
    if daily:
        forecast["native_temperature"] = row.get("temperature_high_c")
        forecast["native_templow"] = row.get("temperature_low_c")
    else:
        forecast["native_temperature"] = row.get("temperature_c")
    return forecast


class WeatherDataLoggerWeather(CoordinatorEntity[WeatherDataLoggerCoordinator], WeatherEntity):
    """Weather entity backed by the Visual Crossing forecast tables."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(self, coordinator: WeatherDataLoggerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_weather")},
            name=WEATHER_DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model="Visual Crossing forecast",
        )

    @property
    def _current(self) -> dict | None:
        return self.coordinator.data.forecast_current

    @property
    def condition(self) -> str | None:
        return self._current["weather_condition"] if self._current else None

    @property
    def native_temperature(self) -> float | None:
        return self._current["temperature_c"] if self._current else None

    @property
    def native_pressure(self) -> float | None:
        return self._current["pressure_mb"] if self._current else None

    @property
    def humidity(self) -> float | None:
        return self._current["humidity_pct"] if self._current else None

    @property
    def native_wind_speed(self) -> float | None:
        return self._current["wind_speed_ms"] if self._current else None

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self._current["wind_gust_ms"] if self._current else None

    @property
    def wind_bearing(self) -> float | None:
        return self._current["wind_bearing_deg"] if self._current else None

    @property
    def native_visibility(self) -> float | None:
        return self._current["visibility_km"] if self._current else None

    @property
    def uv_index(self) -> float | None:
        return self._current["uv_index"] if self._current else None

    @property
    def available(self) -> bool:
        return super().available and self._current is not None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        rows = self.coordinator.data.forecast_hourly
        return [_row_to_forecast(row, daily=False) for row in rows] if rows else None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        rows = self.coordinator.data.forecast_daily
        return [_row_to_forecast(row, daily=True) for row in rows] if rows else None
