"""Tests for the sensor description table in sensor.py."""

from custom_components.weatherdatalogger.sensor import SENSOR_DESCRIPTIONS

REALTIME_ROW = {
    "air_temperature_c": 18.4,
    "relative_humidity_pct": 72.0,
    "wind_avg_ms": 2.1,
    "battery_volts": 2.8,
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
    }
