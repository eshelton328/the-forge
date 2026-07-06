# esp32s3-devkit — bench bring-up checklist

First-article test plan for assembled boards. The SPICE suite (`sim.yml`)
covers wiring/topology regressions with a quasi-ideal converter model, so
**dynamics live here**: real droop, ripple, current, and RF behavior are
bench measurements. Work top to bottom; stop and diagnose on any failure.

Power source for all steps: 3×AA in a battery holder wired to **J1 pin 2
(VBAT, +)** and **J1 pin 1 (GND, −)**. There is no barrel jack or USB power
path — USB-C is data-only by design. A bench supply with current limit
(start at 100 mA) substituting for the pack makes steps 1–4 safer.

## 1. Visual + smoke checks (before batteries)

- [ ] Inspect solder on U1 (VQFN — check for bridges on the FB/VAUX side),
      L1, and the ESP32 module edge castellations.
- [ ] Confirm D2 (SOD-323 pads between L1 and SW2 area) is **unpopulated** —
      it is DNP by design.
- [ ] Continuity: VBAT (J1.2) ↔ Q1 drain; GND (J1.1) ↔ USB shell.
- [ ] No short: VBAT→GND, 3V3→GND (meter in continuity mode; a brief cap
      charge blip is normal).

## 2. First power (current-limited supply if available)

- [ ] Supply 4.5 V at VBAT, limit 100 mA, SW1 **off**: current ≈ 0 (only Q1
      gate pulldown leakage path exists and it is gated by SW1).
- [ ] SW1 **on**: D1 (battery LED) lights. Idle current at the supply
      **< ~25 mA** (converter quiescent + LEDs ≈ 4 mA + margin; tens of mA
      or the limit tripping = investigate before proceeding).
- [ ] `3V3` rail (J2.5 vs J2.6): **3.24–3.37 V** (divider gives 3.307 V
      nominal ±1% PWM / ±3% PFM accuracy). D3 (3V3 LED) lights.
- [ ] Reverse-battery test (do this once, deliberately): swap supply leads at
      J1, SW1 on. Current must read ~0 and nothing warms up — Q1 blocking.
      Restore polarity; board must come back up.

## 3. Brown-out / battery-range sweep (bench supply)

- [ ] Sweep VBAT 4.8 → 3.0 V at idle: 3V3 stays in range the whole way
      (converter transitions buck → buck-boost → boost around 3.3–3.5 V in).
- [ ] Continue 3.0 → 2.0 V: rail should hold (running spec); note the
      voltage where it finally drops out.
- [ ] Power-cycle at 2.8 V: converter may legitimately **fail to restart**
      (start-up needs ≥ 3.0 V). Confirm it restarts at ≥ 3.0 V.

## 4. Flashing over USB (the core requirement)

- [ ] Batteries in, SW1 on, USB-C to computer: device enumerates
      (`USB JTAG/serial debug unit` — ESP32-S3 native USB).
- [ ] Hold BOOT (SW3), tap RESET (SW2), release BOOT → ROM download mode
      (`esptool.py chip_id` succeeds).
- [ ] Flash a blink/hello sketch; RESET; it runs.
- [ ] Confirm the board does **not** enumerate or power up from USB alone
      (SW1 off): VBUS must not back-feed the 3.3 V rail.
- [ ] Flash again while powered at 3.2 V pack voltage (weak batteries) —
      verifies boot strapping (IO0/EN pull-ups to 3V3) is solid at the
      bottom of the battery range.

## 5. Load / RF stress (real batteries now)

- [ ] Firmware doing continuous WiFi TX (e.g. iperf or esp-idf
      `wifi_throughput` example). With **fresh cells**: no brown-out, no
      module resets over 10 min. Note pack current (clamp meter or series
      shunt); expect ~0.15–0.25 A average, ~0.5–0.7 A bursts.
- [ ] Same test with a **tired pack (~3.2 V)**: watch for resets — this is
      the boost-mode worst case. If it browns out here, suspect pack ESR
      before blaming the board (alkalines near end-of-life exceed 1 Ω/cell).
- [ ] Feel SW1 and Q1 after the TX soak: warm is acceptable, hot is not
      (SW1's slide contacts are the least-rated element in the path —
      rev-2 candidate: switch U1's EN instead of the power path).
- [ ] Deep-sleep firmware: pack current should drop to **< ~5 mA**
      (dominated by D1's ~2.5 mA battery LED + converter quiescent).
      Record the number — it sets shelf life; a rev-2 could jumper the LEDs.

## 6. Sign-off record

Record per-board: date, pack voltage, idle current, 3V3 reading, deep-sleep
current, flash OK, WiFi soak OK. First article: keep oscilloscope shots of
3V3 ripple at idle and during TX bursts (AC-coupled, 20 MHz BW limit) next
to this file in `docs/`.
