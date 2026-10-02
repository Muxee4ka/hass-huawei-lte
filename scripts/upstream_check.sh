#!/usr/bin/env bash
# Opens an issue when huawei_lte changed in the latest stable HA release.
set -euo pipefail
CUR=$(cat UPSTREAM_VERSION)
LATEST=$(curl -fsS https://pypi.org/pypi/homeassistant/json | python3 -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])')
if [ "$CUR" = "$LATEST" ]; then echo "up to date ($CUR)"; exit 0; fi
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
scripts/fetch_upstream.sh "$CUR" "$TMP/old"
scripts/fetch_upstream.sh "$LATEST" "$TMP/new"
if diff -rq "$TMP/old" "$TMP/new" >/dev/null; then echo "huawei_lte unchanged $CUR -> $LATEST"; exit 0; fi
TITLE="upstream changed: huawei_lte $CUR -> $LATEST"
if [ "$(gh issue list --state open --search "\"$TITLE\" in:title" --json number --jq length)" != "0" ]; then
  echo "issue already open"; exit 0
fi
diff -ru "$TMP/old" "$TMP/new" | head -c 60000 > "$TMP/diff.txt" || true
{
  echo "Core \`huawei_lte\` changed between $CUR and $LATEST."
  echo
  echo "To sync: \`scripts/sync_upstream.sh $LATEST && git merge upstream && scripts/port_core_tests.sh $LATEST && python3 scripts/apply_overlay.py && pytest\`"
  echo
  echo '```diff'; cat "$TMP/diff.txt"; echo '```'
} > "$TMP/body.md"
gh issue create --title "$TITLE" --body-file "$TMP/body.md"
