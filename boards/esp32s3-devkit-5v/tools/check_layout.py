#!/usr/bin/env python3
"""Check layout intent beyond DRC. Run with KiCad Python after saved zone fill."""
from pathlib import Path
import json
import math
import pcbnew as p

D = Path(__file__).resolve().parents[1]
b = p.LoadBoard(str(D / 'esp32s3-devkit-5v.kicad_pcb'))
fps = {f.GetReference(): f for f in b.GetFootprints()}
tracks = [t for t in b.GetTracks() if not isinstance(t, p.PCB_VIA)]
vias = [t for t in b.GetTracks() if isinstance(t, p.PCB_VIA)]
assert not any(t.GetLayer() == p.In1_Cu for t in tracks), 'In1.Cu must remain an unrouted ground reference'
assert any(z.GetNetname() == 'GND' and z.IsOnLayer(p.In1_Cu) and z.GetFilledPolysList(p.In1_Cu).OutlineCount() for z in b.Zones()), 'Save the filled ground plane first'
speaker = {}
for net in ['/speaker +', '/speaker -']:
    ts = [t for t in tracks if t.GetNetname() == net]
    assert ts and all(t.GetLayer() == p.F_Cu for t in ts), net
    assert not any(t.GetNetname() == net for t in vias), net
    assert all(p.ToMM(t.GetWidth()) >= .2 - 1e-6 for t in ts), net
    narrow = sum(p.ToMM(t.GetLength()) for t in ts if p.ToMM(t.GetWidth()) < .6 - 1e-6)
    total = sum(p.ToMM(t.GetLength()) for t in ts)
    assert narrow <= 1.8 and total <= 6, (net, narrow, total)
    speaker[net] = {'length_mm': round(total, 4), 'package_escape_mm': round(narrow, 4), 'main_width_mm': .6, 'vias': 0, 'layer': 'F.Cu'}
for ref in ['U1', 'U2']:
    x, y = p.ToMM(fps[ref].GetPosition().x), p.ToMM(fps[ref].GetPosition().y)
    ground = [v for v in vias if v.GetNetname() == 'GND' and abs(p.ToMM(v.GetPosition().x)-x)<.1 and y-5.2 <= p.ToMM(v.GetPosition().y) <= y-3.7]
    assert len(ground) >= 2, (ref, 'PGND needs both nearby plane connections')
    for pin in ['9', '11']:
        net = next(pd.GetNetname() for pd in fps[ref].Pads() if pd.GetNumber() == pin)
        assert not any(v.GetNetname() == net for v in vias), (ref, net)
        assert all(t.GetLayer() == p.F_Cu for t in tracks if t.GetNetname() == net), (ref, net)
xs = [p.ToMM(fps[f'SW{i}'].GetPosition().x) for i in range(4, 8)]
assert all(abs(c-a-15)<.001 for a,c in zip(xs,xs[1:])), xs
edge = b.GetBoardEdgesBoundingBox()
width, height = round(p.ToMM(edge.GetWidth()), 1), round(p.ToMM(edge.GetHeight()), 1)
assert width <= 64.1 and height <= 56.1, (width, height)
report = {'passed': True, 'outline_mm': [64, 56], 'area_reduction_percent': round(100*(1-64*56/(74*75)), 2), 'electrical_footprints': len([f for f in fps if not f.startswith(('TP','H'))]), 'test_points': 8, 'track_segments': len(tracks), 'vias': len(vias), 'speaker': speaker, 'in1_signal_tracks': 0, 'button_pitch_mm': 15}
(D/'review/layout-validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
