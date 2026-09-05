"""Four-sheet steady-state finite-volume thermal screening using actual PCB copper.

This is a PCB temperature model, not a package/junction or enclosure FEM model.
Copper coverage is homogenized inside each lateral cell. No isothermal edge sink.
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
import shapely
from shapely.geometry import box
from copper import layer_shapes
from shapely.geometry import Polygon
from shapely.ops import unary_union


def thermal_grid(data, pitch):
    xmin,ymin,xmax,ymax=data['bounds']
    nx=int(np.ceil((xmax-xmin)/pitch));ny=int(np.ceil((ymax-ymin)/pitch))
    dx=(xmax-xmin)/nx;dy=(ymax-ymin)/ny
    x=xmin+(np.arange(nx)+.5)*dx;y=ymin+(np.arange(ny)+.5)*dy
    xx,yy=np.meshgrid(x,y)
    cells=shapely.box(xx.ravel()-dx/2,yy.ravel()-dy/2,xx.ravel()+dx/2,yy.ravel()+dy/2)
    copper=layer_shapes(data)
    cover=np.array([shapely.area(shapely.intersection(cells,g))/(dx*dy) for g in copper])
    cover=np.clip(cover,0,1).reshape(4,ny,nx)
    return x,y,cells,cover,dx,dy


def solve_thermal(data, pitch=.5, h=10., sources=None, k_fr4=.3, k_copper=385.):
    if sources is None:
        raise ValueError('An explicit component loss budget is required')
    x,y,cells,cover,dx,dy=thermal_grid(data,pitch)
    nx,ny=len(x),len(y);n=nx*ny;area=dx*dy*1e-6
    # Assumed 1.6 mm total, outer Cu35um, inner Cu17.5um.
    # Copper center spacings .20/1.165/.20 mm; outer surfaces +/-17.5um.
    copper_t=np.array([35,17.5,17.5,35])*1e-6
    separation=np.array([.2,1.165,.2])*1e-3
    dielectric=separation-(copper_t[:-1]+copper_t[1:])/2
    slices=np.array([dielectric[0]/2,(dielectric[0]+dielectric[1])/2,
                     (dielectric[1]+dielectric[2])/2,dielectric[2]/2])
    # The unused portion of nominal copper layers is laminate, not vacuum.
    sheet=k_copper*copper_t[:,None,None]*cover+k_fr4*(slices[:,None,None]+copper_t[:,None,None]*(1-cover))
    ids=np.arange(4*n).reshape(4,ny,nx)
    total_unknowns=4*n+len(sources)
    row=[];col=[];val=[];diag=np.zeros(total_unknowns)
    def add(a,b,g):
        a=np.asarray(a).ravel();b=np.asarray(b).ravel();g=np.broadcast_to(g,a.shape).ravel()
        np.add.at(diag,a,g);np.add.at(diag,b,g)
        row.extend(a);col.extend(b);val.extend(-g)
        row.extend(b);col.extend(a);val.extend(-g)
    harmonic=lambda a,b: 2*a*b/(a+b)
    add(ids[:,:,:-1],ids[:,:,1:],(harmonic(sheet[:,:,:-1],sheet[:,:,1:])*dy/dx).ravel())
    add(ids[:,:-1,:],ids[:,1:,:],(harmonic(sheet[:,:-1,:],sheet[:,1:,:])*dx/dy).ravel())
    via_area=np.zeros((3,ny,nx))
    layer_names=['F.Cu','In1.Cu','In2.Cu','B.Cu']
    for v in data['vias']:
        ix=int((v['xy'][0]-data['bounds'][0])/dx);iy=int((v['xy'][1]-data['bounds'][1])/dy)
        if 0<=ix<nx and 0<=iy<ny:
            # 25um plating, ring area based on finished drill diameter.
            a=np.pi*((v['drill']/2+.025)**2-(v['drill']/2)**2)*1e-6
            for j in range(3):
                if {layer_names[j],layer_names[j+1]}.issubset(v['layers']):
                    via_area[j,iy,ix]+=a
    for j in range(3):
        # Series copper half-thicknesses and FR4 between sheets. Copper vias
        # provide a parallel path. Hole dielectric displaced by via neglected
        # at cell scale; quantify this as a homogenization limitation.
        g=np.full((ny,nx),k_fr4*area/dielectric[j])+k_copper*via_area[j]/separation[j]
        add(ids[j],ids[j+1],g.ravel())
    cooling=np.zeros(total_unknowns)
    cooling[ids[0].ravel()]+=h*area
    cooling[ids[3].ravel()]+=h*area
    # All four board edges insulated: no fictitious metal heatsink.
    q=np.zeros(total_unknowns);weights={}
    for source_index,(ref,source) in enumerate(sources.items()):
        lands=[]
        for item in data['copper']:
            if item['kind']=='pad' and item['layer']=='F.Cu' and item['ref']==ref:
                lands.extend(Polygon(p['outer'],p['holes']) for p in item['polygons'])
        footprint=unary_union(lands)
        overlap=shapely.area(shapely.intersection(cells,footprint))
        if overlap.sum()==0:raise ValueError(f'No thermal source overlap: {ref}')
        weights[ref]=overlap/overlap.sum()
        contact_nodes=np.flatnonzero(overlap>1e-12)
        package_node=4*n+source_index
        # An isothermal package landing node distributes heat into its actual
        # solder lands. 50 W/mK solder / 50um thickness = 1e6 W/m2K.
        # This prevents fictitious heating of empty laminate under a package.
        # Internal die/package resistance is excluded, so this is NOT Tjunction.
        add(contact_nodes,np.full(contact_nodes.shape,package_node),overlap[contact_nodes])
        q[package_node]=source['watts']
    diag+=cooling
    row.extend(np.arange(total_unknowns));col.extend(np.arange(total_unknowns));val.extend(diag)
    matrix=sp.csr_matrix((val,(row,col)),shape=(total_unknowns,total_unknowns))
    rise=spsolve(matrix,q)
    if not np.isfinite(rise).all() or rise.min() < -1e-6:
        raise ValueError('Invalid thermal solution')
    pin=float(q.sum());pout=float(cooling@rise)
    result={'pitch_mm':pitch,'h_w_m2k_each_face':h,'input_w':pin,'heat_out_w':pout,
            'energy_relative_error':abs(pin-pout)/pin if pin else 0,
            'peak_pcb_rise_c':float(rise[:4*n].max()),'min_pcb_rise_c':float(rise[:4*n].min()),
            'source_pcb_rise_c':{r:float(w@rise[:n]) for r,w in weights.items()},
            'unknowns':total_unknowns,'copper_coverage_fraction':cover.mean(axis=(1,2)).tolist()}
    return result, rise[:4*n].reshape(4,ny,nx), (x,y)
