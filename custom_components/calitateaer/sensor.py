"""Senzori pentru integrarea CalitateAer Romania (RNMCA)."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTRIBUTION,
    POLLUTANTS,
    POLLUTANT_ICONS,
    AQI_LEVELS,
    AQI_LEVELS_EN,
    AQI_ICONS,
    ATTR_STATION_NAME,
    ATTR_STATION_CODE,
    ATTR_NETWORK,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_ALTITUDE,
    ATTR_AQI_LEVEL,
    ATTR_AQI_LABEL,
    ATTR_MEASUREMENT_TIME,
    ATTR_AVERAGING_PERIOD,
)
from .coordinator import CalitateAerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapare unitate API -> constantă HA
UNIT_MAP = {
    "µg/m³": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    "mg/m³": CONCENTRATION_MILLIGRAMS_PER_CUBIC_METER,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurare senzori din config entry."""
    coordinator: CalitateAerDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    stations_data = coordinator.data.get("stations", {})

    if not stations_data:
        _LOGGER.warning(
            "Nu s-au găsit date pentru stații pentru a crea senzori"
        )
        return

    entities = []

    for station_id, station_data in stations_data.items():
        station_info = station_data.get("info", {})
        latest = station_data.get("latest", {})

        # Senzor AQI General per stație
        entities.append(
            CalitateAerAQISensor(
                coordinator, entry, station_id, station_info
            )
        )

        # Senzori per poluant (doar pentru cei care au date)
        for pollutant_name in POLLUTANTS:
            # Creăm senzor chiar dacă nu are date încă
            # (stația poate să nu raporteze toți poluanții)
            if pollutant_name in latest or _station_has_parameter(
                station_info, pollutant_name
            ):
                entities.append(
                    CalitateAerPollutantSensor(
                        coordinator,
                        entry,
                        station_id,
                        station_info,
                        pollutant_name,
                    )
                )

    async_add_entities(entities)
    _LOGGER.info("Au fost creați %d senzori CalitateAer", len(entities))


def _station_has_parameter(
    station_info: Dict[str, Any], param_name: str
) -> bool:
    """Verifică dacă o stație are un anumit parametru în configurare."""
    parameters = station_info.get("parameters", [])
    for param in parameters:
        if isinstance(param, dict):
            if param.get("name", "") == param_name:
                return True
        elif isinstance(param, str):
            if param == param_name:
                return True
    return False


class CalitateAerBaseSensor(CoordinatorEntity, SensorEntity):
    """Senzor de bază pentru CalitateAer."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CalitateAerDataUpdateCoordinator,
        entry: ConfigEntry,
        station_id: str,
        station_info: Dict[str, Any],
    ) -> None:
        """Inițializare senzor de bază."""
        super().__init__(coordinator)
        self.entry = entry
        self.station_id = station_id
        self._station_info = station_info
        self._station_name = station_info.get("name", "Necunoscut")
        self._station_code = station_info.get("code", "")
        self._network = station_info.get("network", "")

    def _get_station_data(self) -> Dict[str, Any]:
        """Obține datele stației din coordinator."""
        stations = self.coordinator.data.get("stations", {})
        return stations.get(self.station_id, {})

    def _get_latest(self) -> Dict[str, Any]:
        """Obține cele mai recente măsurători."""
        station_data = self._get_station_data()
        return station_data.get("latest", {})

    @property
    def device_info(self) -> Dict[str, Any]:
        """Informații despre device (grupare senzori per stație)."""
        info = {
            "identifiers": {
                (DOMAIN, f"{self.entry.entry_id}_{self.station_id}")
            },
            "name": f"CalitateAer {self._station_name}",
            "manufacturer": "RNMCA",
            "model": "Stație Monitorizare Calitate Aer",
            "entry_type": "service",
        }

        # Adăugăm configurarea stației dacă avem coordonate
        lat = self._station_info.get("latitude")
        lon = self._station_info.get("longitude")
        if lat is not None and lon is not None:
            info["configuration_url"] = (
                f"https://calitateaer.ro"
            )

        return info


class CalitateAerAQISensor(CalitateAerBaseSensor):
    """Senzor pentru indexul general al calității aerului (AQI)."""

    _attr_icon = "mdi:air-filter"

    def __init__(
        self,
        coordinator: CalitateAerDataUpdateCoordinator,
        entry: ConfigEntry,
        station_id: str,
        station_info: Dict[str, Any],
    ) -> None:
        """Inițializare senzor AQI."""
        super().__init__(coordinator, entry, station_id, station_info)
        self._attr_name = "Index Calitate Aer"
        self._attr_unique_id = (
            f"{entry.entry_id}_{station_id}_aqi"
        )

    @property
    def native_value(self) -> Optional[int]:
        """Returnează indexul AQI general (1-6)."""
        latest = self._get_latest()
        aqi_data = latest.get("General AQI", {})
        if aqi_data:
            return aqi_data.get("index")
        return None

    @property
    def icon(self) -> str:
        """Icon dinamic bazat pe nivelul AQI."""
        value = self.native_value
        if value and value in AQI_ICONS:
            return AQI_ICONS[value]
        return "mdi:air-filter"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Atribute adiționale."""
        latest = self._get_latest()
        aqi_data = latest.get("General AQI", {})

        attrs = {
            ATTR_STATION_NAME: self._station_name,
            ATTR_STATION_CODE: self._station_code,
            ATTR_NETWORK: self._network,
        }

        # Coordonate GPS
        lat = self._station_info.get("latitude")
        lon = self._station_info.get("longitude")
        alt = self._station_info.get("altitude")
        if lat is not None:
            attrs[ATTR_LATITUDE] = lat
        if lon is not None:
            attrs[ATTR_LONGITUDE] = lon
        if alt is not None:
            attrs[ATTR_ALTITUDE] = alt

        if aqi_data:
            index = aqi_data.get("index")
            if index:
                attrs[ATTR_AQI_LEVEL] = index
                attrs[ATTR_AQI_LABEL] = AQI_LEVELS.get(index, "Necunoscut")
                attrs["aqi_label_en"] = AQI_LEVELS_EN.get(index, "Unknown")
            attrs[ATTR_MEASUREMENT_TIME] = aqi_data.get("timestamp")

        # Adăugăm indexul AQI per poluant
        for pollutant_name in POLLUTANTS:
            poll_data = latest.get(pollutant_name, {})
            if poll_data and poll_data.get("index") is not None:
                attrs[f"{pollutant_name}_aqi"] = poll_data.get("index")
                attrs[f"{pollutant_name}_aqi_label"] = poll_data.get(
                    "index_label", ""
                )

        return attrs


