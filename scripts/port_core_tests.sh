#!/usr/bin/env bash
# Usage: port_core_tests.sh <ha-version>
# Copies tests/components/huawei_lte from core <ha-version> into tests/core with imports rewritten.
set -euo pipefail
VER=$1; DEST=tests/core
FILES=$(gh api "repos/home-assistant/core/git/trees/$VER?recursive=1" \
  --jq '.tree[] | select(.type=="blob") | .path | select(startswith("tests/components/huawei_lte/"))')
rm -rf "$DEST"; mkdir -p "$DEST"
for f in $FILES; do
  rel=${f#tests/components/huawei_lte/}
  mkdir -p "$DEST/$(dirname "$rel")"
  curl -fsSL "https://raw.githubusercontent.com/home-assistant/core/$VER/$f" -o "$DEST/$rel"
done
# Default syrupy extension is in effect for these tests: it reads __snapshots__/, not core's snapshots/.
if [ -d "$DEST/snapshots" ]; then mv "$DEST/snapshots" "$DEST/__snapshots__"; fi
find "$DEST" -name '*.py' -exec sed -i -E \
  -e 's/homeassistant\.components\.huawei_lte/custom_components.huawei_lte/g' \
  -e 's/^from tests\.common import/from pytest_homeassistant_custom_component.common import/' \
  -e 's/^from tests\.components\.diagnostics import/from pytest_homeassistant_custom_component.components.diagnostics import/' \
  -e 's/^from tests\.typing import/from pytest_homeassistant_custom_component.typing import/' {} +
echo "ported $(echo "$FILES" | wc -l) files from core $VER"
