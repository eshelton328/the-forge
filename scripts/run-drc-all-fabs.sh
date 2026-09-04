#!/usr/bin/env bash
set -euo pipefail

BOARD_DIR="${1:?Usage: $0 <board-directory>}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

BOARD_NAME="$(basename "$BOARD_DIR")"
PCB_FILE="$BOARD_DIR/$BOARD_NAME.kicad_pcb"
DRU_FILE="$BOARD_DIR/$BOARD_NAME.kicad_dru"
BOARD_YML="$BOARD_DIR/board.yml"

if [ ! -f "$PCB_FILE" ]; then
    echo "ERROR: PCB file not found: $PCB_FILE"
    exit 1
fi

if [ ! -f "$BOARD_YML" ]; then
    echo "ERROR: board.yml not found: $BOARD_YML"
    exit 1
fi

FAB_TARGETS=$(grep '^\s*-\s' "$BOARD_YML" | sed 's/^\s*-\s*//' || true)

if [ -z "$FAB_TARGETS" ]; then
    echo "No fab targets defined in board.yml — skipping fab DRC"
    exit 0
fi

FAILED=0
PASS_LIST=""
FAIL_LIST=""

# Preserve persistent board rules, even on interruption or a failing fab pass.
SAVED_BOARD_RULES=$(mktemp)
HAD_BOARD_RULES=0
if [ -f "$DRU_FILE" ]; then
    cp "$DRU_FILE" "$SAVED_BOARD_RULES"
    HAD_BOARD_RULES=1
fi
restore_board_rules() {
    if [ "$HAD_BOARD_RULES" -eq 1 ]; then
        cp "$SAVED_BOARD_RULES" "$DRU_FILE"
    else
        rm -f "$DRU_FILE"
    fi
    rm -f "$SAVED_BOARD_RULES"
}
trap restore_board_rules EXIT

for FAB in $FAB_TARGETS; do
    FAB_RULE="$REPO_ROOT/fab-rules/$FAB.kicad_dru"

    if [ ! -f "$FAB_RULE" ]; then
        echo "WARNING: Rule file not found for $FAB: $FAB_RULE (skipping)"
        continue
    fi

    echo ""
    echo "============================================"
    echo "  DRC: $BOARD_NAME against $FAB"
    echo "============================================"

    cp "$FAB_RULE" "$DRU_FILE"
    # Later board rules retain their specific restrictions alongside fab limits.
    if [ "$HAD_BOARD_RULES" -eq 1 ]; then
        sed '/^[[:space:]]*(version[[:space:]]/d' "$SAVED_BOARD_RULES" >> "$DRU_FILE"
    fi

    REPORT_FILE="$BOARD_DIR/drc-fab-$FAB.json"

    if kicad-cli pcb drc \
        --output "$REPORT_FILE" \
        --format json \
        --severity-all \
        --refill-zones \
        --exit-code-violations \
        "$PCB_FILE"; then
        echo "PASS: $FAB"
        PASS_LIST="$PASS_LIST $FAB"
    else
        EXIT_CODE=$?
        if [ "$EXIT_CODE" -eq 5 ]; then
            echo "FAIL: $FAB -- DRC violations found (see $REPORT_FILE)"
            FAIL_LIST="$FAIL_LIST $FAB"
            FAILED=1
        else
            echo "ERROR: kicad-cli exited with code $EXIT_CODE for $FAB"
            FAILED=1
        fi
    fi
done

echo ""
echo "============================================"
echo "  Summary: $BOARD_NAME"
echo "============================================"
if [ -n "$PASS_LIST" ]; then
    echo "  PASS:$PASS_LIST"
fi
if [ -n "$FAIL_LIST" ]; then
    echo "  FAIL:$FAIL_LIST"
fi
echo ""

exit $FAILED
