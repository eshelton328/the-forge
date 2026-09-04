#!/usr/bin/env python3
"""Route remaining prototype connections with a conservative three-layer grid.
Critical switching and USB traces are supplied by generate_pcb.py. In1.Cu is
reserved entirely for GND. KiCad DRC is mandatory after this geometric pass.
Requires numpy and /tmp/esp32_grid_search.dylib compiled from grid_search.cpp.
"""
import pcbnew as p
import numpy as np
from pathlib import Path
import ctypes as ct
import math, json, time
D=Path(__file__).resolve().parents[1];pcb=D/'esp32s3-devkit-5v.kicad_pcb';b=p.LoadBoard(str(pcb))
step=.05;ox,oy=100.,70.;nx,ny=1481,1501;layers=[p.F_Cu,p.In2_Cu,p.B_Cu];area=nx*ny
lib=ct.CDLL('/tmp/esp32_grid_search.dylib');fn=lib.find_path
P8=ct.POINTER(ct.c_uint8);PI=ct.POINTER(ct.c_int)
fn.argtypes=[ct.c_int,ct.c_int,ct.c_int,P8,P8,ct.c_int,ct.c_int,PI,ct.c_int,ct.c_int];fn.restype=ct.c_int
out=np.zeros(200000,dtype=np.int32)
def mm(pt):return p.ToMM(pt.x),p.ToMM(pt.y)
def vec(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
def grid(q):return int(round((q[0]-ox)/step)),int(round((q[1]-oy)/step))
def real(x,y):return round(ox+x*step,5),round(oy+y*step,5)
def nid(q,l=0):x,y=grid(q);return l*area+y*nx+x
def dec(i):return i%nx,(i%area)//nx,i//area
def addtrace(net,points,width=.2,layer=p.F_Cu):
 for a,c in zip(points,points[1:]):
  if a==c:continue
  t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(c));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNetCode(net);b.Add(t)
def addvia(net,pt,size=.55,drill=.25):
 v=p.PCB_VIA(b);v.SetPosition(vec(pt));v.SetWidth(p.FromMM(size));v.SetDrill(p.FromMM(drill));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(net);b.Add(v)
# Conservative bounding rectangles for pads; track/via circles use exact distance.
padobs=[];pads=[]
for f in b.GetFootprints():
 for pd in f.Pads():
  box=pd.GetBoundingBox();rect=[p.ToMM(box.GetX()),p.ToMM(box.GetY()),p.ToMM(box.GetRight()),p.ToMM(box.GetBottom())]
  ls=[j for j,l in enumerate(layers) if pd.IsOnLayer(l)]
  hole=p.ToMM(max(pd.GetDrillSize().x,pd.GetDrillSize().y))
  if ls:padobs.append((pd.GetNetCode(),rect,ls,hole,pd))
  if pd.GetNumber() and pd.GetNetCode() and not pd.GetNetname().startswith('unconnected-'):pads.append(pd)
def paintrect(a,rect,r=0):
 x1,y1=grid((rect[0]-r,rect[1]-r));x2,y2=grid((rect[2]+r,rect[3]+r));x1=max(0,x1);y1=max(0,y1);x2=min(nx-1,x2);y2=min(ny-1,y2)
 if x2>=x1 and y2>=y1:a[y1:y2+1,x1:x2+1]=1

def paintseg(a,start,end,r):
 x1,y1=grid((min(start[0],end[0])-r,min(start[1],end[1])-r));x2,y2=grid((max(start[0],end[0])+r,max(start[1],end[1])+r));x1=max(0,x1);y1=max(0,y1);x2=min(nx-1,x2);y2=min(ny-1,y2)
 if x2<x1 or y2<y1:return
 xx=ox+np.arange(x1,x2+1)*step; yy=oy+np.arange(y1,y2+1)*step;X=xx[None,:]-start[0];Y=yy[:,None]-start[1];dx=end[0]-start[0];dy=end[1]-start[1];den=dx*dx+dy*dy
 t=np.clip((X*dx+Y*dy)/den,0,1) if den else 0
 mask=(X-dx*t)**2+(Y-dy*t)**2<=r*r
 a[y1:y2+1,x1:x2+1]|=mask.astype(np.uint8)

