"""Binary sensor platform for WeatherDataLogger — station problem flags read
from combined_realtime (see sensor.py's module docstring for how the
underlying station_roles merge works).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, STATION_DEVICE_NAME
from .coordinator import WeatherDataLoggerCoordinator


@dataclass(frozen=True, kw_only=True)
class WeatherDataLoggerBinarySensorDescription(BinarySensorEntityDescription):
    """Adds which combined_realtime dict key a binary sensor reads from."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[WeatherDataLoggerBinarySensorDescription, ...] = (
    WeatherDataLoggerBinarySensorDescription(
        key="battery_low",
        translation_key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda row: row.get("battery_low"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up station binary sensors from a config entry."""
    coordinator: WeatherDataLoggerCoordinator = entry.runtime_data
    async_add_entities(
        WeatherDataLoggerBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class WeatherDataLoggerBinarySensor(
    CoordinatorEntity[WeatherDataLoggerCoordinator], BinarySensorEntity
):
    """A single flag from combined_realtime."""

    entity_description: WeatherDataLoggerBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherDataLoggerCoordinator,
        entry: ConfigEntry,
        description: WeatherDataLoggerBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        # See the matching comment in sensor.py: suggest an English
        # object_id explicitly so a Danish-language HA instance doesn't
        # slugify the translated name into the entity_id.
        self.entity_id = f"binary_sensor.{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_station")},
            name=STATION_DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model="Merged station readings (combined_realtime)",
        )

    @property
    def _row(self) -> dict[str, Any] | None:
        return self.coordinator.data.realtime

    @property
    def is_on(self) -> bool | None:
        row = self._row
        if row is None or self.entity_description.value_fn is None:
            return None
        value = self.entity_description.value_fn(row)
        return None if value is None else bool(value)

    @property
    def available(self) -> bool:
        return super().available and self._row is not None
