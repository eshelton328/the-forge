#!/usr/bin/env python3
"""Regenerate auto-generated sections in each board's README.md.

Handles three fenced regions (delimited by HTML comment markers):

  <!-- board-images-start --> … <!-- board-images-end -->
    Rebuilt from whichever image files exist in boards/<name>/docs/.

  <!-- drc-summary-start --> … <!-- drc-summary-end -->
    Rebuilt from ERC/DRC JSON in boards/<name>/docs/. Format matches the PR
    comment from scripts/ci/compose-kicad-report-comment.sh (summary table +
    nested details, all violations listed).

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


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def _erc_violations(data: dict[str, object]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for sheet in data.get("sheets", []):
        if not isinstance(sheet, dict):
            continue
        out.extend(sheet.get("violations", []))  # type: ignore[arg-type]
    return out


def _drc_violation_lists(data: dict[str, object]) -> tuple[
        list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    v = [x for x in (data.get("violations") or []) if isinstance(x, dict)]
    s = [x for x in (data.get("schematic_parity") or []) if isinstance(x, dict)]
    u = [x for x in (data.get("unconnected_items") or []) if isinstance(x, dict)]
    return (v, s, u)  # type: ignore[return-value]


def _count_severity(violations: list[dict[str, object]]) -> tuple[int, int]:
    errors = sum(1 for v in violations if v.get("severity") == "error")
    warnings = sum(1 for v in violations if v.get("severity") == "warning")
    return (errors, warnings)


def _format_counts(errors: int, warnings: int) -> str:
    """Match scripts/ci/compose-kicad-report-comment.sh format_counts()."""
    parts: list[str] = []
    if errors > 0:
        parts.append(
            f"🔴 {errors} error{'' if errors == 1 else 's'}",
        )
    if warnings > 0:
        parts.append(
            f"🟡 {warnings} warning{'' if warnings == 1 else 's'}",
        )
    if not parts:
        return "✅"
    return ", ".join(parts)


def _icon_for_severity(severity: str) -> str:
    if severity == "error":
        return "🔴"
    if severity == "warning":
        return "🟡"
    return "⚪"


def _grouped_type_blocks(violations: list[dict[str, object]]) -> list[str]:
    """Same grouping as compose-kicad-report-comment.sh print_grouped (all items)."""
    if not violations:
        return []
    from collections import defaultdict

    by_type: dict[str, list[dict[str, object]]] = defaultdict(list)
    for v in violations:
        t = str(v.get("type", "unknown"))
        by_type[t].append(v)

    def sort_key(t: str) -> tuple:
        g = by_type[t]
        s0 = str(g[0].get("severity", "warning"))
        err_first = 0 if s0 == "error" else 1
        return (err_first, t)

    out: list[str] = []
    for t in sorted(by_type, key=sort_key):
        group = by_type[t]
        s0 = str(group[0].get("severity", "warning"))
        icon = _icon_for_severity(s0)
        n = len(group)
        if n == 1:
            w = "error" if s0 == "error" else "warning" if s0 == "warning" else s0
        else:
            w = "errors" if s0 == "error" else "warnings" if s0 == "warning" else f"{s0}s"
        out += [
            "<details>",
            f"<summary>{icon} <b><code>{t}</code></b> — {n} {w}</summary>",
            "",
        ]
        out.append(str(group[0].get("description", "")))
        for v in group:
            items = v.get("items")
            if isinstance(items, list) and len(items) > 0:
                parts = " / ".join(
                    f"`{str(it.get('description', '(no details)'))}`"
                    for it in items
                    if isinstance(it, dict)
                )
                if parts:
                    out.append(f"- {parts}")
            else:
                out.append(
                    f"- `{str(v.get('description', '(no details)'))}`",
                )
        out += ["", "</details>", ""]
    return out


def _blockquote_block(lines: list[str]) -> list[str]:
    return [f"> {line}" if line else ">" for line in lines]


def _outer_details(title: str, counts: str, body_lines: list[str]) -> list[str]:
    bq = _blockquote_block(body_lines)
    return [
        "<details>",
        f"<summary><strong>{title}</strong> — {counts}</summary>",
        "",
        *bq,
        "</details>",
        "",
    ]


def _build_drc_section(board_name: str, docs_dir: Path) -> str:
    """Build DRC/ERC block matching PR comment format (compose-kicad-report-comment.sh)."""
    lines: list[str] = [
        DRC_START,
        "## Design Rule Checks",
        "",
        "_Same layout as the KiCad check summary on pull requests. Auto-generated on merge to main._",
        "",
    ]

    erc_path = docs_dir / "erc.json"
    drc_path = docs_dir / "drc.json"

    if not erc_path.exists() and not drc_path.exists():
        lines += ["_No DRC/ERC reports available yet._", "", DRC_END]
        return "\n".join(lines)

    # Summary table: | Check | Result |  (align with PR)
    row_erc: str | None = None
    row_drc: str | None = None
    body_parts: list[str] = []

    if erc_path.exists():
        data = _load_json(erc_path)
        ev = _erc_violations(data)
        e_ct, w_ct = _count_severity(ev)
        total = e_ct + w_ct
        row_erc = _format_counts(e_ct, w_ct)
        if total > 0:
            inner = _grouped_type_blocks(ev)
            body_parts.extend(
                _outer_details("ERC", row_erc, inner),
            )

    if drc_path.exists():
        ddata = _load_json(drc_path)
        dv, ds, du = _drc_violation_lists(ddata)
        allv = list(dv) + list(ds) + list(du)
        e_ct, w_ct = _count_severity(allv)
        total = e_ct + w_ct
        row_drc = _format_counts(e_ct, w_ct)
        if total > 0:
            inner2: list[str] = []
            n_v, n_s, n_u = len(dv), len(ds), len(du)
            if n_v > 0:
                inner2.append(f"**Violations** ({n_v})")
                inner2.append("")
                inner2.extend(_grouped_type_blocks(dv))
            if n_s > 0:
                inner2.append(f"**Schematic parity** ({n_s})")
                inner2.append("")
                inner2.extend(_grouped_type_blocks(ds))
            if n_u > 0:
                inner2.append(f"**Unconnected items** ({n_u})")
                inner2.append("")
                inner2.extend(_grouped_type_blocks(du))
            body_parts.extend(
                _outer_details("DRC", row_drc, inner2),
            )

    if row_erc is not None or row_drc is not None:
        lines += [
            "| Check | Result |",
            "|:------|:-------|",
        ]
        if row_erc is not None:
            lines.append(f"| ERC | {row_erc} |")
        if row_drc is not None:
            lines.append(f"| DRC | {row_drc} |")
        lines.append("")

    lines.extend(body_parts)

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
