# TPS63070 Buck-Boost Breakout

Standalone breakout board for the TPS63070 buck-boost converter. Provides a regulated 3.3V output from a wide input voltage range (2V–16V).

## Key Components

| Component | Part Number | Description |
|-----------|-------------|-------------|
| U1 | TPS630701RNMR | 2A buck-boost converter |
| L1 | XFL4020-152MEC | 1.5µH power inductor |

## Specifications

- **Input voltage**: 2V – 16V
- **Output voltage**: 3.3V (default, configurable via feedback divider)
- **Output current**: up to 2A
- **Layers**: 2
- **Thickness**: 1.6mm

## Output Voltage Variants

The output voltage is set by the feedback resistor divider (R1/R2). See the TPS63070 datasheet for calculating values for other output voltages.

| Output Voltage | Status |
|---------------|--------|
| 3.3V | Default configuration |
| 5V | Planned ([#4](https://github.com/eshelton328/the-forge/issues/4)) |

## Status

**Migrated** — previously developed as a standalone project ("genesis"). First revision has been fabricated and validated.
