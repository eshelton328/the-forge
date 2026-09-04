#!/usr/bin/env python3
"""Generate the review placement and hand-routed critical power cells.
Run with KiCad's Python. Input schematic netlist must be exported first.
The original PCB is preserved separately; this generator creates a new PCB.
"""
from pathlib import Path
import pcbnew as p
import xml.etree.ElementTree as E
import json, math
D=Path(__file__).resolve().parents[1]
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
ROOT=D.parents[1]
xm=E.parse(D/'review/netlist.xml').getroot()
b=p.BOARD();b.SetCopperLayerCount(4)
components={c.attrib['ref']:c for c in xm.find('components')}
nets={}; padnets={}
for n in xm.find('nets'):
 ni=p.NETINFO_ITEM(b,n.attrib['name']);b.Add(ni);nets[n.attrib['name']]=ni
 for x in n:padnets[x.attrib['ref'],x.attrib['pin']]=ni
fps={}
for ref,c in components.items():
 lib,name=c.findtext('footprint').split(':',1)
 path=D/'footprints/Board.pretty' if lib=='Board' else ROOT/'libs/footprints'/f'{lib}.pretty' if lib in ['TPS63070','RF_Module','Switches'] else LIB/f'{lib}.pretty'
 f=p.FootprintLoad(str(path),name)
 if f is None:raise RuntimeError((ref,path,name))
 f.SetReference(ref);f.SetValue(c.findtext('value'));f.SetFPID(p.LIB_ID(lib,name))
 for field in c.findall('fields/field'):
  if field.attrib['name']!='Footprint':f.SetField(field.attrib['name'],field.text or '')
 kp=p.KIID_PATH()
 for u in (c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps')).strip('/').split('/'):
  kp.push_back(p.KIID(u))
 f.SetPath(kp);f.SetSheetname('/');f.SetSheetfile(D.name+'.kicad_sch')
 f.SetDNP(ref=='R11')
 b.Add(f);fps[ref]=f
 for pd in f.Pads():
  if (ref,pd.GetNumber()) in padnets:pd.SetNet(padnets[ref,pd.GetNumber()])
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for field in f.GetFields():
  if field.GetName() not in ['Reference','Value']:field.SetVisible(False)
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def pos(ref,x,y,angle=0):
 f=fps[ref];f.SetPosition(v(x,y));f.SetOrientationDegrees(angle)
 f.Reference().SetPosition(v(x,y+3.0));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetTextSize(v(1,1));f.Reference().SetTextThickness(p.FromMM(.15))
def xy(pt):return (p.ToMM(pt.x),p.ToMM(pt.y))
def pads(ref,num):return [pd for pd in fps[ref].Pads() if pd.GetNumber()==str(num)]
def pt(ref,num):return xy(pads(ref,num)[0].GetPosition())
def track(net,points,width=.2,layer=p.F_Cu):
 for a,c in zip(points,points[1:]):
  if a==c:continue
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
def link(a,an,c,cn,width=.2,via_points=(),layer=p.F_Cu):
 track(pads(a,an)[0].GetNetname(),[pt(a,an),*via_points,pt(c,cn)],width,layer)
def via(net,x,y,size=.55,drill=.25):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(size));t.SetDrill(p.FromMM(drill));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets[net]);b.Add(t)
# Module antenna overhangs north edge: embedded all-copper keepout ends y=69.75.
pos('U3',133,76.5)
pos('J2',102.4,88,-90);pos('U4',112.3,88,0)
pos('R15',108,81.7,0);pos('R14',109,84,0);pos('C20',113,83.5,0)
pos('R34',121,86.5,180);pos('R35',121,87.75,180)
pos('C17',119,73,0);pos('C18',122,71.8,0);pos('C19',119,75.5,0);pos('R13',122,75.5,0)
pos('SW2',112,74,0);pos('R12',145,88,0);pos('SW3',151,88,0)
pos('D1',118,92,0);pos('R11',114.5,92,0)
# Two identical converter cells; input left, output right, inductor north.
for ix,(u,base,x,y) in enumerate([('U1',0,113,102),('U2',8,136,102)]):
 pos(u,x,y);pos('L'+str(ix+1),x,y-5.1)
 for c,dx,dy,angle in [(1,-6.5,-6.5,90),(2,-6.5,-2.5,90),(3,-3.8,-2.6,0),(4,.3,2,-90),(5,3.8,-2.6,180),(6,6.5,-3,90),(7,9.7,-3,90),(8,12.9,-3,90)]:
  pos('C'+str(base+c),x+dx,y+dy,angle)
 rbase=0 if ix==0 else 4
 pos('R'+str(3+rbase),x-3.8,y+.7,0)
 pos('R'+str(4+rbase),x+3.3,y+.1,180)
 pos('R'+str(5+rbase),x+3.3,y+1.5,0)
 pos('R'+str(6+rbase),x-.9,y+2.8,90)
