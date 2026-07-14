# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-07-14

### Added

- The config flow now discovers **forecast location** and **forecast provider** from the database instead of asking for free text: after the connection details are validated, a *Forecast location* dropdown shows the location slugs already found in `forecast_current`/`forecast_hourly`/`forecast_daily`, followed by a *Forecast provider* dropdown scoped to the chosen location. Both default sensibly (`home` / `visualcrossing`) and still accept a typed value for a location or provider that hasn't written any forecast rows yet. The *Forecast provider* step matches the `provider` column added to those same tables upstream in WeatherDatalogger — required now that they key on `(provider, location)` instead of `location` alone, since a second forecast provider configured for the same location would otherwise make `db.py`'s queries match more than one row.

### Changed

- Existing config entries (created before the provider field existed) are migrated automatically on first load after upgrading: a config-entry migration backfills `provider: "visualcrossing"` into the entry's persisted data and bumps it to config flow version 2. No user action is required.
- README's *Prerequisites* section now leads with WeatherDatalogger's own `scripts/create_ha_readonly_user.sh` (idempotent, prompts for the password) for creating the read-only DB user, keeping the manual `sql/create_readonly_user.sql` route as a fallback.

## [0.2.5] - 2026-07-13

### Added

- New *Forecast description* `sensor` entity, reading the `description` field from `forecast_current`. It belongs to the **WeatherDataLogger Forecast** device, alongside the weather entity.

### Changed

- Corrected the Danish translation for *Wind lull* to "Minimum vindhastighed".

### Fixed

- *Lightning last detected* raised `ValueError: ... missing timezone information` and failed to add whenever a strike had actually been recorded, because MariaDB returns its `DATETIME` columns as naive datetimes and Home Assistant's `TIMESTAMP` device class requires timezone-aware ones. The value is now marked as UTC, matching how the forecast entity already handles `forecast_time`.
- Bumped `pytest-homeassistant-custom-component` to 0.13.346 to match `homeassistant==2026.7.2` — the previous pairing (0.13.345 / 2026.7.1) made `pip install -r requirements_test.txt` fail with a dependency conflict once `homeassistant` was upgraded to 2026.7.2.

## [0.2.4] - 2026-07-09

### Changed

- The weather entity's current temperature, pressure, humidity, wind speed/gust/bearing, and UV index now come from `combined_realtime` (the station's own live reading) instead of `forecast_current` (Visual Crossing's). Condition and visibility still come from `forecast_current`, which has no `combined_realtime` equivalent.
- *Dew point*, *Heat index*, *Wind chill*, *Wind lull*, *Wind (Beaufort)*, *Solar radiation*, and *Wind bearing average today* are no longer marked as diagnostic entities.

## [0.2.3] - 2026-07-09

### Added

- New *Battery low* `binary_sensor` entity, reading the `battery_low` field added to `combined_realtime`.
- The weather entity now credits its data source via an `attribution` attribute: "Weather data provided by Visual Crossing".

### Changed

- *Rain values* now has a default display precision of 1 decimal.

### Fixed

- *Battery voltage* is no longer created for stations that never report it (e.g. Davis), instead of being added as a permanently unavailable entity.

## [0.2.2] - 2026-07-08

### Changed

- *Pressure trend* now reads from the sea level pressure trend field instead of station pressure, and a new *Pressure trend value* sensor exposes the underlying mb value. Both are no longer marked as diagnostic entities.
- Documented in the README that lightning sensors stay unavailable until the first detected strike, and pressure trend sensors need up to 3 hours after WeatherDatalogger's first start before they report a value.

## [0.2.1] - 2026-07-08

### Fixed

- Corrected the Danish translations for the *Station pressure* and *Sea level pressure* sensor names.
- Fixed a missing Python path in the dev container configuration.

## [0.2.0] - 2026-07-08

### Added

- **Reconfigure flow**: update the database host, port, credentials, or forecast location for an existing entry from Settings → Devices & Services → entry **⋮** menu → *Reconfigure*, without removing and re-adding the integration. The form is pre-filled with the entry's current values.
- **Options flow**: change the polling interval after setup (15 seconds to 5 minutes, default 60s) from the entry's *Options*. Saving reloads the entry automatically.
- Helper text for every config flow field, and a Danish translation of the config flow, options flow, and entity names, alongside English.

### Changed

- Adjusted display precision for select sensors.

## [0.1.0] - 2026-07-08

### Added

- Initial release: reads the `weatherdatalogger` MariaDB database read-only and exposes it as two Home Assistant devices — a `weather` entity (Visual Crossing forecast) and ~30 station `sensor` entities merged from `combined_realtime` / `combined_realtime_stats`.
- Config flow for setting up the MariaDB connection (host, port, database, credentials, forecast location), validated against the database before the entry is created.
