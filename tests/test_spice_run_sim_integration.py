"""End-to-end run_sim smoke (skipped if ngspice not installed)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_SIM = REPO_ROOT / "scripts" / "sim" / "run_sim.py"
SMOKE_YML = REPO_ROOT / "sim" / "fixtures" / "rc_divider" / "sim.yml"


needs_ngspice = pytest.mark.skipif(
    shutil.which("ngspice") is None,
    reason="ngspice not on PATH",
)


@needs_ngspice
def test_run_sim_rc_fixture_passes(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUN_SIM),
            "--config",
            str(SMOKE_YML),
            "--report",
            str(report),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    text = report.read_text()
    assert "PASS" in text
    assert "v_n2" in text


@needs_ngspice
def test_run_sim_fails_when_limit_tight(tmp_path: Path) -> None:
    """Copy config with impossible max voltage — expect failure exit 1."""
    bad_yml = tmp_path / "bad.yml"
    raw = SMOKE_YML.read_text()
    bad_yml.write_text(raw.replace("max: 5.01", "max: 1.0"))
    report = tmp_path / "bad.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUN_SIM),
            "--config",
            str(bad_yml),
            "--report",
            str(report),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
