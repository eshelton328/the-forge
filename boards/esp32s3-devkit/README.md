# ESP32-S3 DevKit

Development board built around the [ESP32-S3-WROOM-1](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) module with an integrated [TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf) buck-boost converter and USB-C connectivity.

## Specifications

- **MCU**: ESP32-S3-WROOM-1 (Wi-Fi + BLE, dual-core, 32-bit)
- **Power**: TPS63070 buck-boost (2V–16V input, 3.3V regulated output)
- **Interface**: USB-C (USB 2.0, 14-pin receptacle)
- **ESD protection**: USBLC6-2SC6 on USB data lines
- **Layers**: 4
- **Thickness**: 1.6mm
- **Fab targets**: JLCPCB 4-layer, PCBWay 4-layer

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
| ERC | 🔴 3 errors, 🟡 6 warnings |
| DRC | 🔴 1 error, 🟡 2 warnings |
| Fab: jlcpcb-4layer | 🔴 159 errors, 🟡 5 warnings |
| Fab: pcbway-4layer | 🔴 28 errors, 🟡 75 warnings |

<details>
<summary><strong>ERC</strong> — 🔴 3 errors, 🟡 6 warnings</summary>

> <details>
> <summary>🔴 <b><code>power_pin_not_driven</code></b> — 3 errors</summary>
>
> Input Power pin not driven by any Output Power pins
> - `Symbol U1 Pin 12 [VIN, Power input, Line]`
> - `Symbol U1 Pin 7 [VOUT, Power input, Line]`
> - `Symbol U1 Pin 4 [GND, Power input, Line]`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>footprint_link_issues</code></b> — 1 warning</summary>
>
> The current configuration does not include the footprint library ''
> - `Symbol J3 [USB_C_Receptacle_USB2.0_14P]`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>lib_symbol_mismatch</code></b> — 2 warnings</summary>
>
> Symbol 'TPS630701RNMR' doesn't match copy in library 'TPS630701 Buck-Boost'
> - `Symbol U1 [TPS630701RNMR]`
> - `Symbol J3 [USB_C_Receptacle_USB2.0_14P]`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>pin_to_pin</code></b> — 3 warnings</summary>
>
> Pins of type Unspecified and Passive are connected
> - `Symbol U1 Pin 11 [L1, Unspecified, Line]` / `Symbol L1 Pin 1 [1, Passive, Line]`
> - `Symbol U1 Pin 3 [VAUX, Unspecified, Line]` / `Symbol C4 Pin 1 [Passive, Line]`
> - `Symbol U1 Pin 9 [L2, Unspecified, Line]` / `Symbol L1 Pin 2 [2, Passive, Line]`
>
> </details>
>
</details>

<details>
<summary><strong>DRC</strong> — 🔴 1 error, 🟡 2 warnings</summary>

> **Violations** (2)
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
> **Unconnected items** (1)
>
> <details>
> <summary>🔴 <b><code>unconnected_items</code></b> — 1 error</summary>
>
> Missing connection between items
> - `Track [Net-(J3-CC1)] on F.Cu, length 1.1738 mm` / `Track [Net-(J3-CC1)] on F.Cu, length 1.3789 mm`
>
> </details>
>
</details>

<details>
<summary><strong>Fab DRC: jlcpcb-4layer</strong> — 🔴 159 errors, 🟡 5 warnings</summary>

