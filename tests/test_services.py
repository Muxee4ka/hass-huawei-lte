"""SMS management services."""

from unittest.mock import call

from huawei_lte_api.exceptions import ResponseErrorException
import pytest

from custom_components.huawei_lte.const import DOMAIN
from homeassistant.exceptions import HomeAssistantError

from .helpers import MOCK_URL, raw_sms, setup_router, sms_client


async def test_mark_read_list(hass):
    client = sms_client()
    await setup_router(hass, client)
    await hass.services.async_call(
        DOMAIN, "sms_mark_read", {"index": [4, 5]}, blocking=True
    )
    assert client.sms.set_read.call_args_list == [call(4), call(5)]


async def test_delete_single_string_index(hass):
    client = sms_client()
    await setup_router(hass, client)
    await hass.services.async_call(
        DOMAIN, "sms_delete", {"index": "7", "url": MOCK_URL}, blocking=True
    )
    client.sms.delete_sms.assert_called_once_with(7)


async def test_unknown_url_does_nothing(hass):
    client = sms_client()
    await setup_router(hass, client)
    await hass.services.async_call(
        DOMAIN,
        "sms_delete",
        {"index": 1, "url": "http://other.example.com"},
        blocking=True,
    )
    client.sms.delete_sms.assert_not_called()


async def test_delete_read_walks_pages(hass):
    client = sms_client()
    await setup_router(hass, client)
    page1 = [raw_sms(i, read=i % 2 == 0) for i in range(1, 21)]
    page2 = [raw_sms(i, read=True) for i in range(21, 24)]
    pages = {1: page1, 2: page2}
    client.sms.get_sms_list.side_effect = lambda page, *a: {
        "Count": "23",
        "Messages": {"Message": pages.get(page, [])},
    }
    await hass.services.async_call(DOMAIN, "sms_delete_read", {}, blocking=True)
    deleted = [c.args[0] for c in client.sms.delete_sms.call_args_list]
    assert deleted == [*range(2, 21, 2), 21, 22, 23]


async def test_modem_error_raises(hass):
    client = sms_client()
    await setup_router(hass, client)
    client.sms.delete_sms.side_effect = ResponseErrorException("fail", 113018)
    with pytest.raises(HomeAssistantError, match="sms_delete failed"):
        await hass.services.async_call(
            DOMAIN, "sms_delete", {"index": 1}, blocking=True
        )
