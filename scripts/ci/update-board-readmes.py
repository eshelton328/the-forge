#!/usr/bin/env python3
"""Regenerate auto-generated sections in each board's README.md.

Handles two fenced regions (delimited by HTML comment markers):

  <!-- board-images-start --> … <!-- board-images-end -->
    Rebuilt from whichever image files exist in boards/<name>/docs/.

  <!-- validation-summary-start --> … <!-- validation-summary-end -->
    Rebuilt by running validate_board.py against the board.

Prints which files were changed so the caller can decide whether to commit.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_board import validate_board  # noqa: E402

IMG_START = "<!-- board-images-start -->"
IMG_END = "<!-- board-images-end -->"
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

    fcu = docs_dir / "pcb-F_Cu.svg"
    bcu = docs_dir / "pcb-B_Cu.svg"
    allsvg = docs_dir / "pcb-all-layers.svg"
    if fcu.exists() or bcu.exists() or allsvg.exists():
        lines += ["### PCB Layout", ""]
        header = "| "
        divider = "| "
        images = "| "
        if fcu.exists():
            header += "Front Copper | "
            divider += ":---: | "
            images += "![F.Cu](docs/pcb-F_Cu.svg) | "
        if bcu.exists():
            header += "Back Copper | "
            divider += ":---: | "
            images += "![B.Cu](docs/pcb-B_Cu.svg) | "
        if allsvg.exists():
            header += "All Layers | "
            divider += ":---: | "
            images += "![All](docs/pcb-all-layers.svg) | "
        lines += [header.rstrip(" | ") + " |",
                  divider.rstrip(" | ") + " |",
                  images.rstrip(" | ") + " |", ""]

    front_3d = docs_dir / "3d-front.png"
    back_3d = docs_dir / "3d-back.png"
    if front_3d.exists() or back_3d.exists():
        lines += ["### 3D Render", ""]
        header = "| "
        divider = "| "
        images = "| "
        if front_3d.exists():
            header += "Front | "
            divider += ":---: | "
            images += "![Front](docs/3d-front.png) | "
        if back_3d.exists():
            header += "Back | "
            divider += ":---: | "
            images += "![Back](docs/3d-back.png) | "
        lines += [header.rstrip(" | ") + " |",
                  divider.rstrip(" | ") + " |",
                  images.rstrip(" | ") + " |", ""]

    if not any((docs_dir / f).exists() for f in [
        "schematic.svg", "pcb-F_Cu.svg", "pcb-B_Cu.svg",
        "pcb-all-layers.svg", "3d-front.png", "3d-back.png",
    ]):
        lines += ["_No images generated yet. Images are created on merge to main._", ""]

    lines.append(IMG_END)
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
    boards_dir = REPO_ROOT / "boards"
    changed: list[str] = []
    for board_dir in sorted(boards_dir.iterdir()):
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
