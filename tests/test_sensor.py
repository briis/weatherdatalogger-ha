"""Tests for the sensor description table in sensor.py."""

from dataclasses import dataclass
from typing import Any

from custom_components.weatherdatalogger.sensor import SENSOR_DESCRIPTIONS, _has_initial_value

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


def test_only_battery_voltage_is_flagged_skip_if_none() -> None:
    # battery_volts is Tempest-only; Davis stations leave it NULL forever, so
    # it's the only sensor that should be dropped when unpopulated.
    flagged = {d.key for d in SENSOR_DESCRIPTIONS if d.skip_if_none}
    assert flagged == {"battery_volts"}


@dataclass
class _FakeSnapshot:
    realtime: dict[str, Any] | None
    realtime_stats: dict[str, Any] | None = None


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
