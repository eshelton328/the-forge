# ESP32-S3 compact dual-rail design review

Revised 2026-09-04 for PR #122. This is a routed engineering prototype, with battery/load and enclosure specifications still provisional. The current native schematic and PCB supersede the previous 74 × 75 mm placement.

## Implemented changes

| Area | Revised implementation |
|---|---|
| Board | 64 × 56 mm, four layers; 35.42% less area. Four M3 holes; 15 mm button pitch retained. Module antenna overhang remains beyond the north edge. |
| Converter cells | U1/U2 retain input-left, output-right orientation and inductors on the north side. Their centers are 23 mm apart. Nearest ceramic ground pads face north, with local ground vias; supply-pad centers are 1.81 mm from their IC power pins, with direct 0.4 mm F.Cu connections. VAUX and feedback lower resistors return explicitly on the AGND side. PGND has two nearby plane vias per converter. Inductor connections stay on F.Cu. |
| Audio | U6 sits beside J3. Both BTL outputs are 5.373 mm long on F.Cu: 1.673 mm of 0.2 mm package escape, then 0.6 mm main conductors. Zero speaker vias. The prior 0.15 mm paths used different layers and two vias each. KiCad rules and `check_layout.py` now guard this. |
| USB | Q4/Q5 and R40–R44 produce a positive presence signal on GPIO7. VBUS reaches Q4 through 100 kΩ; GPIO7 is pulled only to 3.3 V. With the board off, there is no direct VBUS-to-GPIO divider or clamp path. Two stages preserve the polarity expected by self-powered TinyUSB configuration. This is presence detection, not a precision VBUS undervoltage comparator. |
| Battery measurement | Q6/Q7, R45–R49 and C34 provide switched 33 kΩ/10 kΩ sensing on GPIO2, enabled by GPIO12. Default OFF; 0–6 V protected-node envelope. See `battery-sensing.md`. |
| Power-good | U1 PG → GPIO15; U2 PG → GPIO13. Both 100 kΩ pull-ups connect to 3.3 V. U2's former 5 V pull-up was changed before connecting its PG to the MCU. |
| Mechanics/library | SW1 consistently selects MSK12C02. The manufacturer drawing agrees with asymmetric 3.0/1.5 mm terminal spacing, 3 mm locating-pin spacing and the selected footprint. USB, module and speaker overhang variants live in `footprints/Board.pretty`; their assembly outlines use F.Fab. Strict DRC no longer reports library mismatches. |
| Test access | Eight unpopulated underside probe pads: GND, PFET, 3.3 V, 5 V, GPIO15/PG3, GPIO13/PG5, EN_3V3 and GPIO18/EN5. |
| Simulation | U7/U8 explicitly excluded where no device model exists. Fresh hierarchical exports are handled correctly. Stimuli feed PFET and close SW1 between SW_ON and EN_3V3. Added an actual-schematic dual-rail enabled/load scenario and six monitoring scenarios. |

## Follow-up after the capacitor placement concern

The first compact revision, 77e62ed, rotated C3/C5/C11/C13 to put ground pads inward but increased their explicit VIN/VOUT route length from about 1.91 mm to 4.38 mm. That tradeoff was not adequately covered by the earlier checks, and calling it an unqualified improvement was too strong.

The correction restores north-facing ceramic ground pads and moves the four capacitor centers closer to the IC. Their power-pad center separation is 1.8085 mm, with a direct top-side supply segment at least 0.4 mm wide. Ground pads remain within 0.70 mm of their local ground vias. U2's enable escape was moved away from C11. The compact outline, regulator orientation, inductors, quiet returns and two PGND plane vias remain. `check_layout.py` now checks proximity, the direct supply connection and nearby capacitor ground vias. It passes the corrected PCB and rejects the saved 77e62ed PCB as a negative control.

These are geometry checks, not a PCB parasitic extraction. Complete-loop inductance, ringing, emissions and thermal performance remain unverified. The existing SPICE converter is a behavioral approximation; 25 passing measures must not be interpreted as physical switching or layout validation.

## Buck-boost placement assessment

The original cell orientation was fundamentally sensible; blindly mirroring a regulator would not improve its electrical behavior. The revised layout keeps repeated cells, small top-side switching nodes and a continuous In1.Cu ground reference. Converter control components stay on the quieter south side. Input/output ceramics retain their nominal capacitance budget while their local returns improve. Feedback and VAUX have explicit short ground connections; the ground pours and In1.Cu plane remain common, without a split plane under signal returns.

The package's narrow PGND escape is not the sole return path: filled ground copper also connects the device, with two nearby PGND plane vias and separate capacitor-return vias. The analog ground arrangement is a deliberate local return, not an isolated analog ground island. Inspect the [power/audio copper detail](power-audio-copper.png) and [ground-plane view](pcb-copper.png) as well as the 3D rendering. None of these geometric checks substitute for conducted/radiated EMI, thermal or load-transient measurements.

## Circuit functions retained

