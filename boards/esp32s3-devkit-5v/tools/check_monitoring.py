#!/usr/bin/env python3
"""Exercise monitoring topology from the exported schematic, using generic models.

These are functional DC/settling checks, not transistor characterization. The
MOS model omits manufacturer parasitics. A separate forced-leakage case checks
the divider's off-state discharge path. Run with Python 3 and ngspice on PATH.
"""
from pathlib import Path
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as E

D = Path(__file__).resolve().parents[1]
root = E.parse(D / "review/netlist.xml").getroot()
components = {c.get("ref"): c for c in root.find("components")}
nodes = {}
for i, net in enumerate(root.find("nets")):
    for node in net:
        nodes[node.get("ref"), node.get("pin")] = "0" if net.get("name") == "GND" else f"n{i}"


def n(ref, pin):
    return nodes[ref, str(pin)]


parts = []
for ref in [f"R{i}" for i in range(40, 50)] + ["C34"]:
    value = components[ref].findtext("value").replace("F", "").replace("Ω", "")
    if value.endswith("M"):
        value = value[:-1] + "Meg"  # SPICE's M suffix means milli, not mega.
    parts.append(f"{ref} {n(ref, 1)} {n(ref, 2)} {value}")
for ref in ["Q4", "Q5", "Q7"]:
    parts.append(f"{ref} {n(ref, 3)} {n(ref, 1)} {n(ref, 2)} NPN_MIN_GAIN")
parts.append(f"MQ6 {n('Q6', 3)} {n('Q6', 1)} {n('Q6', 2)} {n('Q6', 2)} PMOS_FUNCTIONAL L=1u W=1u")
parts += [".model NPN_MIN_GAIN NPN (IS=6.7f BF=40 VAF=100)", ".model PMOS_FUNCTIONAL PMOS (LEVEL=1 VTO=-0.7 KP=5)"]
cases = [
    ("usb_absent", 3.3, 0, 4.8, 0, 0),
    ("usb_present", 3.3, 4.4, 4.8, 0, 0),
    ("usb_board_off", 0, 5.5, 6, 0, 0),
    ("battery_read_3v", 3.3, 0, 3, 3.3, 0),
    ("battery_read_6v", 3.3, 5.5, 6, 3.3, 0),
    ("battery_off_5uA_leakage", 0, 5.5, 6, 0, 5e-6),
]
results = []
with tempfile.TemporaryDirectory(prefix="forge-monitor-") as tmp:
    for name, vdd, vbus, vbat, enable, leakage in cases:
        deck = [f"* {name}; schematic-derived monitoring topology", *parts,
                f"VVDD {n('R44', 1)} 0 {vdd}", f"VUSB {n('R40', 1)} 0 {vbus}",
                f"VBAT {n('Q6', 2)} 0 {vbat}", f"VEN {n('R46', 1)} 0 {enable}",
                f"ILEAK {n('Q6', 2)} {n('Q6', 3)} {leakage}",
                ".tran 10u 20m", f".meas tran usb_gpio FIND v({n('Q5', 3)}) AT=19m",
                f".meas tran battery_adc FIND v({n('R49', 1)}) AT=19m", ".end"]
        path = Path(tmp) / f"{name}.cir"
        path.write_text("\n".join(deck) + "\n")
        run = subprocess.run(["ngspice", "-b", str(path)], capture_output=True, text=True)
        log = run.stdout + run.stderr
        assert run.returncode == 0, log
        values = {key: float(re.search(rf"(?m)^{key}\s*=\s*([-+0-9.eE]+)", log)[1]) for key in ["usb_gpio", "battery_adc"]}
        if vdd and vbus:
            assert values["usb_gpio"] > 0.75 * vdd, (name, values)
        else:
            assert abs(values["usb_gpio"]) < 0.1, (name, values)
        target = vbat / 4.3 if enable else leakage * 10000
        assert abs(values["battery_adc"] - target) < 0.005, (name, values, target)
        results.append({"case": name, **values, "passed": True})
(D / "review/monitoring-validation.json").write_text(json.dumps({"scope": "Schematic-derived functional model; not manufacturer device characterization", "cases": results}, indent=2) + "\n")
print(f"PASS: {len(results)} monitoring cases, including USB with MCU supply off and battery-switch leakage.")
