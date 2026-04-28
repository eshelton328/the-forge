"""sim.yml loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sim.config import load_sim_config

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_YML = REPO_ROOT / "sim" / "fixtures" / "rc_divider" / "sim.yml"
BOARD_SIM_YML = REPO_ROOT / "boards" / "tps63070-breakout" / "sim.yml"


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


def test_load_board_assembly_config() -> None:
    cfg = load_sim_config(BOARD_SIM_YML)
    assert cfg.assembly is not None
    assert cfg.assembly.main_rel == "sim/main.cir"
    assert cfg.assembly.includes_rel == ()
    assert cfg.netlist_path.name == "assembled.cir"
    assert cfg.netlist_path.parent.name == "sim"
