# ESP32-S3 DevKit

Development board built around the [ESP32-S3-WROOM-1](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) module with an integrated [TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf) buck-boost converter and USB-C connectivity.

## Specifications

- **MCU**: ESP32-S3-WROOM-1 (Wi-Fi + BLE, dual-core, 32-bit)
- **Power**: TPS63070 buck-boost (2V–16V input, 3.3V regulated output)
- **Interface**: USB-C (USB 2.0, 14-pin receptacle)
- **ESD protection**: USBLC6-2SC6 on USB data lines
- **Layers**: 4
- **Thickness**: 1.6mm
- **Fab targets**: JLCPCB 4-layer advanced, PCBWay 4-layer advanced

## Key Components

| Ref | Value | Description |
|-----|-------|-------------|
| U1 | ESP32-S3-WROOM-1 | Wi-Fi + BLE SoC module |
| U2 | TPS630701RNMR | Buck-boost converter (3.3V output) |
| U3 | USBLC6-2SC6 | USB ESD protection |
| J1 | USB-C 14P | USB-C receptacle (USB 2.0) |
| J2, J3 | Conn_01x16 | GPIO breakout headers |
| L1 | 1.5µH | Buck-boost inductor |
| Q1 | P-MOSFET | Power path control |
| SW1 | ON/OFF | SPST — main power switch |
| SW2 | RESET | Push — ESP32 reset |
| SW3 | BOOT | Push — boot / download mode |
| LED1, LED2 | LED | Status indicators |

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
| ERC | ✅ |
| DRC | 🔴 1 error, 🟡 4 warnings |
| Fab: jlcpcb-4layer-advanced | 🟡 7 warnings |
| Fab: pcbway-4layer-advanced | 🔴 12 errors, 🟡 77 warnings |

<details>
<summary><strong>DRC</strong> — 🔴 1 error, 🟡 4 warnings</summary>

> **Violations** (4)
>
> <details>
> <summary>🟡 <b><code>silk_edge_clearance</code></b> — 2 warnings</summary>
>
> Silkscreen clipped by board edge
> - `Rectangle on Edge.Cuts` / `Segment of U2 on F.Silkscreen`
> - `Rectangle on Edge.Cuts` / `Segment of U2 on F.Silkscreen`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>track_dangling</code></b> — 2 warnings</summary>
>
> Track has unconnected end
> - `Track [/D+] on B.Cu, length 0.0200 mm`
> - `Track [/D+] on B.Cu, length 0.0100 mm`
>
> </details>
>
> **Unconnected items** (1)
>
> <details>
> <summary>🔴 <b><code>unconnected_items</code></b> — 1 error</summary>
>
> Missing connection between items
> - `Track [Net-(J3-CC1)] on F.Cu, length 1.1738 mm` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
>
> </details>
>
</details>

<details>
<summary><strong>Fab DRC: jlcpcb-4layer-advanced</strong> — 🟡 7 warnings</summary>

