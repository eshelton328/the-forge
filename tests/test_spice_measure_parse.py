"""Golden parsing for ngspice-style .measure lines (no simulator required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sim.measure_parse import check_limits, parse_measure_value

FIXTURE_TEXT = Path(__file__).resolve().parent / "fixtures" / "spice" / "golden_ngspice_measure.txt"


def test_parse_measure_from_golden_file() -> None:
    txt = FIXTURE_TEXT.read_text()
    v = parse_measure_value(txt, "v_n2")
    assert v is not None
    assert v == pytest.approx(5.0)


@pytest.mark.parametrize(
    ("line", "expected"),
    (
        ("v_n2 = 5.000000e+00\n", 5.0),
        ("VMID =  \t12.500e-03\n", 0.0125),
    ),
)
def test_parse_measure_inline(line: str, expected: float) -> None:
    v = parse_measure_value(line, "v_n2" if "v_n2" in line else "VMID")
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
