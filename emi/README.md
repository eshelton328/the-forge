# EMI-oriented open simulation (openEMS + gerber2ems)

This folder wires **[openEMS](https://www.openems.de/)** (FDTD field solver) and Antmicro’s **[gerber2ems](https://github.com/antmicro/gerber2ems)** (Gerber → geometry → simulation) into the repo so we can run **repeatable electromagnetic regression smoke** locally and in CI.

## Naming / scope

People often say “open EMI” when they mean **open-source EM tooling** (FDTD / full-wave from layout), not a single product called “Open EMI.” Here we use the same stack Antmicro documents for PCB EM work (SI-focused with EMI-adjacent insight — energy leaving the structure, field dumps, etc.). It is **not** a substitute for **chamber measurements or regulatory sign-off** (same boundary as ngspice-only flows in [`sim/README.md`](../sim/README.md)).

## Docker image

[`emi/docker/Dockerfile`](docker/Dockerfile) builds a self-contained image (no repo context required except the Dockerfile directory). **Pinned revisions:** openEMS commit recommended by gerber2ems; gerber2ems git SHA shared with [`scripts/ci/run-emi-fixture.sh`](../scripts/ci/run-emi-fixture.sh).

```bash
docker build -t the-forge-open-emi:local -f emi/docker/Dockerfile emi/docker
```

## Fixture (upstream example)

We do **not** vendor Gerber slices under `emi/` yet. The CI/local script clones **gerber2ems** at the pinned SHA and runs **`examples/stub_short`**:

```bash
bash scripts/ci/run-emi-fixture.sh the-forge-open-emi:local
```

Or from the Makefile: **`make emi-fixture-docker`**.

## Board-owned simulations (future)

A practical next step is `boards/<name>/emi/` with:

- `fab/` Gerbers + `stackup.json` + drill + port CSV (see gerber2ems README),
- `simulation.json` frequency sweep and mesh settings,
- optional CI matrix entry once runtime and artifacts are acceptable.

Until then, the fixture proves the toolchain stays healthy after dependency bumps.

## CI

[`.github/workflows/emi-checks.yml`](../.github/workflows/emi-checks.yml) builds the image and runs the fixture when **`emi/**`**, the workflow file, or **`scripts/ci/run-emi-fixture.sh`** changes, or when you **workflow_dispatch** manually. First-time image builds compile openEMS and can take **many minutes**; adjust timeouts if runners struggle.
