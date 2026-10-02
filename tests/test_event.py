"""Incoming SMS event entity."""

from datetime import timedelta

from huawei_lte_api.exceptions import ResponseErrorNotSupportedException
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback

from .helpers import EVENT_ENTITY, raw_sms, set_inbox, setup_router, sms_client, tick


def capture(hass: HomeAssistant) -> list[int]:
    """Collect SMS indexes of fired events, in order."""
    fired: list[int] = []

    @callback
    def _listener(event):
        new = event.data["new_state"]
        if event.data["entity_id"] == EVENT_ENTITY and new and "index" in new.attributes:
            fired.append(new.attributes["index"])

    hass.bus.async_listen(EVENT_STATE_CHANGED, _listener)
    return fired


async def test_first_run_is_silent(hass):
    client = sms_client([raw_sms(1), raw_sms(2), raw_sms(3)])
    await setup_router(hass, client)
    fired = capture(hass)
    await tick(hass)
    assert fired == []
    assert hass.states.get(EVENT_ENTITY).state == STATE_UNKNOWN


async def test_new_sms_fires_event(hass):
    old = [raw_sms(1), raw_sms(2)]
    client = sms_client(old)
    await setup_router(hass, client)
    await tick(hass)
    set_inbox(client, [*old, raw_sms(3, phone="RSCHS", text="Внимание!")], unread=1)
    await tick(hass)
    attrs = hass.states.get(EVENT_ENTITY).attributes
    assert attrs["event_type"] == "received"
    assert (attrs["phone"], attrs["text"], attrs["index"]) == ("RSCHS", "Внимание!", 3)
    assert attrs["date"] == "2026-10-02 14:00:03"


async def test_several_new_fire_oldest_first(hass):
    client = sms_client([raw_sms(1)])
    await setup_router(hass, client)
    await tick(hass)
    fired = capture(hass)
    set_inbox(client, [raw_sms(1), raw_sms(2), raw_sms(3)], unread=2)
    await tick(hass)
    assert fired == [2, 3]


async def test_unchanged_counts_skip_list(hass):
    client = sms_client([raw_sms(1)])
    await setup_router(hass, client)
    await tick(hass)
    client.sms.get_sms_list.reset_mock()
    await tick(hass)
    client.sms.get_sms_list.assert_not_called()


async def test_sms_while_down_fires_once(hass, hass_storage):
    hass_storage["huawei_lte.sms_seen.test_entry"] = {
        "version": 1,
        "minor_version": 1,
        "key": "huawei_lte.sms_seen.test_entry",
        "data": {"seen": [f"{i}|2026-10-02 14:00:{i:02d}|MegaFon" for i in (1, 2)]},
    }
    client = sms_client([raw_sms(1), raw_sms(2), raw_sms(3)], unread=1)
    await setup_router(hass, client)
    fired = capture(hass)
    await tick(hass)
    await tick(hass)
    assert fired == [3]


async def test_journal_persisted(hass, hass_storage, freezer):
    client = sms_client([raw_sms(1)])
    await setup_router(hass, client)
    await tick(hass)
    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass_storage["huawei_lte.sms_seen.test_entry"]["data"]["seen"] == [
        "1|2026-10-02 14:00:01|MegaFon"
    ]


async def test_list_not_supported_no_entity(hass):
    client = sms_client()
    client.sms.get_sms_list.side_effect = ResponseErrorNotSupportedException("nope", 100002)
    entry = await setup_router(hass, client)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(EVENT_ENTITY) is None


async def test_unload_after_key_dropped(hass):
    client = sms_client([raw_sms(1)])
    entry = await setup_router(hass, client)
    await tick(hass)
    set_inbox(client, [raw_sms(1), raw_sms(2)], unread=1)
    client.sms.get_sms_list.side_effect = ResponseErrorNotSupportedException("nope", 100002)
    await tick(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_diagnostics_redacts_sms(hass, hass_client):
    client = sms_client([raw_sms(1, phone="+79991234567", text="код 1234")])
    entry = await setup_router(hass, client)
    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    assert diag["router"]["sms_sms_list"] == "**REDACTED**"
    assert "код 1234" not in str(diag)


async def test_list_error_does_not_break_setup_or_polling(hass):
    from huawei_lte_api.exceptions import ResponseErrorException

    client = sms_client([raw_sms(1)])
    client.sms.get_sms_list.side_effect = ResponseErrorException("busy", 125003)
    entry = await setup_router(hass, client)
    assert entry.state is ConfigEntryState.LOADED
    client.lan.host_info.reset_mock()
    set_inbox(client, [raw_sms(1), raw_sms(2)], unread=1)
    client.sms.get_sms_list.side_effect = KeyError("Index")
    await tick(hass)
    client.lan.host_info.assert_called()  # rest of update() still ran