pos('R19',132.3,105,90)
# Protected battery input; slide switch only carries enable current.
pos('J1',119,112,0);pos('Q1',112,108,0);pos('R1',109,109,90)
pos('SW1',102.5,105,-90);pos('R31',107,106.5,0);pos('R32',109,106.5,0)
# RTC and display branch, separated from both inductors.
pos('U5',154,78,0);pos('R16',154,83.5,90);pos('R17',156,83.5,90);pos('R18',150.3,79,90)
pos('C29',158,78.6,90);pos('R33',158,81,0);pos('C21',150.5,73,90)
pos('J4',161,86,0);pos('Q2',151,94,0);pos('Q3',152,101.5,0)
pos('R21',154,95,90);pos('R22',148,94,90);pos('R23',155,102.5,0)
pos('U7',157,97.5,0);pos('C30',157,95,0);pos('R36',155.5,92,90)
pos('R37',161,98,90);pos('R38',161,100,90);pos('C31',157,101,0)
# Amplifier beside the speaker connector, with a local exposed-pad ground via.
pos('U6',153,106,0);pos('C28',153.5,109.2,0);pos('C27',152,111.5,0);pos('C26',153,115,0)
pos('J3',160,106.5,-90);pos('U8',146.5,108,0);pos('C32',143,108,90);pos('C33',149.5,105.5,0)
pos('R20',150,108,90);pos('R39',146.5,111,0)
# Presence detector near USB; filtered ADC node directly beside GPIO2.
pos('Q4',116,79.5);pos('Q5',120,80)
for ref,x,y,a in [('R40',113,79,90),('R41',115,82,0),('R42',117.5,77,90),('R43',117.5,82.5,0),('R44',121,83,0)]:pos(ref,x,y,a)
pos('Q6',125.5,94);pos('Q7',143,93.5)
for ref,x,y,a in [('R45',123,94,90),('R46',146,93.5,90),('R47',143,96,0),('R48',145,72.5,90),('R49',145,75,90),('C34',145,77,90)]:pos(ref,x,y,a)
# User controls along south edge: VOL-, MODE, VOL+, BATTERY (GPIO4/5/6/10).
for j,(sw,r,c,x) in enumerate([('SW4','R24','C22',109),('SW5','R25','C23',124),('SW6','R26','C24',139),('SW7','R27','C25',154)]):
 pos(sw,x,121);pos(r,x,117,0);pos(c,x+2,117,0)
pos('D2',134,112,0);pos('R28',132,115,90);pos('R29',134,115,90);pos('R30',136,115,90)
assert set(fps)==set(components)
# Rectangular 64 x 56 mm prototype, antenna projects beyond north edge.
for a,c in [((100,70),(164,70)),((164,70),(164,126)),((164,126),(100,126)),((100,126),(100,70))]:
 s=p.PCB_SHAPE(b);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(v(*a));s.SetEnd(v(*c));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
