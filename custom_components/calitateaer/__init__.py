"""Integrarea CalitateAer pentru Home Assistant."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import CalitateAerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configurare componentă din configuration.yaml (nu este folosită)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurare integrare din config entry."""
    _LOGGER.debug(
        "=== CalitateAer: Începem setup pentru entry %s ===",
        entry.entry_id,
    )

    # Inițializăm coordinator-ul
    coordinator = CalitateAerDataUpdateCoordinator(hass, entry)

    # Facem primul refresh de date
    await coordinator.async_config_entry_first_refresh()

    # Stocăm coordinator-ul în hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Înregistrăm platformele (sensor)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug("=== CalitateAer: Setup completat cu succes ===")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Dezinstalare integrare."""
    _LOGGER.debug(
        "=== CalitateAer: Dezinstalăm entry %s ===", entry.entry_id
    )

    # Dezinstalăm platformele
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    if unload_ok:
        # Ștergem coordinator-ul din hass.data
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Închidem sesiunea API (sync — in executor)
        await hass.async_add_executor_job(coordinator.api.close)

    return unload_ok
