# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - UNRELEASED

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
