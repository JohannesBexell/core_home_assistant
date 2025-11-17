"""API client for Govee VMA."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

API_URL = "https://api.krisinformation.se/v3/testvmas"


class GoveeVmaApiClient:
    """API client for Govee VMA."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the API client."""
        self._session = async_get_clientsession(hass)

    async def async_get_vma_data(self) -> dict[str, Any]:
        """Fetch VMA data from the API."""
        async with self._session.get(
            API_URL,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            response.raise_for_status()
            data = await response.json()
            _LOGGER.debug("Successfully fetched VMA data")
            return data
