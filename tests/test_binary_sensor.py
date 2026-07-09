"""Tests for the binary sensor description table in binary_sensor.py."""

from custom_components.weatherdatalogger.binary_sensor import BINARY_SENSOR_DESCRIPTIONS

REALTIME_ROW = {"battery_low": 0}


def test_all_descriptions_have_unique_keys() -> None:
    keys = [d.key for d in BINARY_SENSOR_DESCRIPTIONS]
    assert len(keys) == len(set(keys))


def test_all_descriptions_have_value_fn() -> None:
    assert all(d.value_fn is not None for d in BINARY_SENSOR_DESCRIPTIONS)


def test_battery_low_value_fn_reads_matching_row_key() -> None:
    by_key = {d.key: d for d in BINARY_SENSOR_DESCRIPTIONS}

    assert by_key["battery_low"].value_fn(REALTIME_ROW) == 0
    assert by_key["battery_low"].value_fn({}) is None
