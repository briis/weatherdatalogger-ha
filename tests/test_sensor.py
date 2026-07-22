"""Tests for the sensor description table in sensor.py."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.util import dt as dt_util

from custom_components.weatherdatalogger.sensor import (
    SENSOR_DESCRIPTIONS,
    WEATHER_CONDITIONS,
    _has_initial_value,
)

REALTIME_ROW = {
    "air_temperature_c": 18.4,
    "relative_humidity_pct": 72.0,
    "wind_avg_ms": 2.1,
    "battery_volts": 2.8,
}

FORECAST_CURRENT_ROW = {
    "weather_condition": "partlycloudy",
    "temperature_high_c": 22.5,
    "temperature_low_c": 12.0,
}

# precipitation_probability_pct / precipitation_mm only exist on
# forecast_daily/forecast_hourly rows, not forecast_current — see
# weather.py's _row_to_forecast vs _apply_current_high_low.
FORECAST_DAILY_TODAY_ROW = {
    "precipitation_probability_pct": 30,
    "precipitation_mm": 1.5,
}


def test_all_descriptions_have_unique_keys() -> None:
    keys = [d.key for d in SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys))


def test_all_descriptions_have_value_fn() -> None:
    assert all(d.value_fn is not None for d in SENSOR_DESCRIPTIONS)


def test_value_fn_reads_matching_row_key() -> None:
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}

    assert by_key["air_temperature_c"].value_fn(REALTIME_ROW) == 18.4
    assert by_key["relative_humidity_pct"].value_fn(REALTIME_ROW) == 72.0
    assert by_key["wind_avg_ms"].value_fn(REALTIME_ROW) == 2.1
    # A key absent from the row (e.g. sensor not populated yet) reads as None,
    # not a KeyError.
    assert by_key["dew_point_c"].value_fn(REALTIME_ROW) is None


def test_stats_sources_are_flagged() -> None:
    stats_keys = {d.key for d in SENSOR_DESCRIPTIONS if d.source == "stats"}
    assert stats_keys == {
        "wind_gust_high_today",
        "wind_bearing_avg_day",
        "rain_total_yesterday",
        "air_temp_high_today",
        "air_temp_low_today",
        "wind_speed_avg_10min",
    }


def test_forecast_sources_are_flagged() -> None:
    forecast_keys = {d.key for d in SENSOR_DESCRIPTIONS if d.source == "forecast"}
    assert forecast_keys == {
        "forecast_description",
        "weather_condition",
        "forecast_temperature_high_today",
        "forecast_temperature_low_today",
    }


def test_forecast_daily_today_sources_are_flagged() -> None:
    # precipitation probability/amount live on forecast_daily, not
    # forecast_current — see the comment on FORECAST_DAILY_TODAY_ROW.
    forecast_daily_keys = {d.key for d in SENSOR_DESCRIPTIONS if d.source == "forecast_daily_today"}
    assert forecast_daily_keys == {
        "forecast_precipitation_probability_today",
        "forecast_precipitation_today",
    }


def test_forecast_value_fns_read_matching_row_key() -> None:
    by_key = {d.key: d for d in SENSOR_DESCRIPTIONS}

    assert by_key["weather_condition"].value_fn(FORECAST_CURRENT_ROW) == "partlycloudy"
    assert by_key["forecast_temperature_high_today"].value_fn(FORECAST_CURRENT_ROW) == 22.5
    assert by_key["forecast_temperature_low_today"].value_fn(FORECAST_CURRENT_ROW) == 12.0
    assert (
        by_key["forecast_precipitation_probability_today"].value_fn(FORECAST_DAILY_TODAY_ROW) == 30
    )
    assert by_key["forecast_precipitation_today"].value_fn(FORECAST_DAILY_TODAY_ROW) == 1.5


def test_weather_condition_is_enum_covering_all_ha_conditions() -> None:
    # forecast_current.weather_condition is already an HA-recognized condition
    # string (see weather.py) — the enum sensor's `options` must list every
    # value that column can hold, or HA raises when it doesn't match.
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "weather_condition")
    assert description.device_class == SensorDeviceClass.ENUM
    assert set(description.options or []) == set(WEATHER_CONDITIONS)


def test_only_battery_voltage_is_flagged_skip_if_none() -> None:
    # battery_volts is Tempest-only; Davis stations leave it NULL forever, so
    # it's the only sensor that should be dropped when unpopulated.
    flagged = {d.key for d in SENSOR_DESCRIPTIONS if d.skip_if_none}
    assert flagged == {"battery_volts"}


@dataclass
class _FakeSnapshot:
    realtime: dict[str, Any] | None
    realtime_stats: dict[str, Any] | None = None
    forecast_current: dict[str, Any] | None = None
    forecast_daily: list[dict[str, Any]] | None = None


@dataclass
class _FakeCoordinator:
    data: _FakeSnapshot


def test_has_initial_value_true_when_row_has_value() -> None:
    battery = next(d for d in SENSOR_DESCRIPTIONS if d.key == "battery_volts")
    coordinator = _FakeCoordinator(_FakeSnapshot(realtime={"battery_volts": 2.8}))

    assert _has_initial_value(coordinator, battery) is True


def test_has_initial_value_false_when_row_missing_key() -> None:
    # Davis-derived combined_realtime row: no battery_volts column populated.
    battery = next(d for d in SENSOR_DESCRIPTIONS if d.key == "battery_volts")
    coordinator = _FakeCoordinator(_FakeSnapshot(realtime={"air_temperature_c": 18.4}))

    assert _has_initial_value(coordinator, battery) is False


def test_has_initial_value_false_when_row_is_none() -> None:
    battery = next(d for d in SENSOR_DESCRIPTIONS if d.key == "battery_volts")
    coordinator = _FakeCoordinator(_FakeSnapshot(realtime=None))

    assert _has_initial_value(coordinator, battery) is False


def test_forecast_description_reads_from_forecast_current() -> None:
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "forecast_description")
    assert description.source == "forecast"

    coordinator = _FakeCoordinator(
        _FakeSnapshot(realtime=None, forecast_current={"description": "Partly cloudy"})
    )

    assert _has_initial_value(coordinator, description) is True
    assert description.value_fn(coordinator.data.forecast_current) == "Partly cloudy"


def test_forecast_precipitation_reads_from_first_forecast_daily_row() -> None:
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "forecast_precipitation_today")
    assert description.source == "forecast_daily_today"

    coordinator = _FakeCoordinator(
        _FakeSnapshot(
            realtime=None,
            forecast_daily=[{"precipitation_mm": 1.5}, {"precipitation_mm": 4.0}],
        )
    )

    assert _has_initial_value(coordinator, description) is True


def test_forecast_precipitation_unavailable_when_forecast_daily_empty() -> None:
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "forecast_precipitation_today")

    coordinator = _FakeCoordinator(_FakeSnapshot(realtime=None, forecast_daily=[]))

    assert _has_initial_value(coordinator, description) is False


def test_lightning_last_detected_attaches_utc_to_naive_datetime() -> None:
    # PyMySQL returns naive datetimes for DATETIME columns, but HA's
    # TIMESTAMP device class rejects a naive value outright — the DB stores
    # these as UTC, so mark it explicitly rather than raising.
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "lightning_last_detected")
    naive = datetime(2026, 7, 12, 16, 12, 18)

    result = description.value_fn({"lightning_last_detected": naive})

    assert result == naive.replace(tzinfo=dt_util.UTC)
    assert result.tzinfo is not None


def test_lightning_last_detected_leaves_aware_datetime_untouched() -> None:
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "lightning_last_detected")
    aware = datetime(2026, 7, 12, 16, 12, 18, tzinfo=dt_util.UTC)

    assert description.value_fn({"lightning_last_detected": aware}) == aware


def test_lightning_last_detected_none_stays_none() -> None:
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "lightning_last_detected")

    assert description.value_fn({}) is None
