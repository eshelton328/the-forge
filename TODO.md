# The Forge — Roadmap

## Vision

Bring software-grade CI/CD, simulation, documentation, and agentic workflows into PCB and hardware development.

The Forge is a KiCad monorepo that treats hardware projects with the same rigor as software: automated design checks in CI, manufacturing artifact generation, structured documentation, and reproducible workflows from schematic capture through board bring-up.

---

## Active Milestones

Tracked on the [project board](https://github.com/users/eshelton328/projects/4).

### Board Work
- Migrate tps63070-breakout into monorepo
- Fix s3-dev-board DRC/ERC violations
- Add 5V output variant for tps63070-breakout
- Standardize board project structure and README template

### Manufacturing and CI
- Add doc/render artifacts to PR workflow (schematic PDF, board renders, iBOM)
- Prototype Gerber diff in PR review
- Add DFM/manufacturability checks
- Evaluate PCB panelization workflow

### Documentation
- Create PR template with design review checklist
- Add design decision records (ADR-style)
- Create board README template

### Repo Quality
- Define hardware versioning scheme (compatible with existing `v*` release tags)
- Add library validation checks for shared libs/

### Tooling
- Improve Makefile developer commands
- Explore machine-readable board constraints

### Firmware
- Add firmware smoke tests for s3-dev-board

---

## Research and Exploration

These are directions of interest, not commitments. They become concrete issues on the project board when scoped into deliverable work.

### Electrical Simulation
- KiCad + ngspice integration for power supply validation
- LTspice for detailed analog analysis
- Qucs-S as an open-source alternative

### Power Integrity
- PI checks for buck-boost and ESP32 power domains
- Output stability simulation under load transients

### Impedance / RF / Signal Integrity
- Impedance checking workflows for controlled-impedance traces
- openEMS for field solver / RF analysis
- Signal integrity checks where board complexity warrants it

### Thermal
- FreeCAD FEM for thermal simulation
- Thermal validation workflows for power components

### EMI / EMC
- Open-source EMI analysis options
- Pre-layout EMC rule checking

### Post-Manufacturing Validation
- Reusable bring-up checklist template (rail verification, ripple/noise, load testing, thermal observations)
- Per-board validation reports and measurement logging
- Structured lessons-learned capture per revision

### CI Simulation Integration
- Fast PR checks vs. deeper milestone simulations
- Post-manufacture validation automation
- Scriptable simulation checks in Makefile and GitHub Actions

### Hardware Forge Ideas
- Unified "Cursor for hardware" concept exploration
- Integrated PCB + firmware + CAD + simulation pipeline
- Hardware digital twin workflows
- Agent-driven layout assistants
- Constraint-aware AI tooling for PCB design

---

## Tooling Stack

### Core
- **KiCad 10** — schematic capture, PCB layout, CLI automation
- **KiBot** — manufacturing output generation (Gerbers, BOM, position files, docs)
- **Make** — local development commands (`make check`, `make erc`, `make drc`, `make fab-drc`)
- **GitHub Actions** — CI/CD (PR checks, release artifact generation)
- **Python** — scripting and tooling

### Simulation (Under Evaluation)
- **ngspice** — SPICE simulation (KiCad-integrated)
- **LTspice** — analog circuit simulation
- **Qucs-S** — open-source circuit simulator
- **openEMS** — electromagnetic field solver
- **FreeCAD FEM** — thermal / mechanical simulation

### Visualization
- **KiBot exporters** — schematic PDF, PCBDraw renders, interactive BOM, STEP
- **Gerber diff tooling** — under evaluation (GrbDiff and alternatives)
- **3D render automation** — via KiBot STEP/VRML export

### Advanced (Future)
- ANSYS
- Keysight ADS
- Cadence / Sigrity