class CalitateAerPollutantSensor(CalitateAerBaseSensor):
    """Senzor pentru un poluant specific (PM2.5, PM10, SO2, NO2, O3, CO)."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: CalitateAerDataUpdateCoordinator,
        entry: ConfigEntry,
        station_id: str,
        station_info: Dict[str, Any],
        pollutant_name: str,
    ) -> None:
        """Inițializare senzor poluant."""
        super().__init__(coordinator, entry, station_id, station_info)
        self._pollutant_name = pollutant_name
        self._attr_name = pollutant_name
        self._attr_unique_id = (
            f"{entry.entry_id}_{station_id}_{pollutant_name.lower().replace('.', '_')}"
        )

        # Unitatea de măsură
        unit = POLLUTANTS.get(pollutant_name, "µg/m³")
        self._attr_native_unit_of_measurement = UNIT_MAP.get(unit, unit)

        # Device class - HA are device class pentru anumite concentrații
        if pollutant_name in ("PM2.5", "PM10"):
            self._attr_device_class = SensorDeviceClass.PM25 if pollutant_name == "PM2.5" else SensorDeviceClass.PM10
        elif pollutant_name == "CO":
            self._attr_device_class = SensorDeviceClass.CO
        elif pollutant_name == "NO2":
            self._attr_device_class = SensorDeviceClass.NITROGEN_DIOXIDE
        elif pollutant_name == "O3":
            self._attr_device_class = SensorDeviceClass.OZONE
        elif pollutant_name == "SO2":
            self._attr_device_class = SensorDeviceClass.SULPHUR_DIOXIDE

        # Icon per poluant
        self._attr_icon = POLLUTANT_ICONS.get(
            pollutant_name, "mdi:molecule"
        )

    @property
    def native_value(self) -> Optional[float]:
        """Returnează concentrația poluantului."""
        latest = self._get_latest()
        poll_data = latest.get(self._pollutant_name, {})
        if poll_data:
            value = poll_data.get("value")
            if value is not None:
                try:
                    return round(float(value), 2)
                except (ValueError, TypeError):
                    return None
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Atribute adiționale."""
        latest = self._get_latest()
        poll_data = latest.get(self._pollutant_name, {})

        attrs = {
            ATTR_STATION_NAME: self._station_name,
            ATTR_STATION_CODE: self._station_code,
            ATTR_NETWORK: self._network,
        }

        if poll_data:
            attrs[ATTR_MEASUREMENT_TIME] = poll_data.get("timestamp")
            attrs[ATTR_AVERAGING_PERIOD] = poll_data.get(
                "averaging_period", ""
            )

            # Index AQI specific poluantului
            index = poll_data.get("index")
            if index is not None:
                attrs[ATTR_AQI_LEVEL] = index
                attrs[ATTR_AQI_LABEL] = AQI_LEVELS.get(
                    index, poll_data.get("index_label", "Necunoscut")
                )

        return attrs
