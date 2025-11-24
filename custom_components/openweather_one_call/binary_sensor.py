from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            OpenWeatherOneCallBinarySensor(
                coordinator=coordinator,
                config_entry=entry,
                sensor_type="alerts_active",
                device_class=BinarySensorDeviceClass.SAFETY,
            ),
        ]
    )


class OpenWeatherOneCallBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Binary Sensor."""

    def __init__(self, coordinator, config_entry, sensor_type, device_class):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._sensor_type = sensor_type

        self._attr_has_entity_name = True
        self._attr_translation_key = sensor_type
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_device_class = device_class

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        data = self.coordinator.data
        if data is None:
            return None

        if self._sensor_type == "alerts_active":
            return bool(data.get("alerts"))
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self.coordinator.data
        if data is None or not data.get("alerts"):
            return None

        if self._sensor_type == "alerts_active":
            alert = data["alerts"][0]
            return {
                "sender_name": alert.get("sender_name"),
                "event": alert.get("event"),
                "description": alert.get("description"),
            }
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
