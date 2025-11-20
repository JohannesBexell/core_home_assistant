"""Mock Govee coordinator."""

import logging

_LOGGER = logging.getLogger(__name__)


class MockGoveeDevice:
    """Mock Govee device."""

    def __init__(self, name: str) -> None:
        """Initialize the mock device."""
        self.name = name
        self.is_on = False
        self.brightness = 0
        self.color = (0, 0, 0)

    async def turn_on(self) -> None:
        """Turn on the light."""
        self.is_on = True
        _LOGGER.debug("%s turned on", self.name)

    async def turn_off(self) -> None:
        """Turn off the light."""
        self.is_on = False
        _LOGGER.debug("%s turned off", self.name)

    async def set_brightness(self, brightness: int) -> None:
        """Set light brightness."""
        self.brightness = brightness
        _LOGGER.debug("%s brightness set to %d", self.name, brightness)

    async def set_rgb_color(self, red: int, green: int, blue: int) -> None:
        """Set light RGB color."""
        self.color = (red, green, blue)
        _LOGGER.debug("%s color set to RGB(%d, %d, %d)", self.name, red, green, blue)


class MockGoveeCoordinator:
    """Mocked Govee Coordinator."""

    async def turn_on(self, device: MockGoveeDevice) -> None:
        """Turn on the light."""
        await device.turn_on()

    async def turn_off(self, device: MockGoveeDevice) -> None:
        """Turn off the light."""
        await device.turn_off()

    async def set_brightness(self, device: MockGoveeDevice, brightness: int) -> None:
        """Set light brightness."""
        await device.set_brightness(brightness)

    async def set_rgb_color(
        self, device: MockGoveeDevice, red: int, green: int, blue: int
    ) -> None:
        """Set light RGB color."""
        await device.set_rgb_color(red, green, blue)
