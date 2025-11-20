"""The Govee VMA integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import GoveeVmaApiClient
from .coordinator import GoveeVmaConfigEntry, GoveeVmaCoordinator
from .light_controller import GoveeLightProvider, LightController
from .mock_govee_coordinator import MockGoveeCoordinator, MockGoveeDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: GoveeVmaConfigEntry) -> bool:
    """Set up Govee VMA from a config entry."""

    api_client = GoveeVmaApiClient(hass)

    govee_coordinator = MockGoveeCoordinator()
    govee_provider = GoveeLightProvider(govee_coordinator)
    light_controller = LightController(govee_provider, hass)
    light_controller.register_device("TEST_DEVICE", MockGoveeDevice("TEST_DEVICE"))

    coordinator = GoveeVmaCoordinator(
        hass,
        entry,
        api_client,
        light_controller,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
