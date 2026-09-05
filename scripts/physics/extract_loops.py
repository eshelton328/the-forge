#!/usr/bin/env python3
"""FastHenry extraction of PCB-only local bypass loops. No device/package model."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import numpy as np
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from copper import copper_shapes, pad

LOOPS = [('U1', 'C3', ['12', '13']), ('U1', 'C5', ['7', '8']),
         ('U2', 'C11', ['12', '13']), ('U2', 'C13', ['7', '8'])]


def extract(data, shapes, ref, cap, pins, pitch, margin, spacing, nhinc, out, executable):
    out.mkdir(parents=True, exist_ok=True)
    u = data['footprints'][ref]['xy']
    power_net = pad(data, ref, pins[0])['net']
    # Same local window about each IC across revisions; expand for boundary check.
    xmin, ymin, xmax, ymax = u[0]-5-margin, u[1]-5.5-margin, u[0]+5+margin, u[1]+1+margin
    region = box(xmin, ymin, xmax, ymax)
    xs = np.arange(xmin, xmax+pitch/2, pitch)
    ys = np.arange(ymin, ymax+pitch/2, pitch)
    lines = ['* PCB-only copper mesh: capacitor and package internals excluded',
             '.units mm', f'.default sigma=58000 nhinc={nhinc} nwinc=1']
    nodes, coords, edges = {}, [], []
    for layer, net, z, thick in [('F.Cu', power_net, 0, .035),
                                 ('F.Cu', 'GND', 0, .035),
                                 ('In1.Cu', 'GND', -spacing, .0175)]:
        geom = shapes[layer, net].intersection(region)
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                if geom.covers(Point(x, y)):
                    n = len(coords)
                    nodes[layer, net, i, j] = n
                    coords.append((float(x), float(y), z, layer, net))
                    lines.append(f'n{n} x={x:.9g} y={y:.9g} z={z:.9g}')
        for (l, nt, i, j), n in list(nodes.items()):
            if (l, nt) != (layer, net):
                continue
            for di, dj in [(1, 0), (0, 1)]:
                key = (layer, net, i+di, j+dj)
                if key in nodes and geom.covers(LineString([coords[n][:2], coords[nodes[key]][:2]])):
                    edges.append((n, nodes[key], pitch, thick, ''))
    equiv = []
    def contact(layer, net, geom):
        ns = [i for i, c in enumerate(coords) if c[3:5] == (layer, net) and geom.covers(Point(c[:2]))]
        if not ns:
            raise ValueError(f'No mesh contact: {ref}/{cap} {layer} {net}; refine pitch')
        return ns
    def short(ns):
        if len(ns)>1:
            # Keep line length modest for the legacy parser.
            for n in ns[1:]:
                equiv.append(f'.equiv n{ns[0]} n{n}')
        return ns[0]
    # Via annuli are ideal contact patches. Barrel = eight parallel copper strips;
    # correct plated area, not a solid drill cylinder. F.Cu to In1 only.
    via_count = 0
    for v in data['vias']:
        if v['net'] != 'GND' or not region.contains(Point(v['xy'])):
            continue
        if not {'F.Cu', 'In1.Cu'}.issubset(v['layers']):
            continue
        patch = Point(v['xy']).buffer(v['diameter']/2)
        try:
            top = contact('F.Cu', 'GND', patch)
            bot = contact('In1.Cu', 'GND', patch)
        except ValueError:
            continue
        a, b = short(top), short(bot)
        via_count += 1
        plating = .025
        radius = (v['drill']+plating)/2
        for k in range(8):
            theta = 2*math.pi*k/8
            x, y = v['xy'][0]+radius*math.cos(theta), v['xy'][1]+radius*math.sin(theta)
            pair = []
            for z in [0, -spacing]:
                n = len(coords)
                coords.append((x, y, z, 'barrel', 'GND'))
                lines.append(f'n{n} x={x:.9g} y={y:.9g} z={z:.9g}')
                pair.append(n)
            equiv.extend([f'.equiv n{a} n{pair[0]}', f'.equiv n{b} n{pair[1]}'])
            edges.append((*pair, 2*math.pi*radius/8, plating,
                          f' wx={-math.sin(theta):.9g} wy={math.cos(theta):.9g} wz=0'))
    def pad_contact(r, numbers):
        polygons = []
        for item in data['copper']:
            if item['kind'] == 'pad' and item['layer'] == 'F.Cu' and item['ref'] == r and item['pad'] in numbers:
                from shapely.geometry import Polygon
                polygons.extend(Polygon(p['outer'],p['holes']) for p in item['polygons'])
        net = pad(data, r, numbers[0])['net']
        return contact('F.Cu', net, unary_union(polygons))
    supply = short(pad_contact(ref, pins))
    pgnd = short(pad_contact(ref, ['10']))
    cpos = short(pad_contact(cap, ['1']))
    cneg = short(pad_contact(cap, ['2']))
    # Collapse each solder land to an equipotential port. External ideal closure
    # across the capacitor excludes its body ESL; add it separately in SPICE.
    equiv.append(f'.equiv n{cpos} n{cneg}')
    for i, (a,b,w,h,orientation) in enumerate(edges):
        lines.append(f'e{i} n{a} n{b} w={w:.9g} h={h:.9g}{orientation}')
    lines.extend(equiv)
    lines.extend([f'.external n{supply} n{pgnd}', '.freq fmin=1 fmax=100000000 ndec=1', '.end'])
    deck = '\n'.join(lines)+'\n'
    deck_path=out/'loop.inp'
    # Only reuse an identical deck with a completed solver transcript. Every
    # impedance matrix is parsed and checked again below, including row count.
    log_path=out/'solver.log'
    identical=(deck_path.exists() and deck_path.read_text()==deck and (out/'Zc.mat').exists()
               and log_path.exists() and 'All impedance matrices dumped' in log_path.read_text())
    options=[]
    if (out/'solver-options.json').exists():
        options=json.loads((out/'solver-options.json').read_text())
    if not identical:
        deck_path.write_text(deck)
        proc = subprocess.run([str(executable), 'loop.inp'], cwd=out, capture_output=True, text=True, timeout=1200)
        log_path.write_text(proc.stdout+proc.stderr)
        options=[]
        if proc.returncode:
            (out/'solver-default-failed.log').write_text(proc.stdout+proc.stderr)
            options=['-p','seg']
            proc=subprocess.run([str(executable),'loop.inp',*options],cwd=out,capture_output=True,text=True,timeout=1200)
            log_path.write_text(proc.stdout+proc.stderr)
        if proc.returncode or 'All impedance matrices dumped' not in log_path.read_text():
            raise RuntimeError(f'FastHenry failed: {out}/solver.log')
    (out/'solver-options.json').write_text(json.dumps(options)+'\n')
    mat = (out/'Zc.mat').read_text()
    rows = []
    for f, r, im in re.findall(r'frequency = ([\deE+.-]+) 1 x 1\s+([\deE+.-]+)\s+([\deE+.-]+)j', mat):
        f,r,im=map(float,(f,r,im))
        if r<=0 or im<=0 or not all(math.isfinite(x) for x in (f,r,im)):
            raise ValueError('Non-passive or non-finite loop extraction')
        rows.append({'frequency_hz': f, 'resistance_ohm': r, 'inductance_h': im/(2*math.pi*f)})
    if len(rows)!=9:
        raise ValueError(f'Expected nine frequency points, got {len(rows)}')
    result = {'ic':ref,'capacitor':cap,'power_net':power_net,'pitch_mm':pitch,
              'window_mm':[xmin,ymin,xmax,ymax],'fcu_in1_centers_mm':spacing,
              'nhinc':nhinc,'solver_options':options,'nodes':len(coords),'segments':len(edges),'ground_vias':via_count,
              'pcb_sha256':data['pcb_sha256'],'deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),
              'results':rows,'scope':'PCB-only F.Cu power/GND and In1.GND local window; equipotential solder-land ports; eight-strip plated vias; remote copper and component/package internals omitted'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('geometry',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--fasthenry',type=Path,required=True)
    p.add_argument('--pitch',type=float,default=.2);p.add_argument('--margin',type=float,default=0)
    p.add_argument('--spacing',type=float,default=.2);p.add_argument('--nhinc',type=int,default=3)
    p.add_argument('--cap',choices=['C3','C5','C11','C13'])
    a=p.parse_args();d=json.loads(a.geometry.read_text());s=copper_shapes(d)
    results=[]
    for ic,cap,pins in LOOPS:
        if a.cap and a.cap!=cap:continue
        r=extract(d,s,ic,cap,pins,a.pitch,a.margin,a.spacing,a.nhinc,a.output/cap,a.fasthenry.resolve())
        results.append(r)
        print(cap,r['results'][6],flush=True)
    (a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
