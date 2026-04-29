"""KiCad SPICE export helper tests."""

from __future__ import annotations

from scripts.sim.export_kicad_spice import postprocess_spicemodel_flat, strip_trailing_spice_end


def test_strip_trailing_spice_end_removes_dot_end() -> None:
    assert strip_trailing_spice_end(".title x\nR1 1 0 1k\n.end\n") == ".title x\nR1 1 0 1k\n"


def test_strip_trailing_spice_end_preserves_without_end() -> None:
    s = ".title x\nR1 1 0 1k\n"
    assert strip_trailing_spice_end(s) == s


def test_postprocess_spicemodel_flat_strips_wrapper_and_ti_include() -> None:
    raw = """*

.subckt tps63070-breakout


.include \"/abs/path/libs/spice/tps63070/TPS63070_TRANS.LIB\"
XU1 1 2 3 TPS63070_TRANS
R1 1 0 1k

.ends
.end
"""
    got = postprocess_spicemodel_flat(raw, board_slug="tps63070-breakout")
    assert ".subckt" not in got.lower()
    assert ".ends" not in got.lower()
    assert "tps63070_trans.lib" not in got.lower()
    assert "XU1" in got
    assert "R1" in got
