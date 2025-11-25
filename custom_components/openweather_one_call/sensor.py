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
from homeassistant.util import dt as dt_util
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
    "sunrise": {"description": "Sunrise", "device_class": SensorDeviceClass.TIMESTAMP, "unit": None, "state_class": None},
    "sunset": {"description": "Sunset", "device_class": SensorDeviceClass.TIMESTAMP, "unit": None, "state_class": None},
    "sunrise_time": {"description": "Sunrise Time", "device_class": None, "unit": None, "state_class": None},
    "sunset_time": {"description": "Sunset Time", "device_class": None, "unit": None, "state_class": None},
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # --- Create sensors for CURRENT conditions ---
    for sensor_type_key, sensor_config in SENSOR_TYPES.items():
        if sensor_type_key.startswith("current."):
            entities.append(
                OpenWeatherOneCallSensor(
                    coordinator,
                    entry,
                    sensor_type=sensor_type_key,
                    device_class=sensor_config.get("device_class"),
                    state_class=sensor_config.get("state_class"),
                    unit=sensor_config.get("unit"),
                )
            )

    # --- Create sensors for DAILY forecasts (Today and Tomorrow) ---
    daily_sensor_keys_to_create = [
        "temp.day", "temp.min", "temp.max", "temp.night", "temp.eve", "temp.morn", "pop",
        "sunrise", "sunset", "sunrise_time", "sunset_time"
    ]

    for day_index in range(2):  # 0 for today, 1 for tomorrow
        for source_key in daily_sensor_keys_to_create:
            if source_key not in SENSOR_TYPES:
                continue

            # Create a unique sensor_type for the entity's unique_id and translation_key
            # e.g., "daily_0_sunrise" or "daily_1_temp_max"
            unique_sensor_type = f"daily_{day_index}_{source_key.replace('.', '_')}"
            sensor_config = SENSOR_TYPES[source_key]

            entities.append(
                OpenWeatherOneCallSensor(
                    coordinator,
                    entry,
                    sensor_type=unique_sensor_type,
                    source_key=source_key,
                    forecast_day=day_index,
                    device_class=sensor_config.get("device_class"),
                    state_class=sensor_config.get("state_class"),
                    unit=sensor_config.get("unit"),
                )
            )

    # --- Create weather alert sensor ---
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
        source_key: str | None = None,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._sensor_type = sensor_type
        self._source_key = source_key
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_translation_key = sensor_type.replace(".", "_")
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._forecast_day = forecast_day

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Use source_key for data lookup if provided, otherwise default to sensor_type
        lookup_key = self._source_key or self._sensor_type

        data = self.coordinator.data
        if data is None:
            return None

        if self._forecast_day is not None:
            if "daily" not in data or len(data["daily"]) <= self._forecast_day:
                return None
            data = data["daily"][self._forecast_day]

        keys = lookup_key.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit() and len(value) > int(key):
                value = value[int(key)]
            else:
                value = None
                break
        
        # Format value for specific sensor types based on the unique sensor_type
        if self._sensor_type.endswith(("_sunrise_time", "_sunset_time")):
            if value is not None:
                utc_dt = datetime.fromtimestamp(value, tz=timezone.utc)
                local_dt = dt_util.as_local(utc_dt)
                return local_dt.strftime("%H:%M")
            return None

        # The check for 'pop' needs to be against the source_key
        if self._source_key == "pop" and value is not None:
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
