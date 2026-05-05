# Board overlay (`sim/overlay.cir`) and parasitic evolution

**Tracks:** [issue #63](https://github.com/eshelton328/the-forge/issues/63) (research), [issue #74](https://github.com/eshelton328/the-forge/issues/74) (extraction hook / fragments), [PRD #43](https://github.com/eshelton328/the-forge/issues/43) (US 14, 25).

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
- **Further modularization**: `.include "extracted_hotloop_fragment.cir"` (or other `extracted_*.cir`) **from inside** `overlay.cir`, so the assembler order stays **includes → main → overlay** while extracted snippets live as separate versioned files under `boards/<board>/sim/`.

### What usually does *not* belong in `overlay.cir`

- **Vendor subcircuits** duplicated per board — prefer one canonical path under **`libs/spice/`** and reference it from **`assembly.includes`** so checksum/license/provenance stay centralized (see **[`libs/spice/README.md`](../libs/spice/README.md)** for the TPS63070 stub pattern).
- **Replacing** the schematic export as the source of topology — `kicad_export.cir` remains the connectivity truth unless export is broken and an explicit escape hatch is documented per board.

## Evolution path (recommended)

| Stage | What changes | CI / driver |
| ----- | ------------- | ----------- |
| **A — Schematic-only** | Overlay holds analysis directives only (or a near-empty stub plus `.end` pattern if required). | Unchanged. |
| **B — Manual parasitics** | Overlay adds small L/R/C (or `.subckt` wrappers) for “hot” loops or filters; optionally split into `sim/manual_parasitics.cir` included from overlay for readability. | Unchanged. |
| **C — Extraction-backed fragments** | Offline tool emits `sim/extracted_*.cir`; overlay adds `.include` of those files (or selective merges). Reviewers see **diffs** on tracked fragments. | **Still unchanged** — same `assemble.py` order; no second pipeline. |

First reference board hook: **[#74](https://github.com/eshelton328/the-forge/issues/74)** — `boards/tps63070-breakout/sim/extracted_hotloop_fragment.cir`, pulled into **`overlay.cir`** (assembled transient deck) and into **`ac_small_signal.cir`** so **secondary `.ac` passes** see the same layout-adjacent elements.

Choosing a specific extractor (KiCad-adjacent field solver exports, third-party RLGC, etc.) is **optional per board**; record it under § **Extracted fragments** below once pinned.

### Extracted fragments (`extracted_*.cir`)

**Goal:** committed ASCII fragments under `boards/<board>/sim/` that extend the schematic export with layout-informed passives (or eventually field-solver snippets), always reached via **`.include` from `overlay.cir`** (and from any **standalone secondary netlists** that must stay consistent — e.g. same `.include` lines duplicated there until a shared snippet mechanism exists).

**Committed filenames**

- Prefer stable names such as `extracted_hotloop_fragment.cir`, `extracted_pdn_fragment.cir`, or tool-prefixed stems if multiple domains are tracked separately.
- Keep files **small and reviewable**; split domains rather than one mega-netlist.

**Refresh command (maintainer contract)**

- Today there is **no** repo-wide extractor CLI — fragments may start as **comment-only stubs** or **hand-maintained** estimates from trace geometry / datasheet ESL.
- When an automated extractor is adopted for a board, **document in the fragment header** (tool name + version) and add a **copy-pastable shell one-liner** here or in that board’s README under **SPICE → extraction-backed files**, for example:
  - `make sim-export-board BOARD=tps63070-breakout` *(schematic export only — layout extraction TBD)*  
  - *Future:* `path/to/extractor --pcb boards/foo/foo.kicad_pcb --out boards/foo/sim/extracted_hotloop_fragment.cir`

**Reviewer expectations**

- Treat diffs like **netlist code**: net names must match KiCad SPICE export conventions; passive values should cite source (rule of thumb, datasheet table, extraction report).
- Expect **metric baseline updates** when fragments gain real elements — refresh `spice_metrics_baseline.json` after intentional physics changes.

**Non-goals**

- Mandating a commercial extractor for CI.
- Replacing `kicad_export.cir` as connectivity truth.

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
