from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAX_DAILY_REQUESTS,
    DEFAULT_MAX_DAILY_REQUESTS,
    PLATFORMS,
)
from .coordinator import OpenWeatherOneCallApi, OpenWeatherOneCallCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenWeatherMap One Call from a config entry."""
    session = async_get_clientsession(hass)
    api = OpenWeatherOneCallApi(
        session,
        entry.data[CONF_API_KEY],
        entry.data[CONF_LATITUDE],
        entry.data[CONF_LONGITUDE],
    )

    update_interval_seconds = _calculate_update_interval(
        entry.options.get(
            CONF_MAX_DAILY_REQUESTS, entry.data.get(CONF_MAX_DAILY_REQUESTS, DEFAULT_MAX_DAILY_REQUESTS)
        )
    )
    update_interval = timedelta(seconds=update_interval_seconds)

    coordinator = OpenWeatherOneCallCoordinator(hass, api, update_interval)

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def _calculate_update_interval(max_daily_requests: int) -> int:
    """Calculate the update interval in seconds."""
    if max_daily_requests <= 0:
        # Default to a safe interval if the value is invalid
        return 15 * 60

    # Ensure we don't exceed 4 requests per hour (15 minute interval)
    # and we respect the 10 minute minimum from the API provider
    interval = max((24 * 3600) / max_daily_requests, 10 * 60)
    return int(interval)
