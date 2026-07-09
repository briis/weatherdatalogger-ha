"""Tests for the forecast-row-to-HA-Forecast mapping in weather.py."""

from datetime import UTC, datetime

from custom_components.weatherdatalogger.weather import (
    WeatherDataLoggerWeather,
    _apply_current_high_low,
    _row_to_forecast,
)


class _FakeConfigEntry:
    entry_id = "test_entry"


def test_attribution_credits_visual_crossing() -> None:
    entity = WeatherDataLoggerWeather(coordinator=None, entry=_FakeConfigEntry())

    assert entity.attribution == "Weather data provided by Visual Crossing"


def test_row_to_forecast_hourly() -> None:
    row = {
        "forecast_time": datetime(2026, 7, 7, 12, 0, 0),
        "weather_condition": "partlycloudy",
        "temperature_c": 21.5,
        "wind_speed_ms": 3.2,
        "wind_gust_ms": 5.1,
        "wind_bearing_deg": 180,
        "pressure_mb": 1013.0,
        "humidity_pct": 60.0,
        "uv_index": 4.0,
        "precipitation_probability_pct": 10,
        "precipitation_mm": 0.0,
        "cloud_cover_pct": 40,
    }

    forecast = _row_to_forecast(row, daily=False)

    assert forecast["datetime"] == "2026-07-07T12:00:00+00:00"
    assert forecast["condition"] == "partlycloudy"
    assert forecast["native_temperature"] == 21.5
    assert "native_templow" not in forecast


def test_row_to_forecast_daily_has_high_low() -> None:
    row = {
        "forecast_time": datetime(2026, 7, 7),
        "weather_condition": "sunny",
        "temperature_high_c": 24.0,
        "temperature_low_c": 14.0,
        "wind_speed_ms": None,
        "wind_gust_ms": None,
        "wind_bearing_deg": None,
        "pressure_mb": None,
        "humidity_pct": None,
        "uv_index": None,
        "precipitation_probability_pct": None,
        "precipitation_mm": None,
        "cloud_cover_pct": None,
    }

    forecast = _row_to_forecast(row, daily=True)

    assert forecast["datetime"] == "2026-07-07T00:00:00+00:00"
    assert forecast["native_temperature"] == 24.0
    assert forecast["native_templow"] == 14.0


def test_row_to_forecast_keeps_existing_tzinfo() -> None:
    row = {
        "forecast_time": datetime(2026, 7, 7, 12, 0, 0, tzinfo=UTC),
        "weather_condition": "sunny",
        "temperature_c": 21.5,
    }

    forecast = _row_to_forecast(row, daily=False)

    assert forecast["datetime"] == "2026-07-07T12:00:00+00:00"


def test_apply_current_high_low_overrides_todays_forecast() -> None:
    forecast = {"native_temperature": 24.0, "native_templow": 14.0}
    current = {"temperature_high_c": 25.5, "temperature_low_c": 13.5}

    _apply_current_high_low(forecast, current)

    assert forecast["native_temperature"] == 25.5
    assert forecast["native_templow"] == 13.5


def test_apply_current_high_low_keeps_forecast_when_current_missing_fields() -> None:
    forecast = {"native_temperature": 24.0, "native_templow": 14.0}
    current = {"temperature_high_c": None, "temperature_low_c": None}

    _apply_current_high_low(forecast, current)

    assert forecast["native_temperature"] == 24.0
    assert forecast["native_templow"] == 14.0


def test_apply_current_high_low_keeps_forecast_when_no_current_row() -> None:
    forecast = {"native_temperature": 24.0, "native_templow": 14.0}

    _apply_current_high_low(forecast, None)

    assert forecast["native_temperature"] == 24.0
    assert forecast["native_templow"] == 14.0
