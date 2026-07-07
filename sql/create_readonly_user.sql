-- Run once on the production weatherdatalogger MariaDB host, as root:
--   mysql -u root weatherdatalogger < sql/create_readonly_user.sql
--
-- Creates a read-only user for this Home Assistant integration. It never
-- writes to the database, so it doesn't need the INSERT/UPDATE privileges
-- the 'weatherlogger' writer user (see ../WeatherDatalogger/weatherdatalogger/
-- database/01_create_database.sql) has.
--
-- Change the password below before running, and update it in Settings ->
-- Devices & Services -> WeatherDataLogger -> Configure afterwards if you
-- ever rotate it.

CREATE USER IF NOT EXISTS 'weatherdatalogger_ha'@'%' IDENTIFIED BY 'CHANGE_ME';

GRANT SELECT ON weatherdatalogger.* TO 'weatherdatalogger_ha'@'%';

FLUSH PRIVILEGES;
