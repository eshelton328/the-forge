"""Machine-readable Spice metrics sidecar JSON (SIM_METRICS_SCHEMA_VERSION).

Written next to ``spice-report.md`` as ``<stem>.metrics.json``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from scripts.sim.baseline_metrics import measure_key, parse_value_for_delta
from scripts.sim.report_md import MeasureRowResult

SIM_METRICS_SCHEMA_VERSION = 1


def metrics_sidecar_path(report_md_path: Path) -> Path:
    """``spice-report.md`` → ``spice-report.metrics.json``."""
    stem = report_md_path.stem
    return report_md_path.with_name(f"{stem}.metrics.json")


def build_metrics_json_document(
    *,
    config_path: Path,
    netlist_path: Path,
    scenario_results: tuple[MeasureRowResult, ...],
    ngspice_version: str,
    simulator_returncode: int,
    kicad_cli_version: str | None,
    kicad_docker_image: str | None,
    baseline_compare: bool,
    baseline_relative_display: str | None,
    baseline_doc_ref: str | None,
    baseline_measures: Mapping[str, float] | None,
    waveform_pngs_rel: tuple[str, ...] = (),
) -> str:
    """Serialize metrics for CI or downstream parsers (no ngspice)."""
    overall_pass = all(r.passed for r in scenario_results)
    baseline_measures_frozen: Mapping[str, float] | None = baseline_measures

    measures_out: list[dict[str, object]] = []
    for row in scenario_results:
        key = measure_key(row.scenario_id, row.measure_id)
        baseline_val: float | None = None
        if baseline_compare and baseline_measures_frozen is not None:
            if key in baseline_measures_frozen:
                baseline_val = baseline_measures_frozen[key]

        value_numeric_raw = parse_value_for_delta(row.value_str)
        item: dict[str, object] = {
            "scenario_id": row.scenario_id,
            "measure_id": row.measure_id,
            "value_str": row.value_str,
            "value_numeric": value_numeric_raw,
            "passed": row.passed,
            "bounds_min": row.bounds_min,
            "bounds_max": row.bounds_max,
            "detail": row.detail,
        }
        if baseline_compare:
            item["baseline_numeric"] = baseline_val
            item["measure_key"] = key
        measures_out.append(item)

    doc: dict[str, object] = {
        "metrics_schema_version": SIM_METRICS_SCHEMA_VERSION,
        "pass": overall_pass,
        "exit_code_hint": 0 if overall_pass else 1,
        "paths": {
            "config": config_path.as_posix(),
            "netlist": netlist_path.as_posix(),
        },
        "toolchain": {
            "ngspice_version_line": ngspice_version,
            "kicad_cli_version_line": kicad_cli_version,
            "kicad_docker_image": kicad_docker_image,
            "simulator_exit_code": simulator_returncode,
            "baseline_compare_enabled": baseline_compare,
        },
        "baseline": (
            None
            if not baseline_compare
            else {
                "baseline_file_rel": baseline_relative_display,
                "doc_ref": baseline_doc_ref,
            }
        ),
        "measures": measures_out,
    }
    if waveform_pngs_rel:
        doc["waveform_pngs_rel"] = list(waveform_pngs_rel)

    return json.dumps(doc, indent=2, sort_keys=True) + "\n"
