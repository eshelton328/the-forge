#!/usr/bin/env bash
# Generate documentation images for a single board using kicad-cli.
#
# Outputs (written to boards/<name>/docs/):
#   schematic.svg          — full schematic (multi-page → one SVG per page)
#   pcb-top.png            — PCB layout, top side (orthographic 3D render)
#   pcb-bottom.png         — PCB layout, bottom side (orthographic 3D render)
#   3d-front.png           — 3D perspective render, front
#   3d-back.png            — 3D perspective render, back
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

# ── PCB + 3D renders ─────────────────────────────────────────────────
if [ -f "$PCB_FILE" ]; then
  echo "Rendering PCB layout views..."

  kicad-cli pcb render \
    --output "$DOCS_DIR/pcb-top.png" \
    --side top \
    --preset follow_pcb_editor \
    --background transparent \
    --width 1600 --height 1200 \
    --quality basic \
    "$PCB_FILE"
  echo "  → pcb-top.png"

  kicad-cli pcb render \
    --output "$DOCS_DIR/pcb-bottom.png" \
    --side bottom \
    --preset follow_pcb_editor \
    --background transparent \
    --width 1600 --height 1200 \
    --quality basic \
    "$PCB_FILE"
  echo "  → pcb-bottom.png"

  echo "Rendering 3D perspective views..."

  kicad-cli pcb render \
    --output "$DOCS_DIR/3d-front.png" \
    --side top \
    --background transparent \
    --width 1600 --height 1200 \
    --quality high \
    --floor \
    --perspective \
    --rotate "-25,0,15" \
    "$PCB_FILE" || echo "  ⚠ 3D front render failed"

  kicad-cli pcb render \
    --output "$DOCS_DIR/3d-back.png" \
    --side bottom \
    --background transparent \
    --width 1600 --height 1200 \
    --quality high \
    --floor \
    --perspective \
    --rotate "25,0,-15" \
    "$PCB_FILE" || echo "  ⚠ 3D back render failed"

  echo "  → 3d-front.png, 3d-back.png"
else
  echo "No PCB found at $PCB_FILE — skipping."
fi

echo "Done: $DOCS_DIR"
ls -lh "$DOCS_DIR"
