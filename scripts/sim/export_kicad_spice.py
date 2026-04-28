#!/usr/bin/env python3
"""Export a board schematic to ``sim/kicad_export.cir`` for SPICE assembly (issue #46).

Runs ``kicad-cli sch export netlist --format spice`` on ``<board>/<board>.kicad_sch``.
The KiCad exporter appends ``.end``, which would stop the parser before ``sim/overlay.cir``
is included by ``assemble.py``; this script strips a trailing ``.end`` line so overlay can
add sources and ``.op`` / ``.end``.

Typical CI / local Docker (same image as ``.github/workflows/pr-checks.yml``)::

    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/workspace/.kicad-ci-home \\
      -v "$PWD:/workspace" -w /workspace "$KICAD_IMAGE" bash -c '
        source /workspace/scripts/ci/setup-kicad-env.sh &&
        python3 scripts/sim/export_kicad_spice.py --board-dir boards/my-board
      '
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def strip_trailing_spice_end(text: str) -> str:
    """Remove a trailing ``.end`` so an assembled deck can append overlay/analysis."""
    lines = text.splitlines()
    while lines and lines[-1].strip() == "":
        lines.pop()
    if lines and lines[-1].strip().lower() == ".end":
        lines.pop()
    return "\n".join(lines).rstrip() + "\n"


def export_spice_netlist(
    board_dir: Path,
    *,
    kicad_cli: str,
    output_rel: Path = Path("sim/kicad_export.cir"),
) -> Path:
    """Run kicad-cli and write the post-processed netlist. Returns absolute output path."""
    root = board_dir.resolve()
    name = root.name
    sch = root / f"{name}.kicad_sch"
    if not sch.is_file():
        msg = f"schematic not found: {sch}"
        raise FileNotFoundError(msg)

    out = root / output_rel
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        kicad_cli,
        "sch",
        "export",
        "netlist",
        "--format",
        "spice",
        "--output",
        str(out),
        str(sch),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        msg = f"kicad-cli failed ({proc.returncode}): {err}"
        raise RuntimeError(msg)

    raw = out.read_text()
    out.write_text(strip_trailing_spice_end(raw))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Export KiCad schematic to sim/kicad_export.cir")
    parser.add_argument(
        "--board-dir",
        type=Path,
        required=True,
        help="Board root (directory containing <name>.kicad_sch and sim.yml)",
    )
    parser.add_argument(
        "--kicad-cli",
        default="kicad-cli",
        help="kicad-cli executable (default: kicad-cli on PATH)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sim/kicad_export.cir"),
        help="Path relative to board dir (default: sim/kicad_export.cir)",
    )
    args = parser.parse_args()

    try:
        written = export_spice_netlist(
            args.board_dir,
            kicad_cli=args.kicad_cli,
            output_rel=args.output,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e

    print(f"Wrote {written.relative_to(_repo_root())}")


if __name__ == "__main__":
    main()
