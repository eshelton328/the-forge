"""Independent mathematical controls for the optional physical-screening suite.

The dedicated workflow installs scripts/physics/requirements.txt. Lightweight
repository tests may skip this module when the optional numerical stack is absent.
"""
import importlib.util
import json
from pathlib import Path
import sys
import math
import pytest

np=pytest.importorskip('numpy')
pytest.importorskip('scipy')
pytest.importorskip('shapely')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/physics'))
from circuit_tests import capacitance, impedance, ring_metrics
from thermal import solve_thermal
from run_screening import heat_sources


def uniform_board():
    rectangle={'outer':[[0,0],[10,0],[10,10],[0,10]],'holes':[]}
    return {'bounds':[0,0,10,10], 'tracks':[], 'vias':[], 'footprints':{'U1':{'xy':[5,5]}},
            'copper':[{'kind':'pad' if l=='F.Cu' else 'zone','layer':l,'net':'GND','ref':'U1','pad':'1','polygons':[rectangle]} for l in ['F.Cu','In1.Cu','In2.Cu','B.Cu']]}


def test_uniform_heat_matches_closed_form_slab():
    # Exact uniform slab: q/A = h*Ttop + h*Tbottom;
    # Ttop-Tbottom = h*Tbottom*Rthrough. No datasheet thetaJA involved.
    q=.2;area=1e-4;h=10.;k=.3
    copper=np.array([35,17.5,17.5,35])*1e-6
    gaps=np.array([.2,1.165,.2])*1e-3-(copper[:-1]+copper[1:])/2
    rthrough=gaps.sum()/k
    expected=q/area*(1+h*rthrough)/(h*(2+h*rthrough))
    r,t,_=solve_thermal(uniform_board(),2,h,{'U1':{'watts':q}},k_fr4=k)
    assert r['peak_pcb_rise_c']==pytest.approx(expected,rel=1e-8)
    assert r['energy_relative_error']<1e-8
    assert np.ptp(t[0])<1e-8


def test_thermal_linearity_and_cooling_monotonicity():
    d=uniform_board()
    a,*_=solve_thermal(d,2,10,{'U1':{'watts':.2}})
    b,*_=solve_thermal(d,2,10,{'U1':{'watts':.4}})
    c,*_=solve_thermal(d,2,20,{'U1':{'watts':.2}})
    assert b['peak_pcb_rise_c']==pytest.approx(2*a['peak_pcb_rise_c'],rel=1e-10)
    assert c['peak_pcb_rise_c']<a['peak_pcb_rise_c']


def test_series_rlc_at_resonance_and_parallel_scaling():
    part={'r_ohm':.01,'l_h':2e-9,'c_f':10e-6}
    f=1/(2*math.pi*math.sqrt(part['l_h']*part['c_f']))
    z=impedance([f],[part])[0]
    assert z.real==pytest.approx(.01)
    assert abs(z.imag)<1e-12
    assert impedance([f],[part,part])[0]==pytest.approx(z/2)


def test_negative_control_missing_capacitance_changes_impedance():
    bank=[{'r_ohm':.01,'l_h':2e-9,'c_f':10e-6}]*3
    assert abs(impedance([1e3],bank[:1])[0])==pytest.approx(3*abs(impedance([1e3],bank)[0]))


@pytest.mark.parametrize('text,value',[('10µF',1e-5),('22μF',22e-6),('0.1uF',1e-7),('300pF',300e-12)])
def test_component_units_against_si(text,value):
    assert capacitance(text)==pytest.approx(value)


def test_loss_budget_does_not_turn_delivered_power_into_converter_heat():
    c=json.loads((ROOT/'boards/esp32s3-devkit-5v/analysis/assumptions.json').read_text())
    s=heat_sources(c,.85)
    stage=sum(s[r]['watts'] for r in ['U1','U2','L1','L2'])
    assert stage==pytest.approx(4.65*(1/.85-1))
    assert stage<4.65
    assert sum(v['watts'] for v in s.values())==pytest.approx(stage+1.)


def test_ringing_metric_preserves_incomplete_end_time():
    # Reaching an early solver stop must never masquerade as a complete trace.
    a=np.array([[0,0,0],[50e-9,0,0],[100e-9,-.5,1.]])
    r=ring_metrics(a,1.,.5)
    assert r['end_time_s']<400e-9


def report_fixture(tmp_path):
    import hashlib
    d=tmp_path/'board';(d/'review/physical-validation').mkdir(parents=True);(d/'analysis').mkdir()
    (d/'board.kicad_pcb').write_text('board revision A')
    (d/'analysis/assumptions.json').write_text('{}')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'pcb_sha256':sha(d/'board.kicad_pcb'),'config_sha256':sha(d/'analysis/assumptions.json'),
              'source_hashes':{},'physical_release_approved':False}
    (d/'review/physical-validation/summary.json').write_text(json.dumps({'manifest':manifest}))
    return d


def test_stale_board_report_is_rejected(tmp_path):
    from check_report_freshness import check
    d=report_fixture(tmp_path);check(d)
    (d/'board.kicad_pcb').write_text('board revision B')
    with pytest.raises(ValueError,match='PCB changed'):check(d)


def test_stale_assumptions_report_is_rejected(tmp_path):
    from check_report_freshness import check
    d=report_fixture(tmp_path);check(d)
    (d/'analysis/assumptions.json').write_text('{"ambient":50}')
    with pytest.raises(ValueError,match='assumptions changed'):check(d)
