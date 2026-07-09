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

- **WeatherDataLogger Forecast** — a `weather` entity with hourly and daily forecasts sourced from the Visual Crossing forecast tables (`forecast_hourly` / `forecast_daily`). Most current-condition values come from `combined_realtime` instead — the station's own live reading — with only condition and visibility taken from `forecast_current`, which don't have a `combined_realtime` equivalent.
- **WeatherDataLogger Station** — 36 `sensor` entities plus 1 `binary_sensor` entity, sourced from `combined_realtime` / `combined_realtime_stats`: the latest merged reading regardless of which physical station (Tempest/Davis/AirLink) `station_roles` currently assigns each measurement to.

This integration is **polling, not push-based**: it queries the database on an interval (default 60s, configurable from 15s to 5 minutes — see [Options](#options)) rather than subscribing to MQTT directly, so it stays decoupled from whichever dataloggers happen to be running upstream.

## Entities

### Weather entity — WeatherDataLogger Forecast

A single `weather.*` entity exposing:

- Current condition and visibility from `forecast_current`; temperature, pressure (sea level), humidity, wind speed/gust/bearing, and UV index from `combined_realtime`.
- **Hourly forecast** (temperature, wind, pressure, humidity, UV index, precipitation probability/amount, cloud coverage).
- **Daily forecast** (high/low temperature plus the same fields as hourly). Today's high/low is taken from `forecast_current`, which is refreshed every poll with the actual observed high/low so far — more accurate than the static prediction `forecast_daily` had at midnight.

### Sensor entities — WeatherDataLogger Station

All 36 sensors belong to a single **WeatherDataLogger Station** device. Entities marked **Diagnostic** are grouped separately in the entity list (rather than the main dashboard) since they're more useful for troubleshooting than everyday viewing.

| Sensor | Diagnostic | Description |
|---|---|---|
| **Temperature & humidity** | | |
| Temperature | | Current outdoor air temperature. |
| Humidity | | Current outdoor relative humidity. |
| Dew point | | Temperature at which the air becomes saturated and dew starts to form. |
| Feels like | | Apparent temperature, combining the heat index and wind chill as conditions warrant. |
| Heat index | | Perceived temperature from the combined effect of heat and humidity. |
| Wind chill | | Perceived temperature from the combined effect of wind and cold. |
| Wet bulb | ✓ | Lowest temperature achievable by evaporative cooling at the current conditions. |
| Indoor temperature | | Temperature reported by an indoor sensor (e.g. a console/hub). |
| Indoor humidity | | Relative humidity reported by an indoor sensor. |
| **Pressure** | | |
| Station pressure | ✓ | Raw barometric pressure at the station's altitude, uncorrected for elevation. |
| Sea level pressure | | Barometric pressure adjusted to sea level, so it's comparable across locations. |
| Pressure trend | | Rising / falling / steady trend derived from recent sea level pressure history. |
| Pressure trend value | | Numeric hPa change over the trend window backing the pressure trend sensor. |
| **Wind** | | |
| Wind speed | | Average wind speed over the current sample interval. |
| Wind gust | | Highest wind speed recorded during the current sample interval. |
| Wind lull | | Lowest wind speed recorded during the current sample interval. |
| Wind direction | | Wind direction, in degrees. |
| Wind (Beaufort) | | Wind speed expressed on the Beaufort scale. |
| **Solar & UV** | | |
| Illuminance | | Ambient light level. |
| UV index | | Current UV index. |
| Solar radiation | | Solar irradiance reaching the station. |
| **Rain** | | |
| Rain today | | Rainfall accumulated since local midnight. |
| Rain rate | | Current rainfall intensity. |
| **Lightning** | | |
| Lightning strikes (3h) | ✓ | Number of lightning strikes detected in the trailing 3 hours. |
| Lightning distance | ✓ | Estimated distance to the nearest strike in the trailing 3 hours. |
| Lightning last detected | ✓ | Timestamp of the last detected lightning strike. |
| **Air quality (AirLink)** | | |
| PM2.5 | | Fine particulate matter (≤2.5 µm) concentration. |
| PM10 | | Coarse particulate matter (≤10 µm) concentration. |
| AQI (PM2.5) | | US EPA Air Quality Index derived from PM2.5. |
| AQI (PM10) | | US EPA Air Quality Index derived from PM10. |
| CAQI (PM2.5) | ✓ | European Common Air Quality Index derived from PM2.5. |
| CAQI (PM10) | ✓ | European Common Air Quality Index derived from PM10. |
| **Device** | | |
| Battery voltage | ✓ | The station's reporting battery voltage. Only created if the paired hardware reports it (Tempest does; Davis stations never populate this field, so the entity is skipped rather than added as permanently unavailable). |
| Battery low *(`binary_sensor`, not `sensor`)* | ✓ | On when the station reports a low battery warning. |
| **Daily/rolling stats** | | |
| Wind gust high today | | Highest wind gust recorded since local midnight. |
| Wind bearing average today | | Average wind direction since local midnight. |
| Rain total yesterday | | Total rainfall recorded yesterday. |

> [!NOTE]
> Some sensors are unavailable until the underlying calculation has enough data behind it: the **lightning** sensors stay unset until WeatherDatalogger first detects a strike, and **pressure trend** / **pressure trend value** need up to 3 hours of history after WeatherDatalogger's first start before they report a value.

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
  binary_sensor.py  `binary_sensor` entities (station device)
  brand/            Icon and logo used in Home Assistant and HACS
  strings.json / translations/{en,da}.json   Config/options flow and entity translations
sql/create_readonly_user.sql   Grants for a read-only HA DB user
tests/                         pytest-homeassistant-custom-component tests
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

[MIT](LICENSE) — Copyright (c) 2026 Bjarne Riis.
