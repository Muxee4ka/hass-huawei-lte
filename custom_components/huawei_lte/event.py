"""Support for Huawei LTE incoming SMS events."""

from contextlib import suppress
from typing import override

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HuaweiLteConfigEntry
from .const import (
    KEY_SMS_SMS_COUNT,
    KEY_SMS_SMS_LIST,
    SMS_EVENT_SUBSCRIBER,
    SMS_EVENT_TYPE,
    SMS_RECEIVED_SIGNAL,
)
from .entity import HuaweiLteBaseEntityWithDevice
from .sms import Sms

SUBSCRIBED_KEYS = (KEY_SMS_SMS_COUNT, KEY_SMS_SMS_LIST)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HuaweiLteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up from config entry."""
    router = config_entry.runtime_data
    if KEY_SMS_SMS_LIST in router.data:
        async_add_entities([HuaweiLteSmsEvent(router)])


class HuaweiLteSmsEvent(HuaweiLteBaseEntityWithDevice, EventEntity):
    """Fires when an unseen SMS appears in the modem inbox."""

    _attr_translation_key = "incoming_sms"
    _attr_event_types = [SMS_EVENT_TYPE]

    @property
    @override
    def _device_unique_id(self) -> str:
        return "sms_incoming"

    @override
    async def async_added_to_hass(self) -> None:
        """Subscribe to SMS data and the received signal."""
        await super().async_added_to_hass()
        for key in SUBSCRIBED_KEYS:
            self.router.subscriptions[key].append(SMS_EVENT_SUBSCRIBER)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SMS_RECEIVED_SIGNAL, self._async_handle_sms
            )
        )

    @override
    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe; keys may already be dropped as unsupported."""
        await super().async_will_remove_from_hass()
        for key in SUBSCRIBED_KEYS:
            with suppress(ValueError):
                self.router.subscriptions[key].remove(SMS_EVENT_SUBSCRIBER)

    @override
    async def async_update(self) -> None:
        """Nothing to poll; state changes only on incoming SMS."""

    @callback
    def _async_handle_sms(self, entry_id: str, sms: Sms) -> None:
        if entry_id != self.router.config_entry.entry_id:
            return
        self._trigger_event(SMS_EVENT_TYPE, sms.as_event_data())
        self.async_write_ha_state()
