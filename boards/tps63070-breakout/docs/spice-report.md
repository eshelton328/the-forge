# Spice simulation report

Each **scenario** matches a block in `sim.yml`. **Bounds** repeat those limits; **Baseline** and **Δ** appear only when `sim/spice_metrics_baseline.json` is loaded.

## Run metadata

| Field | Value |
| --- | --- |
| Config | `/Users/erik/Workspaces/the-forge/boards/tps63070-breakout/sim.yml` |
| Netlist | `/Users/erik/Workspaces/the-forge/boards/tps63070-breakout/sim/assembled.cir` |
| KiCad CLI | `10.0.1` |
| KiCad Docker image (CI) | `—` |
| ngspice | `******` |
| Simulator exit | 0 |

## Executive summary

| Metric | Value |
| --- | --- |
| Measures | 28 |
| Passed | 28 |
| Failed | 0 |

## Results by scenario

### `vin_bias_op`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| VIN rail DC (after input distribution) | 10 | min 9.99, max 10.01 | **PASS** |

### `tran_settle`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| Vout steady (post transient) | 3.30704 | min 3.28, max 3.32 | **PASS** |
| Vout minimum over transient | 3.30704 | min 3.25 | **PASS** |
| Output ripple peak-peak | 0 | max 0.15 | **PASS** |

### `tran_load_step`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| Vout at light load sample | 3.30704 | min 3.25, max 3.35 | **PASS** |
| Vout at heavy load sample | 3.30704 | min 3.28, max 3.32 | **PASS** |
| Vout peak during first heavy-load step (118–135 µs) | 3.30704 | max 3.45 | **PASS** |
| Vout sample after heavy-load step (160 µs) | 3.30704 | min 3.25, max 3.34 | **PASS** |

### `tran_stress_extended`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| Vout minimum during duty-cycled load bursts (276–318 µs) | 3.30704 | min 3.15 | **PASS** |
| Vout peak-peak during load bursts (276–318 µs) | 0 | max 0.35 | **PASS** |
| Vout during low-VIN + heavy load (10 V in, 370 µs) | 3.30704 | min 3.05, max 3.38 | **PASS** |
| Vout after line recovery (450 µs, heavy load) | 3.30704 | min 3.22, max 3.34 | **PASS** |

### `ac_small_signal`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| AC \|Vout\| @ 1 kHz (small-signal anchor) | 0 | max 1.0 | **PASS** |
| AC \|Vout\| @ 50 kHz | 0 | max 1.0 | **PASS** |
| AC \|Vout\| @ 10 kHz | 0 | max 1.0 | **PASS** |
| AC \|Vout\| @ 100 kHz | 0 | max 1.0 | **PASS** |
| AC \|Vout\| @ 500 kHz | 0 | max 1.0 | **PASS** |

### `ac_z_out`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| \|Zout\| @ 1 kHz (Ω, Norton I_ac=1 A pk) | 0.022 | max 1.0 | **PASS** |
| \|Zout\| @ 10 kHz (Ω, Norton I_ac=1 A pk) | 0.022 | max 1.0 | **PASS** |
| \|Zout\| @ 100 kHz (Ω, Norton I_ac=1 A pk) | 0.022 | max 1.0 | **PASS** |

### `ac_z_in`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| \|Zin\| @ 1 kHz (Ω, Norton I_ac=1 µA pk → ×1e6) | 0.0499916 | max 100.0 | **PASS** |
| \|Zin\| @ 10 kHz (Ω, Norton I_ac=1 µA pk → ×1e6) | 0.0491805 | max 100.0 | **PASS** |
| \|Zin\| @ 100 kHz (Ω, Norton I_ac=1 µA pk → ×1e6) | 0.0288179 | max 100.0 | **PASS** |

### `tran_startup_ramp`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| Startup ramp — Vout minimum (1–130 µs) | 3.30704 | min 2.4 | **PASS** |
| Startup ramp — Vout at 380 µs | 3.30704 | min 3.25, max 3.34 | **PASS** |

### `tran_corner_stub_cap`

| Measure | Value | Bounds | Result |
| --- | --- | --- | --- |
| Corner (+470 p stub) pulse-train ripple PP (276–318 µs) | 0 | max 0.45 | **PASS** |
| Corner (+470 p stub) pulse-train Vout minimum | 3.30704 | min 3.12 | **PASS** |
| Corner (+470 p stub) heavy-load sample (245 µs) | 3.30704 | min 3.26, max 3.33 | **PASS** |

## Summary

**Overall:** PASS

---

```text
SIM_REPORT_VERSION=1
PASS=true
EXIT_CODE=0
SIM_BASELINE_COMPARE=false
```

