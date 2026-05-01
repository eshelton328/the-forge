#!/usr/bin/env python3
"""Run ngspice against a sim.yml + netlist; write report; exit non-zero on limit fail.

Supports either a single ``netlist:`` path or ``assembly:`` (main + optional includes + mandatory
``sim/overlay.cir``) per issue #45 — assembled deck is written to ``sim/assembled.cir`` before run.

Usage:
  python3 scripts/sim/run_sim.py --config sim/fixtures/rc_divider/sim.yml
  python3 scripts/sim/run_sim.py --config boards/tps63070-breakout/sim.yml --report /tmp/out.md
  python3 scripts/sim/run_sim.py --config boards/foo/sim.yml --write-baseline boards/foo/sim/spice_metrics_baseline.json --write-baseline-ref 'main@abc1234'

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

from scripts.sim.assemble import write_assembled_deck
from scripts.sim.baseline_metrics import (
    BASELINE_FILENAME,
    build_baseline_document,
    load_baseline_file,
    measure_key,
    parse_value_for_delta,
)
from scripts.sim.config import SimConfig, load_sim_config
from scripts.sim.measure_parse import (
    check_limits,
    parse_dc_op_node_voltage,
    parse_measure_value,
)
from scripts.sim.ngspice_runner import ngspice_binary, read_ngspice_version, run_batch
from scripts.sim.report_md import MeasureRowResult, render_report


def _read_kicad_export_toolchain(config_dir: Path) -> str | None:
    meta = config_dir / "sim" / "kicad_export_toolchain.txt"
    if not meta.is_file():
        return None
    text = meta.read_text().strip()
    return text or None


def _bounds_str(min_v: float | None, max_v: float | None) -> str:
    parts: list[str] = []
    if min_v is not None:
        parts.append(f"min {min_v}")
    if max_v is not None:
        parts.append(f"max {max_v}")
    return ", ".join(parts) if parts else "(unbounded)"


def baseline_display_relative(cfg_dir: Path, baseline_file: Path) -> str:
    """Prefer path relative to board root (`sim.yml` directory)."""
    try:
        return baseline_file.resolve().relative_to(cfg_dir.resolve()).as_posix()
    except ValueError:
        return baseline_file.name


def resolve_baseline_loading(
    cfg_dir: Path,
    explicit_file: Path | None,
    *,
    disabled: bool,
) -> tuple[dict[str, float], str | None, str] | None:
    """Return `(measures, doc_ref, display_path)` or `None` if comparison off."""

    def load_or_none(path: Path) -> tuple[dict[str, float], str | None, str] | None:
        if not path.is_file():
            return None
        resolved = path.resolve()
        loaded = load_baseline_file(resolved)
        if loaded is None:
            print(
                f"warning: ignoring invalid baseline JSON (delete or repair): {path}",
                file=sys.stderr,
            )
            return None
        measures, doc_ref = loaded
        return measures, doc_ref, baseline_display_relative(cfg_dir, resolved)

    if disabled:
        return None

    if explicit_file is not None:
        resolved = explicit_file.resolve()
        if not resolved.is_file():
            print(f"baseline error: file not found: {resolved}", file=sys.stderr)
            raise FileNotFoundError(str(resolved))
        loaded = load_baseline_file(resolved)
        if loaded is None:
            print(f"baseline error: invalid JSON in {resolved}", file=sys.stderr)
            raise ValueError("invalid baseline JSON")
        measures, doc_ref = loaded
        return measures, doc_ref, baseline_display_relative(cfg_dir, resolved)

    return load_or_none(cfg_dir / "sim" / BASELINE_FILENAME)


def run_flow(
    config_path: Path,
    report_path: Path | None,
    ngspice_override: str | None,
    *,
    baseline_explicit: Path | None,
    no_baseline: bool,
    write_baseline_path: Path | None,
    write_baseline_ref: str | None,
) -> int:
    try:
        cfg: SimConfig = load_sim_config(config_path)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    try:
        bl = resolve_baseline_loading(
            cfg.config_dir,
            baseline_explicit,
            disabled=no_baseline,
        )
    except FileNotFoundError:
        return 2
    except ValueError:
        return 2
    baseline_measures: dict[str, float] | None
    baseline_doc_ref: str | None
    baseline_rel: str | None
    if bl is None:
        baseline_measures = None
        baseline_doc_ref = None
        baseline_rel = None
    else:
        baseline_measures, baseline_doc_ref, baseline_rel = bl

    try:
        ngspice_exe = ngspice_binary(ngspice_override or os.environ.get("NGSPICE"))
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    if cfg.assembly is not None:
        write_assembled_deck(cfg.config_dir, cfg.assembly, cfg.netlist_path)

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

    kicad_line = _read_kicad_export_toolchain(cfg.config_dir)
    docker_image = os.environ.get("SIM_KICAD_DOCKER_IMAGE")
    report_text = render_report(
        config_path=config_path,
        scenario_results=tuple(rows),
        ngspice_version=ver.raw_line,
        netlist_path=cfg.netlist_path,
        simulator_returncode=sim.returncode,
        kicad_cli_version=kicad_line,
        kicad_docker_image=docker_image,
        baseline_measures=baseline_measures,
        baseline_relative_display=baseline_rel,
        baseline_doc_ref=baseline_doc_ref,
    )

    out = report_path or (config_path.parent / "spice-report.md")
    out.write_text(report_text)
    print(f"Wrote {out}")

    if write_baseline_path is not None:
        if any_fail:
            print(
                "warning: --write-baseline skipped because the run did not fully pass",
                file=sys.stderr,
            )
        else:
            measures_out: dict[str, float] = {}
            for row in rows:
                val = parse_value_for_delta(row.value_str)
                if val is None:
                    continue
                measures_out[measure_key(row.scenario_id, row.measure_id)] = val
            wb = write_baseline_path.resolve()
            wb.parent.mkdir(parents=True, exist_ok=True)
            wb.write_text(build_baseline_document(measures=measures_out, ref=write_baseline_ref))
            print(f"Wrote baseline {wb}")

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
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Explicit baseline JSON (must exist). Default: <board>/sim/spice_metrics_baseline.json if present.",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Disable baseline comparison even if sim/spice_metrics_baseline.json exists.",
    )
    parser.add_argument(
        "--write-baseline",
        type=Path,
        default=None,
        help="After a successful run, write captured numeric measures to this JSON path.",
    )
    parser.add_argument(
        "--write-baseline-ref",
        default=None,
        help="Optional ref string stored in JSON when using --write-baseline (e.g. main commit SHA).",
    )
    args = parser.parse_args()
    ng_exe = args.ngspice or os.environ.get("NGSPICE")
    code = run_flow(
        args.config.resolve(),
        args.report,
        ng_exe,
        baseline_explicit=args.baseline.resolve() if args.baseline else None,
        no_baseline=args.no_baseline,
        write_baseline_path=args.write_baseline.resolve() if args.write_baseline else None,
        write_baseline_ref=args.write_baseline_ref,
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
