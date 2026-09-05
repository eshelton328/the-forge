"""Independent passive-network and bounded commutation tests in ngspice."""
import itertools
import json
import math
from pathlib import Path
import subprocess
import numpy as np
from scipy.signal import find_peaks
from copper import pad


def capacitance(value):
    value=value.replace('µ','u').replace('μ','u').replace('F','').strip()
    for suffix,scale in [('p',1e-12),('n',1e-9),('u',1e-6),('m',1e-3)]:
        if value.endswith(suffix): return float(value[:-1])*scale
    return float(value)


def spice(deck,out,name='run',timeout=120):
    out.mkdir(parents=True,exist_ok=True)
    (out/(name+'.cir')).write_text(deck)
    p=subprocess.run(['ngspice','-n','-b',name+'.cir'],cwd=out,capture_output=True,text=True,timeout=timeout)
    log=p.stdout+p.stderr
    (out/(name+'.log')).write_text(log)
    if p.returncode or any(e in log.lower() for e in ['timestep too small','simulation interrupted','fatal error']):
        raise RuntimeError(f'ngspice failed: {out}/{name}.log')
    return log


def local_network(data, loop, references, cfrac, esr, esl, multiplier=1.):
    """Nearest loop extracted; other cap branches use distance-scaled R/L proxies.

    Parallel independent branches omit their mutual coupling/shared spreading.
    This is an explicit sensitivity model, not a complete multiport extraction.
    """
    target=loop['capacitor'];ic=loop['ic'];pin='12' if target in ['C3','C11'] else '7'
    location=pad(data,ic,pin)['xy'];base=math.dist(location,pad(data,target,1)['xy'])
    # Low-frequency R and 10 MHz L; frequency dependence separately documented.
    r=loop['results'][0]['resistance_ohm'];l=loop['results'][7]['inductance_h']
    parts=[]
    for ref in references:
        scale=max(.5,math.dist(location,pad(data,ref,1)['xy'])/base)
        parts.append({'ref':ref,'c_f':capacitance(data['footprints'][ref]['value'])*cfrac,
                      'r_ohm':r*scale+esr,'l_h':l*scale*multiplier+esl,
                      'interconnect_provenance':'FastHenry nearest-loop' if ref==target else 'distance-scaled proxy; not extracted'})
    return parts


def impedance(freq,parts):
    s=2j*np.pi*np.asarray(freq)
    return 1/sum(1/(p['r_ohm']+s*p['l_h']+1/(s*p['c_f'])) for p in parts)


def pdn_deck(parts):
    lines=['* Local passive capacitor bank; no regulator feedback','Itest 0 rail DC 0 AC 1']
    for p in parts:
        r=p['ref']
        lines += [f'R{r} rail r{r} {p["r_ohm"]:.12g}',f'L{r} r{r} l{r} {p["l_h"]:.12g}',f'C{r} l{r} 0 {p["c_f"]:.12g}']
    lines += ['.control','set wr_singlescale','set wr_vecnames','ac dec 120 1000 100Meg',
              'wrdata ac.csv v(rail)','quit','.endc','.end']
    return '\n'.join(lines)+'\n'


