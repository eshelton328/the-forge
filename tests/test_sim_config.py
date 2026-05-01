"""sim.yml loader tests."""

from __future__ import annotations

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
    yml = board / "sim.yml"
    yml.write_text(
        (REPO_ROOT / "boards" / "tps63070-breakout" / "sim.yml").read_text(),
    )
    cfg = load_sim_config(yml)
    assert len(cfg.scenarios) == 2
    assert cfg.scenarios[1].identifier == "tran_settle"
    assert cfg.assembly is not None
    assert cfg.assembly.main_rel == "sim/kicad_export.cir"
    assert cfg.assembly.includes_rel == ("../../libs/spice/tps63070/TPS63070_TRANS.LIB",)
    assert cfg.netlist_path.name == "assembled.cir"
    assert cfg.netlist_path.parent.name == "sim"
