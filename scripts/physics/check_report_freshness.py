#!/usr/bin/env python3
"""Reject a checked-in physical report that describes different design/model input."""
import hashlib
import json
from pathlib import Path
import sys


def check(board):
    report=json.loads((board/'review/physical-validation/summary.json').read_text())
    manifest=report['manifest']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if manifest['pcb_sha256']!=sha(board/(board.name+'.kicad_pcb')):
        raise ValueError('Physical report is stale: PCB changed; rerun screening/report')
    if manifest['config_sha256']!=sha(board/'analysis/assumptions.json'):
        raise ValueError('Physical report is stale: model assumptions changed')
    for name,expected in manifest['source_hashes'].items():
        if sha(Path(__file__).parent/name)!=expected:
            raise ValueError(f'Physical report is stale: {name} changed')
    if manifest['physical_release_approved'] is not False:
        raise ValueError('Screening suite cannot grant physical release approval')
    print('Physical report matches PCB, assumptions and numerical source hashes')
    if any(not row['passed'] for row in report.get('gates',{}).get('copper_mesh',[])):
        print('WARNING: copper mesh convergence is unresolved; physical release is not approved')


if __name__=='__main__':check(Path(sys.argv[1]))
