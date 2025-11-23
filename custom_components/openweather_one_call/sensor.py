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
    CONCENTRATION_PARTS_PER_MILLION,
    DEGREE,
    LENGTH_METERS,
    PERCENTAGE,
    PRESSURE_HPA,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
    UV_INDEX,
)

from .const import DOMAIN

SENSOR_TYPES = {
    "temp": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "feels_like": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "pressure": {"device_class": SensorDeviceClass.PRESSURE, "unit": PRESSURE_HPA, "state_class": SensorStateClass.MEASUREMENT},
    "humidity": {"device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "dew_point": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "clouds": {"device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "uvi": {"device_class": None, "unit": UV_INDEX, "state_class": SensorStateClass.MEASUREMENT},
    "visibility": {"device_class": None, "unit": LENGTH_METERS, "state_class": SensorStateClass.MEASUREMENT},
    "wind_speed": {"device_class": None, "unit": SPEED_METERS_PER_SECOND, "state_class": SensorStateClass.MEASUREMENT},
    "wind_deg": {"device_class": None, "unit": DEGREE, "state_class": SensorStateClass.MEASUREMENT},
    "wind_gust": {"device_class": None, "unit": SPEED_METERS_PER_SECOND, "state_class": SensorStateClass.MEASUREMENT},
    "weather_main": {"device_class": None, "unit": None, "state_class": None},
    "weather_description": {"device_class": None, "unit": None, "state_class": None},
    "pop": {"device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_day": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_min": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_max": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_night": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_eve": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_temp_morn": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": TEMP_CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "daily_pop": {"device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
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
            self._attr_name = f"{config_entry.data['name']} {sensor_type.replace('_', ' ').title()} {forecast_day}d"
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
            "manufacturer": "OpenWeather",
            "model": "One Call API 3.0",
        }
