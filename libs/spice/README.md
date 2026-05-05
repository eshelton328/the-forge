# Vendor SPICE libraries

Stored here for deterministic, offline ngspice runs and `sim.yml` `.include` paths.

## TI TPS63070 transient model

- Path: [`tps63070/TPS63070_TRANS.LIB`](tps63070/TPS63070_TRANS.LIB)
- **SHA256** (committed `TPS63070_TRANS.LIB`; recompute after any edit):\
  `ddd7e074ddc29fcf75b72179432c6359613adc40b1142a4723ba39703af37ba2`
- **Upstream:** Texas Instruments **TPS63070 Unencrypted PSpice Transient Model** (ZIP `slvmbp8a` from the product page). TI’s netlist macros use PSPICE-only `{{IF(...)}}`-style constructs; **upstream ngspice batch cannot ingest that verbatim file**.
- **In this repo:** the checked-in `TPS63070_TRANS.LIB` is an **ngspice-native behavioral stub** with the same `.SUBCKT` name (`TPS63070_TRANS`) and pin order as TI’s wrapper so KiCad **`Sim.*`** mappings and **`run_sim`** keep working offline. Replace with TI’s PSPICE copy locally if you use Cadence/ORCAD PSPICE; use this stub for **`ngspice`** CI/board smoke only.
- **License / redistribution:** Downloads from TI (including the original `slvmbp8a` pack) are subject to TI’s published terms at the time you obtain them. The **checked-in `.LIB` file is maintained in-repo as a compatibility stub for ngspice batch / CI**, not as a verbatim redistribution of TI’s shipped netlist macros; cite the datasheet and TI product collateral for device definition. If you substitute TI’s upstream files verbatim, observe whatever license attaches to those files.

## Interpreting transient vs AC with the TPS63070 ngspice stub

- **What this model is:** A pin-compatible **behavioral substitute** so KiCad-exported decks and `run_sim.py` run in **ngspice batch** without PSPICE-only macros. It is **not** a bit-accurate copy of TI’s encrypted transient deck.
- **Transient limits (`sim.yml`):** Guard **regressions against this stub and this schematic export**, not against bench silicon or TI PSPICE. Replacing the `.LIB` with TI’s upstream verbatim file or swapping vendor macros invalidates committed **`spice_metrics_baseline.json`** until limits are re-derived.
- **Ripple and dynamics:** The stub can report **near-ideal** output ripple or switching detail compared to a full vendor model; treat absence of visible ripple as a **modeling limitation**, not proof of performance.
- **Secondary `.ac` deck (`ac_small_signal.cir`):** Small-signal AC is linearized around the **DC bias** from that deck (bias differs from large-signal transient PWL). **`FIND V(...)` AT=<freq>** reports magnitude at that frequency for this linearization — useful for **relative regression** across commits (including multi-point checks such as 10 kHz vs 100 kHz), not for quoting datasheet AC figures without calibration.
- **Layout overlays:** Elements in `boards/<board>/sim/extracted_*.cir` model **PCB adjuncts** (distribution, ESL estimates, etc.). They change waveforms **on top of** the stub; interpret metrics as **schematic + stub + overlay**, not as golden hardware prediction.
