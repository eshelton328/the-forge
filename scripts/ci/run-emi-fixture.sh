#!/usr/bin/env bash
# Run gerber2ems openEMS smoke on Antmicro's stub_short example (cloned at a pinned revision).
# Usage: scripts/ci/run-emi-fixture.sh [DOCKER_IMAGE]
set -euo pipefail

IMAGE="${1:-the-forge-open-emi:local}"
GERBER2EMS_SHA="${GERBER2EMS_SHA:-9eaf3033f8adb0b468045f7177523162b388b020}"

command -v docker >/dev/null 2>&1 || {
  echo "docker required on PATH"
  exit 1
}

tmpdir="$(mktemp -d)"
cleanup() {
  rm -rf "${tmpdir}"
}
trap cleanup EXIT

git clone --quiet https://github.com/antmicro/gerber2ems.git "${tmpdir}/gerber2ems"
git -C "${tmpdir}/gerber2ems" checkout --quiet "${GERBER2EMS_SHA}"

example="${tmpdir}/gerber2ems/examples/stub_short"
test -d "${example}"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${example}:/work" \
  -w /work \
  "${IMAGE}" \
  -a

echo "OK: gerber2ems -a completed (${example})"
