# TPS63070 Buck-Boost Breakout

Standalone breakout board for the [TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf) buck-boost converter. Provides a regulated 3.3V output from a wide input voltage range (2V–16V).

## Specifications

- **Input voltage**: 2V – 16V
- **Output voltage**: 3.3V (default, configurable via feedback divider)
- **Output current**: up to 2A
- **Layers**: 2
- **Thickness**: 1.6mm
- **Fab targets**: JLCPCB 2-layer, PCBWay 2-layer

### Simulation (ngspice)

CI uploads **`docs/spice-report.md`**, **`docs/spice-report.metrics.json`**, and netlists under artifact **`spice-boards`** → `tps63070-breakout/`. Example folder layout: [`docs/spice-report-example.md`](docs/spice-report-example.md).

| Read this | Open this |
| :--- | :--- |
| Scenario limits (voltages, ripple, AC anchors) | [`sim.yml`](sim.yml) |
| Transient stimulus, `.tran`, `.meas`, plot signal | [`sim/overlay.cir`](sim/overlay.cir) |
| Line-transfer small-signal `.ac` (VIN AC → Vout tap) | [`sim/ac_small_signal.cir`](sim/ac_small_signal.cir) |
| Norton output impedance probes (`ac_z_out`) | [`sim/ac_z_out.cir`](sim/ac_z_out.cir) |
| Norton input impedance probes (`ac_z_in`; bench `RBENCH` — see deck comments) | [`sim/ac_z_in.cir`](sim/ac_z_in.cir) |
| Layout-ish parasitics (distribution, stubs) | [`sim/extracted_hotloop_fragment.cir`](sim/extracted_hotloop_fragment.cir), [`sim/manual_parasitics.cir`](sim/manual_parasitics.cir) |
| Parasitic workflow / reviewer expectations | [`sim/OVERLAY-PARASITICS.md`](../../sim/OVERLAY-PARASITICS.md) |
| Full runner / Docker / local commands | [`sim/README.md`](../../sim/README.md) |

**Flow:** KiCad exports **`sim/kicad_export.cir`** (gitignored); assembly merges vendor **`libs/spice`** → export → **`overlay.cir`**. The TI model in-repo is an **ngspice behavioral stub** — see [`libs/spice/README.md`](../../libs/spice/README.md) for what that implies.

