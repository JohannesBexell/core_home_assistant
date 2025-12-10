"""Tests for vma_govee coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

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


async def test_discord_notification_sent(
    hass: HomeAssistant, mock_config_entry, mock_vma_api_client
) -> None:
    """Test that Discord notification is sent when webhook URL is configured."""

    mock_light_controller = AsyncMock()

    # Create coordinator with Discord webhook URL
    coordinator = GoveeVmaCoordinator(
        hass,
        mock_config_entry,
        mock_vma_api_client,
        mock_light_controller,
        update_interval=timedelta(seconds=60),
        discord_webhook_url="https://discord.com/api/webhooks/test",
    )

    # Mock VMA data
    mock_vma_data = [
        {
            "Headline": "Test Alert",
            "Preamble": "This is a test alert",
            "Published": "2025-12-10T15:00:00",
            "Event": "TestEvent",
            "SenderName": "Test Sender",
            "IsTest": True,
            "Web": "https://example.com",
            "Area": [{"Description": "Test Area"}],
            "Identifier": "test-123",
        }
    ]
    mock_vma_api_client.async_get_vma_data.return_value = mock_vma_data

    # Mock the HTTP session at the point where coordinator imports it
    with patch(
        "homeassistant.components.vma_govee.coordinator.async_get_clientsession"
    ) as mock_get_session:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_get_session.return_value = mock_session

        await coordinator.async_refresh()

        # Verify Discord webhook was called
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://discord.com/api/webhooks/test"
        assert "json" in call_args[1]
        json_payload = call_args[1]["json"]
        assert "embeds" in json_payload
        assert len(json_payload["embeds"]) == 1
        assert json_payload["embeds"][0]["title"] == "🧪 TEST - Test Alert"


async def test_discord_notification_skipped_when_no_url(
    hass: HomeAssistant, mock_config_entry, mock_vma_api_client
) -> None:
    """Test that Discord notification is skipped when no webhook URL is configured."""

    mock_light_controller = AsyncMock()

    # Create coordinator WITHOUT Discord webhook URL
    coordinator = GoveeVmaCoordinator(
        hass,
        mock_config_entry,
        mock_vma_api_client,
        mock_light_controller,
        update_interval=timedelta(seconds=60),
        discord_webhook_url="",
    )

    mock_vma_data = [{"Headline": "Test Alert"}]
    mock_vma_api_client.async_get_vma_data.return_value = mock_vma_data

    with patch(
        "homeassistant.components.vma_govee.coordinator.async_get_clientsession"
    ) as mock_get_session:
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        await coordinator.async_refresh()

        # Verify Discord webhook was NOT called
        mock_session.post.assert_not_called()


async def test_persistent_notification_created(
    hass: HomeAssistant, mock_config_entry, mock_vma_api_client
) -> None:
    """Test that persistent notification is created on VMA alert."""

    mock_light_controller = AsyncMock()

    coordinator = GoveeVmaCoordinator(
        hass,
        mock_config_entry,
        mock_vma_api_client,
        mock_light_controller,
        update_interval=timedelta(seconds=60),
    )

    mock_vma_data = [{"Headline": "Test Alert"}]
    mock_vma_api_client.async_get_vma_data.return_value = mock_vma_data

    with patch(
        "homeassistant.components.persistent_notification.async_create"
    ) as mock_notify:
        await coordinator.async_refresh()

        # Verify persistent notification was created
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args[0]
        assert call_args[0] == hass
        assert "VMA alert" in call_args[1]
