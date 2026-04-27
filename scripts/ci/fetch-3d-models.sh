#!/usr/bin/env bash
# Download only the KiCad 3D model libraries needed by boards in this repo.
#
# Scans all .kicad_pcb files for KICAD10_3DMODEL_DIR references, then fetches
# only the required .3dshapes directories from KiCad's GitLab.
#
# Usage:  bash scripts/ci/fetch-3d-models.sh [target-dir]
# Default target: .cache/3dmodels
#
# The caller should set KICAD10_3DMODEL_DIR=<target-dir> when running kicad-cli.

set -euo pipefail

TARGET="${1:-.cache/3dmodels}"
KICAD_3D_REPO="https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master"

mkdir -p "$TARGET"

needed_libs=$(grep -roh '\${KICAD10_3DMODEL_DIR}/[^/]*\.3dshapes' boards/ 2>/dev/null \
  | sed 's|.*3DMODEL_DIR}/||' \
  | sort -u)

if [ -z "$needed_libs" ]; then
  echo "No 3D model libraries referenced — nothing to download."
  exit 0
fi

needed_files=$(grep -roh '\${KICAD10_3DMODEL_DIR}/[^"]*\.step' boards/ 2>/dev/null \
  | sed 's|.*3DMODEL_DIR}/||' \
  | sort -u)

echo "3D model files needed:"
echo "$needed_files" | sed 's/^/  /'
echo ""

downloaded=0
skipped=0
failed=0

while IFS= read -r file; do
  [ -z "$file" ] && continue
  lib_dir=$(dirname "$file")
  dest="$TARGET/$file"
  mkdir -p "$TARGET/$lib_dir"

  if [ -f "$dest" ]; then
    skipped=$((skipped + 1))
    continue
  fi

  url="$KICAD_3D_REPO/$file"
  echo "Downloading $file ..."
  if curl -fsSL --retry 2 -o "$dest" "$url" 2>/dev/null; then
    downloaded=$((downloaded + 1))
  else
    echo "  ⚠ Failed to download: $url"
    rm -f "$dest"
    failed=$((failed + 1))
  fi
done <<< "$needed_files"

echo ""
echo "Done: $downloaded downloaded, $skipped cached, $failed failed"
echo "KICAD10_3DMODEL_DIR=$TARGET"
