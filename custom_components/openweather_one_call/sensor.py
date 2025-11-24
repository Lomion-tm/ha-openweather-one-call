from datetime import datetime, timezone
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    DEGREE,
    UnitOfLength,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UV_INDEX,
)

from .const import DOMAIN, CONF_NAME
from .coordinator import OpenWeatherOneCallCoordinator

SENSOR_TYPES = {
    "current.temp": {"description": "Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "current.feels_like": {"description": "Feels Like Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "current.pressure": {"description": "Pressure", "device_class": SensorDeviceClass.PRESSURE, "unit": UnitOfPressure.HPA, "state_class": SensorStateClass.MEASUREMENT},
    "current.humidity": {"description": "Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "current.dew_point": {"description": "Dew Point", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "current.clouds": {"description": "Cloudiness", "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "current.uvi": {"description": "UV Index", "device_class": None, "unit": UV_INDEX, "state_class": SensorStateClass.MEASUREMENT},
    "current.visibility": {"description": "Visibility", "device_class": None, "unit": UnitOfLength.METERS, "state_class": SensorStateClass.MEASUREMENT},
    "current.wind_speed": {"description": "Wind Speed", "device_class": None, "unit": UnitOfSpeed.METERS_PER_SECOND, "state_class": SensorStateClass.MEASUREMENT},
    "current.wind_deg": {"description": "Wind Degree", "device_class": None, "unit": DEGREE, "state_class": SensorStateClass.MEASUREMENT},
    "current.wind_gust": {"description": "Wind Gust", "device_class": None, "unit": UnitOfSpeed.METERS_PER_SECOND, "state_class": SensorStateClass.MEASUREMENT},
    "current.sunrise": {"description": "Sunrise", "device_class": SensorDeviceClass.TIMESTAMP, "unit": None, "state_class": None},
    "current.sunset": {"description": "Sunset", "device_class": SensorDeviceClass.TIMESTAMP, "unit": None, "state_class": None},
    "current.rain.1h": {"description": "Rain (last 1h)", "device_class": SensorDeviceClass.PRECIPITATION, "unit": "mm/h", "state_class": SensorStateClass.MEASUREMENT}, # Using custom unit string
    "current.snow.1h": {"description": "Snow (last 1h)", "device_class": SensorDeviceClass.PRECIPITATION, "unit": "mm/h", "state_class": SensorStateClass.MEASUREMENT}, # Using custom unit string
    "current.weather.0.main": {"description": "Weather Condition", "device_class": None, "unit": None, "state_class": None},
    "current.weather.0.description": {"description": "Weather Description", "device_class": None, "unit": None, "state_class": None},
    
    # Daily forecast sensors (keys within the daily object)
    "temp.day": {"description": "Daytime Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp.min": {"description": "Minimum Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp.max": {"description": "Maximum Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp.night": {"description": "Nighttime Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp.eve": {"description": "Evening Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp.morn": {"description": "Morning Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "pop": {"description": "Probability of Precipitation", "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    # Current weather sensors
    for sensor_type_key, sensor_config in SENSOR_TYPES.items():
        if sensor_type_key.startswith("current."):
            entities.append(
                OpenWeatherOneCallSensor(
                    coordinator, entry, sensor_type_key,
                    device_class=sensor_config.get("device_class"),
                    state_class=sensor_config.get("state_class"),
                    unit=sensor_config.get("unit"),
                )
            )
        
    # Daily forecast sensors (for today)
    for sensor_type_key, sensor_config in SENSOR_TYPES.items():
        if not sensor_type_key.startswith("current."): # These are our daily forecast keys
            entities.append(
                OpenWeatherOneCallSensor(
                    coordinator, entry, sensor_type_key, # e.g., "temp.day"
                    device_class=sensor_config.get("device_class"),
                    state_class=sensor_config.get("state_class"),
                    unit=sensor_config.get("unit"),
                    forecast_day=0 # Pass forecast_day for daily sensors
                )
            )

    entities.append(
        OpenWeatherOneCallAlertSensor(
            coordinator=coordinator,
            config_entry=entry,
        )
    )

    async_add_entities(entities)


class OpenWeatherOneCallSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OpenWeatherOneCallCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        unit: str | None = None,
        forecast_day: int | None = None,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_translation_key = sensor_type.replace(".", "_")
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._forecast_day = forecast_day

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self.coordinator.data
        if data is None:
            return None

        if self._forecast_day is not None:
            if "daily" not in data or len(data["daily"]) <= self._forecast_day:
                return None
            data = data["daily"][self._forecast_day]

        keys = self._sensor_type.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit() and len(value) > int(key):
                value = value[int(key)]
            else:
                value = None
                break
        
        if self._sensor_type == "pop" and value is not None:
            return value * 100

        if self.device_class == SensorDeviceClass.TIMESTAMP and value is not None:
            return datetime.fromtimestamp(value, tz=timezone.utc)
            
        return value

    @property
    def device_info(self):
        """Link this entity to the device registry."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": self.config_entry.data[CONF_NAME],
            "manufacturer": "Lomion-tm",
            "model": "One Call API 3.0",
        }


class OpenWeatherOneCallAlertSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Weather Alert Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OpenWeatherOneCallCoordinator,
        config_entry: ConfigEntry,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = "weather_alert"
        self._attr_unique_id = f"{config_entry.entry_id}_weather_alert"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and self.coordinator.data.get("alerts"):
            return self.coordinator.data["alerts"][0].get("event")
        return "No active alerts"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data and self.coordinator.data.get("alerts"):
            alert = self.coordinator.data["alerts"][0]
            return {
                "sender_name": alert.get("sender_name"),
                "start": alert.get("start"),
                "end": alert.get("end"),
                "description": alert.get("description"),
            }
        return None

    @property
    def device_info(self):
        """Link this entity to the device registry."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": self.config_entry.data[CONF_NAME],
            "manufacturer": "Lomion-tm",
            "model": "One Call API 3.0",
        }
