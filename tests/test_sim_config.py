"""sim.yml loader tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.sim.config import load_sim_config

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_YML = REPO_ROOT / "sim" / "fixtures" / "rc_divider" / "sim.yml"


def test_load_rc_fixture_config() -> None:
    cfg = load_sim_config(SMOKE_YML)
    assert cfg.spec_version == 1
    assert cfg.spice_engine == "ngspice"
    assert cfg.netlist_path.name == "rc.cir"
    assert cfg.assembly is None
    assert len(cfg.scenarios) == 1
    assert cfg.scenarios[0].identifier == "divider_op"
    assert len(cfg.scenarios[0].measures) == 1
    m0 = cfg.scenarios[0].measures[0]
    assert m0.identifier == "v_n2"
    assert m0.op_node == "2"


def test_load_board_assembly_config(tmp_path: Path) -> None:
    stub_lib = tmp_path / "libs" / "spice" / "tps63070" / "TPS63070_TRANS.LIB"
    stub_lib.parent.mkdir(parents=True)
    stub_lib.write_text("* stub\n")
    board = tmp_path / "boards" / "tps63070-breakout"
    (board / "sim").mkdir(parents=True)
    (board / "sim" / "kicad_export.cir").write_text("* export placeholder\n")
    (board / "sim" / "overlay.cir").write_text("* overlay\n")
    shutil.copy(
        REPO_ROOT / "boards" / "tps63070-breakout" / "sim" / "ac_small_signal.cir",
        board / "sim" / "ac_small_signal.cir",
    )
    yml = board / "sim.yml"
    yml.write_text(
        (REPO_ROOT / "boards" / "tps63070-breakout" / "sim.yml").read_text(),
    )
    cfg = load_sim_config(yml)
    assert len(cfg.scenarios) == 3
    assert cfg.scenarios[1].identifier == "tran_settle"
    assert cfg.scenarios[2].identifier == "tran_load_step"
    assert len(cfg.plots) == 1
    assert cfg.plots[0].png_basename == "tran-vout.png"
    assert cfg.assembly is not None
    assert cfg.assembly.main_rel == "sim/kicad_export.cir"
    assert cfg.assembly.includes_rel == ("../../libs/spice/tps63070/TPS63070_TRANS.LIB",)
    assert cfg.netlist_path.name == "assembled.cir"
    assert cfg.netlist_path.parent.name == "sim"
    assert len(cfg.secondary_passes) == 1
    assert cfg.secondary_passes[0].netlist_path.name == "ac_small_signal.cir"
    assert cfg.secondary_passes[0].scenarios[0].identifier == "ac_small_signal"
    assert len(cfg.secondary_passes[0].scenarios[0].measures) == 3
    assert cfg.secondary_passes[0].scenarios[0].measures[0].identifier == "vout_ac_vm_1k"
    ac0 = cfg.secondary_passes[0].scenarios[0].measures[0]
    assert ac0.display_title is not None and "1 kHz" in ac0.display_title
    assert ac0.display_group == "ac_line_response"


def test_load_measure_optional_title_group(tmp_path: Path) -> None:
    yml = tmp_path / "sim.yml"
    (tmp_path / "sim").mkdir()
    (tmp_path / "sim" / "deck.cir").write_text("* x\n")
    yml.write_text(
        "spec_version: 1\n"
        "spice_engine: ngspice\n"
        "netlist: sim/deck.cir\n"
        "scenarios:\n"
        "  - id: only\n"
        "    measures:\n"
        "      - id: m1\n"
        "        title: My title\n"
        "        group: my_group\n"
        "        max: 1.0\n",
    )
    cfg = load_sim_config(yml)
    m0 = cfg.scenarios[0].measures[0]
    assert m0.display_title == "My title"
    assert m0.display_group == "my_group"
