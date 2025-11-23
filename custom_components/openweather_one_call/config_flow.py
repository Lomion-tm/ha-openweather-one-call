import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_MAX_DAILY_REQUESTS,
    DEFAULT_MAX_DAILY_REQUESTS,
    API_ENDPOINT,
)

async def validate_input(hass, data):
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    params = {
        "lat": data[CONF_LATITUDE],
        "lon": data[CONF_LONGITUDE],
        "appid": data[CONF_API_KEY],
        "exclude": "minutely,hourly,daily,alerts",
    }
    async with session.get(API_ENDPOINT, params=params) as response:
        if response.status == 401:
            raise InvalidAuth
        if response.status != 200:
            raise CannotConnect

    return {"title": data[CONF_NAME]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenWeatherMap One Call."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                unique_id = f"{user_input[CONF_LATITUDE]}-{user_input[CONF_LONGITUDE]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): cv.latitude,
                    vol.Required(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): cv.longitude,
                    vol.Optional(
                        CONF_MAX_DAILY_REQUESTS, default=DEFAULT_MAX_DAILY_REQUESTS
                    ): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MAX_DAILY_REQUESTS,
                        default=self.config_entry.options.get(
                            CONF_MAX_DAILY_REQUESTS,
                            self.config_entry.data.get(
                                CONF_MAX_DAILY_REQUESTS, DEFAULT_MAX_DAILY_REQUESTS
                            ),
                        ),
                    ): int,
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
