#!/usr/bin/env bash
# Usage: sync_upstream.sh <ha-version>
# Commits pristine huawei_lte of <ha-version> to the `upstream` branch.
set -euo pipefail
VER=$1
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean" >&2; exit 1; }
WT=$(mktemp -d)/upstream
git worktree add "$WT" upstream
scripts/fetch_upstream.sh "$VER" "$WT/custom_components/huawei_lte"
echo "$VER" > "$WT/UPSTREAM_VERSION"
git -C "$WT" add -A
git -C "$WT" commit -m "upstream: huawei_lte from core $VER" || echo "no upstream changes"
git worktree remove "$WT"
echo "Next: git merge upstream && scripts/port_core_tests.sh $VER && python3 scripts/apply_overlay.py && pytest"