Context: [#76](https://github.com/eshelton328/the-forge/issues/76) (transient regression), [#79](https://github.com/eshelton328/the-forge/issues/79) (multi-pass `.ac`), [#74](https://github.com/eshelton328/the-forge/issues/74) (overlay fragments).

### Simulation roadmap (long-term)

Goals for automated **design evidence** beyond today’s transient limits (not necessarily all in ngspice alone):

1. **Expected voltage output** — richer reporting vs nominal/datasheet-style bands (line/load tables, ripple budgets, multi-point summaries in artifacts).
2. **Impedance** — frequency-domain or port metrics (e.g. output impedance, PDN **|Z(f)|**) using `.ac` / richer models and, where needed, layout-linked overlays ([`sim/OVERLAY-PARASITICS.md`](../../sim/OVERLAY-PARASITICS.md), [#74](https://github.com/eshelton328/the-forge/issues/74)).
3. **EMI-oriented reporting** — structured EMI-adjacent summaries where the toolchain supports them (e.g. harmonic estimates, documented coupling assumptions); **not** chamber certification or guaranteed emissions compliance ([PRD #43](https://github.com/eshelton328/the-forge/issues/43) scope boundaries).

**Today:** transient + load-step regression ([#76](https://github.com/eshelton328/the-forge/issues/76)); AC **line-response** + Norton **|Zout| / |Zin|** secondary decks (`ac_small_signal.cir`, `ac_z_out.cir`, `ac_z_in.cir`; [#79](https://github.com/eshelton328/the-forge/issues/79)).

**Repo tracking (scope / prioritization):** EMI-adjacent documentation expectations — [#81](https://github.com/eshelton328/the-forge/issues/81); scheduling non-sim backlog (PRD remainder, hardware variants such as [#4](https://github.com/eshelton328/the-forge/issues/4)) — [#82](https://github.com/eshelton328/the-forge/issues/82).

<!-- spice-regression-start -->
## SPICE regression (ngspice)

_Auto-generated when `docs/spice-report.metrics.json` is present (see `sim.yml` and [`sim/README.md`](../../sim/README.md))._

**Last metrics refresh:** 2026-05-07T20:26:11Z · **Overall:** PASS (schema v2)

[Full report (`docs/spice-report.md`)](docs/spice-report.md)

| Scenario | Measure | Value | Bounds | Result |
|:---------|:--------|:------|:-------|:-------|
| vin_bias_op | VIN rail DC (after input distribution) | 10 | min 9.99, max 10.01 | **PASS** |
| tran_settle | Vout steady (post transient) | 3.30704 | min 3.28, max 3.32 | **PASS** |
| tran_settle | Vout minimum over transient | 3.30704 | min 3.25 | **PASS** |
| tran_settle | Output ripple peak-peak | 0 | max 0.15 | **PASS** |
| tran_load_step | Vout at light load sample | 3.30704 | min 3.25, max 3.35 | **PASS** |
| tran_load_step | Vout at heavy load sample | 3.30704 | min 3.28, max 3.32 | **PASS** |
| ac_small_signal | AC |Vout| @ 1 kHz (small-signal anchor) | 0 | max 1.0 | **PASS** |
| ac_small_signal | AC |Vout| @ 10 kHz | 0 | max 1.0 | **PASS** |
| ac_small_signal | AC |Vout| @ 100 kHz | 0 | max 1.0 | **PASS** |

<!-- spice-regression-end -->

## Bill of Materials

| Ref | Value | Part Number | Datasheet |
|-----|-------|-------------|-----------|
| U1 | TPS63070 | TPS630701RNMR | [TI TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf) |
| L1 | 1.5µH | XFL4020-152MEC | [Coilcraft XFL4020](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductors/xfl/xfl4020/) |
| C1, C2, C3 | 10µF | — | Input decoupling |
| C4 | 0.1µF | — | VAUX decoupling |
| C5 | 10µF | — | Output decoupling |
| C6, C7, C8 | 22µF | — | Output bulk capacitance |
| R1 | 10kΩ | — | EN pull-up |
| R2 | 470kΩ | — | Feedback divider (upper) |
| R3 | 150kΩ | — | Feedback divider (lower) |
| R4 | 100kΩ | — | FB → FB2 scaling resistor |
| J1 | 4-pin header | — | VIN, GND, VOUT, PG |

## Output Voltage Variants

The output voltage is set by the feedback resistor divider (R2/R3): `V_OUT = V_REF × (1 + R2 / R3)` where V_REF = 0.8V. See the [TPS63070 datasheet](https://www.ti.com/lit/ds/symlink/tps63070.pdf) §9.2.2.1 for the formula and recommended values.

| Output Voltage | R2 (upper) | R3 (lower) | Status |
|---------------|-----|-----|--------|
| 3.3V | 470kΩ | 150kΩ | Default configuration |
| 5V | — | — | Planned ([#4](https://github.com/eshelton328/the-forge/issues/4)) |

<!-- board-images-start -->
## Board Images

_Auto-generated on merge to main._

### Schematic

![Schematic](docs/schematic.svg)

### PCB Layout

| Top | Bottom |
| :---: | :---: |
| ![Top](docs/pcb-top.png) | ![Bottom](docs/pcb-bottom.png) |

<!-- board-images-end -->

<!-- drc-summary-start -->
## KiCad design checks

_Same layout as the KiCad check summary on pull requests (ERC, DRC, fab rules). Auto-generated on merge to main._

| Check | Result |
|:------|:-------|
| ERC | 🟡 1 warning |
| DRC | ✅ |
| Fab: jlcpcb-2layer-advanced | 🟡 26 warnings |
| Fab: pcbway-2layer-advanced | 🟡 41 warnings |

<details>
<summary><strong>ERC</strong> — 🟡 1 warning</summary>

> <details>
> <summary>🟡 <b><code>lib_symbol_mismatch</code></b> — 1 warning</summary>
>
> Symbol 'TPS630701RNMR' doesn't match copy in library 'TPS630701 Buck-Boost'
> - `Symbol U1 [TPS630701RNMR]`
>
> </details>
>
</details>

<details>
<summary><strong>Fab DRC: jlcpcb-2layer-advanced</strong> — 🟡 26 warnings</summary>

> <details>
> <summary>🟡 <b><code>text_height</code></b> — 13 warnings</summary>
>
> Text height out of range (rule 'JLCPCB Adv: Silkscreen text' min height 1.0000 mm; actual 0.8000 mm)
> - `Reference field of C3`
> - `Reference field of C2`
> - `Reference field of R1`
> - `Reference field of C8`
> - `Reference field of C7`
> - `Reference field of U1`
> - `Reference field of C6`
> - `Reference field of C5`
> - `Reference field of C1`
> - `Reference field of R4`
> - `Reference field of C4`
> - `Reference field of R2`
> - `Reference field of R3`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>text_thickness</code></b> — 13 warnings</summary>
>
> Text thickness out of range (rule 'JLCPCB Adv: Silkscreen text' min thickness 0.1500 mm; actual 0.1000 mm)
> - `Reference field of C3`
> - `Reference field of C2`
> - `Reference field of R1`
> - `Reference field of C8`
> - `Reference field of C7`
> - `Reference field of U1`
> - `Reference field of C6`
> - `Reference field of C5`
> - `Reference field of C1`
> - `Reference field of R4`
> - `Reference field of C4`
> - `Reference field of R2`
> - `Reference field of R3`
>
> </details>
>
</details>

<details>
<summary><strong>Fab DRC: pcbway-2layer-advanced</strong> — 🟡 41 warnings</summary>

> <details>
> <summary>🟡 <b><code>silk_overlap</code></b> — 28 warnings</summary>
>
> Silkscreen clearance (PCBWay Adv: Pad to silkscreen clearance 0.1500 mm; actual 0.1000 mm)
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/VIN 2v to 16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/VIN 2v to 16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/VIN 2v to 16v] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/VIN 2v to 16v] of R1 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 2 [GND] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 1 [/VOUT +3.3v] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 2 [GND] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 1 [/VOUT +3.3v] of C5 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 1 [/VOUT +3.3v] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 2 [Net-(U1-PG)] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 1 [/VOUT +3.3v] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 2 [Net-(U1-PG)] of R4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/VOUT +3.3v] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/VOUT +3.3v] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R2 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [GND] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [GND] of R3 on F.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>text_thickness</code></b> — 13 warnings</summary>
>
> Text thickness out of range (rule 'PCBWay Adv: Silkscreen text' min thickness 0.1500 mm; actual 0.1000 mm)
> - `Reference field of C3`
> - `Reference field of C2`
> - `Reference field of R1`
> - `Reference field of C8`
> - `Reference field of C7`
> - `Reference field of U1`
> - `Reference field of C6`
> - `Reference field of C5`
> - `Reference field of C1`
> - `Reference field of R4`
> - `Reference field of C4`
> - `Reference field of R2`
> - `Reference field of R3`
>
> </details>
>
</details>

<!-- drc-summary-end -->

<!-- validation-summary-start -->
## Validation Summary

_Run `make validate tps63070-breakout` to regenerate locally._

| Check | Status | Details |
|-------|--------|---------|
| required_components | pass | 15/15 components present |
| required_nets | pass | 3/3 nets present |
| capacitor_budget | pass | input: 30µF (min 20µF); output: 76µF (min 60µF); decoupling: C4 |
| voltage_divider | pass | V_OUT = 3.307V (target 3.3V, 0.20% error) — R2=470kΩ, R3=150kΩ, V_REF=0.8V |
| bom_rules | pass | footprints required; no duplicate refs; datasheets on U1 |
<!-- validation-summary-end -->

## Status

**Migrated** — previously developed as a standalone project ("genesis"). First revision has been fabricated and validated at JLCPCB with confirmed 3.3V output.

### Known DRC items

- **ERC**: VIN and GND nets need `PWR_FLAG` symbols (cosmetic warnings, add in KiCad GUI via Place > Power Port)
- **Fab DRC**: Board was designed before fab rules were added; some clearances and via sizes are below published manufacturer minimums. These should be addressed in the next board revision.
