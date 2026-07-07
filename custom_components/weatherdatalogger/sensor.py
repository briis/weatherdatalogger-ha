"""Sensor platform for WeatherDataLogger — one device grouping every reading
from the combined_realtime / combined_realtime_stats views (see
weatherdatalogger/database/02_create_tables.sql upstream). Which physical
station (Tempest/Davis/AirLink) actually supplies a given field is resolved
by station_roles on the database side — this integration just reads
whatever combined_realtime hands back.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    LIGHT_LUX,
    PERCENTAGE,
    EntityCategory,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, STATION_DEVICE_NAME
from .coordinator import WeatherDataLoggerCoordinator

CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = "µg/m³"
STRIKES = "strikes"


@dataclass(frozen=True, kw_only=True)
class WeatherDataLoggerSensorDescription(SensorEntityDescription):
    """Adds which coordinator sub-result and dict key a sensor reads from."""

    source: str = "realtime"  # "realtime" or "stats"
    value_fn: Callable[[dict[str, Any]], Any] | None = None


def _get(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda row: row.get(key)


SENSOR_DESCRIPTIONS: tuple[WeatherDataLoggerSensorDescription, ...] = (
    # Temperature & humidity
    WeatherDataLoggerSensorDescription(
        key="air_temperature_c",
        translation_key="air_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("air_temperature_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="relative_humidity_pct",
        translation_key="relative_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("relative_humidity_pct"),
    ),
    WeatherDataLoggerSensorDescription(
        key="dew_point_c",
        translation_key="dew_point",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("dew_point_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="feels_like_c",
        translation_key="feels_like",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("feels_like_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="heat_index_c",
        translation_key="heat_index",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("heat_index_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wind_chill_c",
        translation_key="wind_chill",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("wind_chill_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wet_bulb_c",
        translation_key="wet_bulb",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("wet_bulb_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="indoor_temperature_c",
        translation_key="indoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("indoor_temperature_c"),
    ),
    WeatherDataLoggerSensorDescription(
        key="indoor_humidity_pct",
        translation_key="indoor_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("indoor_humidity_pct"),
    ),
    # Pressure
    WeatherDataLoggerSensorDescription(
        key="station_pressure_mb",
        translation_key="station_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("station_pressure_mb"),
    ),
    WeatherDataLoggerSensorDescription(
        key="sea_level_pressure_mb",
        translation_key="sea_level_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("sea_level_pressure_mb"),
    ),
    WeatherDataLoggerSensorDescription(
        key="pressure_trend",
        translation_key="pressure_trend",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("pressure_trend"),
    ),
    # Wind
    WeatherDataLoggerSensorDescription(
        key="wind_avg_ms",
        translation_key="wind_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("wind_avg_ms"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wind_gust_ms",
        translation_key="wind_gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("wind_gust_ms"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wind_lull_ms",
        translation_key="wind_lull",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("wind_lull_ms"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wind_direction_deg",
        translation_key="wind_direction",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass-outline",
        value_fn=_get("wind_direction_deg"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wind_beaufort",
        translation_key="wind_beaufort",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:windsock",
        value_fn=_get("wind_beaufort"),
    ),
    # Solar & UV
    WeatherDataLoggerSensorDescription(
        key="illuminance_lux",
        translation_key="illuminance",
        device_class=SensorDeviceClass.ILLUMINANCE,
        native_unit_of_measurement=LIGHT_LUX,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("illuminance_lux"),
    ),
    WeatherDataLoggerSensorDescription(
        key="uv_index",
        translation_key="uv_index",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sun-wireless-outline",
        value_fn=_get("uv_index"),
    ),
    WeatherDataLoggerSensorDescription(
        key="solar_radiation_wm2",
        translation_key="solar_radiation",
        device_class=SensorDeviceClass.IRRADIANCE,
        native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("solar_radiation_wm2"),
    ),
    # Rain
    WeatherDataLoggerSensorDescription(
        key="rain_accumulation_mm",
        translation_key="rain_accumulation_today",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_get("rain_accumulation_mm"),
    ),
    WeatherDataLoggerSensorDescription(
        key="rain_rate_mmh",
        translation_key="rain_rate",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("rain_rate_mmh"),
    ),
    # Lightning
    WeatherDataLoggerSensorDescription(
        key="lightning_count_3h",
        translation_key="lightning_count",
        native_unit_of_measurement=STRIKES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:lightning-bolt",
        value_fn=_get("lightning_count_3h"),
    ),
    WeatherDataLoggerSensorDescription(
        key="lightning_min_dist_3h_km",
        translation_key="lightning_distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("lightning_min_dist_3h_km"),
    ),
    WeatherDataLoggerSensorDescription(
        key="lightning_last_detected",
        translation_key="lightning_last_detected",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("lightning_last_detected"),
    ),
    # Air quality (AirLink)
    WeatherDataLoggerSensorDescription(
        key="pm_2p5_ugm3",
        translation_key="pm_2p5",
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("pm_2p5_ugm3"),
    ),
    WeatherDataLoggerSensorDescription(
        key="pm_10_ugm3",
        translation_key="pm_10",
        device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("pm_10_ugm3"),
    ),
    WeatherDataLoggerSensorDescription(
        key="aqi_pm2p5",
        translation_key="aqi_pm2p5",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("aqi_pm2p5"),
    ),
    WeatherDataLoggerSensorDescription(
        key="aqi_pm10",
        translation_key="aqi_pm10",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get("aqi_pm10"),
    ),
    WeatherDataLoggerSensorDescription(
        key="caqi_pm2p5",
        translation_key="caqi_pm2p5",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("caqi_pm2p5"),
    ),
    WeatherDataLoggerSensorDescription(
        key="caqi_pm10",
        translation_key="caqi_pm10",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("caqi_pm10"),
    ),
    # Device
    WeatherDataLoggerSensorDescription(
        key="battery_volts",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get("battery_volts"),
    ),
    # Daily/rolling stats (combined_realtime_stats)
    WeatherDataLoggerSensorDescription(
        key="wind_gust_high_today",
        translation_key="wind_gust_high_today",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        source="stats",
        value_fn=_get("wind_gust_high_today"),
    ),
    WeatherDataLoggerSensorDescription(
        key="wind_bearing_avg_day",
        translation_key="wind_bearing_avg_day",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        source="stats",
        value_fn=_get("wind_bearing_avg_day"),
    ),
    WeatherDataLoggerSensorDescription(
        key="rain_total_yesterday",
        translation_key="rain_total_yesterday",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        source="stats",
        value_fn=_get("rain_total_yesterday"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up station sensors from a config entry."""
    coordinator: WeatherDataLoggerCoordinator = entry.runtime_data
    async_add_entities(
        WeatherDataLoggerSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class WeatherDataLoggerSensor(
    CoordinatorEntity[WeatherDataLoggerCoordinator], SensorEntity
):
    """A single reading from combined_realtime or combined_realtime_stats."""

    entity_description: WeatherDataLoggerSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherDataLoggerCoordinator,
        entry: ConfigEntry,
        description: WeatherDataLoggerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_station")},
            name=STATION_DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model="Merged station readings (combined_realtime)",
        )

    @property
    def _row(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        return data.realtime if self.entity_description.source == "realtime" else data.realtime_stats

    @property
    def native_value(self) -> Any:
        row = self._row
        if row is None or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(row)

    @property
    def available(self) -> bool:
        return super().available and self._row is not None
