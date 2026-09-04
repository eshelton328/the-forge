# Battery indication: missing hardware

The schematic currently has a BATTERY button on GPIO10 and an RGB LED/OLED interface, but **no battery-to-ADC circuit and no fuel-gauge IC**. Pressing the button cannot currently measure the battery. The regulated 3.3 V/5 V rails are not a useful substitute for battery-voltage measurement because the converters regulate them as the battery discharges.

For a basic low/medium/high indication, the proposed additions are:

- Two precision resistors forming a divider from the protected battery rail to a spare ADC input. Their ratio must keep the highest possible pack voltage within the selected ADC range, including tolerances.
- A local ADC filter capacitor; 100 nF is a reasonable starting point in [Espressif's ADC guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/index.html). Use calibrated readings, adequate settling time and averaging.
- A switchable measurement path with suitable transistor/load-switch bias components, so it does not continuously drain the pack or back-power the ESP32 when its 3.3 V rail is off. Exact topology and voltage ratings depend on the pack. Do not use a permanently connected high-voltage divider without checking the powered-off ADC path.

GPIO2 is presently unused in this module's schematic and is a candidate for the ADC signal, subject to the final channel assignment. The button remains a separate digital input. Firmware would enable sensing, wait for settling, read the battery, disable sensing, then show an indication on the RGB LED or OLED.

A calibrated voltage reading can support broad thresholds, but it is not inherently an accurate state-of-charge percentage. Load, temperature, battery chemistry and discharge history matter. For a dependable percentage or remaining-runtime estimate, evaluate a chemistry-appropriate fuel gauge and its required support components instead. See [Analog Devices' fuel-gauging explanation](https://www.analog.com/en/resources/technical-articles/battery-fuel-gauges-accurately-measuring-charge-level.html).

**Needed before selecting components/values:** battery chemistry, series-cell count (or maximum pack voltage), and whether the desired indication is broad levels or a percentage. No sensing parts have been added yet; selecting a one-cell lithium gauge or a particular divider now would assume a battery specification that has not been supplied.
