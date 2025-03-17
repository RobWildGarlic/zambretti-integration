"""Zambretti Mediterranean Weather Forecast Integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.ERROR)  # Or use logging.INFO for less verbosity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    _LOGGER.warning("✅ async_setup_entry() called for Zambretti.")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # ✅ Forward the entry setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True
    
async def update_listener(hass, entry):
    """Reload the integration when the config entry is updated."""
    _LOGGER.info("✅ async_listener() called for Zambretti.")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration."""
    _LOGGER.info("✅ async_unload_entry() called for Zambretti.")
    if await hass.config_entries.async_forward_entry_unload(entry, "sensor"):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False
    
