# Simulation CI

Ngspice-based regression tests driven by per-board **`sim.yml`** (opt-in), aligned with **`checks.yml`**.

## Implemented (slices)

| Slice | Issue | What shipped |
| ------ | ----- | ------------ |
| Fixture runner | [#44](https://github.com/eshelton328/the-forge/issues/44) | `scripts/sim/run_sim.py`, `sim/fixtures/rc_divider`, **`make sim-fixture`** |
| Assembly + overlay | [#45](https://github.com/eshelton328/the-forge/issues/45) | `assemble.py`, `boards/<name>/sim/overlay.cir` |
| KiCad → `.cir` | [#46](https://github.com/eshelton328/the-forge/issues/46) | `export_kicad_spice.py`, **`make sim-export-board`**, **`make sim-board`** |
| Board models + scenarios | [#47](https://github.com/eshelton328/the-forge/issues/47) (+ PR [#53](https://github.com/eshelton328/the-forge/pull/53)) | Vendor `libs/spice/`, `tps63070-breakout` transient/DC checks |
| PR workflow | [#48](https://github.com/eshelton328/the-forge/issues/48) | [`.github/workflows/spice-checks.yml`](https://github.com/eshelton328/the-forge/blob/main/.github/workflows/spice-checks.yml), [`.github/scripts/detect-spice-boards.sh`](https://github.com/eshelton328/the-forge/blob/main/.github/scripts/detect-spice-boards.sh) |
| Docs + toolchain in reports | [#49](https://github.com/eshelton328/the-forge/issues/49) | This README as runbook; report lists **KiCad CLI**, **pinned Docker image** (when `SIM_KICAD_DOCKER_IMAGE` is set), **ngspice**; [Docker backlog stub](BACKLOG-docker-image.md) |

**Defer (PRD):** compare metrics to a `main` baseline in PR comments — only if prioritized later.

---

## How it works

1. **Optional `boards/<name>/sim.yml`** — `spec_version: 1`, `spice_engine: ngspice`, either `netlist:` (single deck) or `assembly:` (export + includes + `sim/overlay.cir`), then `scenarios` with DC `op_node` and/or `.measure` limits.
2. **`export_kicad_spice.py`** — writes gitignored **`sim/kicad_export.cir`** and **`sim/kicad_export_toolchain.txt`** (first line of `kicad-cli --version`) under the board.
3. **`run_sim.py`** — assembles if needed, runs **`ngspice -b`**, writes markdown via **`scripts/sim/report_md.py`**. Reports include **ngspice** version (`ngspice --version`), **KiCad CLI** line when the export step ran, and **`SIM_KICAD_DOCKER_IMAGE`** when set (CI passes the same digest as `KICAD_IMAGE` in `spice-checks.yml`).
4. **CI** — `spice-board` matrix runs export in **`KICAD_IMAGE`**, then host **`apt install ngspice`**, then Python. Artifacts per board: `docs/spice-report.md`, `sim/assembled.cir`, `sim/kicad_export.cir`. **`spice-fixture`** runs the RC divider only when `detect-spice-boards.sh` sets `run_fixture` (diff touches `sim/fixtures/`, or diff touches `scripts/sim/` while **no** board has `sim.yml` yet); **otherwise that job is skipped**, which is normal.

**KiCad Design Checks** (`pr-checks.yml`) may skip matrix jobs when the PR does not touch their watched paths (e.g. doc-only changes or edits limited to `spice-checks.yml`); see workflow comments there.

---

## Layout (as in repo)

```text
sim/
├── README.md                    # This runbook
├── BACKLOG-docker-image.md      # Optional Dockerfile spike (see #19)
scripts/sim/
├── run_sim.py
├── export_kicad_spice.py
├── assemble.py
├── report_md.py                 # Markdown report
├── ngspice_runner.py
├── config.py
├── measure_parse.py
└── …
libs/spice/                      # Vendor models + README
boards/<name>/
├── sim.yml                      # Opt-in
├── sim/
│   ├── overlay.cir              # When using assembly
│   ├── kicad_export.cir       # gitignored — generated
│   └── kicad_export_toolchain.txt  # gitignored — kicad-cli --version
└── docs/
    └── spice-report.md          # gitignored if generated locally; CI artifact
```

---

## Maintainer checklist

- [ ] **Pin KiCad:** set `KICAD_IMAGE` digest in `spice-checks.yml` (and `pr-checks.yml` / `Makefile`) together when bumping KiCad.
- [ ] **Board opts in:** add `sim.yml` + `sim/overlay.cir` if using `assembly`; symbols need `Sim.*` fields for spicemodel export (`libs/symbols/…`).
- [ ] **Shared paths:** changing `libs/spice/`, `scripts/sim/`, `sim/fixtures/`, etc. retriggers all boards with `sim.yml` — see detect script.
- [ ] **Reports:** optional commit of `docs/spice-report.md` on `main` for diff visibility; default is artifact-only.

---

## Future (not scheduled)

- **Phase 2:** `sim/parasitics_*.cir` includes for layout-aware decks.
- **One Docker image:** [BACKLOG-docker-image.md](BACKLOG-docker-image.md) / [#19](https://github.com/eshelton328/the-forge/issues/19).

---

## Related

- Example report narrative: `boards/tps63070-breakout/docs/spice-report-example.md`
- Board validation (ERC/DRC): `boards/*/checks.yml`, `scripts/validate_board.py`
