from datetime import timedelta
import logging
import async_timeout
import aiohttp

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    API_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


class OpenWeatherOneCallApi:
    def __init__(self, session: aiohttp.ClientSession, api_key: str, latitude: float, longitude: float):
        self._session = session
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude

    async def fetch_data(self):
        """Fetch data from API endpoint."""
        params = {
            "lat": self._latitude,
            "lon": self._longitude,
            "appid": self._api_key,
            "units": "metric",  # Use metric units
        }
        async with self._session.get(API_ENDPOINT, params=params) as response:
            if response.status == 401:
                raise ApiAuthError("Invalid API key")
            if response.status != 200:
                raise ApiError(f"Error communicating with API: {response.status}")
            return await response.json()


class OpenWeatherOneCallCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, api: OpenWeatherOneCallApi, update_interval: timedelta):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(10):
                return await self.api.fetch_data()
        except ApiAuthError as err:
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(str(err))
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


class ApiError(Exception):
    """Raised when API returns an error."""


class ApiAuthError(ApiError):
    """Raised when API key is invalid."""
