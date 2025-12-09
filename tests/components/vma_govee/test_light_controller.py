"""Tests for vma_govee light controller."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.components.vma_govee.light_controller import (
    GoveeLightProvider,
    LightController,
    PatternStep,
)
from homeassistant.core import HomeAssistant


async def test_pattern_execution_logic(hass: HomeAssistant) -> None:
    """Test that run_pattern actually calls the provider correctly."""

    # Create a fake mock provider
    mock_provider = Mock(spec=GoveeLightProvider)
    mock_provider.turn_on = AsyncMock()
    mock_provider.turn_off = AsyncMock()
    mock_provider.set_brightness = AsyncMock()

    # Initialize controller
    controller = LightController(mock_provider, hass)

    # Fake device
    mock_device = "device_1"
    controller.register_device("id_1", mock_device)

    # test pattern
    pattern = [
        PatternStep(duration=0, power=True),
        PatternStep(duration=0, brightness=50),
        PatternStep(duration=0, power=False),
    ]

    # mock discord notification
    with patch.object(controller, "_send_discord_notification", new_callable=AsyncMock):
        await controller.run_pattern(pattern, loop=False)
        await controller._pattern_task

    # verification
    mock_provider.turn_on.assert_called_with(mock_device)
    mock_provider.set_brightness.assert_called_with(mock_device, 50)
    mock_provider.turn_off.assert_called_with(mock_device)


async def test_input_validation() -> None:
    """Test that invalid values raise errors."""
    mock_coordinator = AsyncMock()
    provider = GoveeLightProvider(mock_coordinator)

    # valid brightness
    await provider.set_brightness("device", 50)
    mock_coordinator.set_brightness.assert_called()

    #  invalid brightness
    with pytest.raises(ValueError):
        await provider.set_brightness("device", 0)

    # invalid brightness
    with pytest.raises(ValueError):
        await provider.set_brightness("device", 101)


async def test_pattern_interruption(hass: HomeAssistant) -> None:
    """Test that starting a new pattern stops the previous one."""
    mock_provider = Mock(spec=GoveeLightProvider)
    mock_provider.turn_on = AsyncMock()
    mock_provider.turn_off = AsyncMock()

    controller = LightController(mock_provider, hass)
    controller.register_device("id", "device")

    pattern_1 = [PatternStep(duration=100, power=True)]
    pattern_2 = [PatternStep(duration=0, power=False)]

    with patch.object(controller, "_send_discord_notification", new_callable=AsyncMock):
        await controller.run_pattern(pattern_1, loop=True)
        task_1 = controller._pattern_task
        assert not task_1.done()

        await controller.run_pattern(pattern_2, loop=False)
        task_2 = controller._pattern_task

        await asyncio.sleep(0)
        assert task_1.cancelled() or task_1.done()
        assert task_2 is not task_1

        await task_2

    mock_provider.turn_off.assert_called()
