# Unified KiCad + ngspice Docker image

**Status:** **Done** — [#62](https://github.com/eshelton328/the-forge/issues/62).

Delivered:

- [`sim/docker/Dockerfile`](../docker/Dockerfile) — `FROM` the same digest-pinned `kicad/kicad:10.0` image as CI; **`NGSPICE_DEB_VERSION`** pins the Debian `ngspice` package; Python venv + `requirements.txt` for `run_sim.py`.
- [`sim/docker/README.md`](../docker/README.md) — build, `docker run`, and Compose examples.
- **[`.github/workflows/spice-checks.yml`](../../.github/workflows/spice-checks.yml)** — SPICE jobs build this image and run export + simulation **inside** it (no host `apt install ngspice`).
- **[`scripts/sim/run-spice-in-docker.sh`](../../scripts/sim/run-spice-in-docker.sh)** — local one-command entry point.

**Out of scope:** changing ERC/DRC jobs in `pr-checks.yml` (still use the raw `KICAD_IMAGE`).
