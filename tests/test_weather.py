"""Tests for the forecast-row-to-HA-Forecast mapping in weather.py."""

from datetime import datetime

from custom_components.weatherdatalogger.weather import _row_to_forecast


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

    assert forecast["datetime"] == "2026-07-07T12:00:00"
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

    assert forecast["native_temperature"] == 24.0
    assert forecast["native_templow"] == 14.0