> <details>
> <summary>🔴 <b><code>annular_width</code></b> — 121 errors</summary>
>
> Annular width (rule 'JLCPCB: Annular ring width (via and PTH)' min annular width 0.1500 mm; actual 0.1000 mm)
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [/GPIO13] on F.Cu - B.Cu`
> - `Via [/GPIO13] on F.Cu - B.Cu`
> - `Via [/GPIO12] on F.Cu - B.Cu`
> - `Via [/GPIO11] on F.Cu - B.Cu`
> - `Via [/GPIO10] on F.Cu - B.Cu`
> - `Via [/GPIO9] on F.Cu - B.Cu`
> - `Via [/GPIO46] on F.Cu - B.Cu`
> - `Via [/GPIO3] on F.Cu - B.Cu`
> - `Via [/GPIO8] on F.Cu - B.Cu`
> - `Via [/GPIO18] on F.Cu - B.Cu`
> - `Via [/GPIO17] on F.Cu - B.Cu`
> - `Via [/GPIO16] on F.Cu - B.Cu`
> - `Via [/GPIO15] on F.Cu - B.Cu`
> - `Via [/GPIO7] on F.Cu - B.Cu`
> - `Via [/GPIO6] on F.Cu - B.Cu`
> - `Via [/GPIO5] on F.Cu - B.Cu`
> - `Via [/GPIO4] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [/3v3] on F.Cu - B.Cu`
> - `Via [Net-(U2-EN)] on F.Cu - B.Cu`
> - `Via [Net-(U2-EN)] on F.Cu - B.Cu`
> - `Via [Net-(J3-CC1)] on F.Cu - B.Cu`
> - `Via [Net-(J3-CC1)] on F.Cu - B.Cu`
> - `Via [Net-(J3-CC1)] on F.Cu - B.Cu`
> - `Via [/D-] on F.Cu - B.Cu`
> - `Via [/D-] on F.Cu - B.Cu`
> - `Via [/D+] on F.Cu - B.Cu`
> - `Via [/D+] on F.Cu - B.Cu`
> - `Via [/GPIO14] on F.Cu - B.Cu`
> - `Via [/GPIO14] on F.Cu - B.Cu`
> - `Via [/GPIO21] on F.Cu - B.Cu`
> - `Via [/GPIO21] on F.Cu - B.Cu`
> - `Via [/GPIO47] on F.Cu - B.Cu`
> - `Via [/GPIO47] on F.Cu - B.Cu`
> - `Via [/GPIO48] on F.Cu - B.Cu`
> - `Via [/GPIO48] on F.Cu - B.Cu`
> - `Via [/GPIO45] on F.Cu - B.Cu`
> - `Via [/GPIO45] on F.Cu - B.Cu`
> - `Via [Net-(J3-D--PadA7)] on F.Cu - B.Cu`
> - `Via [Net-(J3-D--PadA7)] on F.Cu - B.Cu`
> - `Via [Net-(J3-D+-PadA6)] on F.Cu - B.Cu`
> - `Via [Net-(J3-D+-PadA6)] on F.Cu - B.Cu`
>
> </details>
>
> <details>
> <summary>🔴 <b><code>clearance</code></b> — 20 errors</summary>
>
> Clearance violation (rule 'JLCPCB: Track to pad' clearance 0.2000 mm; actual 0.1750 mm)
> - `Pad 6 [GND] of U1 on F.Cu` / `Track [Net-(U1-FB)] on F.Cu, length 0.7100 mm`
> - `Track [Net-(U1-FB)] on F.Cu, length 1.4425 mm` / `Pad 2 [GND] of R4 on F.Cu`
> - `Pad 14 [Net-(U1-EN)] of U1 on F.Cu` / `Track [/2-16v] on F.Cu, length 0.0707 mm`
> - `Pad 14 [Net-(U1-EN)] of U1 on F.Cu` / `Track [GND] on F.Cu, length 0.3050 mm`
> - `Pad 14 [Net-(U1-EN)] of U1 on F.Cu` / `Track [GND] on F.Cu, length 0.5409 mm`
> - `Pad 3 [Net-(U1-VAUX)] of U1 on F.Cu` / `Track [Net-(U1-PG)] on F.Cu, length 1.5450 mm`
> - `Track [Net-(U1-L2)] on F.Cu, length 0.0500 mm` / `Pad 10 [GND] of U1 on F.Cu`
> - `Track [Net-(U1-L2)] on F.Cu, length 0.6710 mm` / `Pad 10 [GND] of U1 on F.Cu`
> - `Track [/GPIO39] on F.Cu, length 1.1825 mm` / `PTH pad 11 [/GPIO40] of J1`
> - `PTH pad 11 [/GPIO40] of J1` / `Track [/GPIO39] on F.Cu, length 9.1358 mm`
> - `Track [Net-(U1-L1)] on F.Cu, length 0.0500 mm` / `Pad 10 [GND] of U1 on F.Cu`
> - `Track [Net-(U1-L1)] on F.Cu, length 0.7453 mm` / `Pad 10 [GND] of U1 on F.Cu`
> - `Pad A6 [Net-(J3-D+-PadA6)] of J3 on F.Cu` / `Track [Net-(J3-D--PadA7)] on F.Cu, length 0.4300 mm`
> - `Pad A6 [Net-(J3-D+-PadA6)] of J3 on F.Cu` / `Track [Net-(J3-D--PadA7)] on F.Cu, length 0.4700 mm`
> - `Pad A6 [Net-(J3-D+-PadA6)] of J3 on F.Cu` / `Track [Net-(J3-D--PadA7)] on F.Cu, length 0.7100 mm`
> - `Pad 2 [GND] of C12 on F.Cu` / `Track [Net-(J3-CC1)] on F.Cu, length 0.9440 mm`
> - `Track [Net-(J3-D+-PadA6)] on F.Cu, length 0.0707 mm` / `Pad B7 [Net-(J3-D--PadA7)] of J3 on F.Cu`
> - `Track [Net-(J3-D+-PadA6)] on F.Cu, length 0.9600 mm` / `Pad A7 [Net-(J3-D--PadA7)] of J3 on F.Cu`
> - `Pad B7 [Net-(J3-D--PadA7)] of J3 on F.Cu` / `Track [Net-(J3-D+-PadA6)] on F.Cu, length 0.9350 mm`
> - `Track [Net-(J3-CC2)] on F.Cu, length 1.7100 mm` / `Pad A8 [<no net>] of J3 on F.Cu`
>
> </details>
>
> <details>
> <summary>🔴 <b><code>hole_clearance</code></b> — 18 errors</summary>
>
> Hole clearance violation (rule 'JLCPCB: Track to PTH hole' clearance 0.3300 mm; actual 0.2500 mm)
> - `Track [/GPIO4] on B.Cu, length 7.3950 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [Net-(J3-CC1)] on F.Cu, length 1.6829 mm` / `Via [/D-] on F.Cu - B.Cu`
> - `Track [Net-(U1-L2)] on F.Cu, length 0.6710 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO13] on In2.Cu, length 18.3423 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO5] on B.Cu, length 8.6450 mm` / `Via [/3v3] on F.Cu - B.Cu`
> - `Track [/GPIO12] on B.Cu, length 7.8000 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/D+] on B.Cu, length 10.1889 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO8] on B.Cu, length 10.7692 mm` / `Via [/3v3] on F.Cu - B.Cu`
> - `Track [/GPIO5] on B.Cu, length 8.6450 mm` / `Via [/3v3] on F.Cu - B.Cu`
> - `Track [/GPIO3] on B.Cu, length 5.1950 mm` / `Via [/3v3] on F.Cu - B.Cu`
> - `Track [/GPIO12] on B.Cu, length 2.9550 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [Net-(U1-L2)] on F.Cu, length 2.8730 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO10] on B.Cu, length 3.4921 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [Net-(U1-L2)] on F.Cu, length 0.1480 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [Net-(U1-L1)] on F.Cu, length 0.2230 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO12] on B.Cu, length 2.9550 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [Net-(U1-L1)] on F.Cu, length 2.8230 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [Net-(U1-L1)] on F.Cu, length 0.7453 mm` / `Via [GND] on F.Cu - B.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>hole_to_hole</code></b> — 2 warnings</summary>
>
> Drilled hole too close to other hole (rule 'JLCPCB: Hole to hole, same net' min 0.2535 mm; actual 0.2252 mm)
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
> Text thickness out of range (rule 'JLCPCB: Silkscreen text' min thickness 0.1500 mm; actual 0.1000 mm)
> - `Reference field of U1`
>
> </details>
>
</details>

