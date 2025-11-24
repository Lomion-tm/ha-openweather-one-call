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
    "temp": {"description": "Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "feels_like": {"description": "Feels Like Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "pressure": {"description": "Pressure", "device_class": SensorDeviceClass.PRESSURE, "unit": UnitOfPressure.HPA, "state_class": SensorStateClass.MEASUREMENT},
    "humidity": {"description": "Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "dew_point": {"description": "Dew Point", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "clouds": {"description": "Cloudiness", "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "uvi": {"description": "UV Index", "device_class": None, "unit": UV_INDEX, "state_class": SensorStateClass.MEASUREMENT},
    "visibility": {"description": "Visibility", "device_class": None, "unit": UnitOfLength.METERS, "state_class": SensorStateClass.MEASUREMENT},
    "wind_speed": {"description": "Wind Speed", "device_class": None, "unit": UnitOfSpeed.METERS_PER_SECOND, "state_class": SensorStateClass.MEASUREMENT},
    "wind_deg": {"description": "Wind Degree", "device_class": None, "unit": DEGREE, "state_class": SensorStateClass.MEASUREMENT},
    "wind_gust": {"description": "Wind Gust", "device_class": None, "unit": UnitOfSpeed.METERS_PER_SECOND, "state_class": SensorStateClass.MEASUREMENT},
    "weather_main": {"description": "Weather Condition", "device_class": None, "unit": None, "state_class": None},
    "weather_description": {"description": "Weather Description", "device_class": None, "unit": None, "state_class": None},
    "pop": {"description": "Probability of Precipitation", "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_day": {"description": "Daytime Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_min": {"description": "Minimum Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_max": {"description": "Maximum Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_night": {"description": "Nighttime Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_eve": {"description": "Evening Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_morn": {"description": "Morning Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_pop": {"description": "Probability of Precipitation", "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
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
    for sensor_type in SENSOR_TYPES:
        if sensor_type.startswith("daily_"):
            continue
        entities.append(OpenWeatherOneCallSensor(coordinator, entry, sensor_type))
        
    # Daily forecast sensors (for today)
    for sensor_type in SENSOR_TYPES:
        if sensor_type.startswith("daily_"):
            entities.append(OpenWeatherOneCallSensor(coordinator, entry, sensor_type, forecast_day=0))

    async_add_entities(entities)

    if coordinator.data.get("alerts"):
        async_add_entities(
            [
                OpenWeatherOneCallAlertSensor(
                    coordinator=coordinator,
                    config_entry=entry,
                )
            ]
        )


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
        self._attr_translation_key = sensor_type
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
