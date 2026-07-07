"""Blocking MariaDB access for the WeatherDataLogger integration.

PyMySQL is synchronous, so every public method here is meant to be called
via hass.async_add_executor_job(...) from async code, never awaited directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pymysql
from pymysql.cursors import DictCursor


@dataclass
class WeatherDataLoggerConfig:
    """Connection settings for a weatherdatalogger MariaDB instance."""

    host: str
    port: int
    database: str
    username: str
    password: str
    location: str


class WeatherDataLoggerClient:
    """Thin synchronous wrapper around the weatherdatalogger database.

    Reads only — this integration never writes to the database, so a
    read-only DB user (see sql/create_readonly_user.sql) is enough.
    """

    def __init__(self, config: WeatherDataLoggerConfig) -> None:
        self._config = config

    def _connect(self) -> pymysql.connections.Connection:
        return pymysql.connect(
            host=self._config.host,
            port=self._config.port,
            db=self._config.database,
            user=self._config.username,
            password=self._config.password,
            cursorclass=DictCursor,
            connect_timeout=10,
            read_timeout=10,
        )

    def test_connection(self) -> None:
        """Raise if the configured credentials can't reach combined_realtime."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM combined_realtime LIMIT 1")

    def fetch_all(self) -> "WeatherDataLoggerSnapshot":
        """Fetch everything the two platforms need in one connection."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM combined_realtime LIMIT 1")
            realtime = cur.fetchone()

            cur.execute("SELECT * FROM combined_realtime_stats LIMIT 1")
            realtime_stats = cur.fetchone()

            cur.execute(
                "SELECT * FROM forecast_current WHERE location = %s",
                (self._config.location,),
            )
            forecast_current = cur.fetchone()

            cur.execute(
                "SELECT * FROM forecast_hourly WHERE location = %s ORDER BY forecast_time ASC",
                (self._config.location,),
            )
            forecast_hourly = list(cur.fetchall())

            cur.execute(
                "SELECT * FROM forecast_daily WHERE location = %s ORDER BY forecast_time ASC",
                (self._config.location,),
            )
            forecast_daily = list(cur.fetchall())

        return WeatherDataLoggerSnapshot(
            realtime=realtime,
            realtime_stats=realtime_stats,
            forecast_current=forecast_current,
            forecast_hourly=forecast_hourly,
            forecast_daily=forecast_daily,
        )


@dataclass
class WeatherDataLoggerSnapshot:
    """Everything fetched from the database in a single poll cycle."""

    realtime: dict[str, Any] | None
    realtime_stats: dict[str, Any] | None
    forecast_current: dict[str, Any] | None
    forecast_hourly: list[dict[str, Any]]
    forecast_daily: list[dict[str, Any]]
