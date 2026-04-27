#!/usr/bin/env python3
"""Regenerate the <!-- validation-summary --> section in each board's README.

Runs validate_board.py for every board that has a checks.yml, then replaces the
fenced region between the start/end markers in README.md.  Prints which files
were changed so the caller can decide whether to commit.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_board import validate_board  # noqa: E402

START_MARKER = "<!-- validation-summary-start -->"
END_MARKER = "<!-- validation-summary-end -->"


def _build_section(result: dict[str, object]) -> str:
    """Build the markdown block between the start/end markers."""
    lines = [
        START_MARKER,
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
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_readme(board_dir: Path) -> bool:
    """Return True if the README was changed."""
    readme = board_dir / "README.md"
    if not readme.exists():
        return False

    result = validate_board(board_dir)
    if result.get("skipped") or result.get("error"):
        return False

    section = _build_section(result)
    text = readme.read_text()

    start_idx = text.find(START_MARKER)
    end_idx = text.find(END_MARKER)
    if start_idx == -1 or end_idx == -1:
        return False

    new_text = text[:start_idx] + section + text[end_idx + len(END_MARKER) :]
    if new_text == text:
        return False

    readme.write_text(new_text)
    return True


def main() -> None:
    boards_dir = REPO_ROOT / "boards"
    changed: list[str] = []
    for board_dir in sorted(boards_dir.iterdir()):
        if not board_dir.is_dir():
            continue
        if not (board_dir / "checks.yml").exists():
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
