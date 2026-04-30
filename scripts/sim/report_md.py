"""Render Markdown simulation report + machine-readable footer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MeasureRowResult:
    """One measure row after evaluation."""

    measure_id: str
    scenario_id: str
    value_str: str
    bounds_str: str
    passed: bool
    detail: str | None


def render_report(
    *,
    config_path: Path,
    scenario_results: tuple[MeasureRowResult, ...],
    ngspice_version: str,
    netlist_path: Path,
    simulator_returncode: int,
    kicad_cli_version: str | None = None,
    kicad_docker_image: str | None = None,
) -> str:
    """Build markdown body."""
    kicad_cli_cell = kicad_cli_version if kicad_cli_version else "—"
    kicad_img_cell = kicad_docker_image if kicad_docker_image else "—"
    lines: list[str] = [
        "# Spice simulation report",
        "",
        "## Run metadata",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Config | `{config_path}` |",
        f"| Netlist | `{netlist_path}` |",
        f"| KiCad CLI | `{kicad_cli_cell}` |",
        f"| KiCad Docker image (CI) | `{kicad_img_cell}` |",
        f"| ngspice | `{ngspice_version}` |",
        f"| Simulator exit | {simulator_returncode} |",
        "",
        "## Measures",
        "",
        "| Scenario | Measure | Value | Bounds | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in scenario_results:
        status = "PASS" if row.passed else "FAIL"
        detail = f" {row.detail}" if row.detail else ""
        lines.append(
            f"| {row.scenario_id} | {row.measure_id} | {row.value_str} | {row.bounds_str} | **{status}**{detail} |",
        )
    all_pass = all(r.passed for r in scenario_results)
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"**Overall:** {'PASS' if all_pass else 'FAIL'}",
            "",
            "---",
            "",
            "```text",
            "SIM_REPORT_VERSION=1",
            f"PASS={'true' if all_pass else 'false'}",
            f"EXIT_CODE={0 if all_pass else 1}",
            "```",
            "",
        ],
    )
    return "\n".join(lines) + "\n"
