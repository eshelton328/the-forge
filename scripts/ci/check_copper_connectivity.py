#!/usr/bin/env python3
"""Fail if any pad is electrically stranded — i.e. has no copper on it.

Why this exists
---------------
KiCad's DRC "unconnected items" check uses the ratsnest, which can consider a
pad connected to a zone when the zone's *outline* overlaps the pad even though
the *filled* copper never reaches it. On esp32s3-devkit this shipped a dead
board: the whole battery input (/VBAT) was pour-only with no tracks, the /VBAT
pour was pinched to 0.17 mm against the neighbouring /PFET pour, and Q1's drain
pad ended up outside the fill. DRC reported "0 unconnected items" on every run.

This check tests the real invariant, geometrically:

    every pad on a multi-pad net must be either
      (a) inside the FILLED copper of a same-net zone, or
      (b) touched by a same-net track endpoint or via.

Run:  python3 scripts/ci/check_copper_connectivity.py boards/<board>
Exit: 0 = all pads have copper, 1 = at least one stranded pad, 2 = usage error.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

try:
    import pcbnew
except ImportError:  # pragma: no cover - depends on runtime
    print("check_copper_connectivity: pcbnew unavailable — run under KiCad's python", file=sys.stderr)
    raise SystemExit(2)


def pad_has_copper(board, pad) -> bool:
    """True if this pad actually has same-net copper on it."""
    netcode = pad.GetNetCode()
    pos = pad.GetPosition()

    # (a) filled copper of a same-net zone, on a layer the pad is on
    for zone in board.Zones():
        if zone.GetNetCode() != netcode:
            continue
        for layer in pad.GetLayerSet().Seq():
            if not zone.IsOnLayer(layer):
                continue
            try:
                if zone.HitTestFilledArea(layer, pos, 0):
                    return True
            except Exception:
                continue

    # (b) a same-net track/via touching the pad. Test the track *body*, not just
    # its endpoints: a track routed straight through a pad connects it even
    # though neither endpoint lands on the pad.
    for track in board.GetTracks():
        if track.GetNetCode() != netcode:
            continue
        if isinstance(track, pcbnew.PCB_VIA):
            if pad.HitTest(track.GetPosition()):
                return True
            continue
        if pad.HitTest(track.GetStart()) or pad.HitTest(track.GetEnd()):
            return True
        try:
            if track.HitTest(pos):  # track passes over the pad
                return True
        except Exception:
            pass

    return False


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)

    board_dir = Path(sys.argv[1]).resolve()
    pcb = board_dir / f"{board_dir.name}.kicad_pcb"
    if not pcb.is_file():
        print(f"PCB not found: {pcb}", file=sys.stderr)
        raise SystemExit(2)

    board = pcbnew.LoadBoard(str(pcb))

    # Group by (footprint, pad number). Pads sharing a number in one footprint are
    # the same electrical node (module thermal pads with integrated heatsink vias,
    # switches with two pins per terminal), so the node is fine if ANY instance
    # has copper. Skip single-pad and intentionally-unconnected nets.
    pads_by_net: dict[str, list] = defaultdict(list)
    nodes: dict[tuple[str, str], list] = defaultdict(list)
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            name = pad.GetNetname()
            if not name or name.startswith("unconnected-"):
                continue
            ref = footprint.GetReference()
            pads_by_net[name].append(pad)
            nodes[(ref, pad.GetNumber())].append((name, pad))

    stranded = []
    checked = 0
    for (ref, padnum), entries in sorted(nodes.items()):
        net = entries[0][0]
        if len(pads_by_net[net]) < 2:
            continue  # a lone pad on a net has nothing to connect to
        checked += 1
        if not any(pad_has_copper(board, pad) for _, pad in entries):
            pos = entries[0][1].GetPosition()
            stranded.append(
                f"{ref}.{padnum} net={net} "
                f"at ({pcbnew.ToMM(pos.x):.2f}, {pcbnew.ToMM(pos.y):.2f})"
            )

    print(f"copper connectivity: checked {checked} pad-nodes across {len(pads_by_net)} nets")
    if stranded:
        print(f"\nFAIL: {len(stranded)} pad(s) have no same-net copper (pour outline != filled copper):")
        for item in stranded:
            print(f"  - {item}")
        print("\nFix: route the net with an explicit track, or reshape the pour so the")
        print("filled copper actually reaches the pad. Do not rely on pours alone for power.")
        raise SystemExit(1)

    print("OK: every pad on a multi-pad net has same-net copper.")


if __name__ == "__main__":
    main()
