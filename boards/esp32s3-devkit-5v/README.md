# ESP32-S3 DevKit 5V

Break-off of [esp32s3-devkit](../esp32s3-devkit/) adding a **second TPS63070 buck-boost
stage for a regulated 5 V rail** alongside the existing 3.3 V rail. Motivated by the
rev-2 findings (devkit PR #112 brown-out study): the single-rail board can't support
5 V loads (class-D amp, sensors) from batteries.

This project starts as an exact copy of the devkit (schematic + layout) and diverges
from here. The schematic is hand-edited in KiCad — no generated sheets.

## Planned delta vs esp32s3-devkit

- [ ] Second TPS63070 stage (copy/paste the existing U1 block in eeschema)
  - 5 V feedback divider: **523 kΩ / 100 kΩ** → V_OUT = 0.8 × (1 + 523/100) = 4.98 V
    (confirm against TPS63070 datasheet §9.2.2.1 Table 4; reconcile with
    tps63070-breakout issue #4 so both boards use the same values)
  - Second XFL4020-152MEC inductor + input/output caps
  - Output caps on the 5 V rail must be ≥10 V rated (the 0805 22 µF C45783 is fine;
    do **not** reuse the 6.3 V-rated 0402 10 µF C15525 on this rail)
- [ ] 5 V pin on the GPIO headers (J1/J2 currently expose only 3V3/VBAT/GND)
- [ ] Decide EN scheme for the 5 V stage (always-on with 3.3 V, or GPIO-gated for
      load shedding — a GPIO gate lets firmware kill the 5 V load during battery sag)
- [ ] C3 voltage-rating note from the devkit README (6.3 V-rated 0402 caps limit VBAT)
      — the devkit README's "13 DRC errors" table is stale; DRC is clean on current files
- [ ] Battery: worn alkalines can't deliver 5 V loads (P > Voc²/4R — PR #112);
      plan NiMH/Li-ion like the devkit rev-2 notes say, and re-run the battery-range
      SPICE decks in `sim/` with the 5 V load added
- [ ] Regenerate `fab/` BOM + CPL after the change (hand-maintained; goes stale silently)

## Specifications (inherited until changed)

- **MCU**: ESP32-S3-WROOM-1-N16
- **Power**: battery via VBAT header → AO3401A reverse-polarity PFET → SW1 → TPS63070 (3.3 V)
- **Interface**: USB-C (USB 2.0, data-only), USBLC6-2SC6 ESD
- **Layers**: 4 | **Thickness**: 1.6 mm | **Fab target**: JLCPCB 4-layer advanced

## Status

**Initialized 2026-07-12** — verbatim clone of esp32s3-devkit (schematic, layout, sim
decks, checks). No electrical changes yet; 5 V stage to be drawn by hand in KiCad.
