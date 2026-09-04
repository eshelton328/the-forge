#!/usr/bin/env python3
"""Pin-level design checks for faults ordinary ERC cannot detect.
Regenerate review/netlist.xml with kicad-cli before running this script.
"""
from pathlib import Path
import xml.etree.ElementTree as E
D=Path(__file__).resolve().parents[1]
r=E.parse(D/'review/netlist.xml').getroot();pn={};nets={}
for net in r.find('nets'):
 nodes={(x.attrib['ref'],x.attrib['pin']) for x in net};nets[net.attrib['name']]=nodes
 for node in nodes:pn[node]=net.attrib['name']
def same(*nodes):
 values={pn[n] for n in nodes};assert len(values)==1,(nodes,values)
def apart(a,b):assert pn[a]!=pn[b],(a,b,pn[a])
def exact(net,nodes):assert nets[net]==set(nodes),(net,nets[net])
exact('/USB_CC1',[('J2','A5'),('R15','1')]);same(('J2','B5'),('R14','1'))
exact('/USB_VBUS',[('J2','A4'),('J2','A9'),('J2','B4'),('J2','B9'),('U4','5'),('C20','1'),('R40','1')])
for cc in ['A5','B5']:apart(('J2',cc),('J2','A4'))
same(('SW1','2'),('U1','14'),('R32','1'));same(('SW1','3'),('R32','2'),('J1','2'))
same(('SW1','1'),('R31','2'));same(('R31','1'),('Q1','2'),('U1','12'),('U2','12'))
apart(('SW1','2'),('Q1','2'))
exact('/RTC_VBACKUP',[('U5','6'),('R33','1')]);same(('R33','2'),('U5','5'));same(('C29','1'),('U5','7'))
same(('U3','23'),('U8','3'),('R39','1'));same(('U8','4'),('U6','4'),('R20','1'));apart(('U3','23'),('U6','4'))
same(('U8','1'),('U8','5'),('U3','2'));same(('U8','6'),('U6','7'),('U2','7'))
same(('U3','11'),('U2','14'),('R19','1'))
same(('U3','19'),('U7','3'),('U7','7'),('R36','1'))
same(('U7','1'),('U5','3'),('U3','17'));same(('U7','5'),('U5','4'),('U3','12'))
same(('U7','2'),('J4','3'),('R37','2'));same(('U7','6'),('J4','4'),('R38','2'))
apart(('J4','3'),('U5','3'));apart(('J4','4'),('U5','4'))
same(('J4','2'),('Q2','3'),('R37','1'),('R38','1'))
same(('U3','13'),('R34','1'));same(('U4','6'),('R34','2'));apart(('U3','13'),('U4','6'))
same(('U3','14'),('R35','1'));same(('U4','4'),('R35','2'));apart(('U3','14'),('U4','4'))
same(('U6','9'),('J3','2'));same(('U6','10'),('J3','1'));apart(('J3','1'),('J1','2'))
same(('U3','24'),('U6','16'));same(('U3','25'),('U6','14'));same(('U3','22'),('U6','1'))
same(('U3','34'),('R22','2'))
same(('D2','1'),('U3','2'));same(('D2','3'),('R28','1'));same(('D2','4'),('R29','1'));same(('D2','2'),('R30','1'))
for n in r.find('nets'):
 if n.get('name','').startswith('/GPIO'):
  for node in n:
   if node.get('ref')=='U3':assert node.get('pinfunction','').split('_')[0]=='IO'+n.get('name')[5:], (n.get('name'),node.attrib)
same(('SW4','2'),('U3','4'),('R24','2'),('C22','1'))
same(('SW5','2'),('U3','5'),('R25','2'),('C23','1'))
same(('SW6','2'),('U3','6'),('R26','2'),('C24','1'))
same(('SW7','2'),('U3','18'),('R27','2'),('C25','1'))
# Positive VBUS presence, with no direct VBUS-to-GPIO divider or clamp path.
same(('R40','2'),('R41','1'),('Q4','1'))
same(('Q4','3'),('R42','2'),('R43','1'))
same(('R43','2'),('Q5','1'));same(('Q5','3'),('R44','2'),('U3','7'))
same(('R42','1'),('R44','1'),('U3','2'))
same(('Q4','2'),('Q5','2'),('R41','2'),('J1','2'))
apart(('U3','7'),('J2','A4'))
# High-side switched divider: source faces protected battery; ADC is grounded when off.
same(('Q6','2'),('R45','1'),('Q1','2'))
same(('Q6','1'),('R45','2'),('Q7','3'))
same(('Q6','3'),('R48','1'));same(('Q7','1'),('R46','2'),('R47','1'))
same(('R46','1'),('U3','20'))
same(('R48','2'),('R49','1'),('C34','1'),('U3','38'))
same(('Q7','2'),('R47','2'),('R49','2'),('C34','2'),('J1','2'))
for u,res,mcu in [('U1','R6','8'),('U2','R10','21')]:
 same((u,'2'),(res,'2'),('U3',mcu));same((res,'1'),('U3','2'))
components={c.get('ref'):c for c in r.find('components')}
for ref,value in [('R48','33k'),('R49','10k')]:
 assert components[ref].findtext('value')==value
 assert components[ref].find("fields/field[@name='Tolerance']").text=='0.1%'
print('PASS: USB isolation/presence, battery ADC switch, 3.3 V PG pull-ups, standby, RTC, audio/OLED isolation, USB damping, BTL outputs and GPIO mapping.')
