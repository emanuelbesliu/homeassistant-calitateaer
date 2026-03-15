"""Config flow pentru CalitateAer Romania (RNMCA)."""
import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import CalitateAerAPI
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    CONF_STATIONS,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CalitateAerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow pentru CalitateAer Romania."""

    VERSION = 1

    def __init__(self) -> None:
        """Inițializare config flow."""
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._stations: List[Dict[str, Any]] = []

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Pasul 1: Introducere credențiale (username + password)."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validăm credențialele
                api = CalitateAerAPI(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )

                await self.hass.async_add_executor_job(api.validate_credentials)

                # Salvăm credențialele și lista de stații pentru pasul următor
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                self._stations = api.get_stations()

                await self.hass.async_add_executor_job(api.close)

                # Verificăm dacă nu există deja o intrare cu același username
                await self.async_set_unique_id(self._username)
                self._abort_if_unique_id_configured()

                # Trecem la pasul de selectare stații
                return await self.async_step_stations()

            except Exception as err:
                _LOGGER.error(
                    "Eroare la autentificare CalitateAer: %s", err
                )
                if "401" in str(err) or "invalid" in str(err).lower():
                    errors["base"] = "invalid_auth"
                elif "connect" in str(err).lower() or "timeout" in str(err).lower():
                    errors["base"] = "cannot_connect"
                else:
                    errors["base"] = "unknown"

        # Schema formularului - Pasul 1
        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_stations(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Pasul 2: Selectare stații de monitorizare."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            selected_stations = user_input.get(CONF_STATIONS, [])

            if not selected_stations:
                errors["base"] = "no_stations_selected"
            else:
                # Creăm intrarea de configurare
                return self.async_create_entry(
                    title=f"CalitateAer ({self._username})",
                    data={
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                        CONF_STATIONS: selected_stations,
                        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                    },
                )

        # Construim lista de opțiuni pentru selectare stații
        # Format: {station_id: "Station Name (Network)"}
        station_options = {}
        for station in self._stations:
            station_id = str(station["id"])
            station_name = station.get("name", "Necunoscut")
            network = station.get("network", "")
            label = f"{station_name} ({network})" if network else station_name
            station_options[station_id] = label

        # Sortăm stațiile după nume
        sorted_options = dict(
            sorted(station_options.items(), key=lambda x: x[1])
        )

        # Schema formularului - Pasul 2
        data_schema = vol.Schema(
            {
                vol.Required(CONF_STATIONS): cv.multi_select(sorted_options),
            }
        )

        return self.async_show_form(
            step_id="stations",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Returnează flow-ul de opțiuni."""
        return CalitateAerOptionsFlowHandler(config_entry)


class CalitateAerOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestionează opțiunile pentru CalitateAer."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Inițializare options flow handler."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Gestionează pasul de opțiuni."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Obținem valoarea curentă a intervalului de actualizare
        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(
                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
            ),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=current_interval
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
