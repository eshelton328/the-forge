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
| Docs + toolchain in reports | [#49](https://github.com/eshelton328/the-forge/issues/49) | This README as runbook; report lists **KiCad CLI**, **`SIM_KICAD_DOCKER_IMAGE`** when set, **ngspice**; unified image: **[`sim/docker/`](docker/)** ([BACKLOG-docker-image.md](BACKLOG-docker-image.md) status) |
| Waveform PNG artifacts | [#59](https://github.com/eshelton328/the-forge/issues/59) | Optional `sim.yml` **`plots:`** → **`wrdata`** + **`matplotlib`** under **`sim/plots/`**; **`--no-plots`** / **`SIM_NO_PLOTS`** |
| Metrics JSON sidecar | [#60](https://github.com/eshelton328/the-forge/issues/60) | **`scripts/sim/metrics_json.py`** — **`spice-report.metrics.json`** next to **`spice-report.md`** |
| pytest on PR | [#61](https://github.com/eshelton328/the-forge/issues/61) | [`.github/workflows/pytest.yml`](https://github.com/eshelton328/the-forge/blob/main/.github/workflows/pytest.yml) — **`python3 -m pytest tests/`** |
| Unified sim Docker image | [#62](https://github.com/eshelton328/the-forge/issues/62) | **`sim/docker/Dockerfile`** (KiCad digest + **`NGSPICE_DEB_VERSION`**) — CI runs export + **`run_sim.py`** inside **`the-forge-sim:ci`**; **`scripts/sim/run-spice-in-docker.sh`**, **`make sim-board-docker`** |

**Baseline deltas:** committed optional JSON per board — **[#58](https://github.com/eshelton328/the-forge/issues/58)**.

**Overlay / parasitics roadmap (research):** **[`OVERLAY-PARASITICS.md`](OVERLAY-PARASITICS.md)** — contract for **`sim/overlay.cir`**, schematic-only → manual → extraction-backed fragments on the **same** assemble hook ([**#63**](https://github.com/eshelton328/the-forge/issues/63)).

---

## How it works

1. **Optional `boards/<name>/sim.yml`** — `spec_version: 1`, `spice_engine: ngspice`, either `netlist:` (single deck) or `assembly:` (export + includes + `sim/overlay.cir`), then `scenarios` with DC `op_node` and/or **`ngspice` `.meas` outputs** from the assembled deck (e.g. **`tps63070-breakout`** uses `.op` + `.tran` in `sim/overlay.cir`; see **[#56](https://github.com/eshelton328/the-forge/issues/56)**).
2. **`export_kicad_spice.py`** — writes gitignored **`sim/kicad_export.cir`** and **`sim/kicad_export_toolchain.txt`** (first line of `kicad-cli --version`) under the board.
3. **`run_sim.py`** — assembles if needed, runs **`ngspice -b`**, writes markdown via **`scripts/sim/report_md.py`**, plus a **`spice-report.metrics.json`** sidecar (**[#60](https://github.com/eshelton328/the-forge/issues/60)**). Reports include **ngspice** version (`ngspice --version`), **KiCad CLI** line when the export step ran, and **`SIM_KICAD_DOCKER_IMAGE`** when set (CI sets it to **`the-forge-sim:ci`**, the tag built from **`sim/docker/Dockerfile`**). If **`boards/<name>/sim/spice_metrics_baseline.json`** exists (committed snapshot), reports add **Baseline** and **Δ** columns plus `SIM_BASELINE_COMPARE=true` in the footer (`--no-baseline` skips; `--baseline PATH` overrides; **`--write-baseline PATH`** refreshes the file after a green run). Optional **`plots:`** runs a second ngspice pass and writes PNGs plus a **Waveform plots** section (**[#59](https://github.com/eshelton328/the-forge/issues/59)**; **`--no-plots`** / **`SIM_NO_PLOTS=1`** skips).
4. **CI** — **`spice-board`** builds **`sim/docker/Dockerfile`** once, then runs export + **`run_sim.py`** for each in-scope board inside **`the-forge-sim:ci`** (**[#62](https://github.com/eshelton328/the-forge/issues/62)**). Workflow uploads **`spice-boards`** (per-board subfolders: `docs/spice-report.md`, **`docs/spice-report.metrics.json`**, `sim/assembled.cir`, `sim/kicad_export.cir`). When **`sim/plots/*.png`** exist, artifact **`spice-plots`** contains `/<board>/*.png`. **`spice-fixture`** uses the same image for the RC divider when `detect-spice-boards.sh` sets `run_fixture` (diff touches `sim/fixtures/`, or diff touches `scripts/sim/` while **no** board has `sim.yml` yet); **otherwise that job is skipped**, which is normal.

**KiCad Design Checks** (`pr-checks.yml`) may skip matrix jobs when the PR does not touch their watched paths (e.g. doc-only changes or edits limited to `spice-checks.yml`); see workflow comments there.

**Python tests (`pytest.yml`, [#61](https://github.com/eshelton328/the-forge/issues/61)):** runs on **every PR** — Python **3.12**, `pip install -r requirements.txt`, then **`pytest tests/`**. **`test_spice_run_sim_integration`** is **`skip`**ped when **`ngspice`** or **Docker** is unavailable (normal on this runner), so regressions covered there remain the responsibility of **`spice-checks.yml`** and local smoke runs. No KiCad Docker image is pulled for this job.

---

## Layout (as in repo)

```text
sim/
├── README.md
├── OVERLAY-PARASITICS.md           # Overlay contract + parasitic evolution (#63)
├── BACKLOG-docker-image.md
└── docker/                         # Dockerfile, compose, image README (#62)

scripts/sim/
├── run-spice-in-docker.sh         # Local all-in-container export + sim (#62)
├── run_sim.py
├── export_kicad_spice.py
├── assemble.py
├── report_md.py
├── ngspice_runner.py
├── config.py
├── measure_parse.py
├── baseline_metrics.py            # Optional baseline JSON (#58)
├── metrics_json.py
├── plot_extractions.py
└── …

scripts/ci/
└── run-spice-boards-docker.sh      # CI: loop boards in BOARDS_JSON (#62)

libs/spice/                         # Vendor models + README
boards/<name>/
├── sim.yml
├── sim/
│   ├── overlay.cir
│   ├── plots/
│   ├── spice_metrics_baseline.json
│   ├── kicad_export.cir
│   └── kicad_export_toolchain.txt
└── docs/
    ├── spice-report.md
    └── spice-report.metrics.json
```

---

## Maintainer checklist

- [ ] **Pin KiCad:** set `KICAD_IMAGE` digest in **`sim/docker/Dockerfile`** `FROM`, `spice-checks.yml`, `pr-checks.yml`, `update-readmes.yml`, and **`Makefile`** together when bumping KiCad.
- [ ] **Pin ngspice (Debian):** when rebasing **`sim/docker/Dockerfile`** on a new KiCad image, re-check `NGSPICE_DEB_VERSION` with `docker run --rm <KICAD_DIGEST> apt-cache policy ngspice`.
- [ ] **Board opts in:** add `sim.yml` + `sim/overlay.cir` if using `assembly`; symbols need `Sim.*` fields for spicemodel export (`libs/symbols/…`).
- [ ] **Shared paths:** changing `libs/spice/`, `scripts/sim/`, `sim/fixtures/`, etc. retriggers all boards with `sim.yml` — see detect script.
- [ ] **Reports:** optional commit of `docs/spice-report.md` (and **`spice-report.metrics.json`**) on `main` for diff visibility; default is artifact-only.
- [ ] **Baselines:** if the board commits `sim/spice_metrics_baseline.json`, refresh after intentional schematic or vendor-model changes (`run_sim.py --write-baseline …` only after a **green** run).
- [ ] **Waveform PNGs:** `sim.yml` **`plots:`** needs **`matplotlib`** in the environment (`requirements.txt`); ngspice refuses `wrdata` into missing dirs — runner creates `sim/plots/_data/` automatically.

---

## Future (not scheduled)

- **Layout-aware decks:** follow **[`OVERLAY-PARASITICS.md`](OVERLAY-PARASITICS.md)** — evolve **`sim/overlay.cir`** (and optional `sim/*.cir` includes pulled from it); same CI driver. Spawn a **tool-specific issue** when an extractor is chosen.

---

## Baseline snapshots (`sim/spice_metrics_baseline.json`)

Optional committed JSON under the board **`sim/`** directory. Tracks **[#58](https://github.com/eshelton328/the-forge/issues/58)**.

- **`baseline_version`:** must be **`1`**.
- **`measures`:** object mapping **`"<scenario_id>::<measure_id>"`** → numeric baseline value (same identifiers as `sim.yml`).
- **`ref`:** optional short string for humans (e.g. note or `main` SHA); shown in report metadata.

**CLI:** **`--write-baseline PATH`** emits a fresh snapshot after limits pass; **`--write-baseline-ref`** sets `ref`. The default compares against **`sim/spice_metrics_baseline.json`** when present; **`--no-baseline`** skips; **`--baseline OTHER.json`** selects another file (**hard error** if missing or invalid).

---

## Waveform plots (`sim/plots/*.png`, issue #59)

Optional top-level **`plots:`** in `sim.yml` — list of **`file`** (simple `*.png` basename) and **`signal`** (ngspice expression, e.g. `v(/net)`). After a **green** simulation, `run_sim.py` runs one extra ngspice pass with **`wrdata`**, then **`matplotlib`** renders PNGs under **`boards/<name>/sim/plots/`** (gitignored). Failures are **`stderr` warnings** only; use **`--no-plots`** or env **`SIM_NO_PLOTS=1`** to skip. CI uploads a separate artifact when any `*.png` exists (see `spice-checks.yml`).

---

## Metrics sidecar (`spice-report.metrics.json`, issue #60)

Emitted alongside **`spice-report.md`** on every **`run_sim.py`** run (fixture or board).

- **`metrics_schema_version`:** **`1`** today; bump only when incompatible field changes occur.
- **`pass`**, **`exit_code_hint`:** align with markdown footer semantics (all measure rows **`passed`** ⇒ pass / hint `0`; otherwise **`false`** / **`1`**). Same shape as **`SIM_REPORT_VERSION=1`** block in the report.
- **`paths`:** **`config`** and **`netlist`** as posix strings (whatever paths **`run_sim.py`** used).
- **`toolchain`:** **`ngspice_version_line`**, **`kicad_cli_version_line`** or **`null`**, **`kicad_docker_image`** from **`SIM_KICAD_DOCKER_IMAGE`** or **`null`**, **`simulator_exit_code`**, **`baseline_compare_enabled`**.
- **`baseline`:** **`null`** when comparison off; otherwise **`baseline_file_rel`**, **`doc_ref`** (**`null`** if absent).
- **`measures`:** per row — **`scenario_id`**, **`measure_id`**, **`value_str`**, **`value_numeric`** (parsed float or **`null`** if not parseable, e.g. missing), **`bounds_min`** / **`bounds_max`**, **`passed`**, **`detail`**. With baseline compare enabled, **`measure_key`** (**`scenario::measure`**) and **`baseline_numeric`** (or **`null`** if key missing).
- **`waveform_pngs_rel`:** optional list when optional plots ran (**[#59](https://github.com/eshelton328/the-forge/issues/59)**).

Treat this file as stability-sensitive for dashboards; bump **`metrics_schema_version`** explicitly when renaming or removing keys.

---

## Related

- Example report narrative: `boards/tps63070-breakout/docs/spice-report-example.md`
- Board validation (ERC/DRC): `boards/*/checks.yml`, `scripts/validate_board.py`