# Board-only mechanical footprints; not electrical netlist components.
for i,(x,y) in enumerate([(104,74),(160,74),(104,113),(160,115)],1):
 f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_3.2mm_M3');f.SetReference('H'+str(i));f.SetValue('M3');f.SetPosition(v(x,y));f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES);b.Add(f);f.Reference().SetVisible(False);f.Value().SetVisible(False)
# Unpopulated probe pads on the underside; no extra assembly operation.
for i,(name,x,y) in enumerate([('GND',109,91),('/PFET',119,91),('/3v3',120,106),('/5v',141,106),('/GPIO15',122,108),('/GPIO13',140,110),('/EN_3V3',120,92.8),('/GPIO18',139,92)],1):
 f=p.FootprintLoad(str(LIB/'TestPoint.pretty'),'TestPoint_Pad_D1.0mm')
 b.Add(f);f.SetReference('TP'+str(i));f.SetValue(name.strip('/'));f.SetPosition(v(x,y));f.Flip(v(x,y),False)
 f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
 for pd in f.Pads():pd.SetNet(nets[name])
 f.Reference().SetVisible(False);f.Value().SetVisible(True);f.Value().SetPosition(v(x,y+(1.6 if i in [5,7] else -1.6)));f.Value().SetTextSize(v(1,1));f.Value().SetTextThickness(p.FromMM(.15));f.Value().SetLayer(p.B_SilkS)
# Critical converter conductors: no autorouted switching-node loops.
for ix,u in enumerate(['U1','U2']):
 x,y=xy(fps[u].GetPosition());base=ix*8;L='L'+str(ix+1);C=lambda n:'C'+str(base+n)
 # Join all split lands, then expand after leaving the fine-pitch package.
 for pin,sgn,lp in [('11',-1,1),('9',1,2)]:
  pp=pads(u,pin);n=pp[0].GetNetname();anchor=(x+sgn*.5,y-3.15)
  for pd in pp:track(n,[xy(pd.GetPosition()),anchor],.22)
  track(n,[anchor,(x+sgn*1.185,y-3.835)],.22)
  track(n,[(x+sgn*1.185,y-3.835),pt(L,lp)],.55)
 # Power pad pair to close local input/output ceramic (positive pad points down).
 for pin,cap,sgn in [('12',C(3),-1),('7',C(5),1)]:
  n=pads(u,pin)[0].GetNetname();a=pt(u,pin);neighbor=pt(u,int(pin)+1)
  track(n,[a,neighbor],.4)
  track(n,[a,(pt(cap,1)[0],y-1.4),pt(cap,1)],.4)
 # Ground pins to a short, quiet ground tie beneath the package.
 for pin,dy in [('4',.9),('15',.4),('6',.4)]:
  a=pt(u,pin)
  if pin=='4':dest=(x+1,y+.9);track('GND',[a,dest],.2);via('GND',*dest,size=.5,drill=.2)
  else:
   sgn=-1 if pin=='15' else 1;dest=(x-2.2,y-.15) if pin=='15' else (x+2.1,y-.7);track('GND',[a,dest],.2);via('GND',*dest,size=.5,drill=.2)
 # Center ground paddle, longitudinal path between switching nodes.
 for pd in pads(u,'10'):track('GND',[xy(pd.GetPosition()),(x,y-3.8)],.18)
 via('GND',x,y-3.8,.5,.2)
 track('GND',[(x,y-3.8),(x,y-5.1)],.4);via('GND',x,y-5.1,.5,.2)
 # Local capacitor returns point inward into the power-ground pour.
 for cap in [C(3),C(5)]:
  a=pt(cap,2);dest=(a[0],a[1]-.85)
  track('GND',[a,dest],.4);via('GND',*dest,size=.6,drill=.3)
 # VAUX, feedback and PG stay on the quiet side of the package.
 link(u,3,C(4),1,.18)
 rb=ix*4
 link(u,5,'R'+str(4+rb),2,.18)
 link('R'+str(4+rb),2,'R'+str(5+rb),1,.18)
 # Feedback lower resistor and VAUX return share the quiet AGND-side copper.
 a=pt('R'+str(5+rb),2);groundcap=pt(C(4),2)
 track('GND',[a,(a[0]-(groundcap[1]-a[1]),groundcap[1]),groundcap],.2)
 track('GND',[(x+1,y+.9),(x+1,groundcap[1]),groundcap],.2)
 link(u,2,'R'+str(6+rb),2,.18)
 link(u,1,'R'+str(3+rb),2,.18)
 # Reserve an escape corridor for EN between the local input ceramic and logic ground.
 ennet=pads(u,14)[0].GetNetname()
 track(ennet,[pt(u,14),(x-2.26,y-.9),(x-2.96,y-.2),(x-4.3,y-.2)],.15)
 via(ennet,x-4.3,y-.2,.55,.25)
