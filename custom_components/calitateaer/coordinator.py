"""Data Update Coordinator pentru CalitateAer."""
import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import CalitateAerAPI
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    CONF_STATIONS,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CalitateAerDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator pentru actualizarea datelor CalitateAer."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Inițializare coordinator."""
        self.entry = entry

        # Inițializăm API-ul
        self.api = CalitateAerAPI(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        )

        # Lista de stații selectate de utilizator
        self._station_ids = entry.data.get(CONF_STATIONS, [])

        # Intervalul de actualizare (implicit 1 oră)
        update_interval = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """
        Actualizează datele de la API.

        Returns:
            Dict cu datele pentru toate stațiile selectate
        """
        try:
            data = await self.hass.async_add_executor_job(
                self._fetch_data
            )
            return data
        except Exception as err:
            _LOGGER.error(
                "Eroare la actualizarea datelor CalitateAer: %s", err
            )
            raise UpdateFailed(
                f"Eroare la actualizarea datelor: {err}"
            ) from err

    def _fetch_data(self) -> Dict[str, Any]:
        """
        Fetch sincron al datelor de la API (rulează în executor).

        Obține configurarea (pentru metadata stații) și datele recente
        pentru fiecare stație selectată.

        Returns:
            Dict structurat cu datele pentru toate stațiile
        """
        _LOGGER.debug(
            "=== CalitateAer Coordinator: Începem actualizarea datelor ==="
        )

        # Ne asigurăm că avem configurarea încărcată (include validare credențiale)
        stations = self.api.get_stations()
        if not stations:
            _LOGGER.warning(
                "Nu s-au găsit stații de monitorizare"
            )
            return {"stations": {}, "config": None}

        # Construim un map station_id -> station_info
        station_map = {}
        for station in stations:
            station_map[station["id"]] = station

        _LOGGER.debug(
            "Actualizăm date pentru %d stații selectate din %d disponibile",
            len(self._station_ids),
            len(stations),
        )

        # Structura de date
        data = {
            "stations": {},
            "config": self.api.get_config(),
        }

        # Pentru fiecare stație selectată, obținem datele recente
        for station_id in self._station_ids:
            station_id_int = int(station_id)
            station_info = station_map.get(station_id_int)

            if not station_info:
                _LOGGER.warning(
                    "Stația %s nu a fost găsită în configurare, sărim",
                    station_id,
                )
                continue

            try:
                location_data = self.api.get_recent_data_for_location(
                    station_id_int
                )

                # Extragem cea mai recentă măsurătoare per parametru
                latest = self._extract_latest_measurements(location_data)

                data["stations"][str(station_id_int)] = {
                    "info": station_info,
                    "raw_data": location_data,
                    "latest": latest,
                }

            except Exception as err:
                _LOGGER.warning(
                    "Eroare la obținerea datelor pentru stația %s (%s): %s",
                    station_info.get("name", station_id),
                    station_id,
                    err,
                )
                # Păstrăm datele vechi dacă există
                if str(station_id_int) not in data["stations"]:
                    data["stations"][str(station_id_int)] = {
                        "info": station_info,
                        "raw_data": None,
                        "latest": {},
                    }

        _LOGGER.debug(
            "=== CalitateAer Coordinator: Actualizare finalizată ==="
        )
        return data

    def _extract_latest_measurements(
        self, location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrage cele mai recente valori de măsurători din datele Simplified API.

        Simplified API returnează date într-un format uman-lizibil.
        Structura tipică a răspunsului:
        {
            "locationId": 123,
            "locationName": "...",
            "data": [
                {
                    "parameterName": "PM2.5",
                    "parameterUnit": "µg/m³",
                    "values": [
                        {
                            "value": 12.3,
                            "timestamp": "2024-01-15T10:00:00",
                            "averagingPeriod": "1h",
                            "index": 1,
                            "indexLabel": "Good"
                        },
                        ...
                    ]
                },
                ...
            ]
        }

        Args:
            location_data: Răspunsul JSON de la simplified/data/recent/location

        Returns:
            Dict mapând numele parametrului la cea mai recentă valoare:
            {
                "PM2.5": {"value": 12.3, "unit": "µg/m³", "timestamp": "...",
                           "index": 1, "index_label": "Good", "averaging": "1h"},
                "General": {"index": 2, "index_label": "Acceptable"},
                ...
            }
        """
        latest = {}

        # Extragem datele per parametru
        param_data = location_data.get("data", [])

        for param in param_data:
            param_name = param.get("parameterName", "")
            param_unit = param.get("parameterUnit", "")
            values = param.get("values", [])

            if not values:
                continue

            # Ultima valoare din listă este cea mai recentă
            # (API returnează în ordine cronologică)
            most_recent = values[-1]

            latest[param_name] = {
                "value": most_recent.get("value"),
                "unit": param_unit,
                "timestamp": most_recent.get("timestamp"),
                "averaging_period": most_recent.get("averagingPeriod", ""),
                "index": most_recent.get("index"),
                "index_label": most_recent.get("indexLabel", ""),
            }

        # Extragem indexul general (AQI) dacă există
        general_index = location_data.get("generalIndex")
        if general_index is not None:
            latest["General AQI"] = {
                "value": None,
                "unit": "",
                "timestamp": location_data.get("timestamp", ""),
                "averaging_period": "",
                "index": general_index.get("index") if isinstance(general_index, dict) else general_index,
                "index_label": general_index.get("indexLabel", "") if isinstance(general_index, dict) else "",
            }

        return latest
