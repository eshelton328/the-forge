# The Forge

Hardware design monorepo for KiCad PCB projects with automated CI/CD.

## Repository Structure

```
the-forge/
├── Makefile          # make check / erc / drc / fab-drc
├── boards/           # Individual board projects
│   ├── s3-dev-board/        # ESP32-S3 development board
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
| [s3-dev-board](boards/s3-dev-board/) | ESP32-S3-WROOM-1 dev board with TPS63070 buck-boost, USB-C | 4 | In Development |
| [tps63070-breakout](boards/tps63070-breakout/) | TPS63070 3.3V buck-boost breakout board | 2 | Migrated |

## CI/CD Pipeline

Every pull request automatically runs:
- **PR title** must follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat:`, `fix:`, `chore:`, `ci:`)
- **ERC** (Electrical Rules Check) on schematics
- **DRC** (Design Rules Check) against multiple fab house rules (JLCPCB, PCBWay)

The KiCad workflow always runs, but it only **executes** ERC/DRC for boards that are in scope: changes under `boards/<name>/` check only those boards, while changes to `libs/`, `fab-rules/`, `kibot/`, `scripts/`, the root `Makefile`, or `.github/workflows/pr-checks.yml` trigger checks on all boards. Doc-only diffs (e.g. just `README.md`) skip the heavy KiCad jobs to save time.

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

From the repository root, the **Makefile** is the usual entry point. **Each command checks one board** — the one named by `BOARD` (default: `s3-dev-board`). Nothing scans every board unless you ask for that explicitly.

```bash
make help           # list targets
make list-boards    # show board folder names you can pass as BOARD=...

# Default single board (s3-dev-board)
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

Raw commands (equivalent to the Makefile):

```bash
kicad-cli sch erc --exit-code-violations --format json -o boards/s3-dev-board/erc.json \
  boards/s3-dev-board/s3-dev-board.kicad_sch

kicad-cli pcb drc --exit-code-violations --refill-zones --schematic-parity --format json \
  -o boards/s3-dev-board/drc-default.json boards/s3-dev-board/s3-dev-board.kicad_pcb

./scripts/run-drc-all-fabs.sh boards/s3-dev-board
```

### Adding a new board

1. Create a new directory under `boards/`
2. Add a `board.yml` with layer count and fab targets
3. If using shared libraries, create project-local `fp-lib-table` / `sym-lib-table` pointing to `../../libs/`
4. Push a PR -- CI will automatically run checks

## Fab House Rules

DRC rules for each fab house are stored in `fab-rules/` as `.kicad_dru` files. CI swaps these in and runs DRC to tell you which fabs your design is compatible with.

| Fab House | Rule File | Source |
|-----------|-----------|--------|
| JLCPCB (2-layer) | `jlcpcb-2layer.kicad_dru` | [labtroll/KiCad-DesignRules](https://github.com/labtroll/KiCad-DesignRules) + [JLCPCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) |
| JLCPCB (4-layer) | `jlcpcb-4layer.kicad_dru` | [labtroll/KiCad-DesignRules](https://github.com/labtroll/KiCad-DesignRules) |
| PCBWay (2-layer) | `pcbway-2layer.kicad_dru` | [pcbway/PCBWay-Design-Rules](https://github.com/pcbway/PCBWay-Design-Rules) + [PCBWay Capabilities](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_Capabilities.html) |
| PCBWay (4-layer) | `pcbway-4layer.kicad_dru` | [pcbway/PCBWay-Design-Rules](https://github.com/pcbway/PCBWay-Design-Rules) |