J1 feeds AO3401A reverse-polarity Q1 and both TPS63070 inputs. U1 regulates to `0.8 × (1 + 470/150) = 3.3067 V`; U2 regulates to `0.8 × (1 + 680/130) = 4.9846 V`. Both use 1.5 µH XFL4020 inductors. PS/SYNC HIGH selects power save. SW1 carries enable current only, selecting U1 EN through R31 or grounding it; it is standby control, not battery isolation. Q1 is not a charger, fuse or battery undervoltage protector.

The MAX98357A uses its BTL output and 12 dB gain setting. Neither speaker terminal is ground. U8 provides dual-supply isolation for SD_MODE. The OLED supply switch and U7 I²C branch switch let the RTC remain connected while OLED power is off. The RV-3028 uses the manufacturer's no-backup connection; disable backup switching/trickle charging, and expect loss of time when U1 is switched off. R11 remains DNP to avoid a continuous power-LED load. The common-anode RGB outputs are active LOW.

Nominal capacitance remains 30 µF at each converter input, 198 µF across the distributed 3.3 V output network and 186 µF across the distributed 5 V network. These are bookkeeping totals, not effective capacitance at bias and not proof of stability.

## Datasheet checks and sources


- [TI TPS63070](https://www.ti.com/lit/ds/symlink/tps63070.pdf): cold start requires at least 3.0 V at VIN while output is below 3 V. Its 3.6 A switch rating is not a 3.6 A output guarantee. The 1.5 µH application lists 15 µF minimum effective output capacitance; nominal MLCC values alone do not demonstrate compliance. VAUX is bypassed locally and has no external load. Both unused VSEL pins are grounded; FB2 is grounded. Reviewed the recommended power-loop and feedback layout.
- [Coilcraft XFL4020-152](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xfl/xfl4020/xfl4020-152/): selected XFL4020-152MEC, 1.5 µH ±20%, maximum DCR 15.8 mΩ, 4.1 A saturation rating at 10% inductance drop. Temperature and ripple still require checking at the selected load.
- [Espressif module datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf), [schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html), [PCB guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html): checked module pin functions, reset network, supply capacity, USB series components, continuous USB ground reference and antenna placement. A supply capable of at least 500 mA is required for the ESP32-S3 design; RF bursts and the other loads need additional margin.
- [Analog Devices MAX98357A/B](https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf): checked 2.5–5.5 V operation, BTL output, gain/channel selection, bypassing and control-pin limits. DIN/BCLK/LRCLK have independent 6 V absolute limits; SD_MODE is constrained to VDD + 0.3 V. Drive I²S low before powering down anyway.
- [Micro Crystal RV-3028 manual](https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3028-C7_App-Manual.pdf), especially the no-backup application, and [datasheet](https://www.microcrystal.com/fileadmin/Media/Products/RTC/Datasheet/RV-3028-C7.pdf): checked no-backup connection, I²C, interrupt and local bypassing. Disable backup switching and trickle charging; time is lost when 3.3 V turns off.
- [ST USBLC6-2](https://www.st.com/resource/en/datasheet/usblc6-2.pdf), [AOS AO3401A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf), [onsemi MMBT3904](https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf): checked ESD pin routing, PMOS source/drain/gate assignment and transistor base drive.
- [TI SN74LVC2G66](https://www.ti.com/lit/ds/symlink/sn74lvc2g66.pdf), [TI SN74LVC1T45](https://www.ti.com/lit/ds/symlink/sn74lvc1t45.pdf): package pin maps and enable/direction/supply behavior are reflected in local `Review.kicad_sym` symbols. The bus switch uses a constant 3.3 V supply; the translator provides partial-power isolation.
- [Wuerth RGB LED drawing](https://www.we-online.com/components/products/datasheet/150141M173100.pdf): verified physical pin map from the mechanical/electrical drawing, rather than assuming the generic KiCad LED symbol matched.
- [JST PH connector specification](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf): 2 A rating with specified wire. Connector, cable and battery resistance limit usable system power.
- [Murata GRM31CR61C226KE15L](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR61C226KE15-01A.pdf): 22 µF, 16 V, 1206 candidate for C6–C8 and C14–C16. Increased the packages from the incoming design. Obtain DC-bias curves for the actual ordered parts before asserting effective capacitance. C3/C5/C11/C13 moved from 0402 to 0603.


- [Shouhan MSK12C02 manufacturer specification and drawing](https://files.keeb.supply/products/MSK12C02/datasheet.pdf): drawing on the final page; 12 V/50 mA contacts are adequate for the enable-only function.
- [Espressif self-powered USB guidance](https://docs.espressif.com/projects/esp-iot-solution/en/release-v2.0/usb/usb_overview/usb_device_self_power.html): monitor VBUS presence and configure the device as self-powered.

## Firmware contract

The complete map is in `gpio-map.csv`. I²S uses GPIO47 BCLK, GPIO48 LRCLK and GPIO14 DIN. GPIO18 enables the 5 V rail; GPIO21 controls audio through U8. GPIO41 enables OLED power, and GPIO11 connects its bus. Buttons are GPIO4/5/6/10 in VOL−/MODE/VOL+/BATTERY order. RGB GPIO38/39/40 are active LOW.

At boot, hold GPIO18, GPIO21, GPIO41, GPIO11 and GPIO12 LOW; drive RGB outputs HIGH for off. Configure GPIO15 and GPIO13 as PG inputs. For audio, assert GPIO18 and wait for GPIO13 HIGH with a timeout before asserting GPIO21; keep a device settling delay appropriate to the amplifier. Shut down SD_MODE and drive I²S low before disabling the rail. Read U1 PG on GPIO15 for diagnostics; it does not replace brownout supervision.

Configure TinyUSB as self-powered with `vbus_monitor_io = GPIO_NUM_7`; GPIO7 is HIGH when VBUS is present. Verify attach/detach with battery power and USB in both connector orientations. The detector's thresholds are transistor-based, not USB supply-quality qualification.

For OLED power-up, assert GPIO41, allow its supply/reset to settle, then assert GPIO11. Disconnect GPIO11 before turning GPIO41 off. For battery indication, assert GPIO12, wait 10 ms, read calibrated GPIO2 ADC voltage, multiply by 4.3, then deassert GPIO12. Define chemistry-specific thresholds separately. This hardware revision updates the circuit and pin map; firmware integration remains application-specific.

## Power and manufacturing envelope still to confirm

At 85% converter efficiency, 0.5 A on each output at 3 V input requires approximately 1.63 A from the battery. A 3.2 W audio output at an assumed 90% amplifier efficiency plus a 0.5 A 3.3 V load requires approximately 2.04 A before additional losses. That exceeds the JST-PH input's 2 A rating with specified wire. These are estimates, not measured operating ratings; establish limits for the chosen battery and speaker.

Before fabrication:

1. Confirm battery chemistry/cell count, maximum voltage (≤6 V for this measurement design), loaded minimum voltage, speaker impedance, continuous/peak audio demand and standby behavior. There is no hardware battery cutoff or charger.
2. Complete capacitor MPNs and DC-bias/ESR checks, especially C21/C26 at 100 µF/1206 and the 10 µF ceramics. The retained nominal bank does not prove the TPS63070 minimum effective output capacitance. `component-inventory.csv` is not a released purchasing BOM.
3. Confirm the fabricator's four-layer stackup and solve the USB 90 Ω geometry. The current main pair uses 0.15 mm tracks and a nominal 0.15 mm gap; impedance is not yet established. The prototype minimums are 0.15 mm track/clearance and 0.2 mm through-via drill. Select a compatible filled/capped thermal-via/stencil process for the exposed-pad footprints.
4. Check enclosure, connector access and antenna clearance in real mechanics. Hole centers relative to the board's northwest corner are (4,4), (60,4), (4,43), (60,45) mm. The bottom holes are intentionally offset around connectors/buttons; this is not a drop-in match for the old board. Keep batteries, cables and enclosure metal out of the antenna clearance volume.
5. Bench-test current-limited startup, USB attach/detach and off-state behavior, both power-good signals, standby current, ADC accuracy/leakage, OLED isolation, RTC wake, combined Wi-Fi/audio load, battery sag and component temperatures. Class-D speaker cable EMI depends on the final cable and enclosure; validate before choosing any output filter.

## Verification

The JLCPCB four-layer advanced rule profile also passes with zero violations; the fab runner now combines and restores persistent board rules. CI runs the new pin/layout checks and monitoring fixtures.

KiCad 10.0.1: 0 ERC violations, 0 DRC violations including warnings, 0 unconnected items and 0 schematic parity issues. All 342 checked pad nodes across 70 nets have actual saved copper. Layout checks enforce speaker geometry, top-side switching nodes, two PGND plane vias per converter, button pitch and an unrouted In1.Cu ground reference. The final board has 112 electrical footprints, four mounting holes, eight test pads, 3,022 track segments and 219 vias.

All 25 configured ngspice measures and six schematic-derived monitoring scenarios pass. All 18 focused board-validator, SPICE-export and fabrication-rule-preservation tests pass, including hierarchical sheet instances, missing/cyclic sheets, multiline root ports and preserved SPICE child definitions. Numerical 1 TΩ shunts regularize passive nodes left floating by excluded digital ICs; nodeset supplies an initial guess for the ideal feedback model. Neither forces a final rail voltage. The TPS63070 model is the repository's behavioral approximation, not TI's switching model. The additional ESP-NOW/battery fixtures are illustrative behavioral load scenarios, not extracted physical power performance. No ripple, EMI, thermal, endurance or USB compliance claim follows from these simulations.

The two-page schematic, top/bottom copper and rendered component placement were inspected. All 112 electrical footprints resolve local models; J1/J3/U5/U6 use documented approximations. The updated assembly STEP was re-imported. Actuator heights and exact molding still need confirmation against final purchased parts.