> <details>
> <summary>🟡 <b><code>hole_to_hole</code></b> — 2 warnings</summary>
>
> Drilled hole too close to other hole (rule 'JLCPCB Adv: Hole to hole, same net' min 0.2535 mm; actual 0.2252 mm)
> - `Via [GND] on F.Cu - B.Cu` / `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu` / `Via [GND] on F.Cu - B.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>silk_edge_clearance</code></b> — 2 warnings</summary>
>
> Silkscreen clipped by board edge
> - `Rectangle on Edge.Cuts` / `Segment of U2 on F.Silkscreen`
> - `Rectangle on Edge.Cuts` / `Segment of U2 on F.Silkscreen`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>text_thickness</code></b> — 1 warning</summary>
>
> Text thickness out of range (rule 'JLCPCB Adv: Silkscreen text' min thickness 0.1500 mm; actual 0.1000 mm)
> - `Reference field of U1`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>track_dangling</code></b> — 2 warnings</summary>
>
> Track has unconnected end
> - `Track [/D+] on B.Cu, length 0.0200 mm`
> - `Track [/D+] on B.Cu, length 0.0100 mm`
>
> </details>
>
</details>

<details>
<summary><strong>Fab DRC: pcbway-4layer-advanced</strong> — 🔴 12 errors, 🟡 77 warnings</summary>

> <details>
> <summary>🔴 <b><code>drill_out_of_range</code></b> — 12 errors</summary>
>
> Hole size out of range (rule 'PCBWay Adv: Pad size' min hole 0.5000 mm; actual 0.2000 mm)
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
> - `PTH pad 41 [GND] of U2`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>hole_to_hole</code></b> — 2 warnings</summary>
>
> Drilled hole too close to other hole (rule 'PCBWay Adv: Via to via, same net' min 0.2535 mm; actual 0.2252 mm)
> - `Via [GND] on F.Cu - B.Cu` / `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu` / `Via [GND] on F.Cu - B.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>silk_edge_clearance</code></b> — 2 warnings</summary>
>
> Silkscreen clipped by board edge
> - `Rectangle on Edge.Cuts` / `Segment of U2 on F.Silkscreen`
> - `Rectangle on Edge.Cuts` / `Segment of U2 on F.Silkscreen`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>silk_overlap</code></b> — 70 warnings</summary>
>
> Silkscreen clearance (PCBWay Adv: Pad to silkscreen clearance 0.1500 mm; actual 0.1000 mm)
> - `Segment of R6 on F.Silkscreen` / `Pad 2 [Net-(D3-K)] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 1 [/3v3] of R6 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 2 [Net-(U2-EN)] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 1 [/3v3] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 2 [Net-(U2-EN)] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 1 [/3v3] of R8 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [/3v3] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [/3v3] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of SW1 on F.Silkscreen` / `Pad 2 [/2-16v] of SW1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(D1-K)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/2-16v] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(D1-K)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/2-16v] of R1 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 2 [GND] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 2 [GND] of C12 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 2 [GND] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 1 [/3v3] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 2 [GND] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 1 [/3v3] of C10 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 1 [Net-(U2-EN)] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 2 [GND] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 1 [Net-(U2-EN)] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 2 [GND] of C11 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/2-16v] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/2-16v] of R2 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 1 [/3v3] of R5 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 2 [Net-(U1-PG)] of R5 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 1 [/3v3] of R5 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 2 [Net-(U1-PG)] of R5 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 2 [GND] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 1 [Net-(U1-FB)] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 2 [GND] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 1 [Net-(U1-FB)] of R4 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 1 [/3v3] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 2 [GND] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 1 [/3v3] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 2 [GND] of C5 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/2-16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/2-16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of SW1 on F.Silkscreen` / `Pad 1 [/PFET] of SW1 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 2 [GND] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 2 [GND] of R10 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 2 [GND] of R11 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 1 [Net-(Q1-G)] of R11 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 2 [GND] of R11 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 1 [Net-(Q1-G)] of R11 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 1 [Net-(J3-CC2)] of R9 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 2 [GND] of R9 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 2 [GND] of R9 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 1 [Net-(J3-CC2)] of R9 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 1 [/3v3] of R7 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 2 [Net-(U2-IO0)] of R7 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 1 [/3v3] of R7 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 2 [Net-(U2-IO0)] of R7 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 2 [Net-(D3-K)] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 1 [/3v3] of R6 on F.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>text_thickness</code></b> — 1 warning</summary>
>
> Text thickness out of range (rule 'PCBWay Adv: Silkscreen text' min thickness 0.1500 mm; actual 0.1000 mm)
> - `Reference field of U1`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>track_dangling</code></b> — 2 warnings</summary>
>
> Track has unconnected end
> - `Track [/D+] on B.Cu, length 0.0200 mm`
> - `Track [/D+] on B.Cu, length 0.0100 mm`
>
> </details>
>
</details>

<!-- drc-summary-end -->

## Status

**In Development** — schematic and initial PCB layout complete. Not yet fabricated.
