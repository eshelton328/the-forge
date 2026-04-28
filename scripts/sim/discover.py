"""Discover board directories that opt in to SPICE via ``sim.yml``."""

from __future__ import annotations

from pathlib import Path


def discover_board_roots_with_sim_yml(repo_root: Path) -> tuple[Path, ...]:
    """Return sorted board roots under ``boards/`` that contain ``sim.yml``."""
    boards = repo_root / "boards"
    if not boards.is_dir():
        return ()
    found: list[Path] = []
    for d in sorted(boards.iterdir()):
        if d.is_dir() and (d / "sim.yml").is_file():
            found.append(d)
    return tuple(found)
