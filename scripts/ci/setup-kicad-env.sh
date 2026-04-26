#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$HOME/.config/kicad/10.0"
cp /usr/share/kicad/template/sym-lib-table "$HOME/.config/kicad/10.0/"
cp /usr/share/kicad/template/fp-lib-table  "$HOME/.config/kicad/10.0/"
