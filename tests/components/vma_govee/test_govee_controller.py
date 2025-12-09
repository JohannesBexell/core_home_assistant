"""Tests for vma_govee Govee device controller."""

from unittest.mock import AsyncMock

from homeassistant.components.vma_govee.govee_coordinator import GoveeDevice
from homeassistant.core import HomeAssistant


async def test_rgb_color_math(hass: HomeAssistant) -> None:
    """Test that RGB inputs are correctly converted to the Govee integer format."""

    device = GoveeDevice("id", "sku", "name", hass, "apikey")
    device._control_device = AsyncMock(return_value={"code": 200})

    # Red (255, 0, 0)
    # (255 << 16) + 0 + 0 = 16711680
    await device.set_rgb_color(255, 0, 0)

    # Verify the math
    device._control_device.assert_called_with(
        capability_type="devices.capabilities.color_setting",
        instance="colorRgb",
        value=16711680,
    )

    # Blue (0, 0, 255)
    # Expected: 255
    await device.set_rgb_color(0, 0, 255)
    device._control_device.assert_called_with(
        capability_type="devices.capabilities.color_setting",
        instance="colorRgb",
        value=255,
    )

    # Test Random
    await device.set_rgb_color(128, 255, 100)
    device._control_device.assert_called_with(
        capability_type="devices.capabilities.color_setting",
        instance="colorRgb",
        value=8453988,
    )


async def test_brightness_clamping(hass: HomeAssistant) -> None:
    """Test that GoveeDevice clamps brightness to 1-100 range."""
    device = GoveeDevice("id", "sku", "name", hass, "apikey")
    device._control_device = AsyncMock(return_value={"code": 200})

    # 0 should become 1
    await device.set_brightness(0)
    device._control_device.assert_called_with(
        capability_type="devices.capabilities.range", instance="brightness", value=1
    )

    # 150 should become 100
    await device.set_brightness(150)
    device._control_device.assert_called_with(
        capability_type="devices.capabilities.range", instance="brightness", value=100
    )
