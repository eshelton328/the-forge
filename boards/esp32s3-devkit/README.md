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
## Design Rule Checks

_Auto-generated on merge to main._

### ERC (Electrical Rules) 🔴 3 errors, 4 warnings

| Violation | Severity | Count |
|-----------|----------|-------|
| lib_symbol_mismatch | 🟡 warning | 1 |
| pin_to_pin | 🟡 warning | 3 |
| power_pin_not_driven | 🔴 error | 3 |

### DRC (Design Rules) 🔴 8 errors, 4 warnings

| Violation | Severity | Count |
|-----------|----------|-------|
| clearance | 🔴 error | 7 |
| hole_clearance | 🔴 error | 1 |
| lib_footprint_mismatch | 🟡 warning | 2 |
| silk_edge_clearance | 🟡 warning | 2 |

<!-- drc-summary-end -->

## Status

**In Development** — schematic and initial PCB layout complete. Not yet fabricated.
