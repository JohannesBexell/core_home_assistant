"""The Govee VMA integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant

from .api import GoveeVmaApiClient
from .coordinator import GoveeVmaConfigEntry, GoveeVmaCoordinator
from .govee_coordinator import GoveeCoordinator
from .light_controller import GoveeLightProvider, LightController

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: GoveeVmaConfigEntry) -> bool:
    """Set up Govee VMA from a config entry."""

    api_key = entry.data.get(CONF_API_KEY, "")

    # Initialize VMA API client (for VMA alerts)
    api_client = GoveeVmaApiClient(hass)

    # Initialize real Govee coordinator with API key
    govee_coordinator = GoveeCoordinator(hass, api_key)

    # Get Govee devices from API
    govee_devices = await govee_coordinator.get_devices()

    # Set up light provider and controller
    govee_provider = GoveeLightProvider(govee_coordinator)
    light_controller = LightController(govee_provider, hass)

    # Register all discovered Govee devices
    for device in govee_devices:
        light_controller.register_device(device.device_id, device)
        _LOGGER.info("Registered Govee device: %s", device.name)

    # Set up VMA coordinator
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
