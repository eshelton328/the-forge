"""End-to-end run_sim smoke (skipped if ngspice not installed)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_SIM = REPO_ROOT / "scripts" / "sim" / "run_sim.py"
SMOKE_YML = REPO_ROOT / "sim" / "fixtures" / "rc_divider" / "sim.yml"
BOARD_SIM_YML = REPO_ROOT / "boards" / "tps63070-breakout" / "sim.yml"
SIM_ENV_PATH = "/opt/homebrew/bin:/usr/local/bin"


def _ngspice_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{SIM_ENV_PATH}:{env.get('PATH', '')}"
    return env


def _ngspice_available() -> bool:
    merged = f"{SIM_ENV_PATH}:{os.environ.get('PATH', '')}"
    return shutil.which("ngspice", path=merged) is not None


def _docker_available() -> bool:
    return shutil.which("docker") is not None


needs_ngspice = pytest.mark.skipif(
    not _ngspice_available(),
    reason="ngspice not found (brew install ngspice)",
)

needs_docker = pytest.mark.skipif(
    not _docker_available(),
    reason="docker not available (KiCad export for board sim)",
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
        env=_ngspice_env(),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    text = report.read_text()
    assert "PASS" in text
    assert "v_n2" in text
    assert "| KiCad CLI | `—` |" in text
    assert "| KiCad Docker image (CI) | `—` |" in text


@needs_ngspice
def test_run_sim_fails_when_limit_tight(tmp_path: Path) -> None:
    """Edit copied fixture with impossible max voltage — expect failure exit 1."""
    dest = tmp_path / "rc_divider"
    shutil.copytree(REPO_ROOT / "sim" / "fixtures" / "rc_divider", dest)
    sim_yml = dest / "sim.yml"
    sim_yml.write_text(sim_yml.read_text().replace("max: 5.01", "max: 1.0"))
    report = tmp_path / "bad.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUN_SIM),
            "--config",
            str(sim_yml),
            "--report",
            str(report),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=_ngspice_env(),
    )
    assert proc.returncode == 1, proc.stderr + proc.stdout


@needs_ngspice
@needs_docker
def test_run_sim_tps63070_assembly_passes(tmp_path: Path) -> None:
    mk = subprocess.run(
        ["make", "sim-export-board", "BOARD=tps63070-breakout"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=_ngspice_env(),
    )
    if mk.returncode != 0:
        err = (mk.stderr + mk.stdout).lower()
        if "docker" in err and (
            "permission denied" in err
            or "cannot connect" in err
            or "connection refused" in err
        ):
            pytest.skip("Docker daemon not reachable")
        pytest.fail(mk.stderr + mk.stdout)

    report = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(RUN_SIM),
            "--config",
            str(BOARD_SIM_YML),
            "--report",
            str(report),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=_ngspice_env(),
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    text = report.read_text()
    assert "PASS" in text
    assert "v_vin" in text
    assert "| Baseline file | `sim/spice_metrics_baseline.json` |" in text
    assert "SIM_BASELINE_COMPARE=true" in text
    assert "| KiCad CLI | `" in text
    toolchain = BOARD_SIM_YML.parent / "sim" / "kicad_export_toolchain.txt"
    assert toolchain.is_file()
    assert toolchain.read_text().strip() in text
    assembled = BOARD_SIM_YML.parent / "sim" / "assembled.cir"
    assert assembled.is_file()
    assert "overlay.cir" in assembled.read_text()
    assert "kicad_export.cir" in assembled.read_text()
