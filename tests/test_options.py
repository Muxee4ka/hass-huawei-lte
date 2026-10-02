"""After-receive option."""

from huawei_lte_api.exceptions import ResponseErrorException
import pytest

from custom_components.huawei_lte.const import (
    CONF_SMS_AFTER_RECEIVE,
    CONF_TRACK_WIRED_CLIENTS,
    CONF_UNAUTHENTICATED_MODE,
)
from homeassistant.const import CONF_NAME, CONF_RECIPIENT, EVENT_STATE_CHANGED
from homeassistant.core import callback

from .helpers import EVENT_ENTITY, raw_sms, set_inbox, setup_router, sms_client, tick


async def _receive_one(hass, options):
    client = sms_client([raw_sms(1)])
    await setup_router(hass, client, options=options)
    await tick(hass)
    set_inbox(client, [raw_sms(1), raw_sms(2)], unread=1)
    await tick(hass)
    return client


async def test_default_leaves_message(hass):
    client = await _receive_one(hass, {})
    client.sms.set_read.assert_not_called()
    client.sms.delete_sms.assert_not_called()


@pytest.mark.parametrize(
    ("option", "method"), [("mark_read", "set_read"), ("delete", "delete_sms")]
)
async def test_action_applied(hass, option, method):
    client = await _receive_one(hass, {CONF_SMS_AFTER_RECEIVE: option})
    getattr(client.sms, method).assert_called_once_with(2)


async def test_action_failure_no_duplicate(hass):
    client = sms_client([raw_sms(1)])
    await setup_router(hass, client, options={CONF_SMS_AFTER_RECEIVE: "mark_read"})
    await tick(hass)
    fired = []

    @callback
    def _listener(event):
        new = event.data["new_state"]
        if event.data["entity_id"] == EVENT_ENTITY and new and "index" in new.attributes:
            fired.append(new.attributes["index"])

    hass.bus.async_listen(EVENT_STATE_CHANGED, _listener)
    set_inbox(client, [raw_sms(1), raw_sms(2)], unread=1)
    client.sms.set_read.side_effect = ResponseErrorException("busy", 100004)
    await tick(hass)
    set_inbox(client, [raw_sms(1), raw_sms(2)], unread=2)  # counts moved again -> refetch
    client.sms.set_read.side_effect = ResponseErrorException("busy", 100004)
    await tick(hass)
    assert fired == [2]
    client.sms.set_read.assert_called_once_with(2)


async def test_options_flow_sets_value(hass):
    entry = await setup_router(hass, sms_client())
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "huawei_lte",
            CONF_RECIPIENT: "",
            CONF_TRACK_WIRED_CLIENTS: True,
            CONF_UNAUTHENTICATED_MODE: False,
            CONF_SMS_AFTER_RECEIVE: "delete",
        },
    )
    assert entry.options[CONF_SMS_AFTER_RECEIVE] == "delete"
