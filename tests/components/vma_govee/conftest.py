"""Fixtures for vma_govee integration tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.vma_govee.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture
def mock_setup_entry():
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.vma_govee.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_govee_coordinator():
    """Mock the GoveeCoordinator to avoid real API calls."""
    with patch(
        "homeassistant.components.vma_govee.config_flow.GoveeCoordinator", autospec=True
    ) as mock_coord_cls:
        coordinator = mock_coord_cls.return_value
        # Mock getting devices successfully
        mock_device = MagicMock()
        mock_device.device_id = "00:11:22:33:44:55"
        mock_device.name = "Test Light"
        coordinator.get_devices = AsyncMock(return_value=[mock_device])
        yield coordinator


@pytest.fixture
def mock_vma_api_client():
    """Mock the VMA API Client."""
    with patch(
        "homeassistant.components.vma_govee.coordinator.GoveeVmaApiClient",
        autospec=True,
    ) as mock_api_cls:
        client = mock_api_cls.return_value
        client.async_get_vma_data = AsyncMock(return_value={"test": "data"})
        yield client


@pytest.fixture
def mock_config_entry(hass: HomeAssistant):
    """Create a mock config entry."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test_api_key"},
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry
