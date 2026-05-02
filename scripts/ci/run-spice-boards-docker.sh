#!/usr/bin/env bash
# Run export + run_sim.py for each board in BOARDS_JSON (JSON array of folder names).
# Requires a pre-built image tag (default the-forge-sim:ci) with KiCad + ngspice + Python venv.
set -euo pipefail

: "${BOARDS_JSON:?BOARDS_JSON must be set to a JSON array of board names}"
: "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE must be set}"
ROOT="${GITHUB_WORKSPACE}"
IMAGE="${SIM_DOCKER_IMAGE:-the-forge-sim:ci}"
SIM_KICAD_DOCKER_IMAGE="${SIM_KICAD_DOCKER_IMAGE:-$IMAGE}"

failed=0
while IFS= read -r board; do
  [[ -z "${board}" ]] && continue
  echo "=== SPICE board: ${board} ==="
  if ! docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/workspace/.kicad-ci-home \
    -e BOARD="${board}" \
    -e SIM_KICAD_DOCKER_IMAGE \
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
    '; then
    failed=1
  fi
done < <(echo "${BOARDS_JSON}" | jq -r '.[]')

exit "${failed}"
