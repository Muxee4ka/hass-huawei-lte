"""Forward SMS blueprint."""

from pathlib import Path
import shutil

from pytest_homeassistant_custom_component.common import async_mock_service

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.setup import async_setup_component

BLUEPRINT = (
    Path(__file__).parent.parent / "blueprints/automation/huawei_lte/forward_sms.yaml"
)
ENTITY = "event.modem_incoming_sms"


async def _setup(hass, tmp_path, **inputs):
    hass.config.config_dir = str(tmp_path)
    dest = tmp_path / "blueprints/automation/huawei_lte"
    dest.mkdir(parents=True)
    shutil.copy(BLUEPRINT, dest / "forward_sms.yaml")
    calls = async_mock_service(hass, "test", "forward")
    hass.states.async_set(ENTITY, STATE_UNKNOWN, {"event_types": ["received"]})
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "use_blueprint": {
                    "path": "huawei_lte/forward_sms.yaml",
                    "input": {
                        "sms_event": ENTITY,
                        "forward_action": [
                            {
                                "action": "test.forward",
                                "data": {"message": "{{ phone }}: {{ text }} ({{ date }})"},
                            }
                        ],
                        **inputs,
                    },
                }
            }
        },
    )
    await hass.async_block_till_done()
    return calls


def _sms(hass, n, phone, text):
    hass.states.async_set(
        ENTITY,
        f"2026-10-02T12:00:{n:02d}.000+00:00",
        {
            "event_types": ["received"],
            "event_type": "received",
            "phone": phone,
            "text": text,
            "date": "2026-10-02 15:00:00",
            "index": n,
        },
    )


async def test_block_filters(hass, tmp_path):
    calls = await _setup(
        hass, tmp_path, block_senders=["megafon"], block_keywords=["реклама"]
    )
    _sms(hass, 1, "RSCHS", "Внимание")
    _sms(hass, 2, "MegaFon", "Баланс")
    _sms(hass, 3, "Bank", "Это РЕКЛАМА вклада")
    await hass.async_block_till_done()
    assert [c.data["message"] for c in calls] == [
        "RSCHS: Внимание (2026-10-02 15:00:00)"
    ]


async def test_allow_list(hass, tmp_path):
    calls = await _setup(hass, tmp_path, allow_senders=["RSCHS"])
    _sms(hass, 1, "MegaFon", "x")
    _sms(hass, 2, "rschs", "y")
    await hass.async_block_till_done()
    assert [c.data["message"] for c in calls] == ["rschs: y (2026-10-02 15:00:00)"]


async def test_restore_does_not_forward(hass, tmp_path):
    calls = await _setup(hass, tmp_path)
    hass.states.async_set(ENTITY, STATE_UNAVAILABLE, {"event_types": ["received"]})
    _sms(hass, 1, "RSCHS", "old one restored after reload")
    await hass.async_block_till_done()
    assert calls == []
