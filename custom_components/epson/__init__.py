"""The epson integration."""
import asyncio
import logging

from epson_projector import Projector
from epson_projector.const import POWER, STATE_UNAVAILABLE as EPSON_STATE_UNAVAILABLE

from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_PLATFORM
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .exceptions import CannotConnect, PoweredOff

PLATFORMS = [MEDIA_PLAYER_PLATFORM]

PWR_OFF = '04'

_LOGGER = logging.getLogger(__name__)


async def validate_projector(hass: HomeAssistant, host, check_powered_on=True):
    """Validate the given host and port allows us to connect."""
    epson_proj = Projector(
        host=host,
        loop=hass.loop,
        type='tcp'
    )
    if check_powered_on:
        _power = await epson_proj.get_property(POWER)
        _LOGGER.debug("Power retrieved %s", _power)
        if not _power or _power == EPSON_STATE_UNAVAILABLE:
            raise CannotConnect
        if _power == PWR_OFF:
            _LOGGER.debug("Projector is off")
            raise PoweredOff
    return epson_proj


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the epson component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up epson from a config entry."""
    try:
        projector = await validate_projector(
            hass=hass, host=entry.data[CONF_HOST], check_powered_on=False
        )
    except CannotConnect:
        _LOGGER.warning("Cannot connect to projector %s", entry.data[CONF_HOST])
        return False
    hass.data[DOMAIN][entry.entry_id] = projector
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
