"""Ngspice ``wrdata`` helpers and matplotlib PNG export (#59)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sim.plot_extractions import (
    build_plot_driver_deck,
    parse_wrdata_two_column_table,
    validate_plot_png_basename,
    validate_plot_signal,
    wrdata_ascii_to_png,
)


def test_validate_plot_png_basename() -> None:
    assert validate_plot_png_basename("a-z_1.0.png") == "a-z_1.0.png"
    with pytest.raises(ValueError):
        validate_plot_png_basename("../x.png")
    with pytest.raises(ValueError):
        validate_plot_png_basename("nope.jpg")


def test_validate_plot_signal_rejects_meta() -> None:
    with pytest.raises(ValueError):
        validate_plot_signal(".include bad")
    validate_plot_signal("v(/vout_+3.3v)")


def test_parse_wrdata_two_column_table() -> None:
    txt = "0 1\n1e-6 1.1\n"
    xs, ys = parse_wrdata_two_column_table(txt)
    assert xs == [0.0, 1e-6]
    assert ys == [1.0, 1.1]


def test_build_plot_driver_deck() -> None:
    deck = build_plot_driver_deck(
        "*cell\n",
        (("plots/_data/a.txt", "v(1)"),),
    )
    assert "wrdata plots/_data/a.txt v(1)" in deck
    assert deck.strip().endswith(".end")


def test_wrdata_ascii_to_png_writes_file(tmp_path: Path) -> None:
    data = tmp_path / "d.txt"
    data.write_text(
        " 0.0  0.0\n"
        " 1e-9  1.0\n"
        " 2e-9  2.0\n",
    )
    png = tmp_path / "out.png"
    wrdata_ascii_to_png(wrdata_txt=data, png_out=png, title="t", signal_label="v(test)")
    assert png.is_file()
    assert png.stat().st_size > 200
