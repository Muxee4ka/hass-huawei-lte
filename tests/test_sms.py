"""Tests for SMS parsing and the seen-message journal."""

from custom_components.huawei_lte.sms import Sms, SmsTracker, parse_sms_list


def raw(index, phone="MegaFon", text="hi", date="2026-10-02 14:00:00", read=False):
    return {
        "Smstat": "1" if read else "0",
        "Index": str(index),
        "Phone": phone,
        "Content": text,
        "Date": date,
        "Sca": "",
        "SaveType": "4",
        "Priority": "0",
        "SmsType": "1",
    }


def sms(index, date="2026-10-02 14:00:00", phone="MegaFon"):
    return Sms(index=index, phone=phone, text="t", date=date, read=False)


def test_parse_list():
    resp = {"Count": "2", "Messages": {"Message": [raw(2, read=True), raw(1)]}}
    assert parse_sms_list(resp) == [
        Sms(2, "MegaFon", "hi", "2026-10-02 14:00:00", True),
        Sms(1, "MegaFon", "hi", "2026-10-02 14:00:00", False),
    ]


def test_parse_single_dict_and_empty():
    assert [m.index for m in parse_sms_list({"Messages": {"Message": raw(7)}})] == [7]
    assert parse_sms_list({"Count": "0", "Messages": {"Message": []}}) == []
    assert parse_sms_list({"Count": "0", "Messages": None}) == []
    assert parse_sms_list(None) == []
    assert parse_sms_list("garbage") == []


def test_parse_none_content_and_unicode():
    msgs = parse_sms_list(
        {"Messages": {"Message": [raw(1, text=None), raw(2, text="Привет\r\nмир 🙂")]}}
    )
    assert msgs[0].text == ""
    assert msgs[1].text == "Привет\r\nмир 🙂"


def test_event_data():
    assert sms(5).as_event_data() == {
        "phone": "MegaFon",
        "text": "t",
        "date": "2026-10-02 14:00:00",
        "index": 5,
    }


def test_first_run_is_baseline():
    tracker = SmsTracker(None)
    assert tracker.process([sms(2), sms(1)]) == []
    assert tracker.process([sms(3), sms(2), sms(1)]) == [sms(3)]


def test_known_journal_reports_new_oldest_first():
    tracker = SmsTracker([sms(1).key])
    new = tracker.process(
        [sms(3, "2026-10-02 15:00:00"), sms(2, "2026-10-02 14:30:00"), sms(1)]
    )
    assert [m.index for m in new] == [2, 3]
    assert (
        tracker.process([sms(3, "2026-10-02 15:00:00"), sms(2, "2026-10-02 14:30:00")])
        == []
    )


def test_index_reuse_with_new_date_is_new():
    tracker = SmsTracker([sms(1, "2026-01-01 00:00:00").key])
    assert tracker.process([sms(1, "2026-10-02 14:00:00")]) == [
        sms(1, "2026-10-02 14:00:00")
    ]


def test_journal_capped():
    tracker = SmsTracker([], max_seen=3)
    tracker.process([sms(i, f"2026-10-02 14:00:0{i}") for i in range(1, 6)])
    assert len(tracker.as_data()["seen"]) == 3


def test_as_data_roundtrip():
    tracker = SmsTracker(None)
    tracker.process([sms(1)])
    again = SmsTracker(tracker.as_data()["seen"])
    assert again.process([sms(1)]) == []
