# TPS63070 Buck-Boost Breakout

Standalone breakout board for the [TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf) buck-boost converter. Provides a regulated 3.3V output from a wide input voltage range (2V–16V).

## Specifications

- **Input voltage**: 2V – 16V
- **Output voltage**: 3.3V (default, configurable via feedback divider)
- **Output current**: up to 2A
- **Layers**: 2
- **Thickness**: 1.6mm
- **Fab targets**: JLCPCB 2-layer, PCBWay 2-layer
- **SPICE (ngspice):** CI uploads reports under artifact **`spice-boards`** → folder `tps63070-breakout/` (`docs/spice-report.md`, `docs/spice-report.metrics.json`, netlists). Example layout: [`docs/spice-report-example.md`](docs/spice-report-example.md). Scenario limits are in [`sim.yml`](sim.yml); transient stimulus and `.meas` live in [`sim/overlay.cir`](sim/overlay.cir); optional **small-signal AC** runs as a **second ngspice batch** via [`sim.yml`](sim.yml) `secondary_passes` → [`sim/ac_small_signal.cir`](sim/ac_small_signal.cir) ([#79](https://github.com/eshelton328/the-forge/issues/79)). The checked-in TPS63070 library under [`libs/spice/`](../../libs/spice/README.md) is an **ngspice-oriented behavioral stub** — ripple and dynamics may look ideal until that model is enriched; transient regression landed in [#76](https://github.com/eshelton328/the-forge/issues/76).

### Simulation roadmap (long-term)

Goals for automated **design evidence** beyond today’s transient limits (not necessarily all in ngspice alone):

1. **Expected voltage output** — richer reporting vs nominal/datasheet-style bands (line/load tables, ripple budgets, multi-point summaries in artifacts).
2. **Impedance** — frequency-domain or port metrics (e.g. output impedance, PDN **|Z(f)|**) using `.ac` / richer models and, where needed, layout-linked overlays ([`sim/OVERLAY-PARASITICS.md`](../../sim/OVERLAY-PARASITICS.md), [#74](https://github.com/eshelton328/the-forge/issues/74)).
3. **EMI-oriented reporting** — structured EMI-adjacent summaries where the toolchain supports them (e.g. harmonic estimates, documented coupling assumptions); **not** chamber certification or guaranteed emissions compliance ([PRD #43](https://github.com/eshelton328/the-forge/issues/43) scope boundaries).

**Today:** transient + load-step regression ([#76](https://github.com/eshelton328/the-forge/issues/76)); small-signal AC secondary deck ([#79](https://github.com/eshelton328/the-forge/issues/79)).

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
