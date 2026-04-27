"""Pytest wrapper for board validation.

Discovers boards with a checks.yml and runs validate_board against each.
CI invokes this via: pytest tests/test_board_checks.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BOARDS_DIR = REPO_ROOT / "boards"
VALIDATOR = REPO_ROOT / "scripts" / "validate_board.py"


def _boards_with_checks() -> list[str]:
    """Return board names that have a checks.yml file."""
    boards: list[str] = []
    if not BOARDS_DIR.is_dir():
        return boards
    for board_dir in sorted(BOARDS_DIR.iterdir()):
        if board_dir.is_dir() and (board_dir / "checks.yml").exists():
            boards.append(board_dir.name)
    return boards


BOARDS = _boards_with_checks()

if not BOARDS:
    pytest.skip("No boards with checks.yml found", allow_module_level=True)


@pytest.fixture(scope="module")
def validation_results() -> dict[str, dict[str, object]]:
    """Run the validator once per board and cache results for assertions."""
    results: dict[str, dict[str, object]] = {}
    for board in BOARDS:
        board_dir = BOARDS_DIR / board
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), str(board_dir)],
            capture_output=True,
            text=True,
        )
        try:
            results[board] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            results[board] = {
                "board": board,
                "error": f"validator returned non-JSON (exit {proc.returncode}): {proc.stderr}",
                "passed": False,
            }
    return results


@pytest.mark.parametrize("board", BOARDS)
def test_board_validation_passes(
    board: str,
    validation_results: dict[str, dict[str, object]],
) -> None:
    result = validation_results[board]
    if result.get("error"):
        pytest.fail(f"{board}: {result['error']}")
    if result.get("skipped"):
        pytest.skip(f"{board}: {result.get('reason', 'skipped')}")

    failing: list[str] = []
    for check in result.get("checks", []):
        if check["status"] != "pass":  # type: ignore[index]
            for v in check.get("violations", []):  # type: ignore[union-attr]
                failing.append(f"  [{check['category']}] {v['message']}")  # type: ignore[index]

    if failing:
        pytest.fail(f"{board}: {len(failing)} violation(s):\n" + "\n".join(failing))


@pytest.mark.parametrize("board", BOARDS)
def test_board_output_json(
    board: str,
    validation_results: dict[str, dict[str, object]],
) -> None:
    """Verify the validator produces well-formed JSON with required keys."""
    result = validation_results[board]
    assert "board" in result, "missing 'board' key"
    if not result.get("skipped"):
        assert "checks" in result, "missing 'checks' key"
        assert "passed" in result, "missing 'passed' key"
