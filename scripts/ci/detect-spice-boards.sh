#!/usr/bin/env bash
# Emit GitHub Actions outputs for SPICE CI: which boards have sim.yml in scope, and whether
# to run the lightweight fixture. Intended for pull_request with fetch-depth: 0.
set -euo pipefail

base_ref="${BASE_REF:-main}"
base="origin/${base_ref}"
files=$(git diff --name-only "${base}...HEAD" || true)

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
    # sim/fixtures/ only under sim/ — README/architecture edits under sim/ must not force ngspice.
    echo "$files" | grep -qE '^(libs/spice/|libs/symbols/|scripts/sim/|sim/fixtures/|\.github/workflows/spice-checks\.yml|Makefile|requirements\.txt)' \
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

run_fixture=false
changed_boards=""

if broad_spice_touch; then
    changed_boards=$all_sim_boards
elif echo "$files" | grep -qE '^boards/'; then
    touched=$(board_touch_names)
    changed_boards=$(intersect_sim_boards "$touched")
fi

# RC fixture: exercise sim/fixtures when that tree changes, or when there is no opt-in board yet
# but simulation scripts changed (runner-only PRs).
if echo "$files" | grep -qE '^sim/fixtures/'; then
    run_fixture=true
elif [ -z "$all_sim_boards" ] && echo "$files" | grep -qE '^scripts/sim/'; then
    run_fixture=true
fi

if [ -z "$changed_boards" ]; then
    boards_json="[]"
else
    boards_json=$(echo "$changed_boards" | jq -R -s -c 'split("\n") | map(select(. != ""))')
fi

gh_out="${GITHUB_OUTPUT:-}"
if [ -n "$gh_out" ]; then
    {
        echo "boards=${boards_json}"
        echo "run_fixture=${run_fixture}"
    } >>"$gh_out"
fi

echo "detect-spice-boards: boards=${boards_json} run_fixture=${run_fixture}"