def obstacles(net,width,vd=.55):
 blocked=np.zeros((3,ny,nx),np.uint8);vb=np.zeros((ny,nx),np.uint8);clr=.155
 for a in [*blocked,vb]:
  paintrect(a,[ox,oy,174,70.65]);paintrect(a,[ox,144.35,174,145]);paintrect(a,[ox,oy,100.65,145]);paintrect(a,[173.35,oy,174,145])
 # All module antenna keepout is outside board, but preserve it if origin changes.
 for pn,rect,ls,hole,pd in padobs:
  if pn!=net:
   for l in ls:paintrect(blocked[l],rect,clr+width/2)
  # No new via-in-pad (thermal vias already exist in the critical layout).
  paintrect(vb,rect,clr+vd/2)
  if hole:
   # Hole clearance applies on internal layers even if copper not present.
   cp=mm(pd.GetPosition());r=hole/2+.27+width/2
   for l in range(3):
    if pn!=net:paintseg(blocked[l],cp,cp,r)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   pt=mm(t.GetPosition());rr=p.ToMM(t.GetWidth(p.F_Cu))/2
   if t.GetNetCode()!=net:
    for a in blocked:paintseg(a,pt,pt,rr+clr+width/2)
   paintseg(vb,pt,pt,rr+vd/2+.21)
  else:
   if t.GetNetCode()==net:continue
   if t.GetLayer() not in layers:continue
   l=layers.index(t.GetLayer());a,c=mm(t.GetStart()),mm(t.GetEnd());rr=p.ToMM(t.GetWidth())/2
   paintseg(blocked[l],a,c,rr+clr+width/2);paintseg(vb,a,c,rr+clr+vd/2)
 vo=1-vb
 # Existing same-net plated vias are legal layer transitions, not obstacles.
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) and t.GetNetCode()==net:
   x,y=grid(mm(t.GetPosition()))
   if 0<=x<nx and 0<=y<ny and not any(blocked[l,y,x] for l in range(3)):vo[y,x]=1
 return blocked,vo

def pathfind(a,c,blocked,vo,l1=0,l2=0):
 start=nid(a,l1);goal=nid(c,l2)
 if not(0<=start<3*area and 0<=goal<3*area):return None
 # Same-net copper was excluded, so blocked terminals indicate insufficient clearance.
 if blocked.reshape(-1)[start] or blocked.reshape(-1)[goal]:return None
 n=fn(nx,ny,3,blocked.ctypes.data_as(P8),vo.ctypes.data_as(P8),start,goal,out.ctypes.data_as(PI),len(out),8000000)
 return [dec(int(i)) for i in out[:n]] if n>0 else None

def emit(net,path,a,c,width,vd=.55,drill=.25):
 # Compress collinear steps. Keep a point at each layer transition.
 pts=[]
 for i,q in enumerate(path):
  if i==0 or i==len(path)-1:pts.append(q);continue
  before=tuple(q[j]-path[i-1][j] for j in range(3));after=tuple(path[i+1][j]-q[j] for j in range(3))
  if before!=after:pts.append(q)
 addtrace(net,[a,real(*pts[0][:2])],width,layers[pts[0][2]])
 for q,r in zip(pts,pts[1:]):
  pa,pc=real(*q[:2]),real(*r[:2])
  if q[2]!=r[2]:
   exists=any(isinstance(t,p.PCB_VIA) and t.GetNetCode()==net and grid(mm(t.GetPosition()))==q[:2] for t in b.GetTracks())
   if not exists:addvia(net,pa,vd,drill)
  else:addtrace(net,[pa,pc],width,layers[q[2]])
 addtrace(net,[real(*pts[-1][:2]),c],width,layers[pts[-1][2]])

