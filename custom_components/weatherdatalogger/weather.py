"""Weather platform for WeatherDataLogger. Current condition and visibility
come from the Visual Crossing forecast tables (forecast_current) — the
`weather_condition` column already holds an HA-recognized condition string
(see db_writer.py / migrations/20260707_add_forecast_tables.sql), so no
condition mapping is needed here. The other current-conditions values
(temperature, pressure, humidity, wind, UV index) are read straight from
combined_realtime instead, since that's the station's own live reading
rather than Visual Crossing's periodically-fetched observation. Hourly and
daily forecasts still come entirely from the forecast tables — combined_realtime
has no forecast data.
"""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
)
from homeassistant.components.weather.const import (
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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import CONF_LOCATION, DEFAULT_LOCATION, DOMAIN, MANUFACTURER, WEATHER_DEVICE_NAME
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
    forecast_time = row["forecast_time"]
    if forecast_time.tzinfo is None:
        # DB stores forecast_time as naive UTC — mark it explicitly so the
        # frontend doesn't misread it as naive local time (shifting the
        # calendar day, which breaks the "is this today?" check).
        forecast_time = forecast_time.replace(tzinfo=dt_util.UTC)
    forecast: Forecast = {
        "datetime": forecast_time.isoformat(),
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


def _apply_current_high_low(forecast: Forecast, current: dict | None) -> None:
    """Prefer forecast_current's live-updated today high/low over forecast_daily's.

    forecast_daily's row for today is a static prediction; forecast_current is
    refreshed each poll with the actual observed high/low so far today.
    """
    if current is None:
        return
    if current.get("temperature_high_c") is not None:
        forecast["native_temperature"] = current["temperature_high_c"]
    if current.get("temperature_low_c") is not None:
        forecast["native_templow"] = current["temperature_low_c"]


class WeatherDataLoggerWeather(CoordinatorEntity[WeatherDataLoggerCoordinator], WeatherEntity):
    """Weather entity backed by the Visual Crossing forecast tables, with
    current conditions read from combined_realtime instead of forecast_current.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_attribution = "Weather data provided by Visual Crossing"
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
        # Suggest an English, location-scoped entity_id (see the matching
        # comment in sensor.py) so a second location/station configured on
        # the same HA instance gets its own weather.wdl_<location>_weather
        # entity instead of colliding on plain weather.weatherdatalogger_forecast.
        location_slug = slugify(entry.data.get(CONF_LOCATION, DEFAULT_LOCATION))
        self.entity_id = f"weather.wdl_{location_slug}_weather"
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
    def _realtime(self) -> dict | None:
        return self.coordinator.data.realtime

    @property
    def condition(self) -> str | None:
        return self._current["weather_condition"] if self._current else None

    @property
    def native_temperature(self) -> float | None:
        return self._realtime.get("air_temperature_c") if self._realtime else None

    @property
    def native_pressure(self) -> float | None:
        return self._realtime.get("sea_level_pressure_mb") if self._realtime else None

    @property
    def humidity(self) -> float | None:
        return self._realtime.get("relative_humidity_pct") if self._realtime else None

    @property
    def native_wind_speed(self) -> float | None:
        return self._realtime.get("wind_avg_ms") if self._realtime else None

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self._realtime.get("wind_gust_ms") if self._realtime else None

    @property
    def wind_bearing(self) -> float | None:
        return self._realtime.get("wind_direction_deg") if self._realtime else None

    @property
    def native_visibility(self) -> float | None:
        return self._current["visibility_km"] if self._current else None

    @property
    def uv_index(self) -> float | None:
        return self._realtime.get("uv_index") if self._realtime else None

    @property
    def available(self) -> bool:
        return super().available and self._current is not None and self._realtime is not None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        rows = self.coordinator.data.forecast_hourly
        return [_row_to_forecast(row, daily=False) for row in rows] if rows else None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        rows = self.coordinator.data.forecast_daily
        if not rows:
            return None
        forecasts = [_row_to_forecast(row, daily=True) for row in rows]
        _apply_current_high_low(forecasts[0], self._current)
        return forecasts
