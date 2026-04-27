#!/usr/bin/env bash
# Generate documentation images for a single board using kicad-cli.
#
# Outputs (written to boards/<name>/docs/):
#   schematic.svg          — full schematic (multi-page → one SVG per page)
#   pcb-all-layers.svg     — composite of all copper + silkscreen + mask + edge
#   pcb-F_Cu.svg           — front copper + edge cuts
#   pcb-B_Cu.svg           — back copper + edge cuts
#   3d-front.png           — 3D render, top side
#   3d-back.png            — 3D render, bottom side
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

# ── PCB layer SVGs ────────────────────────────────────────────────────
if [ -f "$PCB_FILE" ]; then
  echo "Exporting PCB layer SVGs..."

  kicad-cli pcb export svg \
    --output "$DOCS_DIR/pcb-F_Cu.svg" \
    --layers "F.Cu,Edge.Cuts" \
    --page-size-mode 2 \
    --exclude-drawing-sheet \
    "$PCB_FILE"
  echo "  → pcb-F_Cu.svg"

  kicad-cli pcb export svg \
    --output "$DOCS_DIR/pcb-B_Cu.svg" \
    --layers "B.Cu,Edge.Cuts" \
    --page-size-mode 2 \
    --exclude-drawing-sheet \
    "$PCB_FILE"
  echo "  → pcb-B_Cu.svg"

  kicad-cli pcb export svg \
    --output "$DOCS_DIR/pcb-all-layers.svg" \
    --layers "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" \
    --page-size-mode 2 \
    --exclude-drawing-sheet \
    "$PCB_FILE"
  echo "  → pcb-all-layers.svg"

  # ── 3D renders ────────────────────────────────────────────────────
  echo "Rendering 3D views..."

  kicad-cli pcb render \
    --output "$DOCS_DIR/3d-front.png" \
    --side top \
    --background transparent \
    --width 1600 --height 1200 \
    --quality high \
    "$PCB_FILE" || echo "  ⚠ 3D front render failed (missing 3D models?)"

  kicad-cli pcb render \
    --output "$DOCS_DIR/3d-back.png" \
    --side bottom \
    --background transparent \
    --width 1600 --height 1200 \
    --quality high \
    "$PCB_FILE" || echo "  ⚠ 3D back render failed (missing 3D models?)"

  echo "  → 3d-front.png, 3d-back.png"
else
  echo "No PCB found at $PCB_FILE — skipping."
fi

echo "Done: $DOCS_DIR"
ls -lh "$DOCS_DIR"
