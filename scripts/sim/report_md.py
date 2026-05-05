"""Render Markdown simulation report + machine-readable footer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from scripts.sim.baseline_metrics import format_delta_cell, measure_key, parse_value_for_delta


@dataclass(frozen=True)
class MeasureRowResult:
    """One measure row after evaluation."""

    measure_id: str
    scenario_id: str
    value_str: str
    bounds_str: str
    passed: bool
    detail: str | None
    bounds_min: float | None = None
    bounds_max: float | None = None
    display_title: str | None = None
    display_group: str | None = None


def _scenario_order(rows: tuple[MeasureRowResult, ...]) -> list[str]:
    ordered: list[str] = []
    for row in rows:
        if row.scenario_id not in ordered:
            ordered.append(row.scenario_id)
    return ordered


def _render_measures_grouped(
    *,
    scenario_results: tuple[MeasureRowResult, ...],
    use_baseline_compare: bool,
    baseline_measures: Mapping[str, float] | None,
) -> list[str]:
    lines: list[str] = []
    total = len(scenario_results)
    n_pass = sum(1 for r in scenario_results if r.passed)
    n_fail = total - n_pass
    lines.extend(
        [
            "## Executive summary",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Measures | {total} |",
            f"| Passed | {n_pass} |",
            f"| Failed | {n_fail} |",
            "",
        ],
    )
    if n_fail > 0:
        lines.append("**Failed checks:**")
        lines.append("")
        for row in scenario_results:
            if not row.passed:
                label = row.display_title or row.measure_id
                extra = f" — {row.detail}" if row.detail else ""
                lines.append(f"- `{row.scenario_id}` / **{label}**{extra}")
        lines.append("")

    lines.append("## Results by scenario")
    lines.append("")

    for sid in _scenario_order(scenario_results):
        lines.append(f"### `{sid}`")
        lines.append("")
        chunk = tuple(r for r in scenario_results if r.scenario_id == sid)
        if use_baseline_compare:
            assert baseline_measures is not None
            lines.extend(
                [
                    "| Measure | Value | Baseline | Δ | Bounds | Result |",
                    "| --- | --- | --- | --- | --- | --- |",
                ],
            )
            for row in chunk:
                status = "PASS" if row.passed else "FAIL"
                detail = f" {row.detail}" if row.detail else ""
                mk = measure_key(row.scenario_id, row.measure_id)
                baseline_val = baseline_measures.get(mk)
                current_val = parse_value_for_delta(row.value_str)
                base_cell, delta_cell = format_delta_cell(current_val, baseline_val)
                label = row.display_title or row.measure_id
                lines.append(
                    f"| {label} | {row.value_str} | {base_cell} | {delta_cell} | "
                    f"{row.bounds_str} | **{status}**{detail} |",
                )
        else:
            lines.extend(
                [
                    "| Measure | Value | Bounds | Result |",
                    "| --- | --- | --- | --- |",
                ],
            )
            for row in chunk:
                status = "PASS" if row.passed else "FAIL"
                detail = f" {row.detail}" if row.detail else ""
                label = row.display_title or row.measure_id
                lines.append(
                    f"| {label} | {row.value_str} | {row.bounds_str} | **{status}**{detail} |",
                )
        lines.append("")

    return lines


def render_report(
    *,
    config_path: Path,
    scenario_results: tuple[MeasureRowResult, ...],
    ngspice_version: str,
    netlist_path: Path,
    simulator_returncode: int,
    kicad_cli_version: str | None = None,
    kicad_docker_image: str | None = None,
    baseline_measures: Mapping[str, float] | None = None,
    baseline_relative_display: str | None = None,
    baseline_doc_ref: str | None = None,
) -> str:
    """Build markdown body."""
    use_baseline_compare = baseline_measures is not None
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
    ]
    if use_baseline_compare and baseline_relative_display:
        lines.append(f"| Baseline file | `{baseline_relative_display}` |")
        doc_ref_cell = baseline_doc_ref if baseline_doc_ref else "—"
        lines.append(f"| Baseline ref (documented) | `{doc_ref_cell}` |")
    lines.extend(
        _render_measures_grouped(
            scenario_results=scenario_results,
            use_baseline_compare=use_baseline_compare,
            baseline_measures=baseline_measures,
        ),
    )
    all_pass = all(r.passed for r in scenario_results)
    lines.extend(
        [
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
            f"SIM_BASELINE_COMPARE={'true' if use_baseline_compare else 'false'}",
            "```",
            "",
        ],
    )
    return "\n".join(lines) + "\n"
