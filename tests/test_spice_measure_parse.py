"""Golden parsing for ngspice-style .measure lines (no simulator required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sim.measure_parse import (
    check_limits,
    parse_dc_op_node_voltage,
    parse_measure_value,
)

FIXTURE_TEXT = Path(__file__).resolve().parent / "fixtures" / "spice" / "golden_ngspice_measure.txt"


def test_parse_measure_from_golden_file() -> None:
    txt = FIXTURE_TEXT.read_text()
    v = parse_measure_value(txt, "v_n2")
    assert v is not None
    assert v == pytest.approx(5.0)


@pytest.mark.parametrize(
    ("line", "measure_key", "expected"),
    (
        ("v_n2 = 5.000000e+00\n", "v_n2", 5.0),
        ("VMID =  \t12.500e-03\n", "VMID", 0.0125),
        ("v_out_steady        =  3.30000e+00\n", "v_out_steady", 3.3),
        ("v_out_min           =  3.30000e+00 at=  2.50000e-04\n", "v_out_min", 3.3),
        ("vout_ripple_pp      =  1.00000e-02 from=  2.00000e-04 to=  2.50000e-04\n", "vout_ripple_pp", 0.01),
    ),
)
def test_parse_measure_inline(line: str, measure_key: str, expected: float) -> None:
    v = parse_measure_value(line, measure_key)
    assert v is not None
    assert v == pytest.approx(expected)


def test_check_limits_pass() -> None:
    ok, reason = check_limits(5.0, 4.0, 6.0)
    assert ok
    assert reason is None


def test_check_limits_min_fail() -> None:
    ok, reason = check_limits(3.0, 4.0, 6.0)
    assert not ok
    assert reason is not None


def test_check_limits_max_fail() -> None:
    ok, reason = check_limits(7.0, 4.0, 6.0)
    assert not ok
    assert reason is not None


OP_TABLE_SAMPLE = """  Measurements for DC Analysis

	Node                                  Voltage
	----                                  -------
	----	-------
	V(2)                             5.000000e+00
	V(1)                             1.000000e+01
"""


def test_parse_dc_op_node_voltage_fixture() -> None:
    assert parse_dc_op_node_voltage(OP_TABLE_SAMPLE, "2") == pytest.approx(5.0)
    assert parse_dc_op_node_voltage(OP_TABLE_SAMPLE, "1") == pytest.approx(10.0)
    assert parse_dc_op_node_voltage(OP_TABLE_SAMPLE, "99") is None


def test_parse_dc_op_whitespace_tolerance() -> None:
    txt = "\t\tV(\t\t2 )\t\t3e0\n"
    assert parse_dc_op_node_voltage(txt, "2") == pytest.approx(3.0)


KICAD_STYLE_NET_LOG = """  Measurements for DC Analysis

	Node                                  Voltage
	----                                  -------
	----	-------
	/vin_2v_to_16v                   1.000000e+01
"""


def test_parse_dc_op_kicad_style_slash_net() -> None:
    assert parse_dc_op_node_voltage(KICAD_STYLE_NET_LOG, "/VIN_2v_to_16v") == pytest.approx(10.0)
    assert parse_dc_op_node_voltage(KICAD_STYLE_NET_LOG, "VIN_2v_to_16v") == pytest.approx(10.0)
