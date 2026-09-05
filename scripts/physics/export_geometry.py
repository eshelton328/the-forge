#!/usr/bin/env python3
"""Export saved, filled KiCad copper without modifying the board (KiCad Python)."""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as p


def xy(q):
    return [p.ToMM(q.x), p.ToMM(q.y)]


def polygons(q):
    def ring(r):
        return [xy(r.CPoint(j)) for j in range(r.PointCount())]
    return [{'outer': ring(q.COutline(i)),
             'holes': [ring(q.CHole(i, h)) for h in range(q.HoleCount(i))]}
            for i in range(q.OutlineCount())]


def export(board_path):
    b = p.LoadBoard(str(board_path))
    layers = [p.F_Cu, p.In1_Cu, p.In2_Cu, p.B_Cu]
    edges=[e for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts]
    if len(edges)!=4 or any(e.GetShape()!=p.SHAPE_T_SEGMENT for e in edges):
        raise ValueError('Thermal export currently requires a four-line rectangular outline')
    points=[xy(q) for e in edges for q in [e.GetStart(),e.GetEnd()]]
    if any(e.GetStart().x!=e.GetEnd().x and e.GetStart().y!=e.GetEnd().y for e in edges):
        raise ValueError('Thermal export requires an axis-aligned outline')
    bounds=[min(q[0] for q in points),min(q[1] for q in points),
            max(q[0] for q in points),max(q[1] for q in points)]
    d = {'schema': 1, 'pcb_sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(),
         'kicad': p.Version(), 'units': 'mm',
         'bounds': bounds,
         'footprints': {}, 'tracks': [], 'vias': [], 'copper': []}
    for f in b.GetFootprints():
        pads = []
        for pd in f.Pads():
            pads.append({'number': pd.GetNumber(), 'net': pd.GetNetname(),
                         'xy': xy(pd.GetPosition()), 'size': xy(pd.GetSize()),
                         'drill': xy(pd.GetDrillSize())})
            for layer in layers:
                if pd.IsOnLayer(layer):
                    d['copper'].append({'kind': 'pad', 'ref': f.GetReference(),
                        'pad': pd.GetNumber(), 'net': pd.GetNetname(),
                        'layer': b.GetLayerName(layer),
                        'polygons': polygons(pd.GetEffectivePolygon(layer))})
        d['footprints'][f.GetReference()] = {'xy': xy(f.GetPosition()),
            'angle': f.GetOrientationDegrees(), 'value': f.GetValue(),
            'footprint': f.GetFPIDAsString(), 'pads': pads}
    for t in b.GetTracks():
        if isinstance(t, p.PCB_VIA):
            d['vias'].append({'xy': xy(t.GetPosition()), 'diameter': p.ToMM(t.GetWidth(p.F_Cu)),
                'drill': p.ToMM(t.GetDrillValue()), 'net': t.GetNetname(),
                'layers': [b.GetLayerName(l) for l in layers if t.IsOnLayer(l)]})
        else:
            if type(t).__name__ == 'PCB_ARC':
                raise ValueError('Arc tracks require tessellation before extraction')
            d['tracks'].append({'a': xy(t.GetStart()), 'b': xy(t.GetEnd()),
                'width': p.ToMM(t.GetWidth()), 'layer': b.GetLayerName(t.GetLayer()),
                'net': t.GetNetname()})
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for l in layers:
            if z.IsOnLayer(l):
                d['copper'].append({'kind': 'zone', 'net': z.GetNetname(),
                    'layer': b.GetLayerName(l), 'polygons': polygons(z.GetFilledPolysList(l))})
    return d


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(export(args.board), separators=(',', ':'))+'\n')
