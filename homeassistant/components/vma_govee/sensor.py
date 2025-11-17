"""Sensor platform for Govee VMA."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Govee VMA sensor."""
    _LOGGER.warning("Setting up VMA sensor - START")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.warning("Coordinator data: %s", coordinator.data)
    async_add_entities([GoveeVMASensor(coordinator)])
    _LOGGER.warning("Setting up VMA sensor - COMPLETE")


class GoveeVMASensor(CoordinatorEntity, SensorEntity):
    """Representation of a Govee VMA sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "VMA Test Data"
        self._attr_unique_id = "govee_vma_test"
        _LOGGER.warning("Sensor initialized with name: %s", self._attr_name)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = str(self.coordinator.data)
        _LOGGER.warning("Sensor value updated: %s", value)
        return value
