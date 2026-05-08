#!/usr/bin/env bash
# Run gerber2ems openEMS smoke on Antmicro's stub_short example (cloned at a pinned revision).
# Usage: scripts/ci/run-emi-fixture.sh [DOCKER_IMAGE]
# Revisions come from emi/docker/emi-pinned-versions.env unless GERBER2EMS_SHA is preset.
set -euo pipefail

IMAGE="${1:-the-forge-open-ems:local}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VERS_ENV="${REPO_ROOT}/emi/docker/emi-pinned-versions.env"

if [[ -z "${GERBER2EMS_SHA:-}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${VERS_ENV}"
  set +a
fi

command -v docker >/dev/null 2>&1 || {
  echo "docker required on PATH"
  exit 1
}

tmpdir="$(mktemp -d)"
cleanup() {
  rm -rf "${tmpdir}"
}
trap cleanup EXIT

clone_root="${tmpdir}/gerber2ems"
git init -q "${clone_root}"
git -C "${clone_root}" remote add origin https://github.com/antmicro/gerber2ems.git
GIT_TERMINAL_PROMPT=0 git -C "${clone_root}" fetch --depth 1 origin "${GERBER2EMS_SHA}"
git -C "${clone_root}" checkout -q FETCH_HEAD

example="${clone_root}/examples/stub_short"
test -d "${example}"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "${example}:/work" \
  -w /work \
  "${IMAGE}" \
  -a

echo "OK: gerber2ems -a completed (${example})"
