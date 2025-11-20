"""Light controller with provider abstraction for extensibility."""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


@dataclass
class LightState:
    """Represents the state of a light device."""

    is_on: bool
    brightness: int  # 0-100
    color: tuple[int, int, int]  # RGB values (0-255)


class LightProvider(ABC):
    """Abstract base class for light providers."""

    @abstractmethod
    async def turn_on(self, device: Any) -> None:
        """Turn on the light."""

    @abstractmethod
    async def turn_off(self, device: Any) -> None:
        """Turn off the light."""

    @abstractmethod
    async def set_brightness(self, device: Any, brightness: int) -> None:
        """Set light brightness (0-100)."""

    @abstractmethod
    async def set_rgb_color(self, device: Any, red: int, green: int, blue: int) -> None:
        """Set light RGB color (0-255 for each channel)."""

    @abstractmethod
    async def get_state(self, device: Any) -> LightState:
        """Get current light state."""


class GoveeLightProvider(LightProvider):
    """Govee implementation of LightProvider."""

    def __init__(self, coordinator) -> None:
        """Initialize Govee light provider."""
        self._coordinator = coordinator

    async def turn_on(self, device: Any) -> None:
        """Turn on the light."""
        await self._coordinator.turn_on(device)

    async def turn_off(self, device: Any) -> None:
        """Turn off the light."""
        await self._coordinator.turn_off(device)

    async def set_brightness(self, device: Any, brightness: int) -> None:
        """Set light brightness (0-100)."""
        if not 0 <= brightness <= 100:
            raise ValueError(f"Brightness must be between 0 and 100, got {brightness}")
        await self._coordinator.set_brightness(device, brightness)

    async def set_rgb_color(self, device: Any, red: int, green: int, blue: int) -> None:
        """Set light RGB color (0-255 for each channel)."""
        if not all(0 <= c <= 255 for c in (red, green, blue)):
            raise ValueError("RGB values must be between 0 and 255")
        await self._coordinator.set_rgb_color(device, red, green, blue)

    async def get_state(self, device: Any) -> LightState:
        """Get current light state."""
        return LightState(
            is_on=device.is_on,
            brightness=device.brightness,
            color=device.color,
        )


@dataclass
class PatternStep:
    """A single step in a light pattern.

    Each step defines what the light should do and for how long.
    """

    duration: float  # How long to stay in this state (seconds)
    power: bool | None = None  # None = keep current
    brightness: int | None = None  # 0-100, None=keep current
    rgb: tuple[int, int, int] | None = None  # (red, green, blue), None=keep current


Pattern = list[PatternStep]


class LightController:
    """Universal light controller that works with any provider."""

    DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1439971478962573446/IykLFzmlKdoBRf1ZArHjZRTcXFOL7r2BQJYUnOJR-l21oNg9MR5sDav_wns1qb0Bm4rK"

    def __init__(self, provider: LightProvider, hass: HomeAssistant) -> None:
        """Initialize the light controller."""
        self._provider = provider
        self._devices: dict[str, Any] = {}
        self._hass = hass
        self._pattern_task: asyncio.Task | None = None
        self._stop_pattern = False

    def register_device(self, device_id: str, device: Any) -> None:
        """Register a light device with the controller."""
        self._devices[device_id] = device
        _LOGGER.info("Registered device: %s", device_id)

    def unregister_device(self, device_id: str) -> None:
        """Unregister a light device."""
        if device_id in self._devices:
            del self._devices[device_id]
            _LOGGER.info("Unregistered device: %s", device_id)

    def get_device(self, device_id: str) -> Any | None:
        """Get a registered device by ID."""
        return self._devices.get(device_id)

    def list_devices(self) -> list[str]:
        """List all registered device IDs."""
        return list(self._devices.keys())

    async def turn_on(self) -> None:
        """Turn on all lights."""
        for dev_id, device in self._devices.items():
            await self._provider.turn_on(device)
            await self._send_discord_notification(
                {"device_id": dev_id, "action": "turn_on"}
            )

    async def turn_off(self) -> None:
        """Turn off all lights."""
        for dev_id, device in self._devices.items():
            await self._provider.turn_off(device)
            _LOGGER.info("Turned off device: %s", dev_id)

    async def set_brightness(self, brightness: int) -> None:
        """Set brightness for all lights."""
        for dev_id, device in self._devices.items():
            await self._provider.set_brightness(device, brightness)
            _LOGGER.info("Set brightness for device %s to %d", dev_id, brightness)

    async def set_rgb_color(self, red: int, green: int, blue: int) -> None:
        """Set RGB color for all lights."""
        for dev_id, device in self._devices.items():
            await self._provider.set_rgb_color(device, red, green, blue)
            _LOGGER.info(
                "Set color for device %s to RGB(%d, %d, %d)",
                dev_id,
                red,
                green,
                blue,
            )

    async def get_state(self, device_id: str) -> LightState:
        """Get current state of a light device."""
        device = self._devices[device_id]
        return await self._provider.get_state(device)

    async def run_pattern(self, pattern: Pattern, loop: bool = True) -> None:
        """Run a pattern on all lights."""
        # Stop any existing pattern
        await self.stop_pattern()

        # Start new pattern
        self._pattern_task = asyncio.create_task(self._execute_pattern(pattern, loop))

    async def stop_pattern(self) -> None:
        """Stop the currently running pattern."""
        if self._pattern_task and not self._pattern_task.done():
            self._stop_pattern = True
            self._pattern_task.cancel()
            self._pattern_task = None

    async def _execute_pattern(self, pattern: Pattern, loop: bool) -> None:
        """Execute a pattern."""
        try:
            while True:
                for step in pattern:
                    if self._stop_pattern:
                        return

                    await self._apply_step_to_devices(step)
                    await asyncio.sleep(step.duration)

                if not loop:
                    break

        except asyncio.CancelledError:
            _LOGGER.info("Pattern execution cancelled")
            raise

    async def _apply_step_to_devices(self, step) -> None:
        """Apply a pattern step to all devices."""
        for device in self._devices.values():
            if step.power is not None:
                if step.power:
                    await self._provider.turn_on(device)
                else:
                    await self._provider.turn_off(device)

            if step.brightness is not None:
                await self._provider.set_brightness(device, step.brightness)

            if step.rgb is not None:
                await self._provider.set_rgb_color(device, *step.rgb)

            await self._send_discord_notification(
                {
                    "power": step.power,
                    "brightness": step.brightness,
                    "rgb": step.rgb,
                    "duration": step.duration,
                }
            )

    # TEMPORARY TESTING PURPOSES
    async def _send_discord_notification(self, data: dict[str, Any]) -> None:
        try:
            session = async_get_clientsession(self._hass)

            payload = {
                "content": f"Light action performed: ```{data}```",
            }

            async with session.post(
                self.DISCORD_WEBHOOK_URL,
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
