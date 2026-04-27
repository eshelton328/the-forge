#!/usr/bin/env python3
"""Regenerate auto-generated sections in each board's README.md.

Handles three fenced regions (delimited by HTML comment markers):

  <!-- board-images-start --> … <!-- board-images-end -->
    Rebuilt from whichever image files exist in boards/<name>/docs/.

  <!-- drc-summary-start --> … <!-- drc-summary-end -->
    Rebuilt from ERC/DRC JSON reports in boards/<name>/docs/.

  <!-- validation-summary-start --> … <!-- validation-summary-end -->
    Rebuilt by running validate_board.py against the board.

Prints which files were changed so the caller can decide whether to commit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_board import validate_board  # noqa: E402

IMG_START = "<!-- board-images-start -->"
IMG_END = "<!-- board-images-end -->"
DRC_START = "<!-- drc-summary-start -->"
DRC_END = "<!-- drc-summary-end -->"
VAL_START = "<!-- validation-summary-start -->"
VAL_END = "<!-- validation-summary-end -->"


def _replace_section(text: str, start: str, end: str, replacement: str) -> str:
    """Replace the region between *start* and *end* markers (inclusive)."""
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1:
        return text
    return text[:s] + replacement + text[e + len(end) :]


def _build_images_section(board_name: str, docs_dir: Path) -> str:
    """Build the board-images markdown block from files in docs/."""
    lines = [
        IMG_START,
        "## Board Images",
        "",
        f"_Auto-generated on merge to main._",
        "",
    ]

    sch = docs_dir / "schematic.svg"
    extra_pages = sorted(docs_dir.glob("schematic-page*.svg"))
    if sch.exists():
        lines += ["### Schematic", "", "![Schematic](docs/schematic.svg)", ""]
        for page in extra_pages:
            lines.append(f"![{page.stem}](docs/{page.name})")
        if extra_pages:
            lines.append("")

    pcb_top = docs_dir / "pcb-top.png"
    pcb_bot = docs_dir / "pcb-bottom.png"
    if pcb_top.exists() or pcb_bot.exists():
        lines += ["### PCB Layout", ""]
        header = "| "
        divider = "| "
        images = "| "
        if pcb_top.exists():
            header += "Top | "
            divider += ":---: | "
            images += "![Top](docs/pcb-top.png) | "
        if pcb_bot.exists():
            header += "Bottom | "
            divider += ":---: | "
            images += "![Bottom](docs/pcb-bottom.png) | "
        lines += [header.rstrip(" | ") + " |",
                  divider.rstrip(" | ") + " |",
                  images.rstrip(" | ") + " |", ""]

    if not any((docs_dir / f).exists() for f in [
        "schematic.svg", "pcb-top.png", "pcb-bottom.png",
    ]):
        lines += ["_No images generated yet. Images are created on merge to main._", ""]

    lines.append(IMG_END)
    return "\n".join(lines)


def _parse_kicad_report(report_path: Path) -> dict[str, dict[str, int]]:
    """Parse a KiCad ERC/DRC JSON report and return violation counts by type and severity."""
    data = json.loads(report_path.read_text())
    counts: dict[str, dict[str, int]] = {}

    violations: list[dict[str, object]] = []
    for sheet in data.get("sheets", []):
        violations.extend(sheet.get("violations", []))  # type: ignore[arg-type]
    for v in data.get("violations", []):
        violations.append(v)  # type: ignore[arg-type]

    for v in violations:
        vtype = str(v.get("type", "unknown"))
        severity = str(v.get("severity", "warning"))
        if vtype not in counts:
            counts[vtype] = {"error": 0, "warning": 0}
        counts[vtype][severity] = counts[vtype].get(severity, 0) + 1

    return counts


def _severity_emoji(errors: int, warnings: int) -> str:
    if errors > 0:
        return "🔴"
    if warnings > 0:
        return "🟡"
    return "✅"


def _build_drc_section(board_name: str, docs_dir: Path) -> str:
    """Build the DRC/ERC summary markdown block from JSON reports."""
    lines = [
        DRC_START,
        "## Design Rule Checks",
        "",
        "_Auto-generated on merge to main._",
        "",
    ]

    erc_path = docs_dir / "erc.json"
    drc_path = docs_dir / "drc.json"

    if not erc_path.exists() and not drc_path.exists():
        lines += ["_No DRC/ERC reports available yet._", ""]
        lines.append(DRC_END)
        return "\n".join(lines)

    for label, path in [("ERC (Electrical Rules)", erc_path),
                         ("DRC (Design Rules)", drc_path)]:
        if not path.exists():
            continue
        counts = _parse_kicad_report(path)
        total_errors = sum(c.get("error", 0) for c in counts.values())
        total_warnings = sum(c.get("warning", 0) for c in counts.values())
        emoji = _severity_emoji(total_errors, total_warnings)

        if total_errors == 0 and total_warnings == 0:
            lines += [f"### {label} {emoji}", "", "No violations.", ""]
            continue

        summary_parts: list[str] = []
        if total_errors:
            summary_parts.append(f"{total_errors} error{'s' if total_errors != 1 else ''}")
        if total_warnings:
            summary_parts.append(f"{total_warnings} warning{'s' if total_warnings != 1 else ''}")
        lines += [f"### {label} {emoji} {', '.join(summary_parts)}", ""]
        lines += ["| Violation | Severity | Count |",
                   "|-----------|----------|-------|"]
        for vtype in sorted(counts):
            for severity in ("error", "warning"):
                count = counts[vtype].get(severity, 0)
                if count > 0:
                    sev_emoji = "🔴" if severity == "error" else "🟡"
                    lines.append(f"| {vtype} | {sev_emoji} {severity} | {count} |")
        lines.append("")

    lines.append(DRC_END)
    return "\n".join(lines)


def _build_validation_section(result: dict[str, object]) -> str:
    """Build the validation-summary markdown block."""
    lines = [
        VAL_START,
        "## Validation Summary",
        "",
        "_Run `make validate {board}` to regenerate locally._".format(
            board=result["board"]
        ),
        "",
        "| Check | Status | Details |",
        "|-------|--------|---------|",
    ]
    for check in result.get("checks", []):  # type: ignore[union-attr]
        status = check["status"]  # type: ignore[index]
        category = check["category"]  # type: ignore[index]
        summary = check.get("summary", "")  # type: ignore[union-attr]
        lines.append(f"| {category} | {status} | {summary} |")
    lines.append(VAL_END)
    return "\n".join(lines)


def update_readme(board_dir: Path) -> bool:
    """Return True if the README was changed."""
    readme = board_dir / "README.md"
    if not readme.exists():
        return False

    text = readme.read_text()
    original = text

    docs_dir = board_dir / "docs"
    if docs_dir.is_dir() and text.find(IMG_START) != -1:
        section = _build_images_section(board_dir.name, docs_dir)
        text = _replace_section(text, IMG_START, IMG_END, section)

    if docs_dir.is_dir() and text.find(DRC_START) != -1:
        section = _build_drc_section(board_dir.name, docs_dir)
        text = _replace_section(text, DRC_START, DRC_END, section)

    if (board_dir / "checks.yml").exists() and text.find(VAL_START) != -1:
        result = validate_board(board_dir)
        if not result.get("skipped") and not result.get("error"):
            section = _build_validation_section(result)
            text = _replace_section(text, VAL_START, VAL_END, section)

    if text == original:
        return False

    readme.write_text(text)
    return True


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("board", nargs="?", default=None,
                        help="Single board name to update (default: all boards)")
    args = parser.parse_args()

    boards_dir = REPO_ROOT / "boards"
    if args.board:
        candidates = [boards_dir / args.board]
    else:
        candidates = sorted(boards_dir.iterdir())

    changed: list[str] = []
    for board_dir in candidates:
        if not board_dir.is_dir():
            continue
        if not (board_dir / "README.md").exists():
            continue
        if update_readme(board_dir):
            changed.append(board_dir.name)
            print(f"updated: boards/{board_dir.name}/README.md")
        else:
            print(f"unchanged: boards/{board_dir.name}/README.md")

    if changed:
        print(f"\n{len(changed)} README(s) updated.")
    else:
        print("\nAll READMEs already up to date.")


if __name__ == "__main__":
    main()
