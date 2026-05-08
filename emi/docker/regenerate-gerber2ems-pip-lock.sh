#!/usr/bin/env bash
# Rebuild gerber2ems-pip.lock.txt and gerber2ems-pip-constraints.txt after changing
# GERBER2EMS_SHA in emi-pinned-versions.env. Requires Docker. Long-running (network + pip-compile).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/emi-pinned-versions.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "missing ${ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [[ -z "${GERBER2EMS_SHA:-}" ]]; then
  echo "GERBER2EMS_SHA unset in ${ENV_FILE}" >&2
  exit 1
fi

DEBIAN_DIGEST="sha256:35b8ff74ead4880f22090b617372daff0ccae742eb5674455d542bef71ef1999"

docker run --rm -v "${SCRIPT_DIR}:/out" "debian:trixie@${DEBIAN_DIGEST}" bash -lc "
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git >/dev/null
python3 -m venv /tmp/v
. /tmp/v/bin/activate
pip install -q pip-tools
printf '%s\n' 'git+https://github.com/antmicro/gerber2ems.git@${GERBER2EMS_SHA}' > /tmp/req.in
pip-compile /tmp/req.in -o /out/gerber2ems-pip.lock.txt --resolver=backtracking
"

python3 << PY
import re
from pathlib import Path
lock_path = Path("${SCRIPT_DIR}") / "gerber2ems-pip.lock.txt"
out_path = Path("${SCRIPT_DIR}") / "gerber2ems-pip-constraints.txt"
text = lock_path.read_text()
pins = []
for line in text.splitlines():
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    if s.startswith("gerber2ems "):
        continue
    if re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*==", s):
        pins.append(s.split()[0])
    elif " @ " in s:
        pins.append(s)
pins = sorted(set(pins), key=str.lower)
header = (
    "# Transitive pins for \`pip install -c ... .\` when installing gerber2ems into the openEMS venv.\\n"
    "# Generated from gerber2ems-pip.lock.txt (same GERBER2EMS_SHA as emi-pinned-versions.env).\\n"
    "# Regenerate: bash emi/docker/regenerate-gerber2ems-pip-lock.sh (from repo root)\\n\\n"
)
out_path.write_text(header + "\\n".join(pins) + "\\n")
print(f\"Wrote {len(pins)} pins to {out_path}\")
PY

echo "OK: refreshed gerber2ems pip lock and constraints under ${SCRIPT_DIR}"
