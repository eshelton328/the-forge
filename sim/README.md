# Simulation CI — design for scale

**Implemented (issue [#44](https://github.com/eshelton328/the-forge/issues/44)):** Fixture-only runner — `scripts/sim/run_sim.py` reads `sim.yml`, runs `ngspice -b` on a `.cir` netlist, checks limits against either **`.`measure`** output lines (`measure_id=value`) **or** DC **OP table** voltages (`op_node`). Example: `sim/fixtures/rc_divider/` and **`make sim-fixture`**. **`make`** runs with a **minimal PATH** — the Makefile prepends `/opt/homebrew/bin` so Homebrew **`ngspice`** is visible after `brew install ngspice`.

**Implemented (issue [#46](https://github.com/eshelton328/the-forge/issues/46)):** KiCad schematic → SPICE — `scripts/sim/export_kicad_spice.py` runs `kicad-cli sch export netlist --format spicemodel` when using `Sim.*` models (fallback `--netlist-format spice` for passive-only stubs), flattens the KiCad `.subckt`/`… .ends` wrapper and drops duplicated vendor `.include` lines, strips a trailing `.end`, and writes `boards/<name>/sim/kicad_export.cir` consumed by **`assemble.py`**. Symbols need **`Sim.Type`/`Sim.Name`/`Sim.Pins`/`Sim.Library`** (see `libs/symbols/TPS630701-Buck-Boost.kicad_sym` and placement on `TPS630701` in the board schematic). **`make sim-export-board BOARD=…`** uses the same **`KICAD_IMAGE`** / Docker volume pattern as **`.github/workflows/pr-checks.yml`**. **`make sim-board`** runs export then **`run_sim.py`** for boards with **`sim.yml`**.

This repo already scales **hardware checks** like this:

- **`boards/<name>/checks.yml`** — per-board YAML consumed by **`scripts/validate_board.py`**
- **`.github/workflows/pr-checks.yml`** — detects which `boards/<name>/` trees changed; runs ERC/DRC/validation selectively

Simulation should follow the **same pattern**: one **reusable runner** + optional **per-board config**, not one-off scripts per PCB.

---

## Goals

| Goal | Approach |
|------|----------|
| **Reuse tooling** across boards | Repo-level `scripts/sim/` (`run_sim.py`) + Docker or pinned **`ngspice`** |
| **Per-board specificity** | `boards/<name>/sim.yml` (limits, scenarios, nets to plot) |
| **Phase 1 first** | Schematic/exported netlist + vendor `.lib` — regressions vs numeric limits |
| **Phase 2 later** | Optional **parasitic overlay** `.cir` or `.include`, versioned beside board |
| **CI fit** | Same **board detection** as KiCad checks; optionally **narrow** paths to include `libs/spice/` when shared models change |

Non-goals (initially): proprietary full-board extraction SI suites; EMI sign-off.

---

## Proposed layout

```text
sim/
└── README.md                 # This file — architecture only

libs/spice/
├── README.md                  # Licensing, TI pack provenance, version pins
├── tps63070/                  # Vendor tree or gitignored mirror + symlink
│   └── TPS63070_TRANS.LIB   # (example — populate per license)

scripts/sim/
├── run_sim.py               # Orchestrator: assemble netlist paths, invoke ngspice, evaluate limits
├── report.py                # Render markdown + optional machine footer
├── lib/                       # Helpers (parse ngspice log, jitter tolerance)
└── templates/
    └── spice-report.md.j2   # Or string template for report skeleton

boards/<name>/
├── sim.yml                   # OPTIONAL — declares tests + limits when board opts in
├── sim/                      # OPTIONAL — overlays not auto-exported from .kicad_sch
│   └── parasitics_revA.cir  # Phase 2: .include after export
├── docs/
│   └── spice-report.md       # OPTIONAL committed snapshot on main (PR diff)
└── *.kicad_sch …             # Source of schematic netlist
```

**Naming:** `sim.yml` mirrors **`checks.yml`** — easy to grep and extend discovery in **`tests/`**.

---

## Responsibilities split

### Shared ( **`scripts/sim/`**, **`libs/spice/`** )

- Spawn **`ngspice -b`** (batch), capture exit status + logs
- **`Measure`** / grep rules from config → **PASS/FAIL**
- Markdown report + optional **`REPORT_VERSION=1`** footer for downstream tooling
- **`kicad-cli`** export via **`export_kicad_spice.py`** + **`make sim-export-board`** (Docker image pinned like ERC)
- **`libs/spice`** holds **deduplicated** vendor libraries (paths referenced by **`sim.yml`**, not duplicated per board when possible)

### Per board (**`boards/<name>/sim.yml`**)

Minimal useful shape (illustrative; evolve with implementation):

```yaml
# boards/tps63070-breakout/sim.yml — sketch only

spice_engine: ngspice
ngspice_version: ">=43"               # Checked before run; fail fast

netlist:
  # One of: exported file path glob, or kicad project + cli export (when wired)
  main: sim/netlist/exported.cir
  includes:
    - ../../libs/spice/tps63070/TPS63070_TRANS.LIB

scenarios:
  - name: startup
    analysis: tran
    card: ".tran …"                   # ngspice line(s) appended or inlined
    measures:
      - name: overshoot_mv
        expr: "MAX(v(VOUT)) - 3.3" 
        limit_max: 0.450

baseline:
  compare_to_ref: refs/main-spice-metrics.json   # Optional; artifact from main CI

reports:
  output_path: docs/spice-report.md
  plots: artifact_only              # CI artifact first; rare commits on main
```

Treat **`sim.yml` as absent** ⇒ **skip** sim CI for that board (opt-in rollout).

---

## CI integration (design)

Extend existing patterns:

1. **Detect boards** — add rule: diff touches **`libs/spice/`**, **`scripts/sim/`**, **`sim/`** root doc → rerun every board that has **`sim.yml`**, not only trees under **`boards/<name>/`** touched (same idea as current “shared libs” rule).
2. **New job **`spice`** (depends on **`detect-boards`**) —
   - Matrix **`board`** only among those with **`sim.yml`** and in the detected change set (or union if shared path touched).
   - Steps: checkout → **`run_sim`** → upload **`docs/spice-report.md`** (+ plots) → fail on thresholds.
3. **PR comment** optional: short delta vs artifact from **`base`** (**`main`**) baseline file.

Keeps **`pr-checks.yml`** ERC/DRC and **`spice`** parallel; timeouts similar to existing jobs.

---

## Phases recapped

| Phase | Inputs | Stored where | CI gates |
|------|--------|--------------|-----------|
| **1** — Schematic | Export/`include` libs | **`sim.yml`** + **`libs/spice`** | Ripple, transient metrics, **`PASS`** thresholds |
| **2** — Layout-ish | **`boards/.../sim/parasitics*.cir`** included by wrapper | beside board | Same **`measures`**; **compare** Phase 1 vs 2 deltas manually at first |

---

## Reports & images

- **Committed on `main`** (optional policy): **`docs/spice-report.md`** + **numeric** **`refs/*.json`** for diff.
- **Artifacts every run**: **`ngspice.log`**, **PNG** plots — avoid binary churn on every branch commit unless team wants **diagrams pinned** like **`docs/pcb-*.png`**.

README per board stays **thin**: one link line to **`docs/spice-report.md`** once sim is live.

---

## Scaling checklist (rollout order)

1. **Pin toolchain** — Docker or `ubuntu` **`apt`** + **`ngspice`** hash in **`env:`** matching local dev docs.
2. **One board** (**`tps63070-breakout`**): minimal **`sim.yml`**, manually exported netlist or scripted export, **`run_sim`**, thresholds.
3. **Wire CI job** gated on **`sim.yml`** presence.
4. **Add **`libs/spice`** README with license note for TI models.
5. **Generalize **`detect`** for **`libs/spice`** changes**.
6. **Later**: parasitic **`include`** + optional **second CI matrix slot** (**`PROFILE=phase1`** / **`PROFILE=phase2`**).

---

## Related files

- Example human-facing report skeleton: **`boards/tps63070-breakout/docs/spice-report-example.md`**
- Existing board checks: **`boards/*/checks.yml`**, **`scripts/validate_board.py`**

This document is **planning only**. Implementation edits **`scripts/`**, **`.github/`**, **`boards/*/sim.yml`**, **`libs/spice`** per tasks above — not mandatory to read **`sim/README.md`** for day-to-day use once tooling exists.
