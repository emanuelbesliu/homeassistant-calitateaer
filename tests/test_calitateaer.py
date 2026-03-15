"""Tests for the CalitateAer API client."""
from unittest.mock import patch, MagicMock

import pytest

# Tests require homeassistant to be installed; skip if not available
pytest.importorskip("homeassistant")

from custom_components.calitateaer.api import CalitateAerAPI
from custom_components.calitateaer.const import (
    DOMAIN,
    API_URL_SIMPLIFIED_CONFIG,
    POLLUTANTS,
    AQI_LEVELS,
)


class TestCalitateAerAPI:
    """Test suite for CalitateAerAPI."""

    def test_init(self):
        """Test API client initialization."""
        api = CalitateAerAPI("testuser", "testpass")
        assert api._username == "testuser"
        assert api._password == "testpass"
        assert api._config is None
        assert api._stations == []
        api.close()

    @patch("custom_components.calitateaer.api.requests.Session")
    def test_validate_credentials_success(self, mock_session_cls):
        """Test successful credential validation."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "locations": [
                {
                    "id": 1,
                    "name": "Statie Test",
                    "code": "ST1",
                    "networkName": "EPA_IS",
                    "networkId": 10,
                    "latitude": 47.16,
                    "longitude": 27.58,
                    "altitude": 50,
                    "parameters": [],
                }
            ]
        }
        mock_session.get.return_value = mock_response

        api = CalitateAerAPI("testuser", "testpass")
        api._session = mock_session
        result = api.validate_credentials()

        assert result is True
        assert len(api.get_stations()) == 1
        assert api.get_stations()[0]["name"] == "Statie Test"

    @patch("custom_components.calitateaer.api.requests.Session")
    def test_validate_credentials_401(self, mock_session_cls):
        """Test credential validation with 401 response."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response

        api = CalitateAerAPI("baduser", "badpass")
        api._session = mock_session

        with pytest.raises(Exception, match="Credențiale invalide"):
            api.validate_credentials()

    @patch("custom_components.calitateaer.api.requests.Session")
    def test_get_recent_data_for_location(self, mock_session_cls):
        """Test fetching recent data for a location."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "locationId": 1,
            "locationName": "Statie Test",
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
                            "indexLabel": "Good",
                        }
                    ],
                }
            ],
        }
        mock_session.get.return_value = mock_response

        api = CalitateAerAPI("testuser", "testpass")
        api._session = mock_session
        data = api.get_recent_data_for_location(1)

        assert data["locationId"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["parameterName"] == "PM2.5"


class TestConstants:
    """Test suite for constants."""

    def test_domain(self):
        """Test domain constant."""
        assert DOMAIN == "calitateaer"

    def test_pollutants(self):
        """Test pollutants are defined."""
        assert "PM2.5" in POLLUTANTS
        assert "PM10" in POLLUTANTS
        assert "SO2" in POLLUTANTS
        assert "NO2" in POLLUTANTS
        assert "O3" in POLLUTANTS
        assert "CO" in POLLUTANTS
        assert len(POLLUTANTS) == 6

    def test_aqi_levels(self):
        """Test AQI levels are defined."""
        assert len(AQI_LEVELS) == 6
        assert AQI_LEVELS[1] == "Bun"
        assert AQI_LEVELS[6] == "Extrem de slab"
