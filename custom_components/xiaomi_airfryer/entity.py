"""Base entity of the Xiaomi AirFryer component."""
# pylint: disable=import-error
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.util import slugify

from .const import CONF_MODEL, DATA_DEVICE, DATA_KEY, DATA_STATE, DOMAIN

# The device reports a new status only a moment after an action was accepted.
REFRESH_DELAY = 3


class XiaomiAirFryerEntity(Entity):
    """Common device info and state access for the control entities."""

    def __init__(self, device, entry, name, entity_id_format):
        """Initialize the entity."""
        self._device = device
        self._host = entry.options[CONF_HOST]
        self._model = entry.options.get(CONF_MODEL)
        self._mac = entry.options[CONF_MAC]
        self._device_id = entry.unique_id
        self._device_name = entry.title
        self._attr_name = name
        self._attr_unique_id = "{}.{}-{}".format(
            DOMAIN, entry.unique_id, name.lower().replace(" ", "-"))
        self.entity_id = entity_id_format.format(
            "{}_{}".format(DOMAIN, slugify(name))
        )

    @property
    def device_info(self):
        """Return the device info."""
        device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "manufacturer": (self._model or "Xiaomi").split(".", 1)[0].capitalize(),
            "name": self._device_name,
            "model": self._model,
        }

        if self._mac is not None:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

        return device_info

    def _shared_state(self):
        """Return the last status fetched by the switch entity, if any."""
        return self.hass.data.get(DATA_KEY, {}).get(self._host, {}).get(DATA_STATE)

    def _patch_shared_state(self, key, value):
        """Store a value just written to the device until the next poll."""
        state = self._shared_state()
        if state is not None and isinstance(getattr(state, "data", None), dict):
            state.data[key] = value

    async def _refresh_switch(self):
        """Ask the switch entity to poll the device now and again shortly after."""
        switch = self.hass.data.get(DATA_KEY, {}).get(self._host, {}).get(DATA_DEVICE)
        if switch is None:
            return
        await switch.async_update_ha_state(True)

        async def _refresh_again(_now):
            await switch.async_update_ha_state(True)

        async_call_later(self.hass, REFRESH_DELAY, _refresh_again)
