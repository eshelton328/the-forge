# Free PCB physical screening

This suite evaluates PR #122's saved copper with free software. It supplements DRC and the repository's idealized TPS63070 topology tests. **A successful program/CI exit means the screening ran and its mathematical controls passed. It does not mean all physical acceptance gates passed.** Read `gates` in `summary.json` and the board's published report.

## Reproduce

Python 3.12, ngspice, Clang/make, and KiCad Python are required. The installer applies [a small statistics-adapter fix](fasthenry-stats.patch) and uses scalar Clang with `-O2 -fno-strict-aliasing -DFOUR`. The WR archive passes its wrapper pointer to Sparse's diagnostic function, which expects the underlying matrix; that invalid read crashes some meshes on Linux and intermittently on Mac. The patch corrects the diagnostic pointer and leaves the numerical equations unchanged. Install the numerical dependencies in a virtual environment; these are separate from KiCad's interpreter. FastHenry is the pinned WR archive with its no-royalty license, not an older differently licensed mirror. No MATLAB, paid solver, or purchased instrument is required.

```sh
python3.12 -m venv .cache/physics-venv
.cache/physics-venv/bin/pip install -r scripts/physics/requirements.txt
bash scripts/physics/install_fasthenry.sh .cache/fasthenry
mkdir -p output/physical-screening
git show f11e64e:boards/esp32s3-devkit-5v/esp32s3-devkit-5v.kicad_pcb > output/physical-screening/original.kicad_pcb
```

On macOS, `KICAD_PY` below can be `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`; on Linux use the Python with `pcbnew` installed. Set that task-specific variable before these commands.

```sh
"$KICAD_PY" scripts/physics/export_geometry.py boards/esp32s3-devkit-5v/esp32s3-devkit-5v.kicad_pcb output/physical-screening/current.json
"$KICAD_PY" scripts/physics/export_geometry.py output/physical-screening/original.kicad_pcb output/physical-screening/original.json
.cache/physics-venv/bin/python scripts/physics/run_screening.py \
  --geometry output/physical-screening/current.json \
  --reference-geometry output/physical-screening/original.json \
  --pcb boards/esp32s3-devkit-5v/esp32s3-devkit-5v.kicad_pcb \
  --config boards/esp32s3-devkit-5v/analysis/assumptions.json \
  --fasthenry .cache/fasthenry/fasthenry-3.0wr/bin/fasthenry \
  --output output/physical-screening/results --profile full
.cache/physics-venv/bin/python -m pytest tests/test_physical_screening.py -v
```

`--profile ci` runs the coarse original/current extraction, all circuit sensitivity cases, and 1/0.5 mm nominal thermal cases. The full profile adds fine copper meshes, an expanded return-plane window, thickness filamentation, 0.25 mm thermal resolution, single-converter thermal cases and cooling/loss extremes. Full extraction takes tens of minutes on a workstation. Identical FastHenry input decks with complete successful transcripts can be reused; matrices are parsed and checked again. Thermal caches include geometry, source budgets, parameters and solver source hashes.

The dedicated GitHub workflow exports fresh KiCad geometry, checks the report's PCB/config/source hashes, runs the CI profile, and uploads raw results. The full checked-in report retains unresolved physical gates; a green CI run does not waive them. No release files are produced.

## Model contract and boundaries

- Geometry export is read-only. It includes saved filled copper and its holes, tracks, pads, via sizes/layers, and axis-aligned rectangular board dimensions. Other outline shapes and arc tracks are rejected. It never regenerates or refills the PCB.
- FastHenry meshes local F.Cu power/GND and In1 GND. Ports cover both VIN or VOUT lands and PGND lands. Each capacitor's two solder lands are shorted externally to isolate the PCB loop. Capacitor body ESL, device/package internals, other copper layers and remote circuits are omitted. Via annuli are equipotential contacts; eight vertical strips represent plated barrels. SMD pads/annuli use contact approximations. Grid strips approximate filled copper, so mesh convergence is mandatory before using absolute R/L or claiming small improvements.
- The reference is the actual pre-compaction board `f11e64e`, not the defective intermediate capacitor rotation. Both revisions use the same ports/materials/window definitions. The 77e62ed regression is separately covered by the existing layout guard.
- Passive bank calculations use selected capacitor counts/nominal values. Only the nearest loop is extracted. Other capacitor branches scale that loop by distance; mutual and shared-path impedance are omitted. These are sensitivity fixtures, not a complete extracted PDN. Missing capacitor bias/ESR/ESL curves remain release work. No regulator feedback appears in the passive tests.
- The ringing fixture is a bounded commutation current ramp driving an RLC network. It maps input/output bypass loops to each converter's L1/L2-side commutation path. The assumed package L, node C, damping and edge rates are not a TPS63070 device model. Constant lumped values above the extractor frequency band are an explicit sensitivity approximation. No switch absolute-maximum pass/fail is inferred.
- Conducted analysis is the differential-mode current-to-voltage transfer through an explicitly defined simplified 5 uH/50 ohm network. It has no common-mode path, actual switching spectrum, regulatory detector, calibrated LISN or radiated-field model. Units are ohms/dB-ohm, not dBuV emissions. Switching copper-to-In1 overlap capacitance is a parallel-plate estimate; it omits fringing and other conductors. No FasterCap or openEMS board simulation is claimed.
- Thermal analysis uses a four-sheet finite-volume network with spatial copper fractions, laminate conduction, plated-via conduction and convection at both PCB faces. Package heat enters actual solder lands through an isothermal landing node and assumed solder conductance. Internal package resistance and package-to-air paths are omitted. Edges are insulated; there is no artificial edge heatsink. The results are PCB temperatures, not junction temperatures. Copper inside a cell is homogenized; holes, plating and materials require final-stackup review. This is a transparent reduced model implemented in SciPy, not an Elmer/FreeCAD package FEM run.
- Stackup thickness and conductor parameters are currently explicit fixed implementations; unsupported changes are rejected instead of silently accepted. Ambient, loss split, load duty and cooling are provisional. Temperature is a linear screening model with fixed material properties; it is not a thermal runaway model.

The optional `probe_ti_model.py OUTPUT_DIRECTORY` downloads and hashes TI's unmodified PSpice library, then checks whether a native ngspice startup attempt actually reaches its requested end time. A compatibility run alone never validates the model. TI's model is not vendored into this repository.

## Independent controls

FastHenry DC resistance is compared with `length/(conductivity*area)`. SPICE rail impedance and conducted transfer are compared with complex-network equations. SPICE ringing is compared with an independent linear transfer function and half-timestep reruns. Thermal tests include the exact uniform-slab solution, energy balance, linearity and cooling monotonicity. A missing-capacitor negative control must change the result. Solver failure, incomplete transients, stale PCB exports, and missing mesh contacts cannot produce passing results.

Sources: [FastHenry WR source](https://github.com/wrcad/xictools/tree/master/fasthenry), [FastHenry manual](https://www.fastfieldsolvers.com/Download/FastHenry_User_Guide.pdf), [ngspice manual](https://ngspice.sourceforge.io/docs.html), [TI TPS63070 datasheet](https://www.ti.com/lit/ds/symlink/tps63070.pdf), [TI original model](https://www.ti.com/lit/zip/slvmbp8), [TI thermal metrics](https://www.ti.com/lit/an/spra953d/spra953d.pdf).
