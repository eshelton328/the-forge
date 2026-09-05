# ESP32-S3 DevKit with switched 5 V audio rail

Fully routed **64 × 56 mm, four-layer engineering prototype**, revised 2026-09-04. The compact layout is **35.42% smaller** than the previous 74 × 75 mm board. The four buttons retain 15 mm spacing and the component-side order **VOL− / MODE / VOL+ / BATTERY**.

Battery J1 feeds an AO3401A reverse-polarity stage and two TPS63070 buck-boost regulators: 3.307 V for the ESP32-S3/RTC and 4.985 V for the MAX98357A amplifier. GPIO18 enables the audio rail. USB-C is data-only. The RTC, switched OLED bus, wake buttons and common-anode RGB indicator remain.

The converter cells keep the nearest input/output ceramics beside the power pins, with their ground pads facing north. Their power-pad centers are 1.81 mm from VIN/VOUT, with direct 0.4 mm top-side connections. Explicit quiet feedback/VAUX returns and two nearby PGND plane connections per converter are retained. The amplifier sits beside the speaker connector. Both speaker traces are 5.37 mm long, entirely on F.Cu, with 0.6 mm main conductors and short 0.2 mm package escapes; neither uses vias. In1.Cu remains the ground reference.

New monitoring hardware provides positive USB-presence detection on GPIO7, switched battery-voltage sensing on GPIO2/ADC1 with GPIO12 enable, and converter power-good inputs on GPIO15/13. Both PG pull-ups use 3.3 V. Eight labeled underside test pads expose ground, protected battery, both rails, enables and power-good signals. SW1 now consistently specifies MSK12C02. Board-local overhang footprint variants eliminate the previous library warnings.

- [Design review, sources, firmware sequencing and remaining release work](review/design-review.md)
- [Battery measurement details](review/battery-sensing.md) and [GPIO map](review/gpio-map.csv)
- [Two-page schematic PDF](review/schematic.pdf)
- [Top render](review/pcb-preview.png), [perspective render](review/pcb-3d-perspective.png), [bottom render](docs/pcb-bottom.png), [assembly STEP](review/esp32s3-devkit-5v-assembly.step)
- [Component inventory](review/component-inventory.csv) and [3D model provenance](3dmodels/README.md)
- [Verification summary](review/verification-summary.json), [layout checks](review/layout-validation.json), [monitoring checks](review/monitoring-validation.json), [SPICE report](docs/spice-report.md)

Verified: **0 ERC violations; 0 DRC violations including warnings; 0 unconnected items; 0 schematic parity issues.** All **342 checked pad nodes across 70 nets** have saved copper. Board intent checks, the JLCPCB four-layer advanced rule profile, all 25 simulation measures, six monitoring scenarios and 80 Python tests pass (one integration test skipped). All 112 electrical footprints have local models; J1/J3/U5/U6 use documented approximations. These checks do not establish thermal, RF, USB compliance or battery endurance performance.

**Physical screening update:** the [full test report](review/physical-validation/report.md), [machine-readable results](review/physical-validation/summary.json), [raw solver data](review/physical-validation/raw-data.zip) and [free-tool runbook](../../scripts/physics/README.md) now cover PCB-only parasitics, passive supply impedance, bounded ringing, differential conducted-noise transfer and comparative PCB temperature. The compact board is **8.4 C warmer** than the original in the reference thermal scenario. A higher-loss, weak-cooling case reaches **132.8 C modeled PCB temperature at 50 C ambient**. These are assumed operating conditions, not measurements or junction temperatures. Copper inductance changes **21.6-31.8% on mesh refinement**, so its convergence gate remains open. **Physical release is not approved.** Confirm loads, cooling, stackup and component models before fabrication; green CI means the screening executes, not that these physical gates are waived.

Battery chemistry, speaker/load limits and final mechanics remain provisional. The measurement circuit is designed for a protected battery node up to 6 V; it is not a fuel gauge, charger or battery protection circuit. Before ordering, confirm the battery/load envelope, capacitor MPNs and effective capacitance, fabricator stackup/USB impedance, thermal-via assembly process and enclosure fit. The existing capacitance budget is retained.

The native KiCad files are authoritative. Placement generation replaces the PCB and requires routing, cleanup, saved zone fill, checks and visual review again. `generate_pcb.py`, `route_pcb.py`, `finalize_pcb.py` and `attach_3d_models.py` record that workflow. Use KiCad Python for PCB tools; compile `tools/grid_search.cpp` to `/tmp/esp32_grid_search.dylib` on macOS for routing. Run cleanup/fill and DRC until no newly exposed unused stubs remain.

From this directory, after schematic edits:

```sh
kicad-cli sch export netlist --format kicadxml -o review/netlist.xml esp32s3-devkit-5v.kicad_sch
python3 tools/check_netlist.py
python3 tools/check_monitoring.py
kicad-cli sch erc --format json --exit-code-violations -o review/erc.json esp32s3-devkit-5v.kicad_sch
kicad-cli pcb drc --refill-zones --schematic-parity --format json --exit-code-violations -o review/drc.json esp32s3-devkit-5v.kicad_pcb
```

Run `tools/check_layout.py` and the repository's `scripts/ci/check_copper_connectivity.py` under KiCad Python after saving filled zones. From the repository root, run `python3 scripts/validate_board.py boards/esp32s3-devkit-5v`, `python3 scripts/sim/export_kicad_spice.py --board-dir boards/esp32s3-devkit-5v`, and `python3 scripts/sim/run_sim.py --config boards/esp32s3-devkit-5v/sim.yml`. Simulation exports are regenerated from the schematic.
