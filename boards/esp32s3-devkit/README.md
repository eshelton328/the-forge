# ESP32-S3 DevKit

Development board built around the [ESP32-S3-WROOM-1](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) module with an integrated [TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf) buck-boost converter and USB-C connectivity.

## Specifications

- **MCU**: ESP32-S3-WROOM-1 (Wi-Fi + BLE, dual-core, 32-bit)
- **Power**: battery only — 3×AA (≈3.0–4.8 V) on the VBAT header pin, through reverse-polarity PFET (Q1) and power switch (SW1) into a TPS63070 buck-boost (3.3 V regulated output)
- **Interface**: USB-C (USB 2.0, 16-pin receptacle) — **data only, by design**; VBUS does not power the board. Batteries must be connected and SW1 on to flash.
- **ESD protection**: USBLC6-2SC6 on USB data lines
- **Layers**: 4
- **Thickness**: 1.6mm
- **Fab targets**: JLCPCB 4-layer advanced
- **Input voltage note**: the TPS63070 accepts up to 16 V, but C3 (10 µF 0402) is 6.3 V-rated — keep VBAT ≤ ~5.5 V unless C3 is upgraded (e.g. 0805/25 V)

## Key Components

| Ref | Value | Description |
|-----|-------|-------------|
| U1 | TPS63070RNMR | Buck-boost converter (3.3V output, adjustable) |
| U2 | ESP32-S3-WROOM-1 | Wi-Fi + BLE SoC module |
| U3 | USBLC6-2SC6 | USB ESD protection |
| J1, J2 | Conn_01x17 | GPIO breakout headers (J1 pin 2 = VBAT battery input) |
| J3 | USB-C 16P | USB-C receptacle (USB 2.0, data only) |
| L1 | 1.5µH | Buck-boost inductor (XFL4020-152ME) |
| Q1 | AO3401A | Reverse-polarity protection PMOS (drain to battery) |
| SW1 | MK-12C03-G015 | SPDT slide switch — main power (latching ON/OFF) |
| SW2 | RESET | Push — ESP32 reset |
| SW3 | BOOT | Push — boot / download mode |
| D1, D3 | LED | Status indicators (D2 zener: DNP) |

## Flashing

First flash: batteries in, SW1 on, hold BOOT, tap RESET, release BOOT, then flash over native USB (CDC/DFU). Subsequent flashes work over USB without buttons.

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
| DRC | ✅ |
| Fab: jlcpcb-4layer-advanced | ✅ |
| Fab: pcbway-4layer-advanced | 🔴 12 errors, 🟡 70 warnings |

<details>
<summary><strong>Fab DRC: pcbway-4layer-advanced</strong> — 🔴 12 errors, 🟡 70 warnings</summary>

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
> <summary>🟡 <b><code>silk_overlap</code></b> — 70 warnings</summary>
>
> Silkscreen clearance (PCBWay Adv: Pad to silkscreen clearance 0.1500 mm; actual 0.1000 mm)
> - `Segment of R6 on F.Silkscreen` / `Pad 2 [Net-(D3-K)] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 1 [/3v3] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 2 [Net-(D3-K)] of R6 on F.Cu`
> - `Segment of R6 on F.Silkscreen` / `Pad 1 [/3v3] of R6 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 1 [/3v3] of R7 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 2 [Net-(U2-IO0)] of R7 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 1 [/3v3] of R7 on F.Cu`
> - `Segment of R7 on F.Silkscreen` / `Pad 2 [Net-(U2-IO0)] of R7 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [/3v3] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 1 [/3v3] of R3 on F.Cu`
> - `Segment of R3 on F.Silkscreen` / `Pad 2 [Net-(U1-FB)] of R3 on F.Cu`
> - `Segment of SW1 on F.Silkscreen` / `Pad 2 [/2-16v] of SW1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/2-16v] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(D1-K)] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 1 [/2-16v] of R1 on F.Cu`
> - `Segment of R1 on F.Silkscreen` / `Pad 2 [Net-(D1-K)] of R1 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 2 [Net-(U2-EN)] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 1 [/3v3] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 2 [Net-(U2-EN)] of R8 on F.Cu`
> - `Segment of R8 on F.Silkscreen` / `Pad 1 [/3v3] of R8 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 2 [Net-(U1-EN)] of R2 on F.Cu`
> - `Segment of R2 on F.Silkscreen` / `Pad 1 [/2-16v] of R2 on F.Cu`
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
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 1 [Net-(U1-VAUX)] of C4 on F.Cu`
> - `Segment of C4 on F.Silkscreen` / `Pad 2 [GND] of C4 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/2-16v] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 2 [GND] of C3 on F.Cu`
> - `Segment of C3 on F.Silkscreen` / `Pad 1 [/2-16v] of C3 on F.Cu`
> - `Segment of SW1 on F.Silkscreen` / `Pad 1 [/PFET] of SW1 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 1 [Net-(U3-VBUS)] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 2 [GND] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 1 [Net-(U3-VBUS)] of C12 on F.Cu`
> - `Segment of C12 on F.Silkscreen` / `Pad 2 [GND] of C12 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 2 [GND] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 1 [/3v3] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 2 [GND] of C10 on F.Cu`
> - `Segment of C10 on F.Silkscreen` / `Pad 1 [/3v3] of C10 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 2 [GND] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 1 [Net-(U2-EN)] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 2 [GND] of C11 on F.Cu`
> - `Segment of C11 on F.Silkscreen` / `Pad 1 [Net-(U2-EN)] of C11 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 2 [GND] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 2 [GND] of R10 on F.Cu`
> - `Segment of R10 on F.Silkscreen` / `Pad 1 [Net-(J3-CC1)] of R10 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 2 [GND] of R11 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 1 [Net-(Q1-G)] of R11 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 2 [GND] of R11 on F.Cu`
> - `Segment of R11 on F.Silkscreen` / `Pad 1 [Net-(Q1-G)] of R11 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 2 [GND] of R9 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 1 [Net-(J3-CC2)] of R9 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 2 [GND] of R9 on F.Cu`
> - `Segment of R9 on F.Silkscreen` / `Pad 1 [Net-(J3-CC2)] of R9 on F.Cu`
>
> </details>
>
</details>

<!-- drc-summary-end -->

## Status

**In Development** — schematic and initial PCB layout complete. Not yet fabricated.
