"""Button entities of the Xiaomi AirFryer component."""
# pylint: disable=import-error
import logging

from homeassistant.components.button import ENTITY_ID_FORMAT, ButtonEntity
from homeassistant.const import CONF_HOST

from .const import DOMAIN
from .entity import XiaomiAirFryerEntity

_LOGGER = logging.getLogger(__name__)

# mapping key (also the device method name): (name, icon)
BUTTON_TYPES = {
    "start_cook": ["Start", "mdi:play"],
    "pause": ["Pause", "mdi:pause"],
    "resume_cooking": ["Resume", "mdi:play-pause"],
    "cancel_cooking": ["Stop", "mdi:stop"],
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the button entities from a config entry."""
    host = config_entry.options[CONF_HOST]
    fryer = hass.data[DOMAIN][host]

    entities = [
        XiaomiAirFryerButton(fryer, config_entry, key, btype)
        for key, btype in BUTTON_TYPES.items()
        if key in fryer.mapping
    ]
    async_add_entities(entities, update_before_add=False)


class XiaomiAirFryerButton(XiaomiAirFryerEntity, ButtonEntity):
    """A cooking action of the air fryer."""

    def __init__(self, device, entry, key, config):
        """Initialize the button."""
        super().__init__(device, entry, config[0], ENTITY_ID_FORMAT)
        self._method = key
        self._attr_icon = config[1]

    async def async_press(self) -> None:
        """Run the action on the device."""
        await self.hass.async_add_executor_job(getattr(self._device, self._method))
