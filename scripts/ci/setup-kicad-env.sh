#!/usr/bin/env bash
# Install global KiCad lib tables so kicad-cli can resolve default libraries.
# The "10.0" config path and template locations are coupled to the pinned
# kicad/kicad:10.0@sha256:… Docker image in pr-checks.yml — update both together.
set -euo pipefail
mkdir -p "$HOME/.config/kicad/10.0"
cp /usr/share/kicad/template/sym-lib-table "$HOME/.config/kicad/10.0/"
cp /usr/share/kicad/template/fp-lib-table  "$HOME/.config/kicad/10.0/"
