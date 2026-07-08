<p align="center">
  <img src="https://github.com/briis/WeatherDatalogger-HA/blob/main/custom_components/weatherdatalogger/brand/logo.png?raw=true" alt="WeatherDataLogger logo" width="360">
</p>

# WeatherDataLogger for Home Assistant

[![Validate](https://github.com/briis/WeatherDatalogger-HA/actions/workflows/validate.yml/badge.svg)](https://github.com/briis/WeatherDatalogger-HA/actions/workflows/validate.yml)
[![Test](https://github.com/briis/WeatherDatalogger-HA/actions/workflows/test.yml/badge.svg)](https://github.com/briis/WeatherDatalogger-HA/actions/workflows/test.yml)
[![GitHub Release](https://img.shields.io/github/release/briis/WeatherDatalogger-HA.svg)](https://github.com/briis/WeatherDatalogger-HA/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/m/briis/WeatherDatalogger-HA.svg)](https://github.com/briis/WeatherDatalogger-HA/commits/main)
[![License](https://img.shields.io/github/license/briis/WeatherDatalogger-HA.svg)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Project Maintenance](https://img.shields.io/badge/maintainer-Bjarne%20Riis-blue.svg)](https://github.com/briis)

A Home Assistant custom integration for [WeatherDatalogger](https://github.com/briis/WeatherDatalogger) — it reads the `weatherdatalogger` MariaDB database directly, **read-only**, and turns it into two Home Assistant devices:

- **WeatherDataLogger Forecast** — a `weather` entity sourced from the Visual Crossing forecast tables (`forecast_current` / `forecast_hourly` / `forecast_daily`), with current conditions plus hourly and daily forecasts.
- **WeatherDataLogger Station** — ~30 `sensor` entities sourced from `combined_realtime` / `combined_realtime_stats`: the latest merged reading regardless of which physical station (Tempest/Davis/AirLink) `station_roles` currently assigns each measurement to.

This integration is **polling, not push-based**: it queries the database on an interval (default 60s, configurable from 15s to 5 minutes — see [Options](#options)) rather than subscribing to MQTT directly, so it stays decoupled from whichever dataloggers happen to be running upstream.

## Entities

### Weather entity — WeatherDataLogger Forecast

A single `weather.*` entity exposing:

- Current condition, temperature, pressure, humidity, wind speed/gust/bearing, visibility, and UV index.
- **Hourly forecast** (temperature, wind, pressure, humidity, UV index, precipitation probability/amount, cloud coverage).
- **Daily forecast** (high/low temperature plus the same fields as hourly). Today's high/low is taken from `forecast_current`, which is refreshed every poll with the actual observed high/low so far — more accurate than the static prediction `forecast_daily` had at midnight.

### Sensor entities — WeatherDataLogger Station

| Category | Sensors |
|---|---|
| Temperature & humidity | Temperature, Humidity, Dew point, Feels like, Heat index, Wind chill, Wet bulb, Indoor temperature, Indoor humidity |
| Pressure | Station pressure, Sea level pressure, Pressure trend |
| Wind | Wind speed, Wind gust, Wind lull, Wind direction, Wind (Beaufort) |
| Solar & UV | Illuminance, UV index, Solar radiation |
| Rain | Rain today, Rain rate |
| Lightning | Lightning strikes (3h), Lightning distance, Lightning last detected |
| Air quality (AirLink) | PM2.5, PM10, AQI (PM2.5), AQI (PM10), CAQI (PM2.5), CAQI (PM10) |
| Device | Battery voltage |
| Daily/rolling stats | Wind gust high today, Wind bearing average today, Rain total yesterday |

Several of these (dew point, heat index, wind chill, wet bulb, station pressure, pressure trend, wind lull, wind Beaufort, solar radiation, lightning\*, CAQI\*, battery voltage, wind bearing average today) are marked as **diagnostic** entities, so they're grouped separately in the entity list rather than cluttering the main dashboard.

## Prerequisites

This integration is a read-only Home Assistant frontend for **[WeatherDatalogger](https://github.com/briis/WeatherDatalogger)** — a separate project that polls your weather station(s) and writes the merged readings and forecast data into a MariaDB database. WeatherDatalogger must already be installed, configured, and running before this add-on has anything to read; see its repository for setup instructions.

Once WeatherDatalogger is running, create a read-only DB user so this integration never needs write access:

```bash
# On the weatherdatalogger production host, edit the password first:
mysql -u root weatherdatalogger < sql/create_readonly_user.sql
```

This grants `SELECT` only on the `weatherdatalogger` database — no `INSERT`/`UPDATE`, unlike the writer user the logger services use.

## Installation

### HACS (recommended)

This repository is structured as a HACS custom integration (see `hacs.json`). Add it as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) in HACS, then install "WeatherDataLogger" from Integrations.

### Manual

Copy `custom_components/weatherdatalogger/` into your Home Assistant `config/custom_components/` directory and restart Home Assistant.

## Configuration

Settings → Devices & Services → Add Integration → **WeatherDataLogger**, then fill in:

| Field | Default | Notes |
|---|---|---|
| Host | — | Address of the MariaDB server |
| Port | `3306` | |
| Database name | `weatherdatalogger` | |
| Username | — | The read-only user created above |
| Password | — | |
| Forecast location | `home` | Must match the `[visualcrossing]` `location` setting in WeatherDatalogger |

Connectivity and credentials are validated against `combined_realtime` before the entry is created. The config flow UI is available in **English and Danish** (`translations/en.json`, `translations/da.json`), following the browser/HA-instance language.

### Reconfigure

If the database host, port, credentials, or forecast location change later, there's no need to remove and re-add the integration: open the entry's **⋮** menu on Settings → Devices & Services and choose **Reconfigure**. The form is pre-filled with the current values, and the underlying config entry is updated and reloaded in place — entity IDs and history are preserved.

### Options

The polling interval can be tuned after setup without removing the entry: entry's **⋮** menu → **Options** (or the settings/cog on newer HA frontends) → **Polling interval**, from 15 seconds up to 5 minutes (300s). Saving reloads the entry automatically so the new interval takes effect immediately.

## Development

This repo's devcontainer installs Home Assistant core + `pytest-homeassistant-custom-component` so you can run a real HA instance against `custom_components/weatherdatalogger` without touching a production HA install.

1. Open this folder in the devcontainer (or run `scripts/setup` locally with Python 3.14+).
2. Run the **"Run Home Assistant"** VS Code task (or `scripts/develop`) — starts HA on [http://localhost:8123](http://localhost:8123) using `config/` as the config dir.
3. Complete onboarding, then Settings -> Devices & Services -> Add Integration -> "WeatherDataLogger", and point it at a reachable weatherdatalogger MariaDB instance (or a local test DB seeded from `../WeatherDatalogger/weatherdatalogger/database/*.sql`).

Other tasks: **"Run tests"** (pytest), **"Lint (ruff)"** (ruff check).

### Keeping up with new Home Assistant releases

`requirements_test.txt` pins `homeassistant==` and `pytest-homeassistant-custom-component==` to the same version — the latter re-exports HA test fixtures/doubles for that exact HA release, so the two must move together. [Dependabot](.github/dependabot.yml) checks weekly and opens a single grouped PR bumping both when a new pair ships on PyPI; CI (`.github/workflows/test.yml` + `validate.yml`) runs hassfest, HACS validation, lint, and tests against it before merge. A weekly scheduled CI run also re-validates against whatever's currently pinned, so a HA-side breaking change surfaces even in the gap before that PR lands.

## Repository layout

```
custom_components/weatherdatalogger/
  __init__.py       Config entry setup/teardown, coordinator wiring
  config_flow.py    UI setup, reconfigure, and options flows (host/port/db/user/pass/location, polling interval)
  coordinator.py    DataUpdateCoordinator — polls the DB on scan_interval
  db.py             Synchronous PyMySQL access (combined_realtime*, forecast_*)
  weather.py        `weather` entity (forecast device)
  sensor.py         `sensor` entities (station device)
  brand/            Icon and logo used in Home Assistant and HACS
  strings.json / translations/{en,da}.json   Config/options flow and entity translations
sql/create_readonly_user.sql   Grants for a read-only HA DB user
tests/                         pytest-homeassistant-custom-component tests
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

[MIT](LICENSE) — Copyright (c) 2026 Bjarne Riis.
