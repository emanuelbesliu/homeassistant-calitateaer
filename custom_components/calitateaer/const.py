"""Constante pentru integrarea CalitateAer Romania (RNMCA)."""

DOMAIN = "calitateaer"

# Adresa de bază API
API_BASE_URL = "https://calitateaer.ro:8443"

# Endpoint-uri API — Modul Simplificat (Simplified Data API)
API_URL_SIMPLIFIED_CONFIG = f"{API_BASE_URL}/airquality/simplified/config/all"
API_URL_SIMPLIFIED_RECENT_NETWORK = (
    f"{API_BASE_URL}/airquality/simplified/data/recent/network"
)
API_URL_SIMPLIFIED_RECENT_LOCATION = (
    f"{API_BASE_URL}/airquality/simplified/data/recent/location"
)

# Endpoint-uri API — Modul AQI (Air Quality Index API)
API_URL_AQI_CONFIG = f"{API_BASE_URL}/airquality/aqi/config"
API_URL_AQI_RECENT = f"{API_BASE_URL}/airquality/aqi/data/recent"

# Valori implicite
DEFAULT_UPDATE_INTERVAL = 3600  # în secunde (1 oră)
MIN_UPDATE_INTERVAL = 600  # 10 minute
MAX_UPDATE_INTERVAL = 86400  # 24 ore

# Chei de configurare
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_STATIONS = "stations"

# Poluanți monitorizați (din Simplified API)
# Cheile corespund numelor din API, valorile sunt unitățile de măsură
POLLUTANTS = {
    "PM2.5": "µg/m³",
    "PM10": "µg/m³",
    "SO2": "µg/m³",
    "NO2": "µg/m³",
    "O3": "µg/m³",
    "CO": "mg/m³",
}

# Parametri meteorologici (opționali, din Simplified API)
METEO_PARAMS = {
    "Temperature": "°C",
    "Relative humidity": "%",
    "Atmospheric pressure": "hPa",
    "Wind speed": "m/s",
    "Wind direction": "°",
    "Solar radiation": "W/m²",
    "Precipitation": "mm",
}

# Niveluri AQI conform legislației românești
# https://calitateaer.ro — 6 nivele
AQI_LEVELS = {
    1: "Bun",  # Good
    2: "Acceptabil",  # Acceptable
    3: "Moderat",  # Moderate
    4: "Slab",  # Poor
    5: "Foarte slab",  # Very Poor
    6: "Extrem de slab",  # Extremely Poor
}

AQI_LEVELS_EN = {
    1: "Good",
    2: "Acceptable",
    3: "Moderate",
    4: "Poor",
    5: "Very Poor",
    6: "Extremely Poor",
}

# Mapare icon MDI per nivel AQI
AQI_ICONS = {
    1: "mdi:emoticon-happy",
    2: "mdi:emoticon-neutral",
    3: "mdi:emoticon-sad",
    4: "mdi:emoticon-angry",
    5: "mdi:emoticon-dead",
    6: "mdi:skull-crossbones",
}

# Mapare icon MDI per poluant
POLLUTANT_ICONS = {
    "PM2.5": "mdi:blur",
    "PM10": "mdi:blur-linear",
    "SO2": "mdi:molecule",
    "NO2": "mdi:molecule",
    "O3": "mdi:weather-sunny-alert",
    "CO": "mdi:molecule-co",
}

# Atribute senzori
ATTR_STATION_NAME = "station_name"
ATTR_STATION_CODE = "station_code"
ATTR_NETWORK = "network"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_ALTITUDE = "altitude"
ATTR_AQI_LEVEL = "aqi_level"
ATTR_AQI_LABEL = "aqi_label"
ATTR_POLLUTANT = "pollutant"
ATTR_MEASUREMENT_TIME = "measurement_time"
ATTR_AVERAGING_PERIOD = "averaging_period"

# Mesaje
ATTRIBUTION = "Date furnizate de RNMCA - Rețeaua Națională de Monitorizare a Calității Aerului"
