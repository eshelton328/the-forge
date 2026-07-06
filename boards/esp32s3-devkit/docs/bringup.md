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

## 5b. ESP-NOW brownout margin (the breadboard failure, quantified)

The brownout seen on the breadboard is battery ESR × burst current sagging
the input (breadboard contact resistance made it worse). The SPICE study
(`sim/tran_espnow_*.cir`, behavioral converter) predicts: a fresh pack
sags to ~4.3 V (fine), a 3.6 V / 1.2 Ω tired pack to ~2.6 V (marginal but
working), and a 3 Ω dead pack collapses mid-burst. Verify on the bench:

- [ ] Scope **VBAT_SW** (C1 positive terminal) and **3V3** together,
      DC-coupled, while firmware sends ESP-NOW bursts. Fresh pack:
      VBAT_SW dips stay above ~4 V.
- [ ] Repeat with a tired pack — or fake one by adding 1 Ω in series with
      fresh cells: VBAT_SW must stay **above ~2.3 V** during bursts. If
      the module resets, the sag you scoped is the real pack ESR talking.
- [ ] Bump the series resistor until bursts fail; record that ESR. It
      converts directly to a firmware low-battery threshold ("stop
      transmitting below X volts") instead of guessing.
- [ ] Firmware mitigation worth measuring: reduce TX power
      (`esp_wifi_set_max_tx_power`) — ESP-NOW at room range rarely needs
      +20 dBm, and the PA is most of the burst current.

## 5c. Rev-2 planning notes (5 V rail + audio amp)

The rev-2 preview deck (`sim/tran_rev2_amp_preview.cir`) shows WiFi + a
3 W-class amp works on a **fresh** pack (VIN sags to ~3.8 V) but has **no
operating point on worn alkalines** — the demanded power exceeds the
pack's physical maximum (V²/4R), so audio-at-volume brownouts on old AAs
are a battery limit, not a board bug. Plan rev-2 around that:

- Low-ESR chemistry: 3x NiMH (fraction of alkaline ESR, same holder) or a
  single Li-ion cell with protection + charger.
- A bulk capacitor bank (≥470 µF electrolytic/polymer) on VBAT_SW to
  soften burst edges — note it cannot ride through ms-long bursts, only
  help the converter's first microseconds.
- Move SW1 out of the power path (switch U1's EN instead) before adding
  amp current on top of its ~0.3 A contact rating.
- Give the amp its own brownout behavior: mute below a pack-voltage
  threshold so audio degrades before the radio/MCU browns out.

## 6. Sign-off record

Record per-board: date, pack voltage, idle current, 3V3 reading, deep-sleep
current, flash OK, WiFi soak OK. First article: keep oscilloscope shots of
3V3 ripple at idle and during TX bursts (AC-coupled, 20 MHz BW limit) next
to this file in `docs/`.
