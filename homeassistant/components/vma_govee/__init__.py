"""The Govee VMA integration."""

from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Govee VMA from a config entry."""

    async def async_update_data():
        """Fetch data from API."""
        async with (
            aiohttp.ClientSession() as session,
            session.get("https://api.krisinformation.se/v3/testvmas") as response,
        ):
            data = await response.json()
            persistent_notification.create(hass, "Yay!", title="VMA API Response")
            return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Govee VMA",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
