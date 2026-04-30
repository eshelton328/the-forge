# Backlog: unified KiCad + ngspice Docker image

**Status:** Not started — tracked for repo-quality / CI-local parity ([#19](https://github.com/eshelton328/the-forge/issues/19)).

Today, **KiCad** runs in the pinned `KICAD_IMAGE` from `.github/workflows/spice-checks.yml` / `pr-checks.yml`, while **ngspice** is installed via `apt` on the GitHub-hosted runner after export. Local developers match that with Docker for KiCad plus Homebrew or system `ngspice`.

**Goal:** Spike a single `Dockerfile` `FROM` the same digest-pinned KiCad image, layer in a pinned **ngspice** build or distro package, and document one command to run `export_kicad_spice.py` + `run_sim.py` so CI and laptops share one toolchain story.

**Out of scope for this doc:** changing ERC/DRC jobs (unless the spike proves a net win).
