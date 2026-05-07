# Spice simulation report

## Run metadata

| Field | Value |
| --- | --- |
| Config | `/workspace/boards/tps63070-breakout/sim.yml` |
| Netlist | `/workspace/boards/tps63070-breakout/sim/assembled.cir` |
| KiCad CLI | `10.0.1` |
| KiCad Docker image (CI) | `the-forge-sim:ci` |
| ngspice | `******` |
| Simulator exit | 0 |
| Baseline file | `sim/spice_metrics_baseline.json` |
| Baseline ref (documented) | `Parasitic enrich VIN+VOUT May 2026; refresh after schematic/model/overlay churn` |
## Executive summary

| Metric | Value |
| --- | --- |
| Measures | 9 |
| Passed | 9 |
| Failed | 0 |

## Results by scenario

### `vin_bias_op`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| VIN rail DC (after input distribution) | 10 | 10 | 0 | min 9.99, max 10.01 | **PASS** |

### `tran_settle`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Vout steady (post transient) | 3.3 | 3.3 | 0 | min 3.28, max 3.32 | **PASS** |
| Vout minimum over transient | 3.3 | 3.3 | 0 | min 3.25 | **PASS** |
| Output ripple peak-peak | 0 | 0 | 0 | max 0.15 | **PASS** |

### `tran_load_step`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Vout at light load sample | 3.3 | 3.3 | 0 | min 3.25, max 3.35 | **PASS** |
| Vout at heavy load sample | 3.3 | 3.3 | 0 | min 3.28, max 3.32 | **PASS** |

### `ac_small_signal`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| AC |Vout| @ 1 kHz (small-signal anchor) | 0 | 0 | 0 | max 1.0 | **PASS** |
| AC |Vout| @ 10 kHz | 0 | 0 | 0 | max 1.0 | **PASS** |
| AC |Vout| @ 100 kHz | 0 | 0 | 0 | max 1.0 | **PASS** |

## Summary

**Overall:** PASS

---

```text
SIM_REPORT_VERSION=1
PASS=true
EXIT_CODE=0
SIM_BASELINE_COMPARE=true
```


## Waveform plots

PNG files (committed path relative to board root):

- `sim/plots/tran-vout.png`