# Reserve module pin escapes before long routes can enclose adjacent pads.
for pin in [4,5,6,7,8,11,12]:
 a=pt('U3',pin);net=pads('U3',pin)[0].GetNetname();dest=(126,a[1])
 track(net,[a,dest],.15);via(net,*dest,.55,.25)
for pin in [27,31,32,33,34,38,39]:
 a=pt('U3',pin);net=pads('U3',pin)[0].GetNetname();dest=(140,a[1])
 track(net,[a,dest],.15);via(net,*dest,.55,.25)
for pin in [20,21,22,24,25]:
 a=pt('U3',pin);net=pads('U3',pin)[0].GetNetname();dest=(a[0],91)
 track(net,[a,dest],.15);via(net,*dest,.55,.25)
# Audio ground via in the exposed pad; extra vias alongside the package.
via('GND',153,106,.5,.2)
link('U6',7,'U6',8,.2)
link('U6',7,'C28',1,.2)
track('/AMP_SD',[pt('U6',4),(150.9,106.75),(150.65,106.5)],.15)
via('/AMP_SD',150.65,106.5,.5,.2)
track('/GPIO14',[pt('U6',1),(150.9,105.25),(150.9,103.65)],.15)
via('/GPIO14',150.9,103.65,.5,.2)
for pin in [14,16]:
 a=pt('U6',pin);net=pads('U6',pin)[0].GetNetname();dest=(a[0],103.6)
 track(net,[a,dest],.15);via(net,*dest,size=.5,drill=.2)
link('U8',6,'C33',1,.2)
link('U8',1,'C32',1,.2)
link('U7',8,'C30',1,.15,via_points=((158.4,94),(156.52,94)))
# Keep BTL outputs adjacent and entirely on F.Cu; 0.6 mm after package escape.
for pin,jn,yy in [(10,1,105.5),(9,2,107.5)]:
 net=pads('U6',pin)[0].GetNetname();a=pt('U6',pin);escape=(155.05,a[1])
 track(net,[a,escape,(155.8,yy)],.2)
 track(net,[(155.8,yy),pt('J3',jn)],.6)
# USB crossing at reversible connector is resolved with one pair behind the pad row.
track(pads('J2','A6')[0].GetNetname(),[pt('J2','A6'),(105.35,87.75),(105.35,88.75),pt('J2','B6')],.15)
track(pads('J2','A7')[0].GetNetname(),[pt('J2','B7'),(107.5,87.25),(107.5,88.25),pt('J2','A7')],.15)
track(pads('J2','A7')[0].GetNetname(),[(107.5,88.25),(108.7,87.05),pt('U4',1)],.15)
track(pads('J2','A6')[0].GetNetname(),[pt('J2','B6'),(107.9,88.75),(108.1,88.95),pt('U4',3)],.15)
track('/D-',[pt('U4',6),(114.5,87.05),(115,87.55),(118.5,87.55),(119.55,86.5),pt('R34',2)],.15)
track('/D+',[pt('U4',4),(114.65,88.95),(115.75,87.85),(119,87.85),(119.1,87.75),pt('R35',2)],.15)
link('R34',1,'U3',13,.15);link('R35',1,'U3',14,.15)
# Fine-pitch and switch terminal escapes precede the general router.
for ref,pin,dest in [('U7',2,(154.3,97.25)),('U7',6,(159.3,97.75)),('SW1',1,(106,103.25))]:
 net=pads(ref,pin)[0].GetNetname();track(net,[pt(ref,pin),dest],.15);via(net,*dest,size=.5,drill=.2)
