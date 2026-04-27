#!/usr/bin/env bash
# Generate documentation images for a single board using kicad-cli.
#
# Outputs (written to boards/<name>/docs/):
#   schematic.svg          — full schematic (multi-page → one SVG per page)
#   pcb-top.png            — PCB top side with silkscreen (high-quality 3D render)
#   pcb-bottom.png         — PCB bottom side with silkscreen (high-quality 3D render)
#
# Usage:  bash scripts/ci/generate-board-images.sh boards/<name>
# Expects kicad-cli on PATH (run inside the KiCad Docker image in CI).
#
# 3D models: set KICAD10_3DMODEL_DIR to point at the standard library.
# The workflow downloads the needed libraries and sets this variable.

set -euo pipefail

BOARD_DIR="${1:?Usage: $0 <board-directory>}"
BOARD_NAME=$(basename "$BOARD_DIR")
SCH_FILE="$BOARD_DIR/$BOARD_NAME.kicad_sch"
PCB_FILE="$BOARD_DIR/$BOARD_NAME.kicad_pcb"
DOCS_DIR="$BOARD_DIR/docs"

mkdir -p "$DOCS_DIR"

# ── Schematic SVG ─────────────────────────────────────────────────────
if [ -f "$SCH_FILE" ]; then
  echo "Exporting schematic SVG..."
  SCH_TMP=$(mktemp -d)
  kicad-cli sch export svg \
    --output "$SCH_TMP" \
    --no-background-color \
    --exclude-drawing-sheet \
    "$SCH_FILE"

  page=0
  for svg in "$SCH_TMP"/*.svg; do
    [ -f "$svg" ] || continue
    if [ "$page" -eq 0 ]; then
      cp "$svg" "$DOCS_DIR/schematic.svg"
    else
      cp "$svg" "$DOCS_DIR/schematic-page${page}.svg"
    fi
    page=$((page + 1))
  done
  rm -rf "$SCH_TMP"
  echo "  → schematic.svg ($page page(s))"
else
  echo "No schematic found at $SCH_FILE — skipping."
fi

# ── PCB top/bottom renders ───────────────────────────────────────────
if [ -f "$PCB_FILE" ]; then
  echo "Rendering PCB top..."
  kicad-cli pcb render \
    --output "$DOCS_DIR/pcb-top.png" \
    --side top \
    --background transparent \
    --width 1600 --height 1200 \
    --quality high \
    "$PCB_FILE"
  echo "  → pcb-top.png"

  echo "Rendering PCB bottom..."
  kicad-cli pcb render \
    --output "$DOCS_DIR/pcb-bottom.png" \
    --side bottom \
    --background transparent \
    --width 1600 --height 1200 \
    --quality high \
    "$PCB_FILE"
  echo "  → pcb-bottom.png"
else
  echo "No PCB found at $PCB_FILE — skipping."
fi

echo "Done: $DOCS_DIR"
ls -lh "$DOCS_DIR"
