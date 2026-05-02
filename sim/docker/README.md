# Unified sim Docker image

Derived from the same digest-pinned `kicad/kicad:10.0` image used in CI (see [`Dockerfile`](./Dockerfile): `FROM …@sha256:…`), with:

- **ngspice** — Debian package version pinned via `NGSPICE_DEB_VERSION` (`ARG` in the Dockerfile; bump when the base OS changes packages).
- **Python** — virtualenv at `/opt/the-forge-sim` with [`requirements.txt`](../../requirements.txt) (`pyyaml`, `pytest`, `matplotlib`) for `scripts/sim/run_sim.py`.

## Pins (keep in sync)

| Pin | Where |
| --- | ----- |
| KiCad image digest | `Dockerfile` `FROM`, `.github/workflows/pr-checks.yml`, `spice-checks.yml`, `update-readmes.yml`, `Makefile` `KICAD_IMAGE` |
| ngspice Debian version | `Dockerfile` `NGSPICE_DEB_VERSION` |

## Build

From the **repository root**:

```bash
docker build -t the-forge-sim:local -f sim/docker/Dockerfile .
```

## Run export + board sim (one shot)

Replace `tps63070-breakout` with your board (must have `boards/<name>/sim.yml`):

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/workspace/.kicad-ci-home \
  -e BOARD=tps63070-breakout \
  -e SIM_KICAD_DOCKER_IMAGE=the-forge-sim:local \
  -v "$PWD:/workspace" \
  -w /workspace \
  the-forge-sim:local \
  bash -c '
    set -euo pipefail
    source /workspace/scripts/ci/setup-kicad-env.sh
    python3 /workspace/scripts/sim/export_kicad_spice.py --board-dir "/workspace/boards/$BOARD"
    python3 /workspace/scripts/sim/run_sim.py \
      --config "/workspace/boards/$BOARD/sim.yml" \
      --report "/workspace/boards/$BOARD/docs/spice-report.md"
  '
```

## Docker Compose

From `sim/docker/`:

```bash
docker compose build
docker compose run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/workspace/.kicad-ci-home \
  -e BOARD=tps63070-breakout \
  -e SIM_KICAD_DOCKER_IMAGE=the-forge-sim:local \
  sim \
  bash -c '
    set -euo pipefail
    source /workspace/scripts/ci/setup-kicad-env.sh
    python3 /workspace/scripts/sim/export_kicad_spice.py --board-dir "/workspace/boards/$BOARD"
    python3 /workspace/scripts/sim/run_sim.py \
      --config "/workspace/boards/$BOARD/sim.yml" \
      --report "/workspace/boards/$BOARD/docs/spice-report.md"
    '
```

Fixture-only (no KiCad):

```bash
docker compose run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/workspace/.kicad-ci-home \
  sim \
  python3 /workspace/scripts/sim/run_sim.py \
    --config /workspace/sim/fixtures/rc_divider/sim.yml \
    --report /workspace/sim/fixtures/rc_divider/spice-report.md
```

## Convenience wrapper

[`scripts/sim/run-spice-in-docker.sh`](../../scripts/sim/run-spice-in-docker.sh) — `--board <name>` or `--fixture` (builds the image if `the-forge-sim:local` is missing).

The unified image uses **Python 3.13** (KiCad base); **`pytest.yml`** still runs tests on **3.12** — simulation numerics should be engine-driven, not Python-version–sensitive.

Tracks [#62](https://github.com/eshelton328/the-forge/issues/62).
