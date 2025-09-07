"""this is hello_state."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

DOMAIN = "hello_state"
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup."""
    hass.states.set("hello_state.world", "Paulus")

    # return boolean to indicate that initialization was successful
    return True
