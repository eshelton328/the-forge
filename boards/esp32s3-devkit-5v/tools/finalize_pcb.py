#!/usr/bin/env python3
"""Apply reviewed DRC cleanup; fill zones and save actual copper, not outlines.
Run with KiCad Python after the initial drc.json has been generated.
"""
from pathlib import Path
import json
import pcbnew as p
D=Path(__file__).resolve().parents[1];f=D/'esp32s3-devkit-5v.kicad_pcb';b=p.LoadBoard(str(f))
r=json.loads((D/'review/drc.json').read_text())
tracks=list(b.GetTracks());footprints=list(b.GetFootprints())
remove=set();fab=set()
for x in r['violations']:
 if x['type'] in ['via_dangling','track_dangling']:remove.add(x['items'][0]['uuid'])
 if x['type']=='holes_co_located':remove.add(x['items'][1]['uuid'])
 if x['type']=='silk_edge_clearance':fab.add(x['items'][1]['uuid'])
for t in tracks:
 if t.m_Uuid.AsString() in remove:b.Remove(t)
for fp in footprints:
 for g in fp.GraphicalItems():
  if g.m_Uuid.AsString() in fab:g.SetLayer(p.F_Fab)
b.BuildConnectivity()
filler=p.ZONE_FILLER(b);filler.Fill(b.Zones())
p.SaveBoard(str(f),b)
print('Saved filled copper; removed',len(remove),'unused stubs/vias or duplicate vias; moved',len(fab),'off-board silk graphics to fabrication layer.')
