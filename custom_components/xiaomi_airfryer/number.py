"""Number entities of the Xiaomi AirFryer component."""
# pylint: disable=import-error
import logging
from datetime import timedelta

from homeassistant.components.number import (
    ENTITY_ID_FORMAT,
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import CONF_HOST, UnitOfTemperature, UnitOfTime

from .const import CONF_MODEL, DOMAIN
from .entity import XiaomiAirFryerEntity
from .fryer_miot import target_temperature_range

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

# mapping key: (name, unit, icon, device class, device method, range function)
NUMBER_TYPES = {
    "target_temperature": [
        "Target Temperature",
        UnitOfTemperature.CELSIUS,
        "mdi:thermometer",
        NumberDeviceClass.TEMPERATURE,
        "target_temperature",
        target_temperature_range,
    ],
    "target_time": [
        "Target Time",
        UnitOfTime.MINUTES,
        "mdi:timer-outline",
        None,
        "target_time",
        lambda model: (1, 1440, 1),
    ],
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the number entities from a config entry."""
    host = config_entry.options[CONF_HOST]
    model = config_entry.options.get(CONF_MODEL)
    fryer = hass.data[DOMAIN][host]

    entities = [
        XiaomiAirFryerNumber(fryer, config_entry, key, ntype)
        for key, ntype in NUMBER_TYPES.items()
        if key in fryer.mapping
    ]
    async_add_entities(entities, update_before_add=False)


class XiaomiAirFryerNumber(XiaomiAirFryerEntity, NumberEntity):
    """A writable target value of the air fryer."""

    _attr_mode = NumberMode.BOX

    def __init__(self, device, entry, key, config):
        """Initialize the number."""
        super().__init__(device, entry, config[0], ENTITY_ID_FORMAT)
        self._key = key
        self._attr_native_unit_of_measurement = config[1]
        self._attr_icon = config[2]
        self._attr_device_class = config[3]
        self._method = config[4]
        (
            self._attr_native_min_value,
            self._attr_native_max_value,
            self._attr_native_step,
        ) = config[5](self._model)
        self._attr_native_value = None

    async def async_update(self):
        """Read the current target value from the shared device state."""
        state = self._shared_state()
        if state is not None:
            self._attr_native_value = getattr(state, self._key, None)

    async def async_set_native_value(self, value: float) -> None:
        """Write the target value to the device."""
        await self.hass.async_add_executor_job(
            getattr(self._device, self._method), int(value)
        )
        self._attr_native_value = int(value)
        self._patch_shared_state(self._key, int(value))
        self.async_schedule_update_ha_state()
