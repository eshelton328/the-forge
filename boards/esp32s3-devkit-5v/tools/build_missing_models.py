#!/usr/bin/env python3
"""Build explicitly simplified mechanical models from published package drawings.
Requires CadQuery. Dimensions are mm. These are visualization models, not
manufacturer-certified tooling/enclosure-clearance models. No PCB copper changes.
"""
from pathlib import Path
import cadquery as cq
D=Path(__file__).resolve().parents[1]/'3dmodels'
D.mkdir(exist_ok=True)
metal=cq.Color(.72,.74,.76);gold=cq.Color(.75,.63,.29);black=cq.Color(.10,.11,.12);ivory=cq.Color(.91,.90,.83)
def box(x,y,z,dx=0,dy=0,dz=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((dx,dy,dz))
def save(a,name):
 a.save(str(D/(name+'.step')))
 print('Generated',name,flush=True)
# Micro Crystal C7: 1.5 x 3.2, 0.8 maximum height, eight 0.4-mm contacts,
# 0.9-mm pitch along the long axis. See RV-3028-C7 datasheet front page.
a=cq.Assembly(name='RV_3028_C7_simplified')
a.add(box(1.5,3.2,.6,dz=.05),name='ceramic',color=black)
a.add(box(1.46,3.16,.15,dz=.65),name='metal_lid',color=gold)
for side in [-1,1]:
 for i,y in enumerate([-1.35,-.45,.45,1.35]):a.add(box(.4,.4,.15,side*.55,y),name=f'contact_{side}_{i}',color=gold)
a.add(cq.Workplane('XY').circle(.10).extrude(.006).translate((-.48,1.26,.8)),name='pin1',color=black)
save(a,'RV-3028-C7_simplified')
# ADI/MAXIM T1633+4: 3 x 3, sixteen perimeter contacts at 0.5 pitch,
# 1.10 x 1.10 nominal exposed pad, drawing 21-0136 variant T1633-4.
# Mold details omitted; 0.8-mm maximum package envelope.
a=cq.Assembly(name='MAX98357A_TQFN16_simplified')
a.add(box(3,3,.73,dz=.07),name='mold',color=black)
a.add(box(1.10,1.10,.10),name='exposed_pad',color=metal)
for side in [-1,1]:
 for i,k in enumerate([-.75,-.25,.25,.75]):
  a.add(box(.4,.25,.15,side*1.3,k),name=f'x_{side}_{i}',color=metal)
  a.add(box(.25,.4,.15,k,side*1.3),name=f'y_{side}_{i}',color=metal)
a.add(cq.Workplane('XY').circle(.14).extrude(.008).translate((-1,1,.80)),name='pin1',color=cq.Color(.36,.37,.38))
save(a,'MAX98357A_TQFN16_simplified')
# JST PH top-entry SMT, 2 circuits: width 7.95, body depth 5, height 6.6.
# Origin follows the KiCad B2B-PH-SM4-TB footprint: housing at CAD y=1.75;
# terminals x=+/-1, mating posts at y=2.5. Internal latch/rib shapes simplified.
a=cq.Assembly(name='JST_B2B_PH_SM4_TB_simplified')
housing=box(7.95,5,6.6,dy=1.75)
housing=housing.cut(box(5.7,3.7,5.7,dy=1.65,dz=1.1))
# Opening/latch recess in the front wall; vertical side ribs remain.
housing=housing.cut(box(2.6,1,2.2,dy=-.45,dz=4.4))
a.add(housing,name='housing',color=ivory)
for i,x in enumerate([-1,1],1):
 a.add(box(.5,.5,4.8,x,2.5,.8),name=f'post_{i}',color=metal)
 a.add(box(.5,5.3,.25,x,-.1),name=f'smt_tail_{i}',color=metal)
for side in [-1,1]:
 a.add(box(1.5,2.9,.22,side*3.4,1.75),name=f'hold_down_foot_{side}',color=metal)
 a.add(box(.25,2.9,2,side*3.75,1.75,.15),name=f'hold_down_side_{side}',color=metal)
save(a,'JST_B2B-PH-SM4-TB_simplified')
