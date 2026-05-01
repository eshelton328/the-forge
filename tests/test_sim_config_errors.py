"""sim.yml validation edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.sim.config import load_sim_config


def test_rejects_netlist_and_assembly_together(tmp_path: Path) -> None:
    p = tmp_path / "sim.yml"
    p.write_text(
        yaml.safe_dump(
            {
                "spec_version": 1,
                "spice_engine": "ngspice",
                "netlist": "a.cir",
                "assembly": {"main": "sim/m.cir", "includes": []},
                "scenarios": [
                    {
                        "id": "s",
                        "measures": [{"id": "m", "min": 0, "max": 1}],
                    },
                ],
            },
        ),
    )
    with pytest.raises(ValueError, match="not both"):
        load_sim_config(p)


def test_rejects_duplicate_plot_files(tmp_path: Path) -> None:
    p = tmp_path / "sim.yml"
    p.write_text(
        yaml.safe_dump(
            {
                "spec_version": 1,
                "spice_engine": "ngspice",
                "netlist": "a.cir",
                "scenarios": [
                    {
                        "id": "s",
                        "measures": [{"id": "m", "min": 0, "max": 1}],
                    },
                ],
                "plots": [
                    {"file": "x.png", "signal": "v(1)"},
                    {"file": "x.png", "signal": "v(2)"},
                ],
            },
        ),
    )
    (tmp_path / "a.cir").write_text("* stub\n.end\n")
    with pytest.raises(ValueError, match="duplicate plots"):
        load_sim_config(p)


def test_rejects_bad_plot_basename(tmp_path: Path) -> None:
    p = tmp_path / "sim.yml"
    p.write_text(
        yaml.safe_dump(
            {
                "spec_version": 1,
                "spice_engine": "ngspice",
                "netlist": "a.cir",
                "scenarios": [
                    {
                        "id": "s",
                        "measures": [{"id": "m", "min": 0, "max": 1}],
                    },
                ],
                "plots": [
                    {"file": "bad/path.png", "signal": "v(1)"},
                ],
            },
        ),
    )
    (tmp_path / "a.cir").write_text("* stub\n.end\n")
    with pytest.raises(ValueError, match="plots"):
        load_sim_config(p)