"""KiCad SPICE export helper tests."""

from __future__ import annotations

from scripts.sim.export_kicad_spice import strip_trailing_spice_end


def test_strip_trailing_spice_end_removes_dot_end() -> None:
    assert strip_trailing_spice_end(".title x\nR1 1 0 1k\n.end\n") == ".title x\nR1 1 0 1k\n"


def test_strip_trailing_spice_end_preserves_without_end() -> None:
    s = ".title x\nR1 1 0 1k\n"
    assert strip_trailing_spice_end(s) == s
