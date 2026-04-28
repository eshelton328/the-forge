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
    assert len(cfg.scenarios) == 1
    assert cfg.scenarios[0].identifier == "divider_op"
    assert len(cfg.scenarios[0].measures) == 1
    assert cfg.scenarios[0].measures[0].identifier == "v_n2"
