#!/usr/bin/env python3
"""Optional native TI/ngspice compatibility probe; no vendor code is redistributed.

Download the unmodified free TI PSpice library, verify it, run a startup attempt,
and explicitly record incomplete transients as unsupported. This does not port
or certify the device model. Uses local .spiceinit for ngbehavior=ps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request
import zipfile


def probe(out):
    out.mkdir(parents=True,exist_ok=True)
    archive=out/'ti-model.zip'
    urllib.request.urlretrieve('https://www.ti.com/lit/zip/slvmbp8',archive)
    expected='235d1a8efd991f8340dafd2e5b7f2d72280a1e1ab129fcc26b6cabf6a0e1cb5f'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
        raise ValueError('TI model package changed; review before running')
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.upper().endswith('TPS63070_TRANS.LIB')]
        if len(names)!=1:raise ValueError('Expected exactly one TI model')
        model=z.read(names[0])
    if hashlib.sha256(model).hexdigest()!='251545a36d3a9d9295eb00a061f622ef492035feacaaef2a61bf33f606caddb8':
        raise ValueError('TI library hash mismatch')
    (out/'TPS63070_TI.lib').write_bytes(model)
    (out/'.spiceinit').write_text('set ngbehavior=ps\n')
    (out/'probe.cir').write_text('''* Native TI model compatibility probe, not board validation
.include TPS63070_TI.lib
Vbat vin 0 4.2
Ven en 0 PULSE(0 4.2 1u 1u 1u 20m 40m)
XU en fb 0 0 l1 l2 pg 0 vin aux vin vin out out 0 TPS63070_TRANS
L1 l1 lm 1.5u
Rl lm l2 .05
C1 vin 0 20u
C2 out 0 66u
C3 aux 0 100n
R1 out fb 523k
R2 fb 0 100k
Rload out 0 25
Rpg pg out 100k
.tran 50n 3m
.print tran v(out)
.end
''')
    try:
        p=subprocess.run(['ngspice','-b','probe.cir'],cwd=out,capture_output=True,text=True,timeout=180)
        log=p.stdout+p.stderr;code=p.returncode
    except subprocess.TimeoutExpired as e:
        log=(e.stdout or b'').decode(errors='replace')+(e.stderr or b'').decode(errors='replace');code=None
    (out/'probe.log').write_text(log)
    rows=re.findall(r'^\d+\s+([\deE+.-]+)\s+([\deE+.-]+)\s*$',log,re.M)
    end=float(rows[-1][0]) if rows else None
    complete=code==0 and end is not None and end>=.003-1e-9 and 'timestep too small' not in log.lower()
    result={'model_sha256':hashlib.sha256(model).hexdigest(),'requested_end_s':.003,
            'actual_end_s':end,'completed':complete,'exit_code':code,
            'status':'COMPATIBILITY ONLY; NOT VALIDATED' if complete else 'UNSUPPORTED / INCOMPLETE TRANSIENT',
            'temperature_modeled':False,'operating_and_shutdown_current_modeled':False}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    probe(p.parse_args().output.resolve())
