"""Invoke ngspice batch and capture toolchain metadata."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NgspiceRunResult:
    """Outputs from ``ngspice -b`` on a netlist."""

    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True)
class NgspiceVersionInfo:
    """Version string parsed from ``ngspice --version``."""

    raw_line: str


def ngspice_binary(preferred: str | None = None) -> str:
    """Return path to ngspice or raise FileNotFoundError."""
    exe = preferred or shutil.which("ngspice")
    if not exe:
        raise FileNotFoundError("ngspice not found on PATH — install ngspice or set NGSPICE path")
    return exe


def read_ngspice_version(ngspice_exe: str) -> NgspiceVersionInfo:
    proc = subprocess.run(
        [ngspice_exe, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    line = proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else proc.stderr.strip()[:500]
    return NgspiceVersionInfo(raw_line=line or "(unknown)")


def run_batch(ngspice_exe: str, netlist_file: Path) -> NgspiceRunResult:
    """Run ngspice in batch mode (-b) against a standalone .cir file."""
    if not netlist_file.is_file():
        raise FileNotFoundError(netlist_file)
    proc = subprocess.run(
        [ngspice_exe, "-b", str(netlist_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    return NgspiceRunResult(
        stdout=proc.stdout,
        stderr=proc.stderr,
        returncode=proc.returncode,
    )
