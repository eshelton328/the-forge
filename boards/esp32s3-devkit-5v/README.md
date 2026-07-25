# ESP32-S3 DevKit 5V

Break-off of [esp32s3-devkit](../esp32s3-devkit/) adding a **second TPS63070 buck-boost
stage for a regulated 5 V rail** alongside the existing 3.3 V rail, plus an **RV-3028
RTC** for scheduled deep-sleep wake. Motivated by the rev-2 findings (devkit PR #112
brown-out study): the single-rail board can't support 5 V loads (class-D amp, sensors)
from batteries.

Started as an exact copy of the devkit and diverges from here. Schematic is hand-edited
in KiCad — no generated sheets. **Status: schematic in progress, no layout yet.**

## Implemented (verified in schematic)

- **Dual rails, both TPS63070 buck-boost:**
  - 3.3 V — U1, R4 470 kΩ / R5 150 kΩ → 0.8 × (1 + 470/150) = **3.31 V**
  - 5 V — U2, R8 680 kΩ / R9 130 kΩ → 0.8 × (1 + 680/130) = **4.98 V**
    (chose 680k/130k over the originally-planned 523k/100k — same 5.23 ratio,
    standard E24 values)
  - Both EN pins pulled to VBAT_SW (R3/R7 10 kΩ) → **always-on** (see open item)
- **RTC — RV-3028-C7 (U5), Package_SON C7 SON-8**, for the deep-sleep alarm wake:
  - /INT → GPIO1 (open-drain, 10 kΩ pull-up R18)
  - I²C: SCL → GPIO9 (R16 4.7 kΩ), SDA → GPIO8 (R17 4.7 kΩ) — one bus pair only
  - VDD + VBACKUP → 3V3 (no separate backup; Cube re-syncs time from the Beacon
    over ESP-NOW — leave the RV-3028 trickle charger OFF), VSS/EVI → GND, CLKOUT NC
  - I²C addr 0x52; JLC/LCSC part **C3019759** (SMT-assemblable, Extended)

## Remaining

- [ ] **5 V EN scheme — DECISION NEEDED.** Firmware (`cube_browns.ino`) defines
      `BOOST_EN 18`, i.e. it expects to gate the 5 V boost from **GPIO18** for
      load-shedding during battery sag. Schematic currently has U2 EN **always-on**
      (R7 → VBAT_SW), so GPIO18 controls nothing. Wire EN to GPIO18 if load-shedding
      is wanted, or drop `BOOST_EN` from firmware if always-on is intended.
- [ ] **Class-D amp** block (I²S 15/16/17, AMP_SD 21 per firmware)
- [ ] **Display** (OLED, shares the I²C bus) behind a **PMOS load switch** (PWR-EN GPIO7)
- [ ] **Battery connector** — JST-PH in place of the flying-lead header (in flux)
- [ ] 5 V pin exposed on the GPIO headers (currently 3V3/VBAT/GND only)
- [ ] **Layout** — still the devkit clone; the 5 V stage, RTC, amp, display are not
      placed or routed yet. Run the copper-connectivity guard before any order.
- [ ] Re-run the battery-range SPICE decks in `sim/` with the 5 V load added; plan
      NiMH/Li-ion (worn alkalines can't deliver 5 V loads — P > Voc²/4R, PR #112)
- [ ] Regenerate `fab/` BOM + CPL after the changes (hand-maintained; goes stale silently)

## Specifications

- **MCU**: ESP32-S3-WROOM-1-N16 (U3)
- **Power**: battery → AO3401A reverse-polarity PFET (Q1) → SW1 → dual TPS63070
  (3.3 V + 5 V rails)
- **RTC**: RV-3028-C7 (U5), I²C, /INT wake on GPIO1
- **Interface**: USB-C (USB 2.0, data-only), USBLC6-2SC6 ESD (U4)
- **Layers**: 4 | **Thickness**: 1.6 mm | **Fab target**: JLCPCB 4-layer advanced

## Status

**WIP — schematic in progress.** Power stages (3.3 V + 5 V) and the RTC are drawn and
ERC-verified; the amp, display, and finalized battery connector are still to come, and
there is no layout work yet. Not order-ready. Tracked in PR #120.
