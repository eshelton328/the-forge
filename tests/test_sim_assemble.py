"""Assembler include-chain contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sim.assemble import AssemblySpec, write_assembled_deck


def _include_paths_from_assembled(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith(".include")]
    out: list[str] = []
    for ln in lines:
        start = ln.index('"') + 1
        end = ln.rindex('"')
        out.append(ln[start:end])
    return out


def test_assembled_include_order(tmp_path: Path) -> None:
    board = tmp_path / "board"
    (board / "lib").mkdir(parents=True)
    (board / "sim").mkdir(parents=True)
    (board / "lib" / "first.cir").write_text("* 1\n")
    (board / "lib" / "second.cir").write_text("* 2\n")
    (board / "sim" / "main.cir").write_text("* main\n")
    (board / "sim" / "overlay.cir").write_text("* overlay\n")

    out = board / "sim" / "assembled.cir"
    spec = AssemblySpec(
        main_rel="sim/main.cir",
        includes_rel=("lib/first.cir", "lib/second.cir"),
    )
    write_assembled_deck(board, spec, out)

    rels = _include_paths_from_assembled(out.read_text())
    assert rels == [
        "../lib/first.cir",
        "../lib/second.cir",
        "main.cir",
        "overlay.cir",
    ]


def test_assemble_requires_overlay(tmp_path: Path) -> None:
    board = tmp_path / "b"
    (board / "sim").mkdir(parents=True)
    (board / "sim" / "main.cir").write_text("* m\n")
    out = board / "sim" / "assembled.cir"
    spec = AssemblySpec(main_rel="sim/main.cir", includes_rel=())
    with pytest.raises(ValueError, match="overlay"):
        write_assembled_deck(board, spec, out)
