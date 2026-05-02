#!/usr/bin/env bash
# Run SPICE export + simulation inside the unified sim image (issue #62).
# Usage: scripts/sim/run-spice-in-docker.sh --board <name> | --fixture
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IMAGE="${SIM_DOCKER_IMAGE:-the-forge-sim:local}"

ensure_image() {
  if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    echo "Building ${IMAGE} from sim/docker/Dockerfile …"
    docker build -t "${IMAGE}" -f "${ROOT}/sim/docker/Dockerfile" "${ROOT}"
  fi
}

run_board() {
  local board="$1"
  ensure_image
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/workspace/.kicad-ci-home \
    -e BOARD="${board}" \
    -e SIM_KICAD_DOCKER_IMAGE="${IMAGE}" \
    -v "${ROOT}:/workspace" \
    -w /workspace \
    "${IMAGE}" \
    bash -c '
      set -euo pipefail
      source /workspace/scripts/ci/setup-kicad-env.sh
      python3 /workspace/scripts/sim/export_kicad_spice.py --board-dir "/workspace/boards/$BOARD"
      python3 /workspace/scripts/sim/run_sim.py \
        --config "/workspace/boards/$BOARD/sim.yml" \
        --report "/workspace/boards/$BOARD/docs/spice-report.md"
    '
}

run_fixture() {
  ensure_image
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/workspace/.kicad-ci-home \
    -v "${ROOT}:/workspace" \
    -w /workspace \
    "${IMAGE}" \
    python3 /workspace/scripts/sim/run_sim.py \
      --config /workspace/sim/fixtures/rc_divider/sim.yml \
      --report /workspace/sim/fixtures/rc_divider/spice-report.md
}

usage() {
  echo "Usage: $0 --board <board_name> | --fixture" >&2
  exit 1
}

case "${1:-}" in
  --board)
    [[ -n "${2:-}" ]] || usage
    run_board "$2"
    ;;
  --fixture)
    run_fixture
    ;;
  *)
    usage
    ;;
esac
