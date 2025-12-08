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
from .light_controller import LightController, PatternStep

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
        light_controller: LightController,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.api_client = api_client
        self.light_controller = light_controller
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
                await self._process_vma_data(data)
                await self._send_persistent_notification(
                    "Govee VMA data updated successfully.", "Govee VMA"
                )
        except EXCEPTIONS as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="vma_update_error",
                translation_placeholders={"error": repr(error)},
            ) from error

        return data

    async def _process_vma_data(self, data: dict[str, Any]) -> None:
        """Process VMA data and control lights."""
        pattern = [
            PatternStep(duration=0.5, rgb=(255, 0, 0)),
            PatternStep(duration=0.5, brightness=100),
            PatternStep(duration=0.5, brightness=1),
            PatternStep(duration=0.5, brightness=100),
            PatternStep(duration=0.5, brightness=1),
            PatternStep(duration=0.5, brightness=100),
            PatternStep(duration=0.5, brightness=1),
            PatternStep(duration=0.5, power=False),
        ]
        await self.light_controller.run_pattern(pattern, loop=False)

    async def _send_persistent_notification(
        self, message: str, title: str = "Govee VMA Alert"
    ) -> None:
        """Send a persistent notification in Home Assistant."""
        persistent_notification.async_create(
            self._hass,
            message,
            title,
            notification_id=DOMAIN,
        )
