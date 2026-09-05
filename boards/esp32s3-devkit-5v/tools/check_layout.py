#!/usr/bin/env python3
"""Check layout intent beyond DRC. Run with KiCad Python after saved zone fill."""
from pathlib import Path
import argparse
import json
import math
import pcbnew as p

D = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--board', type=Path, default=D / 'esp32s3-devkit-5v.kicad_pcb')
parser.add_argument('--report', type=Path, default=D / 'review/layout-validation.json')
args = parser.parse_args()
b = p.LoadBoard(str(args.board))
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
converter_caps = {}
for ref, caps in [('U1', ['C3', 'C5']), ('U2', ['C11', 'C13'])]:
    x, y = p.ToMM(fps[ref].GetPosition().x), p.ToMM(fps[ref].GetPosition().y)
    ground = [v for v in vias if v.GetNetname() == 'GND' and abs(p.ToMM(v.GetPosition().x)-x)<.1 and y-5.2 <= p.ToMM(v.GetPosition().y) <= y-3.7]
    assert len(ground) >= 2, (ref, 'PGND needs both nearby plane connections')
    # Proximity alone cannot certify loop inductance. These bounds prevent the
    # previous regression where rotating ceramics doubled their supply paths.
    for cap, pin in zip(caps, ['12', '7']):
        power = next(pd for pd in fps[ref].Pads() if pd.GetNumber() == pin)
        positive = next(pd for pd in fps[cap].Pads() if pd.GetNumber() == '1')
        negative = next(pd for pd in fps[cap].Pads() if pd.GetNumber() == '2')
        distance = lambda a, c: math.hypot(p.ToMM(a.x-c.x), p.ToMM(a.y-c.y))
        separation = distance(power.GetPosition(), positive.GetPosition())
        assert separation <= 2.0, (ref, cap, 'local supply ceramic too far from power pin', separation)
        def intersects_pad(t, pd):
            a, c, q = t.GetStart(), t.GetEnd(), pd.GetPosition()
            dx, dy = c.x-a.x, c.y-a.y
            ratio = max(0, min(1, ((q.x-a.x)*dx+(q.y-a.y)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
            return pd.HitTest(p.VECTOR2I(round(a.x+ratio*dx), round(a.y+ratio*dy)))
        direct = [t for t in tracks if t.GetNetname() == positive.GetNetname()
                  and t.GetLayer() == p.F_Cu and p.ToMM(t.GetWidth()) >= .4-1e-6
                  and intersects_pad(t, power) and intersects_pad(t, positive)]
        assert direct, (ref, cap, 'requires a direct top-side supply connection at least 0.4 mm wide')
        nearest_ground_via = min(distance(negative.GetPosition(), v.GetPosition())
                                 for v in vias if v.GetNetname() == 'GND')
        assert nearest_ground_via <= 1.2, (ref, cap, 'missing local capacitor return via')
        converter_caps[cap] = {'ic': ref, 'power_pad_separation_mm': round(separation, 4),
                               'direct_supply_track_min_width_mm': .4,
                               'ground_pad_to_via_mm': round(nearest_ground_via, 4)}
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
report['converter_capacitors'] = converter_caps
report['scope'] = 'Geometry and connectivity guards; no extracted parasitic, EMI or thermal validation'
args.report.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
