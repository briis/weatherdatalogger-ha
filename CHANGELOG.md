# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-08

### Added

- **Reconfigure flow**: update the database host, port, credentials, or forecast location for an existing entry from Settings → Devices & Services → entry **⋮** menu → *Reconfigure*, without removing and re-adding the integration. The form is pre-filled with the entry's current values.
- **Options flow**: change the polling interval after setup (15 seconds to 5 minutes, default 60s) from the entry's *Options*. Saving reloads the entry automatically.
- Helper text for every config flow field, and a Danish translation of the config flow, options flow, and entity names, alongside English.
- Changed display precision for several sensors.

### Changed

- Adjusted display precision for select sensors.

## [0.1.0] - 2026-07-08

### Added

- Initial release: reads the `weatherdatalogger` MariaDB database read-only and exposes it as two Home Assistant devices — a `weather` entity (Visual Crossing forecast) and ~30 station `sensor` entities merged from `combined_realtime` / `combined_realtime_stats`.
- Config flow for setting up the MariaDB connection (host, port, database, credentials, forecast location), validated against the database before the entry is created.
