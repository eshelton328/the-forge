# The Forge

Hardware design monorepo for KiCad PCB projects with automated CI/CD.

## Repository Structure

```
the-forge/
├── Makefile          # make check / erc / drc / fab-drc
├── boards/           # Individual board projects
│   ├── esp32s3-devkit/        # ESP32-S3 development board
│   └── tps63070-breakout/   # TPS63070 buck-boost breakout
├── fab-rules/        # DRC rule templates per fab house
├── kibot/            # KiBot output generation configs
├── libs/             # Shared libraries (symbols, footprints, 3D models)
├── scripts/          # Automation scripts
└── .github/workflows # CI/CD pipelines
```

## Boards

| Board | Description | Layers | Status |
|-------|-------------|--------|--------|
| [esp32s3-devkit](boards/esp32s3-devkit/) | ESP32-S3-WROOM-1 dev board with TPS63070 buck-boost, USB-C | 4 | In Development |
| [tps63070-breakout](boards/tps63070-breakout/) | TPS63070 3.3V buck-boost breakout board | 2 | Migrated |

## CI/CD Pipeline

Every pull request automatically runs:
- **PR title** must follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat:`, `fix:`, `chore:`, `ci:`)
- **`pytest`** on `tests/` (Python **3.12**; see [`.github/workflows/pytest.yml`](.github/workflows/pytest.yml) — Spice integration cases skip unless `ngspice`/Docker exist)
- **ERC** (Electrical Rules Check) on schematics
- **DRC** (Design Rules Check) against multiple fab house rules (JLCPCB, PCBWay)

The KiCad workflow always runs, but it only **executes** ERC/DRC for boards that are in scope: changes under `boards/<name>/` check only those boards, while changes to `libs/`, `fab-rules/`, `kibot/`, `scripts/`, the root `Makefile`, or `.github/workflows/pr-checks.yml` trigger checks on all boards. Doc-only diffs (e.g. just `README.md`) skip the heavy KiCad jobs to save time. **`pytest`** (see **`pytest.yml`**) runs on every PR regardless, so Python regressions cannot slip through doc-only merges.

On release tags, the pipeline generates:
- Fab-ready Gerber/drill ZIPs per fab house
- BOM and component placement files
- Schematic PDFs and board renders

## Local Development

### Prerequisites

```bash
brew install --cask kicad    # KiCad 10 (includes kicad-cli)
pip install kibot kikit       # Automation tools
```

### Running checks locally

From the repository root, the **Makefile** is the usual entry point. **Each command checks one board** — the one named by `BOARD` (default: `esp32s3-devkit`). Nothing scans every board unless you ask for that explicitly.

```bash
make help           # list targets
make list-boards    # show board folder names you can pass as BOARD=...

# Default single board (esp32s3-devkit)
make check
make drc

# A different board — either form (folder and .kicad_* basename must match)
make drc BOARD=other-board
make drc other-board
make check other-board

# Optional: run make check for every board under boards/ (e.g. before a release)
make check-all
```

`kicad-cli` is picked up from your `PATH` if present; on macOS it falls back to
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Override with
`KICAD_CLI=/path/to/kicad-cli make check`.

### Python tests (pytest)

```bash
pip install -r requirements.txt
python3 -m pytest tests/
```

With **`ngspice`** and **Docker** available, `tests/test_spice_run_sim_integration.py` runs end-to-end Spice smoke; otherwise those cases are **skipped** (same as default CI for `pytest.yml`).

Raw commands (equivalent to the Makefile):

```bash
kicad-cli sch erc --exit-code-violations --format json -o boards/esp32s3-devkit/erc.json \
  boards/esp32s3-devkit/esp32s3-devkit.kicad_sch

kicad-cli pcb drc --exit-code-violations --refill-zones --schematic-parity --format json \
  -o boards/esp32s3-devkit/drc-default.json boards/esp32s3-devkit/esp32s3-devkit.kicad_pcb

./scripts/run-drc-all-fabs.sh boards/esp32s3-devkit
```

### Adding a new board

1. Create a new directory under `boards/`
2. Add a `board.yml` with layer count and fab targets
3. If using shared libraries, create project-local `fp-lib-table` / `sym-lib-table` pointing to `../../libs/`
4. Push a PR -- CI will automatically run checks

## Fab House Rules

DRC rules for each fab house are stored in `fab-rules/` as `.kicad_dru` files. CI swaps these in and runs DRC to tell you which fabs your design is compatible with.

2-layer rules come in two tiers: **standard** (cheapest process, looser minimums) and **advanced** (tighter vias/clearances, higher cost). Each board declares which tier it targets in `board.yml`.

| Fab House | Rule File | Notes |
|-----------|-----------|-------|
| JLCPCB 2L Standard | `jlcpcb-2layer-standard.kicad_dru` | 0.3mm via drill, 0.15mm annular ring |
| JLCPCB 2L Advanced | `jlcpcb-2layer-advanced.kicad_dru` | 0.2mm via drill, 0.1mm annular ring |
| JLCPCB 4L | `jlcpcb-4layer.kicad_dru` | |
| PCBWay 2L Standard | `pcbway-2layer-standard.kicad_dru` | 0.3mm via drill, 0.45mm via pad |
| PCBWay 2L Advanced | `pcbway-2layer-advanced.kicad_dru` | 0.2mm via drill, 0.35mm via pad |
| PCBWay 4L | `pcbway-4layer.kicad_dru` | |
