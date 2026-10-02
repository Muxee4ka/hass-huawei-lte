"""Manifest must satisfy hassfest's key order: domain, name, then alphabetical."""

import json
from pathlib import Path

MANIFEST = Path(__file__).parent.parent / "custom_components/huawei_lte/manifest.json"


def test_manifest_key_order():
    keys = list(json.loads(MANIFEST.read_text()))
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])


def test_manifest_custom_fields():
    data = json.loads(MANIFEST.read_text())
    assert data["version"]
    assert data["issue_tracker"].startswith("https://github.com/Muxee4ka/")
