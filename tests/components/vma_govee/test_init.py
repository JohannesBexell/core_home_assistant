"""Tests for vma_govee integration setup."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_load_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_govee_coordinator,  # From conftest
    mock_vma_api_client,  # From conftest
) -> None:
    """Test loading and unloading the integration."""
    with (
        patch(
            "homeassistant.components.vma_govee.GoveeCoordinator",
            return_value=mock_govee_coordinator,
        ),
        patch(
            "homeassistant.components.vma_govee.GoveeVmaApiClient",
            return_value=mock_vma_api_client,
        ),
        patch(
            "homeassistant.components.vma_govee.light_controller.LightController._send_discord_notification",
            new_callable=AsyncMock,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state == ConfigEntryState.LOADED

        assert mock_config_entry.runtime_data is not None

        mock_govee_coordinator.get_devices.assert_called_once()

        await hass.config_entries.async_unload(mock_config_entry.entry_id)

        await hass.async_block_till_done()

        assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
