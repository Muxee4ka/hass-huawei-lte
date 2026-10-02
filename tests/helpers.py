"""Helpers for SMS tests on top of the core magic_client."""

from unittest.mock import MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.huawei_lte.const import DOMAIN
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant

from .core import magic_client

MOCK_URL = "http://huawei-lte.example.com"
EVENT_ENTITY = "event.test_router_incoming_sms"


def raw_sms(index, phone="MegaFon", text="hi", date=None, read=False):
    return {
        "Smstat": "1" if read else "0",
        "Index": str(index),
        "Phone": phone,
        "Content": text,
        "Date": date or f"2026-10-02 14:00:{index:02d}",
        "Sca": "",
        "SaveType": "4",
        "Priority": "0",
        "SmsType": "1",
    }


def set_inbox(client: MagicMock, messages: list[dict], unread: int = 0) -> None:
    """Make the mock modem report this inbox (newest first, as the API sorts)."""
    newest_first = sorted(messages, key=lambda m: m["Date"], reverse=True)
    client.sms.get_sms_list = MagicMock(
        return_value={"Count": str(len(messages)), "Messages": {"Message": newest_first}}
    )
    counts = dict(client.sms.sms_count.return_value)
    counts.update(LocalInbox=str(len(messages)), LocalUnread=str(unread))
    client.sms.sms_count = MagicMock(return_value=counts)


def sms_client(messages=(), unread: int = 0) -> MagicMock:
    client = magic_client()
    set_inbox(client, list(messages), unread)
    return client


async def setup_router(
    hass: HomeAssistant, client: MagicMock, options=None, entry_id: str = "test_entry"
) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_URL: MOCK_URL}, options=options or {}, entry_id=entry_id
    )
    entry.add_to_hass(hass)
    with (
        patch("custom_components.huawei_lte.Connection", MagicMock()),
        patch("custom_components.huawei_lte.Client", return_value=client),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def tick(hass: HomeAssistant) -> None:
    """Run one periodic Router.update and let dispatched events land.

    Calls the same Router.update the interval timer runs. Driving the timer with
    a frozen clock proved flaky: a delayed first fire coalesced with the next one.
    """
    entry = hass.config_entries.async_loaded_entries(DOMAIN)[0]
    await hass.async_add_executor_job(entry.runtime_data.update)
    await hass.async_block_till_done()
    await hass.async_block_till_done()
