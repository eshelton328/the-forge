import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize("exit_code", [0, 5])
@pytest.mark.parametrize("persistent_rules", [True, False])
def test_fab_check_restores_board_rules(tmp_path: Path, exit_code: int, persistent_rules: bool) -> None:
    board = tmp_path / "board"
    board.mkdir()
    (board / "board.kicad_pcb").write_text("test PCB")
    (board / "board.yml").write_text("fab_targets:\n  - jlcpcb-4layer-advanced\n")
    rules = board / "board.kicad_dru"
    original = '(version 1)\n(rule "Persistent board rule" (constraint disallow via))\n'
    if persistent_rules:
        rules.write_text(original)
    executable = tmp_path / "kicad-cli"
    executable.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
rules = pathlib.Path(sys.argv[-1]).with_suffix('.kicad_dru').read_text()
assert rules.count('(version 1)') == 1
assert 'JLCPCB' in rules
assert ('Persistent board rule' in rules) == (os.environ['EXPECT_BOARD_RULES'] == '1')
sys.exit(int(os.environ['MOCK_EXIT']))
''')
    executable.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"], MOCK_EXIT=str(exit_code), EXPECT_BOARD_RULES=str(int(persistent_rules)))
    script = Path(__file__).resolve().parents[1] / "scripts/run-drc-all-fabs.sh"
    run = subprocess.run(["bash", str(script), str(board)], env=env, capture_output=True, text=True)
    assert run.returncode == (0 if exit_code == 0 else 1), run.stdout + run.stderr
    if persistent_rules:
        assert rules.read_text() == original
    else:
        assert not rules.exists()