# Every local decoupler gets its own short path to a GND via before signals.
gnd=b.GetNetcodeFromNetname('GND');ground_fail=[]
for pd in pads:
 ref=pd.GetParentFootprint().GetReference()
 if pd.GetNetCode()!=gnd or pd.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
 if ref in ['U1','U2','U3']:continue
 a=mm(pd.GetPosition());blocked,vo=obstacles(gnd,.2)
 ax,ay=grid(a);candidates=[]
 for dy in range(-26,27):
  for dx in range(-26,27):
   x,y=ax+dx,ay+dy
   if 0<=x<nx and 0<=y<ny and .5/step<=math.hypot(dx,dy)<=1.3/step and vo[y,x] and not blocked[0,y,x]:candidates.append((dx*dx+dy*dy,x,y))
 for _,x,y in sorted(candidates)[:24]:
  dest=real(x,y);path=pathfind(a,dest,blocked,vo)
  if path:
   emit(gnd,path,a,dest,.2);addvia(gnd,dest);break
 else:ground_fail.append(ref+'.'+pd.GetNumber())
print('Local GND vias complete; deferred to plane:',ground_fail,flush=True)
# Initial copper groups allow manual power/USB routes to stay intact.
b.BuildConnectivity();cn=b.GetConnectivity()
by_net={}
for pd in pads:
 if pd.GetNetCode()!=gnd:by_net.setdefault(pd.GetNetCode(),[]).append(pd)
def groups_for(pp):
 remaining={pd.m_Uuid.AsString():pd for pd in pp};groups=[]
 while remaining:
  key,pd=next(iter(remaining.items()));todo=[pd];seen=set();group=[]
  while todo:
   item=todo.pop();key=item.m_Uuid.AsString()
   if key in seen:continue
   seen.add(key)
   if key in remaining:group.append(remaining.pop(key))
   for connected in cn.GetConnectedItems(item):
    if connected.GetNetCode()==pd.GetNetCode() and connected.m_Uuid.AsString() not in seen:todo.append(connected)
  groups.append(group)
 return groups
ng={n:groups_for(pp) for n,pp in by_net.items()}
power={'/VBAT','/PFET','/3v3','/5v','/OLED_3V3'}
def order(n):
 name=b.FindNet(n).GetNetname()
 return (0 if name in power else 1,-sum(len(g) for g in ng[n]))
failed=[];done=0
for net in sorted(ng,key=order):
 groups=ng[net];name=b.FindNet(net).GetNetname()
 if len(groups)<2:continue
 width=.6 if name in power else .15;vd=.8 if name in power else .55;drill=.4 if name in power else .25
 groups.sort(key=len,reverse=True);tree=groups.pop(0);blocked,vo=obstacles(net,width,vd)
 while groups:
  choices=[]
  for gi,group in enumerate(groups):
   for aa in tree:
    if aa.GetParentFootprint().GetReference() in ['U1','U2'] and name in power:continue
    for cc in group:
     if cc.GetParentFootprint().GetReference() in ['U1','U2'] and name in power and len(group)>1:continue
     a,c=mm(aa.GetPosition()),mm(cc.GetPosition());dist=(a[0]-c[0])**2+(a[1]-c[1])**2
     choices.append((dist,gi,a,c))
  found=False
  for _,gi,a,c in sorted(choices)[:30]:
   path=pathfind(a,c,blocked,vo)
   if path:
    emit(net,path,a,c,width,vd,drill);tree.extend(groups.pop(gi));done+=1;found=True;break
  if not found:
   failed.append({'net':name,'groups':[[x.GetParentFootprint().GetReference()+'.'+x.GetNumber() for x in g] for g in groups]});break
  # Same-net additions do not change track clearance, but new holes block more vias.
  blocked,vo=obstacles(net,width,vd)
 p.SaveBoard(str(pcb),b)
 print(name,'remaining',len(groups),'routes',done,flush=True)
b.BuildConnectivity();p.SaveBoard(str(pcb),b)
report={'routed_connections':done,'ground_deferred':ground_fail,'unrouted_groups':failed,'tracks_and_vias':len(b.GetTracks())}
(D/'review/routing-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
