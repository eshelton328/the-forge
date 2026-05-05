#!/usr/bin/env bash
# Emit GITHUB_OUTPUT boards= JSON array for push events (before..after SHAs).
# Reuses scope rules from detect-spice-boards.sh for PRs, but diff source is explicit.
set -euo pipefail

before="${1:-}"
after="${2:-}"
if [[ -z "${before}" || -z "${after}" ]]; then
  echo "usage: detect-spice-boards-for-push.sh BEFORE_SHA AFTER_SHA" >&2
  exit 2
fi

if [[ "${before}" =~ ^0+$ ]]; then
  # force push or empty parent; fall back to single-commit tree
  files=$(git diff-tree --no-commit-id --name-only -r "${after}" || true)
else
  files=$(git diff --name-only "${before}" "${after}" || true)
fi

boards_with_sim_yml() {
  local d b
  for d in boards/*/; do
    [ -d "$d" ] || continue
    b=$(basename "$d")
    if [ -f "boards/${b}/sim.yml" ]; then
      echo "$b"
    fi
  done | sort -u
}

all_sim_boards=$(boards_with_sim_yml || true)

broad_spice_touch() {
  echo "$files" | grep -qE '^(libs/spice/|libs/symbols/|scripts/sim/|sim/fixtures/|sim/docker/|\.github/workflows/(spice-checks|update-readmes)\.yml|Makefile|requirements\.txt)' \
    || echo "$files" | grep -qE '^tests/.*(spice|test_sim_)'
}

board_touch_names() {
  echo "$files" | grep -E '^boards/[^/]+/' | cut -d/ -f2 | sort -u
}

intersect_sim_boards() {
  local touched="$1"
  local b
  while IFS= read -r b; do
    [ -z "$b" ] && continue
    if echo "$all_sim_boards" | grep -qx "$b"; then
      echo "$b"
    fi
  done <<<"$touched"
}

changed_boards=""
if broad_spice_touch; then
  changed_boards=$all_sim_boards
elif echo "$files" | grep -qE '^boards/'; then
  touched=$(board_touch_names)
  changed_boards=$(intersect_sim_boards "$touched")
fi

if [ -z "$changed_boards" ]; then
  boards_json="[]"
else
  boards_json=$(echo "$changed_boards" | jq -R -s -c 'split("\n") | map(select(. != ""))')
fi

gh_out="${GITHUB_OUTPUT:-}"
if [ -n "$gh_out" ]; then
  echo "boards=${boards_json}" >>"$gh_out"
fi

echo "detect-spice-boards-for-push: boards=${boards_json}"
