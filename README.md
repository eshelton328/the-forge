# circuit-forge

Hardware design monorepo for KiCad PCB projects with automated CI/CD.

## Repository Structure

```
circuit-forge/
├── boards/           # Individual board projects
│   └── s3-dev-board/ # ESP32-S3 development board
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

## CI/CD Pipeline

Every pull request automatically runs:
- **ERC** (Electrical Rules Check) on schematics
- **DRC** (Design Rules Check) against multiple fab house rules (JLCPCB, PCBWay)

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

```bash
# ERC
kicad-cli sch erc --exit-code-violations boards/s3-dev-board/s3-dev-board.kicad_sch

# DRC with default rules
kicad-cli pcb drc --exit-code-violations boards/s3-dev-board/s3-dev-board.kicad_pcb

# DRC against all target fab houses
bash scripts/run-drc-all-fabs.sh boards/s3-dev-board
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
| JLCPCB (4-layer) | `jlcpcb-4layer.kicad_dru` | [Cimos/KiCad-CustomDesignRules](https://github.com/Cimos/KiCad-CustomDesignRules) |
| PCBWay (4-layer) | `pcbway-4layer.kicad_dru` | [Cimos/KiCad-CustomDesignRules](https://github.com/Cimos/KiCad-CustomDesignRules) |
