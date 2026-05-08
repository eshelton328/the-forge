# Open-source EMS (openEMS + gerber2ems)

This folder wires **[openEMS](https://www.openems.de/)** (FDTD field solver) and Antmicro’s **[gerber2ems](https://github.com/antmicro/gerber2ems)** (Gerber → geometry → simulation) into the repo so we can run **repeatable electromagnetic simulation smoke** locally and in CI — the sort of **open-source EMS** toolchain useful for SI and **EMI-adjacent** engineering (fields, coupling, wideband structure behavior), not a branded “Open EMI” product.

## Scope

**openEMS** is an **electromagnetic solver** (EMS). Results here are **not** chamber measurements or regulatory **EMI/EMC certification** (same boundary as ngspice-only flows in [`sim/README.md`](../sim/README.md)). Antmicro documents this stack primarily for PCB **signal integrity**; it still informs how energy moves and radiates compared to circuit-only models.

## Docker image

[`emi/docker/Dockerfile`](docker/Dockerfile) builds a self-contained image from build context [`emi/docker/`](docker/). **Pinned revisions:** one file of record for openEMS commit and gerber2ems SHA: [`emi/docker/emi-pinned-versions.env`](docker/emi-pinned-versions.env). The Dockerfile and [`scripts/ci/run-emi-fixture.sh`](../scripts/ci/run-emi-fixture.sh) both read those values (`GERBER2EMS_SHA` may be set in the environment before the fixture script runs to override the file).

```bash
docker build -t the-forge-open-ems:local -f emi/docker/Dockerfile emi/docker
```

## Fixture (upstream example)

We do **not** vendor Gerber slices under `emi/` yet. The CI/local script does a shallow fetch of **gerber2ems** at the pinned SHA (from [`emi/docker/emi-pinned-versions.env`](docker/emi-pinned-versions.env), unless overridden) and runs **`examples/stub_short`**:

```bash
bash scripts/ci/run-emi-fixture.sh the-forge-open-ems:local
```

Or from the Makefile: **`make emi-fixture-docker`**.

## Board-owned simulations (future)

A practical next step is `boards/<name>/emi/` with:

- `fab/` Gerbers + `stackup.json` + drill + port CSV (see gerber2ems README),
- `simulation.json` frequency sweep and mesh settings,
- optional CI matrix entry once runtime and artifacts are acceptable.

Until then, the fixture proves the toolchain stays healthy after dependency bumps.

## CI

[`.github/workflows/emi-checks.yml`](../.github/workflows/emi-checks.yml) builds the image and runs the fixture when **`emi/**`**, the workflow itself, **`scripts/ci/run-emi-fixture.sh`**, **`Makefile`**, root **`README.md`**, **`sim/README.md`**, or any of those paths change, or when you **workflow_dispatch** manually (root README/`sim/` filters keep EMI doc/Makefile drift from slipping past unchecked). First-time image builds compile openEMS and can take **many minutes**; adjust timeouts if runners struggle.