# Module thermal vias are already part of its library footprint.
def silk(text,x,y,size=1):
 t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS);b.Add(t)
for text,x,y in [('USB',104,94),('BAT +  -',117,116),('3V3',120,106.5),('5V',140,106.5),('SPK',158.5,112),('OLED',161,83),('RESET',109,78),('BOOT',151,84.4),('VOL-',109,125),('MODE',124,125),('VOL+',139,125),('BAT',154,125)]:silk(text,x,y)
for g in list(fps['D2'].GraphicalItems()):
 if isinstance(g,p.PCB_TEXT) and g.GetLayer()==p.F_SilkS:g.SetLayer(p.F_Fab)
# Uninterrupted primary reference plane; other pours are filled after routing.
for layer in [p.In1_Cu,p.In2_Cu,p.F_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(nets['GND']);z.SetLocalClearance(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.15));z.SetIslandRemovalMode(0)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(100.5,70.5),(163.5,70.5),(163.5,125.5),(100.5,125.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
# Restore the audited project-local model assignments after regenerating placement.
modelmap=json.loads((D/'3dmodels/model-map.json').read_text()) if (D/'3dmodels/model-map.json').is_file() else {}
for f in fps.values():
 entry=modelmap.get(f.GetFPIDAsString())
 if entry:
  f.Models().clear();m=p.FP_3DMODEL();m.m_Filename=entry['path'];m.m_Show=True
  m.m_Offset.x,m.m_Offset.y,m.m_Offset.z=entry['offset']
  m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z=entry['rotation']
  m.m_Scale.x=m.m_Scale.y=m.m_Scale.z=1;f.Add3DModel(m)
b.BuildConnectivity();p.SaveBoard(str(D/'esp32s3-devkit-5v.kicad_pcb'),b)
# Make constraints explicit rather than accepting zero-width/zero-clearance defaults.
pro=D/'esp32s3-devkit-5v.kicad_pro';cfg=json.loads(pro.read_text());rules=cfg['board']['design_settings']['rules']
rules.update(min_clearance=.15,min_track_width=.15,min_via_diameter=.5,min_through_hole_diameter=.2,min_hole_clearance=.25,min_silk_clearance=.15,min_text_height=1,min_text_thickness=.15)
for c in cfg['net_settings']['classes']:
 if c['name']=='Default':c.update(clearance=.15,track_width=.2,via_diameter=.55,via_drill=.25,diff_pair_width=.2,diff_pair_gap=.15)
default=next(c for c in cfg['net_settings']['classes'] if c['name']=='Default')
cfg['net_settings']['classes']=[default,dict(default,name='Power',priority=1,track_width=.6,via_diameter=.8,via_drill=.4),dict(default,name='Speaker',priority=0,track_width=.6)]
cfg['net_settings']['netclass_patterns']=[{'netclass':'Power','pattern':n} for n in ['/VBAT','/PFET','/3v3','/5v','/OLED_3V3']]+[{'netclass':'Speaker','pattern':'/speaker *'}]
pro.write_text(json.dumps(cfg,indent=2)+'\n')
print('Generated',len(fps),'electrical footprints,',len(b.GetTracks()),'critical copper items')
