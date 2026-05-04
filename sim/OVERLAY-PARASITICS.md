# Board overlay (`sim/overlay.cir`) and parasitic evolution

**Tracks:** [issue #63](https://github.com/eshelton328/the-forge/issues/63) (research), [PRD #43](https://github.com/eshelton328/the-forge/issues/43) (US 14, 25).

## Why this exists

Layout-aware effects should ride the **same** assemble → ngspice → measures pipeline as schematic-only runs. The fixed **`sim/overlay.cir`** hook is where parasitic richness grows over time: empty stub → hand-authored L/C/R → optional generated fragments — **without** a second SPICE driver or CI job shape.

## Assembler contract (authoritative)

[`scripts/sim/assemble.py`](../scripts/sim/assemble.py) emits **`sim/assembled.cir`** with this **fixed order** (changing it breaks expectation for overlays and tests):

1. **`assembly.includes`** from `sim.yml`, **in list order** — vendor/device decks (e.g. `libs/spice/…`), shared stubs.
2. **`assembly.main`** — typically KiCad-exported **`sim/kicad_export.cir`** (canonical connectivity from the schematic).
3. **`sim/overlay.cir`** — **mandatory** if the board uses `assembly:`; always last.

All `.include` paths in `assembled.cir` are **relative to `sim/`**, so nested includes resolve consistently under ngspice.

### What belongs in `overlay.cir`

- **Analysis cards** for scenarios declared in `sim.yml`: `.op`, `.tran`, `.ac`, `.meas`, sweep directives, and `.end` when the exported main deck does not terminate the run by itself (see [`boards/tps63070-breakout/sim/overlay.cir`](../boards/tps63070-breakout/sim/overlay.cir)).
- **Board-local parasitics and refinement**: discrete extra elements that bridge nets already present in `kicad_export.cir` (series inductance on a switching node, capacitor ESL/ESR splits, short interconnect R/L). Keep net names aligned with KiCad SPICE export naming (`v(/netname)` style in `.meas`).
- **Further modularization**: `.include "extracted_hotloop.cir"` (or similar) **from inside** `overlay.cir`, so the assembler order stays **includes → main → overlay** while extracted snippets live as separate versioned files under `boards/<board>/sim/`.

### What usually does *not* belong in `overlay.cir`

- **Vendor subcircuits** duplicated per board — prefer one canonical path under **`libs/spice/`** and reference it from **`assembly.includes`** so checksum/license/provenance stay centralized (see **[`libs/spice/README.md`](../libs/spice/README.md)** for the TPS63070 stub pattern).
- **Replacing** the schematic export as the source of topology — `kicad_export.cir` remains the connectivity truth unless export is broken and an explicit escape hatch is documented per board.

## Evolution path (recommended)

| Stage | What changes | CI / driver |
| ----- | ------------- | ----------- |
| **A — Schematic-only** | Overlay holds analysis directives only (or a near-empty stub plus `.end` pattern if required). | Unchanged. |
| **B — Manual parasitics** | Overlay adds small L/R/C (or `.subckt` wrappers) for “hot” loops or filters; optionally split into `sim/manual_parasitics.cir` included from overlay for readability. | Unchanged. |
| **C — Extraction-backed fragments** | Offline tool emits `sim/extracted_*.cir`; overlay adds `.include` of those files (or selective merges). Reviewers see **diffs** on tracked fragments. | **Still unchanged** — same `assemble.py` order; no second pipeline. |

Choosing a specific extractor (KiCad field solver exports, third-party RLGC, etc.) is **out of scope** for this note; when selected, open a **focused implementation issue** for export conventions and file naming under `sim/`.

## Spike: hand-authored hot-loop snippet

Below is **illustrative only** — not a recommendation to paste verbatim onto a board without validating net names and physical meaning.

```spice
* Example manual parasitics (NOT wired into any board by default):
* Assume KiCad export exposes net /vout_+3.3v — add package/trace series elements before bulk cap.
* RVOUT_SER /vout_+3.3v INT_VOUT 0.015
* LVOUT_SER INT_VOUT OUT_HP 2n
* COUT_HP OUT_HP 0 4.7u
```

In practice, hook **`OUT_HP`** (or the chosen internal node) into existing `.meas` targets in `overlay.cir` so `sim.yml` limits remain meaningful.

## Non-goals (per PRD)

- Bundling **full-field EM** sign-off or guaranteed **EMI/radiated** compliance.
- Making **commercial extraction suites** a hard dependency of this repository’s CI.
- Adding a **parallel** SPICE entry point “for layout” — parasitics must converge on **this** overlay hook.

## Maintainer checklist

- [ ] When adding parasitics, **preserve** `assembly.includes` → **main** → **overlay** semantics; extend depth via `.include` **from** `overlay.cir` if files grow large.
- [ ] Keep **vendor models** in **`libs/spice/`** with README + checksum posture where applicable.
- [ ] After adopting an extractor, add a short **“Generated files”** subsection to this board’s README or overlay header comments stating **tool + command** used to refresh fragments.
