"""Constants for the Govee VMA integration."""

from .light_controller import PatternStep

DOMAIN = "vma_govee"
CONF_DISCORD_WEBHOOK_URL = "discord_webhook_url"

# Default alert pattern for VMA notifications
VMA_ALERT_PATTERN = [
    PatternStep(duration=0.5, rgb=(255, 0, 0)),
    PatternStep(duration=0.5, brightness=100),
    PatternStep(duration=0.5, brightness=1),
    PatternStep(duration=0.5, brightness=100),
    PatternStep(duration=0.5, brightness=1),
    PatternStep(duration=0.5, brightness=100),
    PatternStep(duration=0.5, brightness=1),
    PatternStep(duration=0.5, power=False),
]
