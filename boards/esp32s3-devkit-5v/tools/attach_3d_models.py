#!/usr/bin/env python3
"""Attach project-local STEP models without changing electrical geometry.
Run using KiCad Python. Models and transforms are deliberately separate from
footprint pad definitions. Check the generated audit and rendered alignment.
"""
from pathlib import Path
import json,csv,hashlib
import pcbnew as p
D=Path(__file__).resolve().parents[1];fn=D/'esp32s3-devkit-5v.kicad_pcb';b=p.LoadBoard(str(fn))
# Alternate file names, KiCad XYZ offset and clockwise rotation (degrees).
extra={
 'TPS63070:TPS63070':('TPS63070RNM.step',[0,1.125,0],[-90,0,-90],'Existing repository part model'),
 'TPS63070:IND_XFL4020-152MEC':('XFL4020-152MEC.step',[0,0,0],[-90,0,0],'Existing repository part model'),
 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12':('HRO_TYPE-C-31-M-12.step',[-4.47,-3.65,0],[-90,0,0],'Existing repository part model'),
 'Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02':('SW_SPDT_Shouhan_MSK12C02.step',[0,0,0],[0,0,180],'Footprint-specific model; schematic selects MSK12C02'),
 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A':('TS-1187A-B-A-B.step',[0,0,0],[0,0,0],'Community model; actuator variant provisional'),
 'Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical':('JST_B2B-PH-SM4-TB_simplified.step',[0,0,0],[0,0,0],'Generated simplified drawing-based model'),
 'Package_SON:MicroCrystal_C7_SON-8_1.5x3.2mm_P0.9mm':('RV-3028-C7_simplified.step',[0,0,0],[0,0,0],'Generated simplified drawing-based model'),
 'Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm':('MAX98357A_TQFN16_simplified.step',[0,0,0],[0,0,0],'Generated simplified package model')}
extra['Board:USB_C_HRO_Overhang']=extra['Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12']
extra['Board:JST_PH_Speaker_Overhang']=extra['Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical']
extra['Board:ESP32-S3-WROOM-1_Overhang']=('ESP32-S3-WROOM-1.step',[0,0,0],[0,0,0],'KiCad module STEP; antenna overhang footprint variant')
rows=[];mapping={}
for f in b.GetFootprints():
 if f.GetReference().startswith(('H','TP')):continue
 fp=f.GetFPIDAsString();old=list(f.Models())
 if fp in extra:name,off,rot,kind=extra[fp]
 else:
  name=fp.split(':')[-1]+'.step';kind='KiCad library package model'
  off=[old[0].m_Offset.x,old[0].m_Offset.y,old[0].m_Offset.z] if old else [0,0,0]
  rot=[old[0].m_Rotation.x,old[0].m_Rotation.y,old[0].m_Rotation.z] if old else [0,0,0]
 local=D/'3dmodels'/name;assert local.is_file(),(f.GetReference(),local)
 assert local.read_bytes().startswith(b'ISO-10303-21;'),local
 f.Models().clear();m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/3dmodels/'+name;m.m_Show=True
 m.m_Offset.x,m.m_Offset.y,m.m_Offset.z=off;m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z=rot
 m.m_Scale.x=m.m_Scale.y=m.m_Scale.z=1;f.Add3DModel(m)
 entry={'path':m.m_Filename,'offset':off,'rotation':rot,'scale':[1,1,1],'classification':kind,'sha256':hashlib.sha256(local.read_bytes()).hexdigest()}
 mapping[fp]=entry;rows.append({'Reference':f.GetReference(),'Model':name,'Resolved':True,'DNP':f.IsDNP(),'Classification':kind})
import xml.etree.ElementTree as E
assert len(rows)==len(E.parse(D/'review/netlist.xml').getroot().find('components')),len(rows)
p.SaveBoard(str(fn),b)
(D/'3dmodels/model-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
with (D/'review/3d-model-audit.csv').open('w',newline='') as out:
 w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(sorted(rows,key=lambda r:r['Reference']))
print('Attached',len(rows),'models across',len(mapping),'unique types; all STEP paths resolve locally.')
