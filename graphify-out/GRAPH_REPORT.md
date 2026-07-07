# Graph Report - .  (2026-07-07)

## Corpus Check
- Corpus is ~14,120 words - fits in a single context window. You may not need a graph.

## Summary
- 173 nodes · 233 edges · 20 communities (11 shown, 9 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.62)
- Token cost: 84,147 input · 0 output

## Community Hubs (Navigation)
- Integration Core Setup & Data Flow
- Config Flow & Connection Validation
- Weather Entity Implementation
- CI/CD & Dev Workflow
- Sensor Entity Implementation
- Integration Manifest
- Project Overview & DB Access
- Config Flow Tests
- Weather Forecast Tests
- Integration Setup/Teardown
- Sensor Tests
- Test Fixtures
- Dev Script - develop
- Brand Logo Asset
- Dev Script - lint
- Dev Script - setup
- Dev Script - test
- Test Package Init
- Brand Icon Asset
- License

## God Nodes (most connected - your core abstractions)
1. `WeatherDataLoggerWeather` - 19 edges
2. `WeatherDataLoggerClient` - 16 edges
3. `WeatherDataLoggerCoordinator` - 15 edges
4. `WeatherDataLoggerConfig` - 10 edges
5. `WeatherDataLoggerSensor` - 9 edges
6. `async_setup_entry()` - 7 edges
7. `_async_validate_input()` - 7 edges
8. `_row_to_forecast()` - 7 edges
9. `Test Workflow - test job (lint + pytest)` - 7 edges
10. `custom_components.weatherdatalogger integration package` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Test Workflow - test job (lint + pytest)` --references--> `PyMySQL==1.1.1 runtime dependency`  [EXTRACTED]
  .github/workflows/test.yml → requirements.txt
- `test_row_to_forecast_daily_has_high_low()` --calls--> `_row_to_forecast()`  [EXTRACTED]
  tests/test_weather.py → custom_components/weatherdatalogger/weather.py
- `test_row_to_forecast_hourly()` --calls--> `_row_to_forecast()`  [EXTRACTED]
  tests/test_weather.py → custom_components/weatherdatalogger/weather.py
- `Test Workflow - test job (lint + pytest)` --references--> `ruff lint dependency`  [EXTRACTED]
  .github/workflows/test.yml → requirements_test.txt
- `Validate Workflow - hassfest job` --references--> `custom_components.weatherdatalogger integration package`  [INFERRED]
  .github/workflows/validate.yml → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CI quality gates that must pass before merge (lint, tests, hassfest, HACS)** — github_workflows_test_test_job, github_workflows_validate_hassfest_job, github_workflows_validate_hacs_job [EXTRACTED 1.00]
- **Matching homeassistant / pytest-homeassistant-custom-component version-pin mechanism** — requirements_test_homeassistant_pin, requirements_test_pytest_ha_custom_component_pin, github_dependabot_pip_updates, requirements_test_pinned_pair_rationale [EXTRACTED 1.00]
- **Two-device weather integration model built on WeatherDatalogger DB with polling architecture** — readme_weatherdatalogger_forecast_device, readme_weatherdatalogger_station_device, readme_weatherdatalogger_project, readme_polling_architecture [INFERRED 0.80]

## Communities (20 total, 9 thin omitted)

### Community 0 - "Integration Core Setup & Data Flow"
Cohesion: 0.11
Nodes (19): Connection, Constants for the WeatherDataLogger integration., ConfigEntry, HomeAssistant, DataUpdateCoordinator for the WeatherDataLogger integration., Polls the weatherdatalogger MariaDB database on a fixed interval., WeatherDataLoggerCoordinator, Blocking MariaDB access for the WeatherDataLogger integration.  PyMySQL is synch (+11 more)

### Community 1 - "Config Flow & Connection Validation"
Cohesion: 0.14
Nodes (17): ConfigFlow, ConfigFlowResult, _async_validate_input(), CannotConnect, InvalidAuth, Any, HomeAssistant, Config flow for the WeatherDataLogger integration. (+9 more)

### Community 2 - "Weather Entity Implementation"
Cohesion: 0.11
Nodes (8): async_setup_entry(), AddEntitiesCallback, ConfigEntry, HomeAssistant, Set up the weather entity from a config entry., Weather entity backed by the Visual Crossing forecast tables., WeatherDataLoggerWeather, WeatherEntity

### Community 3 - "CI/CD & Dev Workflow"
Cohesion: 0.18
Nodes (17): Enabled HA core platforms/integrations for local dev, Logger config: custom_components.weatherdatalogger set to debug, Commented-out weatherdatalogger integration config entry, custom_components.weatherdatalogger integration package, Dependabot GitHub Actions Updates, Dependabot pip Updates (Home Assistant group), Test Workflow - test job (lint + pytest), Validate Workflow - hacs job (+9 more)

### Community 4 - "Sensor Entity Implementation"
Cohesion: 0.13
Nodes (13): async_setup_entry(), _get(), AddEntitiesCallback, Any, ConfigEntry, HomeAssistant, Set up station sensors from a config entry., A single reading from combined_realtime or combined_realtime_stats. (+5 more)

### Community 5 - "Integration Manifest"
Cohesion: 0.18
Nodes (10): codeowners, config_flow, documentation, domain, integration_type, iot_class, issue_tracker, name (+2 more)

### Community 6 - "Project Overview & DB Access"
Cohesion: 0.28
Nodes (9): sql/create_readonly_user.sql, Polling (not push-based) architecture rationale, Read-only DB user prerequisite, Repository layout (section), station_roles physical-station assignment concept, WeatherDataLogger Forecast device (weather entity), WeatherDatalogger upstream project, WeatherDataLogger Station device (sensor entities) (+1 more)

### Community 7 - "Config Flow Tests"
Cohesion: 0.31
Nodes (8): HomeAssistant, Tests for the WeatherDataLogger config flow., A valid connection creates a config entry., A connection error is surfaced as a form error, not an exception., A MariaDB access-denied error (1045) maps to invalid_auth., test_user_flow_cannot_connect(), test_user_flow_invalid_auth(), test_user_flow_success()

### Community 8 - "Weather Forecast Tests"
Cohesion: 0.39
Nodes (5): _row_to_forecast(), Forecast, Tests for the forecast-row-to-HA-Forecast mapping in weather.py., test_row_to_forecast_daily_has_high_low(), test_row_to_forecast_hourly()

### Community 9 - "Integration Setup/Teardown"
Cohesion: 0.29
Nodes (7): ConfigType, async_setup(), async_unload_entry(), HomeAssistant, Unload a config entry., YAML setup is not supported — config entries only., WeatherDataLoggerConfigEntry

### Community 11 - "Test Fixtures"
Cohesion: 0.50
Nodes (3): auto_enable_custom_integrations(), Shared fixtures for weatherdatalogger tests., Make custom_components/ discoverable, per pytest-homeassistant-custom-component.

## Knowledge Gaps
- **20 isolated node(s):** `domain`, `name`, `codeowners`, `config_flow`, `documentation` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WeatherDataLoggerCoordinator` connect `Integration Core Setup & Data Flow` to `Weather Entity Implementation`, `Sensor Entity Implementation`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `WeatherDataLoggerClient` connect `Integration Core Setup & Data Flow` to `Config Flow & Connection Validation`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `WeatherDataLoggerWeather` connect `Weather Entity Implementation` to `Integration Core Setup & Data Flow`, `Weather Forecast Tests`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `WeatherDataLoggerClient` (e.g. with `CannotConnect` and `InvalidAuth`) actually correct?**
  _`WeatherDataLoggerClient` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `WeatherDataLoggerCoordinator` (e.g. with `WeatherDataLoggerClient` and `WeatherDataLoggerSnapshot`) actually correct?**
  _`WeatherDataLoggerCoordinator` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `WeatherDataLoggerConfig` (e.g. with `CannotConnect` and `InvalidAuth`) actually correct?**
  _`WeatherDataLoggerConfig` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `The WeatherDataLogger integration — reads a weatherdatalogger MariaDB instance (`, `Set up WeatherDataLogger from a config entry.`, `Unload a config entry.` to the rest of the system?**
  _55 weakly-connected nodes found - possible documentation gaps or missing edges._