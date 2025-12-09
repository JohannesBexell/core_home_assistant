"""Tests for vma_govee coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock

from aiohttp.client_exceptions import ClientError

from homeassistant.components.vma_govee.coordinator import GoveeVmaCoordinator
from homeassistant.core import HomeAssistant


async def test_coordinator_updates_data_and_triggers_lights(
    hass: HomeAssistant, mock_config_entry, mock_vma_api_client
) -> None:
    """Test that the coordinator fetches data and triggers the light controller."""

    # Mock the LightController to verify it gets called
    mock_light_controller = AsyncMock()

    coordinator = GoveeVmaCoordinator(
        hass,
        mock_config_entry,
        mock_vma_api_client,
        mock_light_controller,
        update_interval=timedelta(seconds=60),
    )

    # 1. Test successful update
    mock_vma_api_client.async_get_vma_data.return_value = {"status": "alert"}

    # Manually trigger an update
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    # Verify the light pattern was triggered
    mock_light_controller.run_pattern.assert_called_once()


async def test_coordinator_api_failure(
    hass: HomeAssistant, mock_config_entry, mock_vma_api_client
) -> None:
    """Test the coordinator handles API failures gracefully."""

    mock_light_controller = AsyncMock()

    coordinator = GoveeVmaCoordinator(
        hass,
        mock_config_entry,
        mock_vma_api_client,
        mock_light_controller,
        update_interval=timedelta(seconds=60),
    )

    # Simulate API error
    mock_vma_api_client.async_get_vma_data.side_effect = ClientError("Boom")

    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    # Light pattern should NOT trigger on failure
    mock_light_controller.run_pattern.assert_not_called()
