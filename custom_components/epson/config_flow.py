"""Config flow for epson integration."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from . import validate_projector
from .const import DOMAIN
from .exceptions import CannotConnect

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_NAME, default=DOMAIN): str
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for epson."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        errors = {}
        unique_id = (import_config['host'] + import_config['name']).replace('.', '')
        if import_config is not None:
            try:
                projector = await validate_projector(
                    self.hass, import_config[CONF_HOST]
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=import_config.pop(CONF_NAME), data=import_config
                )
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                projector = await validate_projector(
                    self.hass, user_input[CONF_HOST]
                )
                serial_no = await projector.get_serial_number()
                await self.async_set_unique_id(serial_no)
                self._abort_if_unique_id_configured()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.pop(CONF_NAME), data=user_input
                )
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
