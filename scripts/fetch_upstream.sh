#!/usr/bin/env bash
# Usage: fetch_upstream.sh <ha-version> <dest-dir>
# Puts pristine homeassistant/components/huawei_lte from the PyPI wheel into <dest-dir>.
# The wheel (not git) is the source because only it ships built translations/*.json.
set -euo pipefail
VER=$1; DEST=$2
URL=$(curl -fsS "https://pypi.org/pypi/homeassistant/$VER/json" \
  | python3 -c 'import json,sys; print(next(u["url"] for u in json.load(sys.stdin)["urls"] if u["filename"].endswith(".whl")))')
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/ha.whl" "$URL"
unzip -q "$TMP/ha.whl" 'homeassistant/components/huawei_lte/*' -d "$TMP"
mkdir -p "$DEST"
rsync -a --delete "$TMP/homeassistant/components/huawei_lte/" "$DEST/"
