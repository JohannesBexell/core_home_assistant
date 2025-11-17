"""The Govee VMA coordinator."""

from __future__ import annotations

from asyncio import timeout
from datetime import timedelta
import logging
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError, ClientError

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoveeVmaApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

EXCEPTIONS = (ClientError, ClientConnectorError)


type GoveeVmaConfigEntry = ConfigEntry[GoveeVmaCoordinator]


class GoveeVmaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Govee VMA data from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: GoveeVmaConfigEntry,
        api_client: GoveeVmaApiClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.api_client = api_client
        self.device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Krisinformation",
            name="VMA Alerts",
            configuration_url="https://api.krisinformation.se/",
        )
        self._hass = hass

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Govee VMA",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data."""
        try:
            async with timeout(10):
                data = await self.api_client.async_get_vma_data()
                self._send_notification(data)
        except EXCEPTIONS as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="vma_update_error",
                translation_placeholders={"error": repr(error)},
            ) from error

        return data

    def _send_notification(self, data: dict[str, Any]) -> None:
        """Send notification to home assistant."""
        persistent_notification.create(self._hass, "Yay!", title="VMA API Response")
