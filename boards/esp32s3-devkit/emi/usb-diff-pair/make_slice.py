#!/usr/bin/env python3
"""Generate the gerber2ems input slice for the USB D+/D- differential pair.

Run with KiCad's bundled Python (needs pcbnew):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/\
Current/bin/python3 make_slice.py

Produces fab/ (gerbers, PTH drill, port position CSV) plus the intermediate
slice PCB (slice.kicad_pcb, kept out of git). The slice:
  - crops to the /D+ /D- route between U3 (USB ESD) and the ESP32 module,
  - keeps GND tracks/vias/zones inside the crop (return path),
  - retags the In2.Cu 3V3 plane to GND — gerber2ems does not simulate
    capacitors, and at RF the decoupled power plane acts as a ground
    reference, so this follows the upstream guidance to short them,
  - drops all footprints; the pair is terminated by SP1-SP4 simulation
    ports defined in fab/usb-diff-pair-pos.csv (see simulation.json).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent.parent / "esp32s3-devkit.kicad_pcb"
SLICE = HERE / "slice.kicad_pcb"
FAB = HERE / "fab"

# Crop window in board coordinates (mm): the U3->module route incl. meander.
X0, Y0, X1, Y1 = 131.0, 90.5, 155.5, 117.0
NETS = ("/D+", "/D-")

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

# Matches the board's physical stackup (JLC 4-layer, 1.6mm) in gerber2ems
# stackup.json format. Written into fab/ on every export.
def _layer(name, type_, **kw):
    base = {"name": name, "type": type_, "color": None, "thickness": None,
            "material": None, "epsilon": None, "lossTangent": None}
    base.update(kw)
    return base

STACKUP = {
    "layers": [
        _layer("F.Mask", "Top Solder Mask", color="Green", thickness=0.01),
        _layer("F.Cu", "copper", thickness=0.035),
        _layer("dielectric 1", "prepreg", thickness=0.1, material="FR4",
               epsilon=4.5, lossTangent=0.02),
        _layer("In1.Cu", "copper", thickness=0.035),
        _layer("dielectric 2", "core", thickness=1.24, material="FR4",
               epsilon=4.5, lossTangent=0.02),
        _layer("In2.Cu", "copper", thickness=0.035),
        _layer("dielectric 3", "prepreg", thickness=0.1, material="FR4",
               epsilon=4.5, lossTangent=0.02),
        _layer("B.Cu", "copper", thickness=0.035),
        _layer("B.Mask", "Bottom Solder Mask", color="Green", thickness=0.01),
    ],
    "format_version": "1.0",
}

mm = pcbnew.FromMM


def in_crop(pos):
    return (mm(X0) <= pos.x <= mm(X1)) and (mm(Y0) <= pos.y <= mm(Y1))


def pass_footprints() -> None:
    shutil.copy(BOARD, SLICE)
    b = pcbnew.LoadBoard(str(SLICE))
    for fp in list(b.GetFootprints()):
        b.Remove(fp)
    pcbnew.SaveBoard(str(SLICE), b)


def pass_tracks() -> None:
    b = pcbnew.LoadBoard(str(SLICE))
    for t in list(b.GetTracks()):
        net = t.GetNetname()
        if net in NETS:
            if isinstance(t, pcbnew.PCB_VIA):
                # Drop unused inner-layer via pads: the pad island inside
                # the plane antipad voxel-bridges to the plane at FDTD
                # resolution and reads as a dead short at the via.
                t.SetRemoveUnconnected(True)
            continue
        if net == "GND" and isinstance(t, pcbnew.PCB_VIA) and in_crop(t.GetPosition()):
            continue
        if net == "GND" and not isinstance(t, pcbnew.PCB_VIA) \
                and in_crop(t.GetStart()) and in_crop(t.GetEnd()):
            continue
        b.Remove(t)
    pcbnew.SaveBoard(str(SLICE), b)


def pass_zones_retag() -> None:
    b = pcbnew.LoadBoard(str(SLICE))
    gnd = b.FindNet("GND").GetNetCode()
    in1 = b.GetLayerID("In1.Cu")
    in2 = b.GetLayerID("In2.Cu")
    # NB: ZONE.GetLayerName() is unreliable via SWIG here; IsOnLayer works.
    for z in b.Zones():
        if z.IsOnLayer(in2):  # 3V3 plane -> RF ground reference
            z.SetNetCode(gnd)
        if z.IsOnLayer(in1) or z.IsOnLayer(in2):
            # Widen plane antipads: gerber2ems models the via barrel with
            # outer radius drill/2 + plating_thickness, and FDTD voxels
            # bridge sub-0.1mm plane gaps (reads as a short at the via).
            z.SetLocalClearance(pcbnew.FromMM(0.45))
    pcbnew.SaveBoard(str(SLICE), b)


def pass_zones_prune() -> None:
    # Keep only the inner reference planes; the outer-layer pours refill
    # unpredictably once footprints are gone and are not needed for the
    # pair's return path (In1 is the reference).
    b = pcbnew.LoadBoard(str(SLICE))
    in1 = b.GetLayerID("In1.Cu")
    in2 = b.GetLayerID("In2.Cu")
    for z in list(b.Zones()):
        if z.GetNetname() == "GND" and (z.IsOnLayer(in1) or z.IsOnLayer(in2)):
            continue
        b.Remove(z)
    pcbnew.SaveBoard(str(SLICE), b)


def pass_edge() -> None:
    b = pcbnew.LoadBoard(str(SLICE))
    for d in list(b.GetDrawings()):
        if d.GetLayerName() == "Edge.Cuts":
            b.Remove(d)
    rect = pcbnew.PCB_SHAPE(b)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(mm(X0), mm(Y0)))
    rect.SetEnd(pcbnew.VECTOR2I(mm(X1), mm(Y1)))
    rect.SetLayer(b.GetLayerID("Edge.Cuts"))
    rect.SetWidth(mm(0.1))
    b.Add(rect)
    # Drill/aux origin at the crop's bottom-left (KiCad Y grows downward).
    b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(mm(X0), mm(Y1)))
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(str(SLICE), b)


def pass_export() -> None:
    FAB.mkdir(exist_ok=True)
    for old in FAB.glob("*"):
        old.unlink()

    subprocess.run(
        [KICAD_CLI, "pcb", "export", "gerbers",
         "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,Edge.Cuts",
         "--use-drill-file-origin", "--no-x2", "--no-netlist",
         "-o", str(FAB) + "/", str(SLICE)],
        check=True,
    )
    subprocess.run(
        [KICAD_CLI, "pcb", "export", "drill",
         "--format", "excellon", "--drill-origin", "plot",
         "--excellon-separate-th",
         "-o", str(FAB) + "/", str(SLICE)],
        check=True,
    )
    # gerber2ems expects <text>-<layer>.gbr / *-PTH.drl naming.
    for f in FAB.glob("slice-*"):
        if f.suffix == ".gbrjob":
            f.unlink()
        elif f.name == "slice-PTH.drl":
            f.rename(FAB / "usb-diff-pair-PTH.drl")
        elif f.name == "slice-NPTH.drl":
            f.unlink()
        else:  # copper/mask/edge gerber, whatever plot extension KiCad chose
            layer = f.stem.replace("slice-", "")
            f.rename(FAB / f"usb-diff-pair-{layer}.gbr")

    with open(FAB / "stackup.json", "w") as fh:
        json.dump(STACKUP, fh, indent=4)
        fh.write("\n")

    # Port markers: positions relative to bottom-left, Y up.
    def pos(x_kicad, y_kicad):
        return x_kicad - X0, Y1 - y_kicad

    ports = [
        ("SP1", *pos(134.0, 113.907), -90),   # D+ at U3 end, wave -> +X
        ("SP2", *pos(151.438, 93.3), 180),    # D+ at module end, wave -> -Y
        ("SP3", *pos(134.0, 112.015), -90),   # D- at U3 end
        ("SP4", *pos(152.627, 93.3), 180),    # D- at module end
    ]
    with open(FAB / "usb-diff-pair-pos.csv", "w") as fh:
        fh.write("Ref,Val,Package,PosX,PosY,Rot,Side\n")
        for ref, x, y, rot in ports:
            fh.write(
                f'"{ref}","Simulation_Port","Simulation_Port",'
                f"{x:.6f},{y:.6f},{rot:.6f},top\n"
            )

    print("Slice written:", SLICE)
    print("Fab inputs:", sorted(p.name for p in FAB.glob("*")))


PASSES = {
    "footprints": pass_footprints,
    "tracks": pass_tracks,
    "zones_retag": pass_zones_retag,
    "zones_prune": pass_zones_prune,
    "edge": pass_edge,
    "export": pass_export,
}


def main() -> None:
    # KiCad's SWIG bindings corrupt module state after container mutations,
    # so each pass runs in its own interpreter process.
    import sys
    if len(sys.argv) > 1:
        PASSES[sys.argv[1]]()
        return
    for name in ("footprints", "tracks", "zones_retag", "zones_prune",
                 "edge", "export"):
        subprocess.run([sys.executable, __file__, name], check=True)


if __name__ == "__main__":
    main()
