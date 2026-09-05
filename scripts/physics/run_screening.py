#!/usr/bin/env python3
"""Run free-tool screening. A successful run is not physical release approval."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import numpy as np
from copper import copper_shapes, pad
from extract_loops import extract, LOOPS
from circuit_tests import run_pdn, run_ringing, run_conducted
from thermal import solve_thermal


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def json_write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def heat_sources(config,efficiency,stress=False):
    t=config['thermal'];fraction=t['converter_ic_loss_fraction']
    losses=[3.3*t['loads_a']['3v3']*(1/efficiency-1),5*t['loads_a']['5v']*(1/efficiency-1)]
    sources={}
    for i,loss in enumerate(losses,1):
        sources[f'U{i}']={'watts':loss*fraction}
        sources[f'L{i}']={'watts':loss*(1-fraction)}
    key='stress' if stress else 'nominal'
    sources['U3']={'watts':t[key+'_esp32_heat_w']}
    sources['U6']={'watts':t[key+'_amp_heat_w']}
    return sources


def electrostatic_screen(data,config):
    """Parallel-plate overlap only: no FasterCap/full capacitance matrix claim."""
    shapes=copper_shapes(data);ground=shapes['In1.Cu','GND'];eps0=8.8541878128e-12
    er=config['stackup']['fr4_relative_permittivity'];rows=[]
    for ic in ['U1','U2']:
        for pin in ['11','9']:
            net=pad(data,ic,pin)['net'];copper=shapes['F.Cu',net]
            area=copper.intersection(ground).area
            rows.append({'ic':ic,'pin':pin,'net':net,'copper_area_mm2':copper.area,'over_ground_mm2':area,
                         'dielectric_gap_mm':.2-(.035+.0175)/2,
                         'parallel_plate_pf_at_0p2mm':eps0*er*area*1e-6/((.2-(.035+.0175)/2)*1e-3)*1e12,
                         'parallel_plate_pf_spacing_range':[eps0*er*area*1e-6/((h-(.035+.0175)/2)*1e-3)*1e12 for h in [.3,.1]],
                         'scope':'Area/dielectric estimate; fringing, package, cables and other conductor coupling omitted'})
    return rows


def wire_calibration(executable,out):
    out.mkdir(parents=True,exist_ok=True)
    (out/'wire.inp').write_text('* DC wire calibration\n.units mm\n.default sigma=58000 nhinc=3 nwinc=3\nn1 x=0 y=0 z=0\nn2 x=10 y=0 z=0\ne1 n1 n2 w=1 h=.035\n.external n1 n2\n.freq fmin=1 fmax=1 ndec=1\n.end\n')
    p=subprocess.run([str(executable),'wire.inp'],cwd=out,capture_output=True,text=True,timeout=60)
    (out/'solver.log').write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError('Wire calibration failed')
    import re
    r=float(re.search(r'1 x 1\s+([\deE+.-]+)',(out/'Zc.mat').read_text()).group(1))
    expected=.01/(58e6*.001*.000035)
    error=abs(r-expected)/expected
    if error>.01:raise ValueError('FastHenry DC calibration differs by >1%')
    return {'measured_ohm':r,'analytical_ohm':expected,'relative_error':error,'passed':True}


def run_thermal_cases(data,cfg,profile,folder):
    folder.mkdir(exist_ok=True,parents=True)
    cases=[('nominal_1mm',1.,10.,.85,False),('nominal_0p5mm',.5,10.,.85,False)]
    if profile=='full':
        cases += [('nominal_0p25mm',.25,10.,.85,False),('stress_weak_cooling',.5,5.,.85,True),
                  ('nominal_better_cooling',.5,20.,.85,False),('nominal_95pct',.5,10.,.95,False),
                  ('U1_only',.5,10.,.85,False),('U2_only',.5,10.,.85,False)]
    results={}
    for label,pitch,h,eff,stress in cases:
        sources=heat_sources(cfg,eff,stress)
        if label.endswith('_only'):
            ic=label[:2];ind='L'+ic[-1];sources={r:s for r,s in sources.items() if r in [ic,ind]}
        inputs={'pcb_sha256':data['pcb_sha256'],'sources':sources,'pitch':pitch,'h':h,
                'k_fr4':cfg['stackup']['fr4_thermal_conductivity_w_mk'],
                'k_copper':cfg['stackup']['copper_thermal_conductivity_w_mk'],
                'ambient_c':cfg['thermal']['ambient_c'],
                'source_hashes':{p.name:digest(p) for p in [Path(__file__).parent/'thermal.py',Path(__file__).parent/'copper.py']}}
        path=folder/(label+'.json')
        if path.exists() and json.loads(path.read_text()).get('inputs')==inputs and (folder/(label+'.npz')).exists():
            result=json.loads(path.read_text())
        else:
            result,grid,xy=solve_thermal(data,pitch,h,sources,k_fr4=inputs['k_fr4'],k_copper=inputs['k_copper'])
            result['losses_w']={r:s['watts'] for r,s in sources.items()}
            result['ambient_c']=cfg['thermal']['ambient_c']
            result['peak_pcb_c_at_50c']=result['peak_pcb_rise_c']+50
            result['inputs']=inputs
            np.savez_compressed(folder/(label+'.npz'),rise_c=grid,x=xy[0],y=xy[1])
            json_write(path,result)
        results[label]=result
        print('Thermal case',label,round(result['peak_pcb_rise_c'],2),flush=True)
    return results


def run(args):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(args.config.read_text())
    expected_stackup={'total_mm':1.6,'copper_um':[35,17.5,17.5,35],
        'copper_center_spacing_mm':[.2,1.165,.2],'via_plating_um':25,
        'copper_conductivity_s_m':58000000}
    for key,value in expected_stackup.items():
        if cfg['stackup'][key]!=value:
            raise ValueError(f'Update solver stackup implementation before changing {key}')
    data={'current':json.loads(args.geometry.read_text()),'original':json.loads(args.reference_geometry.read_text())}
    if args.pcb and digest(args.pcb)!=data['current']['pcb_sha256']:
        raise ValueError('Geometry is stale: current PCB hash differs')
    manifest={'schema':1,'scope':cfg['scope'],'profile':args.profile,
              'pcb_sha256':data['current']['pcb_sha256'],'reference_pcb_sha256':data['original']['pcb_sha256'],
              'config_sha256':digest(args.config),'python':platform.python_version(),
              'numpy':np.__version__,'ngspice':subprocess.run(['ngspice','--version'],capture_output=True,text=True).stdout.splitlines()[1],
              'fasthenry':'WR 3.0, archive 031424; sha256 6da40d0e31425bca85be46434b33ecc194205d705b47f4459d91568c9f4301ef',
              'source_hashes':{p.name:digest(p) for p in sorted([*Path(__file__).parent.glob('*.py'),Path(__file__).parent/'fasthenry-stats.patch'])},
              'physical_release_approved':False}
    summary={'manifest':manifest,'calibration':wire_calibration(args.fasthenry.resolve(),out/'calibration'),
             'extractions':{},'thermal':{},'circuits':{},'coupling_estimates':{},'gates':{}}
    for rev,d in data.items():
        print('Extracting',rev,flush=True);shapes=copper_shapes(d)
        profiles=[('coarse',.25,0,1)]
        if args.profile=='full':
            profiles+=[('fine',.125,0,1)]
            if rev=='current':profiles+=[('expanded',.25,2,1),('thickness',.2,0,3)]
        summary['extractions'][rev]={}
        for label,pitch,margin,nhinc in profiles:
            folder=out/rev/'extraction'/label
            # Reuse only exact previously generated results with the same
            # script/config hash. Archived decks/results remain independently inspectable.
            stamp={'source_hashes':manifest['source_hashes'],'pcb_sha256':d['pcb_sha256'],
                   'pitch':pitch,'margin':margin,'nhinc':nhinc,'spacing':.2}
            cache=folder/'cache.json'
            if cache.exists() and json.loads(cache.read_text())==stamp:
                loops=json.loads((folder/'results.json').read_text())
            else:
                loops=[extract(d,shapes,ic,cap,pins,pitch,margin,.2,nhinc,folder/cap,args.fasthenry.resolve()) for ic,cap,pins in LOOPS]
                json_write(folder/'results.json',loops);json_write(cache,stamp)
            summary['extractions'][rev][label]=loops
        loops=summary['extractions'][rev].get('fine',summary['extractions'][rev]['coarse'])
        summary['circuits'][rev]={'pdn':run_pdn(d,loops,cfg,out/rev/'pdn'),
            'ringing':run_ringing(loops,cfg,out/rev/'ringing'),
            'conducted':run_conducted(d,loops,cfg,out/rev/'conducted')}
        summary['coupling_estimates'][rev]=electrostatic_screen(d,cfg)
        print('Thermal',rev,flush=True)
        summary['thermal'][rev]=run_thermal_cases(d,cfg,args.profile,out/rev/'thermal')
    # Numerical completion and physical-release gates are deliberately separate.
    summary['gates']['thermal_energy_conservation']=all(v['energy_relative_error']<1e-6 for r in summary['thermal'].values() for v in r.values())
    if args.profile=='full':
        mesh=[];boundary=[];thermal=[]
        for rev in data:
            coarse=summary['extractions'][rev]['coarse'];fine=summary['extractions'][rev]['fine']
            for c,f in zip(coarse,fine):
                changes={key:abs(f['results'][7][key]-c['results'][7][key])/f['results'][7][key] for key in ['resistance_ohm','inductance_h']}
                mesh.append({'revision':rev,'capacitor':c['capacitor'],'relative_changes_10mhz':changes,'passed':max(changes.values())<.05})
            t=summary['thermal'][rev]
            a,b=t['nominal_0p5mm'],t['nominal_0p25mm']
            rel=abs(a['peak_pcb_rise_c']-b['peak_pcb_rise_c'])/b['peak_pcb_rise_c']
            thermal.append({'revision':rev,'peak_rise_relative_change':rel,'passed':rel<.05})
        for a,b in zip(summary['extractions']['current']['coarse'],summary['extractions']['current']['expanded']):
            rel=abs(a['results'][7]['inductance_h']-b['results'][7]['inductance_h'])/b['results'][7]['inductance_h']
            boundary.append({'capacitor':a['capacitor'],'relative_L_change_10mhz':rel,'passed':rel<.05})
        summary['gates'].update({'copper_mesh':mesh,'copper_boundary':boundary,'thermal_mesh':thermal})
    summary['gates']['not_demonstrated']=['validated TPS63070 startup/control behavior','measured switching stress/ringing','radiated or common-mode EMI','EMC compliance','junction temperature','final component bias/loss models']
    json_write(out/'summary.json',summary)
    print('Screening complete; physical_release_approved=false',flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--geometry',type=Path,required=True);p.add_argument('--reference-geometry',type=Path,required=True)
    p.add_argument('--pcb',type=Path);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--fasthenry',type=Path,required=True)
    p.add_argument('--profile',choices=['ci','full'],default='full')
    run(p.parse_args())
