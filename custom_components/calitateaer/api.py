"""
Client API pentru CalitateAer.ro (RNMCA - Rețeaua Națională de Monitorizare a Calității Aerului).

Implementează endpoint-urile din Simplified Data API:
- Configurare (lista stații, parametri, rețele)
- Date recente per rețea sau locație (ultimele 7 zile)

Autentificare: HTTP Basic Auth (username + password obținute de la RNMCA).
"""

import logging
import requests
import urllib3
from typing import Dict, Any, List, Optional

from .const import (
    API_URL_SIMPLIFIED_CONFIG,
    API_URL_SIMPLIFIED_RECENT_NETWORK,
    API_URL_SIMPLIFIED_RECENT_LOCATION,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)


class CalitateAerAPI:
    """Client API pentru CalitateAer.ro (RNMCA)."""

    def __init__(self, username: str, password: str):
        """Inițializare client API."""
        self._username = username
        self._password = password

        # Cache configurare (stații, parametri)
        self._config = None
        self._stations = []

        # Sesiune HTTP cu Basic Auth
        self._session = requests.Session()
        self._session.auth = (self._username, self._password)
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "HomeAssistant-CalitateAer/1.0",
            }
        )

    def validate_credentials(self) -> bool:
        """
        Validează credențialele prin apelarea endpoint-ului de configurare.

        Returns:
            True dacă autentificarea a reușit

        Raises:
            Exception: Dacă credențialele sunt invalide sau serverul nu răspunde
        """
        _LOGGER.debug("CalitateAer: Validăm credențialele API")
        try:
            response = self._session.get(
                API_URL_SIMPLIFIED_CONFIG,
                timeout=30,
            )

            if response.status_code == 401:
                raise Exception(
                    "Credențiale invalide. Verificați username-ul și parola."
                )

            if response.status_code == 403:
                raise Exception(
                    "Acces interzis. Contul nu are permisiuni pentru acest API."
                )

            if response.status_code != 200:
                raise Exception(
                    f"Eroare la conectare: HTTP {response.status_code} - {response.text[:200]}"
                )

            # Parsăm configurarea și o salvăm în cache
            data = response.json()
            self._config = data
            self._parse_stations(data)

            _LOGGER.info(
                "CalitateAer: Autentificare reușită - Găsite %d stații",
                len(self._stations),
            )
            return True

        except requests.exceptions.ConnectionError as err:
            raise Exception(
                f"Nu se poate conecta la calitateaer.ro: {err}"
            ) from err
        except requests.exceptions.Timeout as err:
            raise Exception(
                f"Timeout la conectare cu calitateaer.ro: {err}"
            ) from err

    def _parse_stations(self, config_data: Dict[str, Any]) -> None:
        """
        Extrage lista de stații din configurarea API.

        Simplified config returnează o structură cu:
        - networks: lista de rețele (județe)
        - locations: lista de locații (stații de monitorizare)
        - parameters: lista de parametri măsurați

        Args:
            config_data: Răspunsul JSON de la /simplified/config/all
        """
        stations = []

        # Structura Simplified config: locations conțin stațiile
        locations = config_data.get("locations", [])

        for location in locations:
            station = {
                "id": location.get("id"),
                "name": location.get("name", ""),
                "code": location.get("code", ""),
                "network": location.get("networkName", ""),
                "network_id": location.get("networkId"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "altitude": location.get("altitude"),
                "parameters": location.get("parameters", []),
            }
            stations.append(station)

        self._stations = stations

    def get_stations(self) -> List[Dict[str, Any]]:
        """
        Returnează lista de stații de monitorizare.

        Dacă configurarea nu a fost încărcată, o încarcă automat.

        Returns:
            Lista de stații cu id, name, code, network, lat, lon, altitude, parameters
        """
        if not self._stations:
            self.validate_credentials()
        return self._stations

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Returnează configurarea completă din cache."""
        return self._config

    def get_recent_data_for_location(
        self, location_id: int
    ) -> Dict[str, Any]:
        """
        Obține datele recente (ultimele 7 zile) pentru o locație specifică.

        Folosește Simplified API care returnează date uman-lizibile:
        - Valori măsurate cu unități și timestamp ISO8601
        - Index AQI per poluant și general

        Args:
            location_id: ID-ul locației (stației) din configurare

        Returns:
            Dict cu datele recente pentru locația specificată

        Raises:
            Exception: Dacă cererea eșuează
        """
        url = f"{API_URL_SIMPLIFIED_RECENT_LOCATION}/{location_id}"
        return self._get_request(
            url,
            descriere=f"Date recente pentru locația {location_id}",
        )

    def get_recent_data_for_network(
        self, network_id: int
    ) -> Dict[str, Any]:
        """
        Obține datele recente pentru o rețea întreagă (județ).

        Args:
            network_id: ID-ul rețelei din configurare

        Returns:
            Dict cu datele recente pentru rețeaua specificată
        """
        url = f"{API_URL_SIMPLIFIED_RECENT_NETWORK}/{network_id}"
        return self._get_request(
            url,
            descriere=f"Date recente pentru rețeaua {network_id}",
        )

    def _get_request(
        self,
        url: str,
        descriere: str = "Cerere nedefinită",
    ) -> Dict[str, Any]:
        """
        Execută o cerere GET către API.

        Gestionează automat retry în caz de 401 (session expirat).

        Args:
            url: URL-ul endpoint-ului
            descriere: Descriere pentru logging

        Returns:
            Dict cu răspunsul JSON decodat

        Raises:
            Exception: Dacă răspunsul nu este 200 OK
        """
        _LOGGER.debug("=== Cerere GET: %s (%s) ===", url, descriere)

        try:
            response = self._session.get(url, timeout=30)

            if response.status_code == 401:
                _LOGGER.warning(
                    "Primim 401 la %s, credențiale invalide sau expirate",
                    descriere,
                )
                raise Exception(
                    f"Autentificare eșuată la {descriere}: HTTP 401"
                )

            if response.status_code != 200:
                _LOGGER.error(
                    "Eroare la %s: Status %d - %s",
                    descriere,
                    response.status_code,
                    response.text[:200],
                )
                raise Exception(
                    f"Eroare la {descriere}: {response.status_code}"
                )

            return response.json()

        except requests.exceptions.ConnectionError as err:
            raise Exception(
                f"Nu se poate conecta la calitateaer.ro: {err}"
            ) from err
        except requests.exceptions.Timeout as err:
            raise Exception(
                f"Timeout la {descriere}: {err}"
            ) from err

    def close(self) -> None:
        """Închide sesiunea HTTP."""
        self._session.close()
        _LOGGER.debug("Sesiune CalitateAer închisă")
