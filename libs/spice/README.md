# Vendor SPICE libraries

Stored here for deterministic, offline ngspice runs and `sim.yml` `.include` paths.

## TI TPS63070 transient model

- Path: [`tps63070/TPS63070_TRANS.LIB`](tps63070/TPS63070_TRANS.LIB)
- **SHA256** (committed `TPS63070_TRANS.LIB`; recompute after any edit):\
  `ddd7e074ddc29fcf75b72179432c6359613adc40b1142a4723ba39703af37ba2`
- **Upstream:** Texas Instruments **TPS63070 Unencrypted PSpice Transient Model** (ZIP `slvmbp8a` from the product page). TI’s netlist macros use PSPICE-only `{{IF(...)}}`-style constructs; **upstream ngspice batch cannot ingest that verbatim file**.
- **In this repo:** the checked-in `TPS63070_TRANS.LIB` is an **ngspice-native behavioral stub** with the same `.SUBCKT` name (`TPS63070_TRANS`) and pin order as TI’s wrapper so KiCad **`Sim.*`** mappings and **`run_sim`** keep working offline. Replace with TI’s PSPICE copy locally if you use Cadence/ORCAD PSPICE; use this stub for **`ngspice`** CI/board smoke only.
- **License / redistribution:** Downloads from TI (including the original `slvmbp8a` pack) are subject to TI’s published terms at the time you obtain them. The **checked-in `.LIB` file is maintained in-repo as a compatibility stub for ngspice batch / CI**, not as a verbatim redistribution of TI’s shipped netlist macros; cite the datasheet and TI product collateral for device definition. If you substitute TI’s upstream files verbatim, observe whatever license attaches to those files.
