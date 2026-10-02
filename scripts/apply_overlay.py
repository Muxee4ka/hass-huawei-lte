#!/usr/bin/env python3
"""Merge overlay/translations into the component's translations and strings.json.

Run after every upstream merge: upstream translation files are taken as-is,
our strings are layered on top.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OVERLAY = ROOT / "overlay" / "translations"
COMPONENT = ROOT / "custom_components" / "huawei_lte"


def merge(dst: dict, src: dict) -> None:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            merge(dst[key], value)
        else:
            dst[key] = value


def apply(overlay_lang: str, target: Path, *, built: bool) -> None:
    """Merge one overlay file, keeping the target's upstream formatting.

    Built translations/*.json: 4-space indent, sorted keys, \\u escapes, no trailing newline.
    strings.json: 2-space indent, source key order, trailing newline.
    """
    data = json.loads(target.read_text(encoding="utf-8"))
    merge(data, json.loads((OVERLAY / f"{overlay_lang}.json").read_text(encoding="utf-8")))
    if built:
        text = json.dumps(data, indent=4, sort_keys=True)
    else:
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    target.write_text(text, encoding="utf-8")
    print(f"{overlay_lang} -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    for path in sorted(OVERLAY.glob("*.json")):
        apply(path.stem, COMPONENT / "translations" / path.name, built=True)
    apply("en", COMPONENT / "strings.json", built=False)
