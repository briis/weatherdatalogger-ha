# weatherdatalogger-ha

Home Assistant custom integration for [WeatherDatalogger](https://github.com/briis/WeatherDatalogger) — reads the `weatherdatalogger` MariaDB database directly (read-only) and exposes it as two devices:

- **WeatherDataLogger Forecast** — a `weather` entity sourced from the Visual Crossing forecast tables (`forecast_current`/`forecast_hourly`/`forecast_daily`), with hourly and daily forecast support.
- **WeatherDataLogger Station** — a set of `sensor` entities sourced from `combined_realtime`/`combined_realtime_stats`, i.e. the latest merged reading regardless of which physical station (Tempest/Davis/AirLink) `station_roles` currently assigns each role to.

This integration is polling, not push-based: it queries the database on a fixed interval (default 60s) rather than subscribing to MQTT directly, so it stays decoupled from whichever dataloggers happen to be running.

## Prerequisites

A read-only DB user, so this integration never needs write access:

```bash
# On the weatherdatalogger production host, edit the password first:
mysql -u root weatherdatalogger < sql/create_readonly_user.sql
```

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
  config_flow.py    UI setup flow (host/port/db/user/pass/location)
  coordinator.py    DataUpdateCoordinator — polls the DB on scan_interval
  db.py             Synchronous PyMySQL access (combined_realtime*, forecast_*)
  weather.py        `weather` entity (forecast device)
  sensor.py         `sensor` entities (station device)
sql/create_readonly_user.sql   Grants for a read-only HA DB user
tests/                         pytest-homeassistant-custom-component tests
```

## License

Not yet decided — treat as all-rights-reserved until a LICENSE file is added.
