#!/usr/bin/env python3
"""Export a board schematic to ``sim/kicad_export.cir`` for SPICE assembly (issue #46).

Runs ``kicad-cli sch export netlist`` on ``<board>/<board>.kicad_sch``.
Subcircuits and ``X`` instances require ``--format spicemodel`` so KiCad emits device lines
(and optional ``Sim.*`` mapping). KiCad wraps the deck in ``.subckt <board>/`` … ``.ends`` and may
``.include`` vendor libraries referenced on symbols; ``postprocess_spicemodel_flat()`` removes that
wrapper and drops embedded vendor ``.include`` lines so ``assemble.py`` can own include order relative
to ``sim/``.
Plain ``spice`` format is retained for schematic-only/passive stubs (no simulator models).

Typical CI / local Docker (same image as ``.github/workflows/pr-checks.yml``)::

    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/workspace/.kicad-ci-home \\
      -v "$PWD:/workspace" -w /workspace "$KICAD_IMAGE" bash -c '
        source /workspace/scripts/ci/setup-kicad-env.sh &&
        python3 scripts/sim/export_kicad_spice.py --board-dir boards/my-board
      '
"""

from __future__ import annotations

import argparse
import re
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


def postprocess_spicemodel_flat(raw: str, *, board_slug: str) -> str:
    """Flatten KiCad ``spicemodel`` output for inclusion as ``assembly.main``.

    Drops the outer ``.subckt <board>`` / ``.ends`` wrapper and removes embedded ``.include`` lines
    for TI ``TPS63070_TRANS.LIB`` so ``assembly.includes`` loads the model once with paths relative
    to ``sim/``.
    """
    lines_out: list[str] = []
    subckt_pat = re.compile(r"^\.subckt\s+(\S+)\s*$", re.I)
    for line in raw.splitlines():
        stripped = line.strip()
        m_sub = subckt_pat.match(stripped)
        if m_sub and m_sub.group(1).casefold() == board_slug.casefold():
            continue
        if stripped.upper() == ".ENDS":
            continue
        low = stripped.lower()
        if low.startswith(".include") and "tps63070_trans.lib" in low:
            continue
        lines_out.append(line)

    body = "\n".join(lines_out).strip() + "\n"
    return strip_trailing_spice_end(body)


def export_spice_netlist(
    board_dir: Path,
    *,
    kicad_cli: str,
    output_rel: Path = Path("sim/kicad_export.cir"),
    netlist_format: str = "spicemodel",
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

    fmt = netlist_format.strip().lower()
    if fmt not in ("spicemodel", "spice"):
        msg = f"netlist_format must be spicemodel or spice, got {netlist_format!r}"
        raise ValueError(msg)

    cmd = [
        kicad_cli,
        "sch",
        "export",
        "netlist",
        "--format",
        fmt,
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
    if fmt == "spicemodel":
        out.write_text(postprocess_spicemodel_flat(raw, board_slug=name))
    else:
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
    parser.add_argument(
        "--netlist-format",
        choices=("spicemodel", "spice"),
        default="spicemodel",
        help="KiCad netlist flavor (default: spicemodel for Sim.* / X lines)",
    )
    args = parser.parse_args()

    try:
        written = export_spice_netlist(
            args.board_dir,
            kicad_cli=args.kicad_cli,
            output_rel=args.output,
            netlist_format=args.netlist_format,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e

    print(f"Wrote {written.relative_to(_repo_root())}")


if __name__ == "__main__":
    main()
