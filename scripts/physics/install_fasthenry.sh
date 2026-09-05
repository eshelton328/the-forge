#!/usr/bin/env bash
# Build the checked free WR distribution into a caller-selected directory.
set -euo pipefail
BUILD_DIR="${1:?Usage: install_fasthenry.sh BUILD_DIRECTORY}"
mkdir -p "$BUILD_DIR"
ARCHIVE="$BUILD_DIR/fasthenry.tar.gz"
curl --fail --location --silent --show-error \
  https://raw.githubusercontent.com/wrcad/xictools/master/fasthenry/fasthenry-3.0wr-031424.tar.gz \
  -o "$ARCHIVE"
python3 - "$ARCHIVE" <<'PY'
import hashlib,sys
from pathlib import Path
expected='6da40d0e31425bca85be46434b33ecc194205d705b47f4459d91568c9f4301ef'
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()!=expected:
    raise SystemExit('FastHenry archive SHA-256 mismatch; do not build')
PY
tar -xzf "$ARCHIVE" -C "$BUILD_DIR"
make -C "$BUILD_DIR/fasthenry-3.0wr" clean
# Use the scalar path and conservative aliasing on both platforms. The legacy
# default GCC/AVX build crashes on the Linux runner's multi-conductor meshes.
make -C "$BUILD_DIR/fasthenry-3.0wr" -j2 all CC=clang \
  CFLAGS='-O2 -fno-strict-aliasing -DFOUR'
printf '%s\n' "$BUILD_DIR/fasthenry-3.0wr/bin/fasthenry"
