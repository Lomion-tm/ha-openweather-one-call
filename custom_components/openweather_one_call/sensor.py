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

from .const import DOMAIN

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


class OpenWeatherOneCallSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, config_entry, sensor_type, forecast_day=None):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._sensor_type = sensor_type
        self._forecast_day = forecast_day

        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        if forecast_day is not None:
            self._attr_unique_id += f"_{forecast_day}d"
            day_suffix = "Today" if forecast_day == 0 else f"in {forecast_day}d"
            self._attr_name = f"{config_entry.data['name']} {SENSOR_TYPES[sensor_type]['description']} {day_suffix}"
        else:
            self._attr_has_entity_name = True
            self._attr_translation_key = sensor_type
             
        self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self.coordinator.data
        if data is None:
            return None

        if self._forecast_day is not None:
            if 'daily' in data and len(data['daily']) > self._forecast_day:
                daily_data = data['daily'][self._forecast_day]
                if self._sensor_type == "daily_pop":
                    return daily_data.get('pop', 0) * 100
                elif self._sensor_type.startswith("daily_temp_"):
                    temp_key = self._sensor_type.replace("daily_temp_", "")
                    return daily_data.get('temp', {}).get(temp_key)
                return daily_data.get(self._sensor_type)
        else:
            if 'current' in data:
                if self._sensor_type == "pop":
                    if 'hourly' in data and data['hourly']:
                        return data['hourly'][0].get('pop', 0) * 100
                elif self._sensor_type.startswith("weather_"):
                    weather_key = self._sensor_type.replace("weather_", "")
                    if 'weather' in data['current'] and data['current']['weather']:
                        return data['current']['weather'][0].get(weather_key)
                return data['current'].get(self._sensor_type)
        return None

    @property
    def device_info(self):
        """Link this entity to the device registry."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": self.config_entry.data["name"],
            "manufacturer": "Lomion-tm",
            "model": "One Call API 3.0",
        }