def run_pdn(data,loops,config,out):
    summaries=[]
    freq=np.logspace(3,8,601)
    for loop in loops:
        cap=loop['capacitor'];refs=config['passive']['local_caps'][cap]
        nominal=local_network(data,loop,refs,.5,.01,.6e-9)
        folder=out/cap;spice(pdn_deck(nominal),folder)
        a=np.loadtxt(folder/'ac.csv',skiprows=1);actual=a[:,1]+1j*a[:,2]
        expected=impedance(a[:,0],nominal)
        error=float(np.max(abs(actual-expected)/abs(expected)))
        if error>.001:raise ValueError('SPICE/analytic passive AC disagreement')
        envelopes=[];cases=[]
        for c,e,esl,m in itertools.product(config['passive']['effective_capacitance_fraction'],
                config['passive']['ceramic_esr_ohm'],config['passive']['ceramic_esl_nh'],
                config['passive']['copper_loop_multiplier']):
            parts=local_network(data,loop,refs,c,e,esl*1e-9,m)
            z=abs(impedance(freq,parts));envelopes.append(z)
            f0=2.4e6
            cases.append({'c_fraction':c,'esr_ohm':e,'esl_nh':esl,'loop_multiplier':m,
                          'z_2p4mhz_ohm':float(abs(impedance([f0],parts)[0])),
                          'peak_100khz_30mhz_ohm':float(z[(freq>=1e5)&(freq<=3e7)].max())})
        envelope=np.array(envelopes)
        np.savetxt(folder/'envelope.csv',np.column_stack((freq,abs(impedance(freq,nominal)),envelope.min(0),envelope.max(0))),delimiter=',',header='frequency_hz,nominal_ohm,min_ohm,max_ohm',comments='')
        result={'capacitor':cap,'cases':len(cases),'parts':nominal,'ngspice_analytic_relative_error':error,
                'nominal_z_2p4mhz_ohm':float(abs(impedance([2.4e6],nominal)[0])),
                'z_2p4mhz_range_ohm':[min(c['z_2p4mhz_ohm'] for c in cases),max(c['z_2p4mhz_ohm'] for c in cases)],
                'nominal_effective_c_uf':sum(p['c_f'] for p in nominal)*1e6}
        (folder/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
        summaries.append(result)
    return summaries


def ringing_deck(l,r,c,edge_ns,current,dt_ns):
    return f'''* Bounded current commutation; NOT a TPS63070 waveform prediction
Lloop 0 series {l:.12g}
Rdamp series sw {r:.12g}
Cnode sw 0 {c:.12g}
Iedge sw 0 PWL(0 0 50n 0 {50+edge_ns:.9g}n {current:.9g} 1u {current:.9g})
.options method=gear reltol=1e-5 abstol=1e-10 vntol=1e-8
.control
set wr_singlescale
set wr_vecnames
tran {dt_ns:.9g}n 400n 0 {dt_ns:.9g}n
wrdata transient.csv v(sw) i(Lloop)
quit
.endc
.end
'''


def ring_metrics(a,current,r):
    t=a[:,0];v=a[:,1]
    # Voltage is relative to the clamped rail, so add DC rail only with a
    # justified real commutation topology. No device absolute-limit assertion.
    after=t>=50e-9
    peak=float(np.max(abs(v[after])))
    tail=t>=100e-9
    corrected=v+r*current
    maxima,_=find_peaks(corrected[tail]);ts=t[tail][maxima]
    freq=float(1/np.median(np.diff(ts[:5]))) if len(ts)>2 else None
    beyond=np.flatnonzero((t>=50e-9)&(abs(corrected)>.1*max(peak,1e-9)))
    settle=float((t[beyond[-1]]-50e-9)*1e9) if len(beyond) else 0.
    return {'peak_relative_voltage_v':peak,'ring_frequency_hz':freq,'last_above_10pct_ns':settle,
            'final_current_a':float(a[-1,2]),'end_time_s':float(t[-1])}


def run_ringing(loops,config,out):
    rows=[]
    for loop in loops:
        cap=loop['capacitor']; lpcb=loop['results'][7]['inductance_h']; rpcb=loop['results'][7]['resistance_ohm']
        # One nominal ngspice run per loop plus a timestep refinement. Broader
        # sensitivity solved exactly as a linear LTI system, checked against SPICE.
        l=lpcb+1.5e-9;r=rpcb+.5;c=300e-12;edge=5.;current=1.
        for dt in [.1,.05]:
            folder=out/cap/str(dt)
            spice(ringing_deck(l,r,c,edge,current,dt),folder)
            a=np.loadtxt(folder/'transient.csv',skiprows=1)
            metrics=ring_metrics(a,current,r)
            if abs(metrics['end_time_s']-400e-9)>1e-12:raise ValueError('Incomplete transient')
            if abs(metrics['final_current_a']-current)>.01:raise ValueError('Inductor current balance failed')
            metrics['timestep_ns']=dt
            if dt==.1:coarse=metrics
            else:fine=metrics
        delta=abs(fine['peak_relative_voltage_v']-coarse['peak_relative_voltage_v'])/fine['peak_relative_voltage_v']
        if delta>.05:raise ValueError('Ringing timestep convergence failed')
        # Closed-form response for linear current ramp through R||C/L network.
        # State equation: L C v'' + R C v' + v = -L i' - R i.
        from scipy.signal import lsim, TransferFunction
        times=np.linspace(0,400e-9,4001)
        inp=np.clip((times-50e-9)/(edge*1e-9),0,1)*current
        _,v,_=lsim(TransferFunction([-l,-r],[l*c,r*c,1]),inp,times)
        independent=float(np.max(abs(v)))
        err=abs(independent-fine['peak_relative_voltage_v'])/independent
        if err>.02:raise ValueError('Independent ringing transfer function disagrees')
        sweep=[]
        for edge,cp,lp,damping,lmult in itertools.product(config['ringing']['edge_ns'],
                config['ringing']['node_capacitance_pf'],config['ringing']['package_inductance_nh'],
                config['ringing']['damping_ohm'],config['passive']['copper_loop_multiplier']):
            ll=lpcb*lmult+lp*1e-9;rr=rpcb+damping;cc=cp*1e-12
            inp=np.clip((times-50e-9)/(edge*1e-9),0,1)
            _,vv,_=lsim(TransferFunction([-ll,-rr],[ll*cc,rr*cc,1]),inp,times)
            sweep.append({'edge_ns':edge,'c_pf':cp,'package_l_nh':lp,'damping_ohm':damping,'pcb_l_multiplier':lmult,
                          'peak_v_per_a':float(np.max(abs(vv))),
                          'undamped_frequency_hz':1/(2*np.pi*np.sqrt(ll*cc))})
        (out/cap/'sweep.json').write_text(json.dumps(sweep,indent=2)+'\n')
        rows.append({'capacitor':cap,'pcb_l_nh':lpcb*1e9,'nominal':fine,
                     'timestep_relative_change':delta,'independent_analytic_relative_error':err,
                     'sensitivity_cases':len(sweep),'peak_v_per_a_range':[min(s['peak_v_per_a'] for s in sweep),max(s['peak_v_per_a'] for s in sweep)],
                     'current_scaling_a':config['ringing']['current_step_a']})
    return rows


def run_conducted(data,loops,config,out):
    rows=[]
    for loop in loops:
        if loop['capacitor'] not in ['C3','C11']:continue
        cap=loop['capacitor']
        parts=local_network(data,loop,config['passive']['local_caps'][cap],.5,.01,.6e-9)
        d=pdn_deck(parts).split('.control')[0]
        d=d.replace('Itest 0 rail DC 0 AC 1','Itest 0 rail DC 0 AC 1\nLline rail src 5u\nRsource src 0 0.1\nCcouple rail receiver 0.1u\nRreceiver receiver 0 50')
        d+='\n.control\nset wr_singlescale\nset wr_vecnames\nac dec 120 150k 30Meg\nwrdata transfer.csv v(receiver) v(rail)\nquit\n.endc\n.end\n'
        folder=out/cap;spice(d,folder)
        a=np.loadtxt(folder/'transfer.csv',skiprows=1);f=a[:,0];s=2j*np.pi*f
        receiver=a[:,1]+1j*a[:,2]
        zline=.1+s*5e-6;zrec=50+1/(s*.1e-6);zbank=impedance(f,parts)
        calculated=1/(1/zline+1/zrec+1/zbank)*50/zrec
        err=float(np.max(abs(receiver-calculated)/abs(calculated)))
        if err>.001:raise ValueError('Conducted transfer analytical cross-check failed')
        values=[]
        for harmonic in [1,2,5,10]:
            at=2.4e6*harmonic
            val=float(np.interp(at,f,abs(receiver)))
            values.append({'harmonic':harmonic,'frequency_hz':at,'transfer_ohm':val,'db_ohm':20*math.log10(val)})
        rows.append({'capacitor':cap,'analytic_relative_error':err,'harmonics':values,
                     'scope':'Differential-mode current-to-receiver transfer; uncalibrated simplified 5uH/50ohm network, no emission level or compliance detector'})
    return rows
