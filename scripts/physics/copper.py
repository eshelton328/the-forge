"""Saved copper polygons and finite-volume sheet discretization, millimetres."""
from collections import defaultdict
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']


def copper_shapes(data):
    groups = defaultdict(list)
    for item in data['copper']:
        for poly in item['polygons']:
            if len(poly['outer']) >= 3:
                g = Polygon(poly['outer'], poly['holes'])
                if not g.is_valid:
                    g = shapely.make_valid(g)
                groups[item['layer'], item['net']].append(g)
    for t in data['tracks']:
        groups[t['layer'], t['net']].append(LineString([t['a'], t['b']]).buffer(t['width']/2, quad_segs=8))
    for v in data['vias']:
        annulus = Point(v['xy']).buffer(v['diameter']/2, quad_segs=12)
        for l in v['layers']:
            groups[l, v['net']].append(annulus)
    return {k: unary_union(v).buffer(0) for k, v in groups.items()}


def pad(data, ref, number):
    return next(p for p in data['footprints'][ref]['pads'] if p['number'] == str(number))


def layer_shapes(data):
    shapes = copper_shapes(data)
    return [unary_union([v for (layer, _), v in shapes.items() if layer == l]) for l in LAYERS]
