"""Real Govee coordinator using Govee API."""

from __future__ import annotations

import logging
from typing import Any
import uuid

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

GOVEE_API_URL = "https://openapi.api.govee.com/router/api/v1"


class GoveeDevice:
    """Represents a Govee device."""

    def __init__(
        self,
        device_id: str,
        sku: str,
        name: str,
        hass: HomeAssistant,
        api_key: str,
    ) -> None:
        """Initialize the Govee device."""
        self.device_id = device_id
        self.sku = sku
        self.name = name
        self._hass = hass
        self._api_key = api_key
        self._session = async_get_clientsession(hass)
        self._headers = {
            "Govee-API-Key": api_key,
            "Content-Type": "application/json",
        }
        self.is_on = False
        self.brightness = 0
        self.color = (0, 0, 0)

    async def _control_device(
        self,
        capability_type: str,
        instance: str,
        value: Any,
    ) -> dict[str, Any]:
        """Send control command to the Govee device."""
        url = f"{GOVEE_API_URL}/device/control"

        payload = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": self.sku,
                "device": self.device_id,
                "capability": {
                    "type": capability_type,
                    "instance": instance,
                    "value": value,
                },
            },
        }

        _LOGGER.debug("Sending control command: %s", payload)

        async with self._session.post(
            url,
            json=payload,
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            data = await response.json()
            _LOGGER.debug("Control response: %s", data)

            if response.status == 200 and data.get("code") == 200:
                return data
            _LOGGER.error("Error controlling device: %s", data)
            return data

    async def turn_on(self) -> None:
        """Turn on the light."""
        result = await self._control_device(
            capability_type="devices.capabilities.on_off",
            instance="powerSwitch",
            value=1,
        )
        if result.get("code") == 200:
            self.is_on = True
            _LOGGER.debug("%s turned on", self.name)
        else:
            _LOGGER.error("Failed to turn on %s", self.name)

    async def turn_off(self) -> None:
        """Turn off the light."""
        result = await self._control_device(
            capability_type="devices.capabilities.on_off",
            instance="powerSwitch",
            value=0,
        )
        if result.get("code") == 200:
            self.is_on = False
            _LOGGER.debug("%s turned off", self.name)
        else:
            _LOGGER.error("Failed to turn off %s", self.name)

    async def set_brightness(self, brightness: int) -> None:
        """Set light brightness (1-100, Govee API doesn't accept 0)."""
        # Govee API accepts 1-100, not 0-100. Clamp to valid range.
        clamped_brightness = max(1, min(100, brightness))

        if brightness != clamped_brightness:
            _LOGGER.warning(
                "%s brightness %d out of range, clamped to %d",
                self.name,
                brightness,
                clamped_brightness,
            )

        result = await self._control_device(
            capability_type="devices.capabilities.range",
            instance="brightness",
            value=clamped_brightness,
        )
        if result.get("code") == 200:
            self.brightness = clamped_brightness
            _LOGGER.debug("%s brightness set to %d", self.name, clamped_brightness)
        else:
            _LOGGER.error("Failed to set brightness for %s", self.name)

    async def set_rgb_color(self, red: int, green: int, blue: int) -> None:
        """Set light RGB color."""
        # Convert RGB (0-255 each) to single integer (0-16777215)
        # Formula: (red << 16) | (green << 8) | blue
        color_value = (red << 16) | (green << 8) | blue

        result = await self._control_device(
            capability_type="devices.capabilities.color_setting",
            instance="colorRgb",
            value=color_value,
        )
        if result.get("code") == 200:
            self.color = (red, green, blue)
            _LOGGER.debug(
                "%s color set to RGB(%d, %d, %d) [value: %d]",
                self.name,
                red,
                green,
                blue,
                color_value,
            )
        else:
            _LOGGER.error("Failed to set color for %s", self.name)


class GoveeCoordinator:
    """Real Govee Coordinator that controls devices via API."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        """Initialize the coordinator."""
        self._hass = hass
        self._api_key = api_key
        self._session = async_get_clientsession(hass)
        self._headers = {
            "Govee-API-Key": api_key,
            "Content-Type": "application/json",
        }

    async def turn_on(self, device: GoveeDevice) -> None:
        """Turn on the light."""
        await device.turn_on()

    async def turn_off(self, device: GoveeDevice) -> None:
        """Turn off the light."""
        await device.turn_off()

    async def set_brightness(self, device: GoveeDevice, brightness: int) -> None:
        """Set light brightness."""
        await device.set_brightness(brightness)

    async def set_rgb_color(
        self, device: GoveeDevice, red: int, green: int, blue: int
    ) -> None:
        """Set light RGB color."""
        await device.set_rgb_color(red, green, blue)

    async def get_devices(self) -> list[GoveeDevice]:
        """Get all available Govee devices from the API."""
        url = f"{GOVEE_API_URL}/user/devices"
        _LOGGER.debug("Requesting devices from: %s", url)

        async with self._session.get(
            url,
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            data = await response.json()
            _LOGGER.debug("Devices response: %s", data)

            devices = []
            if response.status == 200 and data.get("code") == 200 and "data" in data:
                for device_data in data["data"]:
                    device = GoveeDevice(
                        device_id=device_data["device"],
                        sku=device_data["sku"],
                        name=device_data.get("deviceName", "Unknown"),
                        hass=self._hass,
                        api_key=self._api_key,
                    )
                    devices.append(device)
                    _LOGGER.info(
                        "Discovered Govee device: %s (SKU: %s)",
                        device.name,
                        device.sku,
                    )
            else:
                _LOGGER.error("Error getting devices: %s", data)

            return devices
