"""Constants for the OpenWeatherMap One Call integration."""

from homeassistant.const import Platform

DOMAIN = "openweather_one_call"

# Configuration Keys
CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_MAX_DAILY_REQUESTS = "max_daily_requests"
CONF_NAME = "name"

# Platforms
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Default values
DEFAULT_MAX_DAILY_REQUESTS = 1000

# API
API_ENDPOINT = "https://api.openweathermap.org/data/3.0/onecall"
