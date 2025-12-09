"""The Govee VMA coordinator."""

from __future__ import annotations

from asyncio import timeout
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ClientError

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoveeVmaApiClient
from .const import DOMAIN, VMA_ALERT_PATTERN
from .light_controller import LightController

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
        discord_webhook_url: str = "",
    ) -> None:
        """Initialize."""
        self.api_client = api_client
        self.light_controller = light_controller
        self.discord_webhook_url = discord_webhook_url
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
        except EXCEPTIONS as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="vma_update_error",
                translation_placeholders={"error": repr(error)},
            ) from error

        return data

    async def _process_vma_data(self, data: dict[str, Any]) -> None:
        """Process VMA data and control lights."""
        await self.light_controller.run_pattern(
            VMA_ALERT_PATTERN, loop=True, loop_count=3
        )
        await self._send_persistent_notification()
        await self._send_discord_notification(data)

    async def _send_persistent_notification(self) -> None:
        """Send a persistent notification in Home Assistant."""
        persistent_notification.async_create(
            self._hass,
            "ALERT: New VMA alert received.",
            "VMA alert",
            notification_id=DOMAIN,
        )

    async def _send_discord_notification(self, data: dict[str, Any]) -> None:
        """Send VMA alert to Discord webhook."""
        # Skip if no webhook URL configured
        if not self.discord_webhook_url:
            _LOGGER.debug("Discord webhook URL not configured, skipping notification")
            return

        try:
            session = async_get_clientsession(self._hass)

            # Extract alerts from the API response (it's a list of alerts)
            if not isinstance(data, list) or not data:
                _LOGGER.debug("No VMA alerts to send")
                return

            embeds = []
            for alert in data:
                # Extract key information from the alert
                headline = alert.get("Headline", "VMA Alert")
                preamble = alert.get("Preamble", "")
                published = alert.get("Published", "")
                event = alert.get("Event", "Alert")
                sender = alert.get("SenderName", "Unknown")
                is_test = alert.get("IsTest", False)
                web_url = alert.get("Web", "")

                # Get affected areas
                areas = alert.get("Area", [])
                area_descriptions = [area.get("Description", "") for area in areas]
                areas_text = (
                    ", ".join(area_descriptions)
                    if area_descriptions
                    else "Unknown area"
                )

                # Build Discord embed
                embed = {
                    "title": f"{'🧪 TEST - ' if is_test else '🚨 '}{headline}",
                    "description": preamble[:4096]
                    if preamble
                    else "No description available",
                    "fields": [
                        {
                            "name": "📍 Affected areas",
                            "value": areas_text[:1024],
                            "inline": False,
                        },
                        {
                            "name": "📅 Published",
                            "value": published,
                            "inline": True,
                        },
                        {
                            "name": "📢 Sender",
                            "value": sender,
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": f"Event: {event} | Identifier: {alert.get('Identifier', 'N/A')}"
                    },
                }

                # Add web link if available
                if web_url:
                    embed["url"] = web_url

                embeds.append(embed)

            payload = {
                "content": "**VMA Alert Notification**"
                if not is_test
                else "**VMA Test Alert**",
                "embeds": embeds[:10],
            }

            async with session.post(
                self.discord_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 204:
                    _LOGGER.debug("Successfully sent Discord notification")
                else:
                    _LOGGER.warning(
                        "Discord webhook returned status %d", response.status
                    )
        except (TimeoutError, aiohttp.ClientError) as ex:
            _LOGGER.error("Failed to send Discord notification: %s", ex)
