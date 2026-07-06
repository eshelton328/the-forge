# Spice simulation report

Each **scenario** matches a block in `sim.yml`. **Bounds** repeat those limits; **Baseline** and **Δ** appear only when `sim/spice_metrics_baseline.json` is loaded.

## Run metadata

| Field | Value |
| --- | --- |
| Config | `/workspace/boards/esp32s3-devkit/sim.yml` |
| Netlist | `/workspace/boards/esp32s3-devkit/sim/assembled.cir` |
| KiCad CLI | `10.0.1` |
| KiCad Docker image (CI) | `the-forge-sim:ci` |
| ngspice | `******` |
| Simulator exit | 0 |
| Baseline file | `sim/spice_metrics_baseline.json` |
| Baseline ref (documented) | `test/esp32s3-devkit-brownout-study@initial` |

## Executive summary

| Metric | Value |
| --- | --- |
| Measures | 22 |
| Passed | 22 |
| Failed | 0 |

## Results by scenario

### `vbat_bias_op`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| VBAT_SW rail DC bias (4.8 V pack at t=0) | 4.8 | 4.8 | 0 | min 4.5, max 4.85 | **PASS** |

### `tran_fresh_4v8`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Vout steady, fresh pack (95 µs) | 3.30704 | 3.30704 | 0 | min 3.28, max 3.33 | **PASS** |
| Vout ripple peak-peak, fresh pack idle | 0 | 0 | 0 | max 0.15 | **PASS** |
| Vout minimum during 0.5 A burst at 4.8 V | 3.30704 | 3.30704 | 0 | min 3.1 | **PASS** |

### `tran_mid_3v6`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Vout steady at 3.6 V (buck-boost transition) | 3.30704 | 3.30704 | 0 | min 3.28, max 3.33 | **PASS** |
| Vout minimum during 0.5 A burst at 3.6 V | 3.30704 | 3.30704 | 0 | min 3.1 | **PASS** |

### `tran_low_3v0`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Vout steady on end-of-life pack (3.0 V) | 3.30704 | 3.30704 | 0 | min 3.28, max 3.33 | **PASS** |
| Vout minimum during 0.5 A burst at 3.0 V (boost mode) | 3.30704 | 3.30704 | 0 | min 3.0 | **PASS** |
| VBAT_SW rail present during worst burst (wiring check) | 3.00011 | 3.00011 | 0 | min 2.5 | **PASS** |
| Battery-side passive drain (pull-ups + FB divider; TI model is quasi-ideal and does not draw converter input current) | 0.000190498 | 0.000190498 | 0 | max 0.002 | **PASS** |

### `tran_recovery`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Vout recovered at idle on dead pack (800 µs) | 3.30704 | 3.30704 | 0 | min 3.28, max 3.33 | **PASS** |

### `tran_startup_3v0`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Cold start at 3.0 V — Vout at 380 µs | 3.30704 | 3.30704 | 0 | min 3.28, max 3.33 | **PASS** |
| Cold start at 3.0 V — Vout floor after settling | 3.30704 | 3.30704 | 0 | min 3.2 | **PASS** |

### `espnow_fresh`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| ESP-NOW bursts, fresh pack — VIN minimum (behavioral converter) | 4.27593 | 4.27593 | 0 | min 4.1 | **PASS** |
| ESP-NOW bursts, fresh pack — 3V3 minimum | 3.2905 | 3.2905 | 0 | min 3.25 | **PASS** |

### `espnow_tired`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| ESP-NOW bursts, tired pack (3.6V/1.2R) — VIN sag stays above 2.0V UVLO | 2.62766 | 2.62766 | 0 | min 2.3, max 3.0 | **PASS** |
| ESP-NOW bursts, tired pack — 3V3 holds | 3.2905 | 3.2905 | 0 | min 3.25 | **PASS** |

### `espnow_dead`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| ESP-NOW burst, dead pack (3.0V/3R) — brownout MUST occur (failure-boundary regression) | 1.59998 | 1.59998 | 0 | max 2.5 | **PASS** |
| Dead-pack brownout — rail recovers after burst | 3.3052 | 3.3052 | 0 | min 3.25, max 3.35 | **PASS** |

### `rev2_amp_preview`

| Measure | Value | Baseline | Δ | Bounds | Result |
| --- | --- | --- | --- | --- | --- |
| Rev-2 preview: WiFi + 3W amp on fresh pack — VIN minimum | 3.83804 | 3.83804 | 0 | min 3.5 | **PASS** |
| Rev-2 preview — 3V3 holds under combined load | 3.2905 | 3.2905 | 0 | min 3.25 | **PASS** |
| Rev-2 preview — 5V amp rail holds | 4.982 | 4.982 | 0 | min 4.9 | **PASS** |

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

- `sim/plots/tran-vout-battery.png`
- `sim/plots/tran-vbat-sw.png`
