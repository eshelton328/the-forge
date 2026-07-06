# USB D+/D- differential pair — openEMS simulation

First board-owned EMS simulation (see [`emi/README.md`](../../../../emi/README.md)
for the toolchain): the USB full-speed differential pair from U3 (USBLC6 ESD
diodes) to the ESP32-S3 module's native USB pins — the only external
interface on this board fast enough to care about, and the path a failed
enumeration would implicate.

## What gets simulated

`make_slice.py` crops the board to the pair's route (board coords
x 131–155.5, y 90.5–117): F.Cu stubs at both ends, the B.Cu diagonal with
the length-matching meander, layer-change vias, nearby GND stitching vias,
the In1.Cu GND plane, and the B.Cu/F.Cu GND pours. The In2.Cu 3V3 plane is
retagged to GND — gerber2ems does not model capacitors, and upstream
guidance is to short decoupled planes, which is what the plane looks like
at RF. All footprints are dropped; the four trace ends are terminated by
simulation ports SP1–SP4 (45 Ω each, USB's 90 Ω differential).

Segment J3→U3 is not included: it is short, and the ESD part between the
two segments cannot be represented in an FDTD geometry anyway.

## Regenerating inputs

`fab/` (gerbers, PTH drill, port CSV, stackup) is committed so the sim can
run without KiCad. To regenerate after layout changes to the pair:

```bash
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 make_slice.py
```

(The script runs each pcbnew mutation in a separate process — the SWIG
bindings corrupt module state otherwise. `slice.kicad_pcb` is a gitignored
intermediate.)

## Running

```bash
docker build -t the-forge-open-ems:local -f emi/docker/Dockerfile emi/docker
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD/boards/esp32s3-devkit/emi/usb-diff-pair:/work" -w /work \
  the-forge-open-ems:local -a
```

On Apple Silicon add `--platform linux/amd64` to both commands — the
pinned `triangle` wheel only exists for x86-64 Linux.

Results land in `ems/results/` (gitignored): S-parameters, impedance
plots, and a Smith chart per excited port.

## Results (first run, 2026-07-06)

- **SDD21 (differential insertion loss): ~0 dB flat to 3 GHz** — no
  resonant suck-outs from the meander or the via transitions. USB
  full-speed content (< ~100 MHz) passes untouched.
- **SDD11 (differential return loss): −10 to −24 dB**, worst around
  1.5–2 GHz, ≈ −14 dB at 100 MHz. Fine for full-speed edge rates.
- **Z_diff swings ~60–160 Ω** with frequency (reflections of an
  uncontrolled line), averaging near the USB spec's 90 Ω. As predicted,
  the pair is not impedance-controlled — acceptable for FS, would need a
  re-route for high-speed (480 Mbps) work.

## Via modeling caveats (hard-won — read before editing)

gerber2ems models each drill hit as a **thin annular tube** from
`drill/2` to `drill/2 + via/plating_thickness`, punched through every
plane. Three failure modes we hit before getting physical results:

1. **Unused inner-layer via pads** leave a copper island inside the
   plane antipad; at FDTD voxel resolution the ~0.2 mm ring bridges and
   reads as a dead short (`|Z| ≈ ωL` of the via, +90°). `make_slice.py`
   sets `SetRemoveUnconnected` on the pair's vias.
2. **Standard antipads (~0.2 mm) are too tight** for the mesh — the
   barrel voxel-bridges to the plane. The slice widens In1/In2 zone
   clearance to 0.45 mm (0.6 mm antipad radius).
3. **The default 50 µm tube wall voxelizes away** at any practical mesh,
   leaving the layers unconnected (capacitive open, −90°). We set
   `via/plating_thickness: 200` so the wall spans ~5 mesh cells. This
   fattens the barrel (0.35 mm vs the real ~0.175 mm outer radius),
   slightly under-reporting via inductance — irrelevant below a few GHz.

Sanity checks when touching any of this: `Arg(Z)` near ±90° across the
whole band means short/open, not a transmission line; S21 ≈ −80 dB means
the ports aren't galvanically connected. The upstream examples never
route signal through a via, so do not assume defaults handle it.