<details>
<summary><strong>Fab DRC: pcbway-4layer</strong> — 🔴 28 errors, 🟡 75 warnings</summary>

> <details>
> <summary>🔴 <b><code>annular_width</code></b> — 4 errors</summary>
>
> Annular width (rule 'PCBWay: Pad size' min annular width 0.2500 mm; actual 0.1957 mm)
> - `PTH pad SH [<no net>] of J3`
> - `PTH pad SH [<no net>] of J3`
> - `PTH pad SH [<no net>] of J3`
> - `PTH pad SH [<no net>] of J3`
>
> </details>
>
> <details>
> <summary>🔴 <b><code>clearance</code></b> — 2 errors</summary>
>
> Clearance violation (rule 'PCBWay: Pad to track' clearance 0.2000 mm; actual 0.1546 mm)
> - `Track [/GPIO39] on F.Cu, length 1.1825 mm` / `PTH pad 11 [/GPIO40] of J1`
> - `PTH pad 11 [/GPIO40] of J1` / `Track [/GPIO39] on F.Cu, length 9.1358 mm`
>
> </details>
>
> <details>
> <summary>🔴 <b><code>drill_out_of_range</code></b> — 17 errors</summary>
>
> Hole size out of range (rule 'PCBWay: Pad size' min hole 0.5000 mm; actual 0.2000 mm)
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
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [GND] on F.Cu - B.Cu`
> - `Via [Net-(U2-EN)] on F.Cu - B.Cu`
> - `Via [Net-(U2-EN)] on F.Cu - B.Cu`
>
> </details>
>
> <details>
> <summary>🔴 <b><code>hole_clearance</code></b> — 5 errors</summary>
>
> Hole clearance violation (rule 'PCBWay: Via to track' clearance 0.2540 mm; actual 0.2500 mm)
> - `Track [/GPIO4] on B.Cu, length 7.3950 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/D+] on B.Cu, length 10.1889 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO12] on B.Cu, length 7.8000 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO10] on B.Cu, length 3.4921 mm` / `Via [GND] on F.Cu - B.Cu`
> - `Track [/GPIO12] on B.Cu, length 2.9550 mm` / `Via [GND] on F.Cu - B.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>hole_to_hole</code></b> — 2 warnings</summary>
>
> Drilled hole too close to other hole (rule 'PCBWay: Via to via, same net' min 0.2535 mm; actual 0.2252 mm)
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
> Silkscreen clearance (PCBWay: Pad to silkscreen clearance 0.1500 mm; actual 0.1000 mm)
> - `Segment of R6 on F.Silkscreen` / `Pad 1 [/3v3] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 2 [Net-(D3-K)] of R6 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 1 [/3v3] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 2 [Net-(U2-EN)] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 1 [/3v3] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 2 [Net-(U2-EN)] of R8 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [/3v3] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [/3v3] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of SW1 on F.Silkscreen` / `Pad 2 [/2-16v] of SW1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(D1-K)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/2-16v] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(D1-K)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/2-16v] of R1 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 2 [GND] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 2 [GND] of C12 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 2 [GND] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 1 [/3v3] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 2 [GND] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 1 [/3v3] of C10 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 1 [Net-(U2-EN)] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 2 [GND] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 2 [GND] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 1 [Net-(U2-EN)] of C11 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/2-16v] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/2-16v] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R2 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 1 [/3v3] of R5 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 2 [Net-(U1-PG)] of R5 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 1 [/3v3] of R5 on F.Cu`
> - `Segment of R5 on F.Silkscreen` / `Pad 2 [Net-(U1-PG)] of R5 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 1 [Net-(U1-FB)] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 2 [GND] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 1 [Net-(U1-FB)] of R4 on F.Cu`
> - `Segment of R4 on F.Silkscreen` / `Pad 2 [GND] of R4 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 2 [GND] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 1 [/3v3] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 2 [GND] of C5 on F.Cu`
> - `Segment of C5 on F.Silkscreen` / `Pad 1 [/3v3] of C5 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/2-16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/2-16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of SW1 on F.Silkscreen` / `Pad 1 [/PFET] of SW1 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 2 [GND] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 2 [GND] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
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
> - `Segment of R6 on F.Silkscreen` / `Pad 1 [/3v3] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 2 [Net-(D3-K)] of R6 on F.Cu`
>
> </details>
>
> <details>
> <summary>🟡 <b><code>text_thickness</code></b> — 1 warning</summary>
>
> Text thickness out of range (rule 'PCBWay: Silkscreen text' min thickness 0.1500 mm; actual 0.1000 mm)
> - `Reference field of U1`
>
> </details>
>
</details>

<!-- drc-summary-end -->

## Status

**In Development** — schematic and initial PCB layout complete. Not yet fabricated.
