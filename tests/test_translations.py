"""Overlay strings must be present in every file HA reads."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
COMPONENT = ROOT / "custom_components" / "huawei_lte"


def leaves(d, prefix=()):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from leaves(v, (*prefix, k))
        else:
            yield (*prefix, k), v


def lookup(d, path):
    for part in path:
        d = d[part]
    return d


@pytest.mark.parametrize(
    ("overlay", "target"),
    [("en", "translations/en.json"), ("ru", "translations/ru.json"), ("en", "strings.json")],
)
def test_overlay_applied(overlay, target):
    src = json.loads((ROOT / "overlay" / "translations" / f"{overlay}.json").read_text())
    dst = json.loads((COMPONENT / target).read_text())
    for path, value in leaves(src):
        assert lookup(dst, path) == value, path


def test_core_strings_kept():
    en = json.loads((COMPONENT / "translations" / "en.json").read_text())
    assert en["services"]["suspend_integration"]["name"] == "Suspend integration"
