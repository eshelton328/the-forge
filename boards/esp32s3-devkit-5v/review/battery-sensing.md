# Switched battery-voltage measurement

The BATTERY button remains GPIO10. Measurement is now implemented separately on **GPIO2, ADC1 channel 1**, enabled by **GPIO12**. The schematic's Power monitoring sheet contains Q6/Q7, R45–R49 and C34.

Q6 is an AO3401A high-side switch: source on protected battery node PFET, drain on BAT_MEAS. R45 pulls its gate to source for default OFF. GPIO12 drives Q7 through R46; R47 keeps Q7 off at reset. GPIO12 HIGH pulls the PMOS gate low and enables the divider. The body diode blocks battery-to-divider current when Q6 is off.

R48 = 33 kΩ and R49 = 10 kΩ, both 0.1%: **Vbattery = Vadc × 4.3**. At 3 V and 6 V battery voltage, the ADC sees approximately 0.698 V and 1.395 V. The divider draws 70–140 µA while enabled. C34 = 100 nF sits beside GPIO2; `(33k || 10k) × 100nF = 0.767 ms`. Allow **10 ms** after enabling, take calibrated ADC readings with averaging, then drive GPIO12 LOW. Use an attenuation setting covering the maximum input; validate settling on hardware. Resistor-only worst-case ratio error is approximately ±0.154%, before ADC, temperature and switch errors.

R49 grounds the ADC node when the switch is off. A deliberately injected 5 µA switch-leakage case produces 50 mV at the ADC in the functional regression. This checks the discharge path; it does not characterize the actual MOSFET over temperature. The USB detector also passes a functional case with VBUS present while 3.3 V is off.

The measurement envelope is **0–6 V at the protected node**. The converters still require at least 3 V at VIN for cold start. Confirm chemistry, cell count and maximum voltage before fabrication. The existing three-AA simulations are scenarios, not a confirmed battery specification.

Firmware sequence:

1. Keep GPIO12 LOW at boot and during sleep.
2. On a battery indication request, set GPIO12 HIGH and wait 10 ms.
3. Read calibrated GPIO2 ADC voltage, average samples and multiply by 4.3.
4. Set GPIO12 LOW; apply chemistry-specific thresholds with hysteresis.
5. Display the result through RGB or OLED. Voltage alone is not a precise state-of-charge percentage.

The measurement is of the protected node, so Q1 and cable loss can make it lower than open-circuit battery voltage under load. Record load state when sampling. This hardware PR provides the circuit and firmware pin/sequencing contract; it does not select or modify an unrelated firmware application.

Sources: [Espressif ADC guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/index.html), [AO3401A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf), [MMBT3904](https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf). `tools/check_monitoring.py` derives six functional fixtures from the exported netlist and records `monitoring-validation.json`.
