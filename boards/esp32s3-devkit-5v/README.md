# ESP32-S3 DevKit with switched 5 V audio rail

Revised schematic and fully routed **74 × 75 mm, four-layer prototype PCB**. Reviewed 2026-09-04. Battery/load limits and enclosure dimensions remain provisional; this is not a manufacturing release.

The battery feeds an AO3401A reverse-polarity stage and two TPS63070 buck-boost regulators: 3.307 V for the ESP32-S3-WROOM-1-N16/RTC and 4.985 V for the MAX98357A amplifier. GPIO18 enables the audio rail. USB-C is data-only. An RV-3028 RTC, switched OLED header, four wake-capable buttons and RGB indicator complete the board. The button row, viewed from the component side, is **VOL− / MODE / VOL+ / BATTERY**, using GPIO4 / GPIO5 / GPIO6 / GPIO10 respectively.

The review fixed USB CC1/VBUS wiring, removed load current from the slide switch, corrected RTC no-backup wiring, added amplifier control supply isolation and OLED I²C isolation, corrected the RGB part's common-anode pinout, added USB series resistors and enlarged selected ceramic capacitor packages. The incoming working files are preserved locally in the Git-ignored `.history/review-original-2026-09-04/` directory.

- [Component analysis, calculations, manufacturer datasheets and release work](review/design-review.md)
- [Schematic PDF](review/schematic.pdf)
- [PCB preview](review/pcb-preview.png), [perspective render](review/pcb-3d-perspective.png) and [assembly STEP](review/esp32s3-devkit-5v-assembly.step). All 97 component footprints have local models; four use documented approximations. See [model provenance and limits](3dmodels/README.md).
- [GPIO changes](review/gpio-map.csv) and [component inventory](review/component-inventory.csv)
- [Electrical checks](review/erc.json), [PCB checks](review/drc.json), [intent validation](review/validation.json)

I²S changes: BCLK GPIO47, LRCLK GPIO48, DIN GPIO14. OLED power moves to GPIO41; GPIO11 controls its bus connection. RGB GPIO38/39/40 are now active LOW. Firmware sequencing is documented in the review. The BATTERY button is an active-low request input; the voltage-sensing circuit and battery-level thresholds are still pending battery chemistry/cell-count or maximum-voltage specifications. No battery measurement input is currently implemented; see [missing components and sensing plan](review/battery-sensing.md).

Verified: **0 ERC violations; 0 PCB DRC errors; 0 unconnected items; 0 schematic parity issues; all 295 checked pad nodes have copper.** Two DRC library warnings document board-local silkscreen changes to J2/U3, moved to F.Fab where their outlines overhang the board. No electrical warnings were suppressed.

The CI DRC command uses `--exit-code-violations`, which returns exit code 5 for these two warnings. The prototype therefore does not yet pass the strict DRC gate; the intentional footprint variants need to be reconciled with their libraries before merge.

Before ordering, confirm battery and audio current, final mechanics, SW1's exact footprint/part match, orderable capacitor MPNs and effective capacitance, fabricator stackup/USB impedance, thermal vias and assembly constraints. No Gerbers or purchasing BOM are released by this review.

The native KiCad files are authoritative. `tools/generate_pcb.py` and `tools/route_pcb.py` record the initial construction workflow; running them replaces the layout and requires repeating cleanup, fill, DRC and visual review. The router uses KiCad Python, NumPy and a small C++ search library compiled from `tools/grid_search.cpp` to `/tmp/esp32_grid_search.dylib` on macOS. `finalize_pcb.py` applies only explicit unused-copper and off-board-silkscreen findings from the current DRC report; rerun DRC after each cleanup.

Checks after edits:

```sh
kicad-cli sch export netlist --format kicadxml -o review/netlist.xml esp32s3-devkit-5v.kicad_sch
python3 tools/check_netlist.py
kicad-cli sch erc --format json -o review/erc.json esp32s3-devkit-5v.kicad_sch
kicad-cli pcb drc --refill-zones --schematic-parity --format json -o review/drc.json esp32s3-devkit-5v.kicad_pcb
```

From the repository root, also run `python3 scripts/validate_board.py boards/esp32s3-devkit-5v` and, under KiCad Python, `scripts/ci/check_copper_connectivity.py boards/esp32s3-devkit-5v`. Ensure ground zones are actually filled and saved; the connectivity guard checks saved copper.
