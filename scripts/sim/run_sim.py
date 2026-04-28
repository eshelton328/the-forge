#!/usr/bin/env python3
"""Run ngspice against a sim.yml + netlist; write report; exit non-zero on limit fail.

Issue #44 — fixture-backed loop (no KiCad).

Usage:
  python3 scripts/sim/run_sim.py --config sim/fixtures/rc_divider/sim.yml
  python3 scripts/sim/run_sim.py --config sim/fixtures/rc_divider/sim.yml --report /tmp/out.md

Exit codes: 0 = all limits pass, 1 = limit fail or simulator error, 2 = usage/config error.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import yaml

from scripts.sim.config import SimConfig, load_sim_config
from scripts.sim.measure_parse import (
    check_limits,
    parse_dc_op_node_voltage,
    parse_measure_value,
)
from scripts.sim.ngspice_runner import ngspice_binary, read_ngspice_version, run_batch
from scripts.sim.report_md import MeasureRowResult, render_report


def _bounds_str(min_v: float | None, max_v: float | None) -> str:
    parts: list[str] = []
    if min_v is not None:
        parts.append(f"min {min_v}")
    if max_v is not None:
        parts.append(f"max {max_v}")
    return ", ".join(parts) if parts else "(unbounded)"


def run_flow(config_path: Path, report_path: Path | None, ngspice_override: str | None) -> int:
    try:
        cfg: SimConfig = load_sim_config(config_path)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    try:
        ngspice_exe = ngspice_binary(ngspice_override or os.environ.get("NGSPICE"))
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    ver = read_ngspice_version(ngspice_exe)
    sim = run_batch(ngspice_exe, cfg.netlist_path)
    combined = sim.stdout + "\n" + sim.stderr

    rows: list[MeasureRowResult] = []
    any_fail = False

    for scenario in cfg.scenarios:
        for m in scenario.measures:
            if m.op_node is not None:
                raw_val = parse_dc_op_node_voltage(combined, m.op_node)
                missing_reason = (
                    f"DC OP voltage V({m.op_node}) not found in ngspice output"
                    if raw_val is None
                    else None
                )
            else:
                raw_val = parse_measure_value(combined, m.identifier)
                missing_reason = (
                    "measure line not found in ngspice output"
                    if raw_val is None
                    else None
                )
            if raw_val is None:
                rows.append(
                    MeasureRowResult(
                        measure_id=m.identifier,
                        scenario_id=scenario.identifier,
                        value_str="(missing)",
                        bounds_str=_bounds_str(m.min_value, m.max_value),
                        passed=False,
                        detail=missing_reason,
                    ),
                )
                any_fail = True
                continue
            ok, reason = check_limits(raw_val, m.min_value, m.max_value)
            if not ok:
                any_fail = True
            rows.append(
                MeasureRowResult(
                    measure_id=m.identifier,
                    scenario_id=scenario.identifier,
                    value_str=f"{raw_val:.6g}",
                    bounds_str=_bounds_str(m.min_value, m.max_value),
                    passed=ok,
                    detail=reason,
                ),
            )

    if sim.returncode != 0:
        any_fail = True

    report_text = render_report(
        config_path=config_path,
        scenario_results=tuple(rows),
        ngspice_version=ver.raw_line,
        netlist_path=cfg.netlist_path,
        simulator_returncode=sim.returncode,
    )

    out = report_path or (config_path.parent / "spice-report.md")
    out.write_text(report_text)
    print(f"Wrote {out}")

    if any_fail:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ngspice batch from sim.yml (fixture runner).")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to sim.yml",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Output markdown path (default: <config-dir>/spice-report.md)",
    )
    parser.add_argument(
        "--ngspice",
        default=None,
        help="Path to ngspice binary (default: PATH / NGSPICE env)",
    )
    args = parser.parse_args()
    ng_exe = args.ngspice or os.environ.get("NGSPICE")
    code = run_flow(args.config.resolve(), args.report, ng_exe)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
