"""Board discovery for sim.yml opt-in."""

from __future__ import annotations

from pathlib import Path

from scripts.sim.discover import discover_board_roots_with_sim_yml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_discover_boards_with_sim_yml_includes_tps63070() -> None:
    roots = discover_board_roots_with_sim_yml(REPO_ROOT)
    names = {p.name for p in roots}
    assert "tps63070-breakout" in names
    assert "esp32s3-devkit" not in names
