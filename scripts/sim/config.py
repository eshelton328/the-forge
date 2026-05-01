"""Load and validate sim.yml for the fixture runner (minimal schema, v1)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.sim.assemble import ASSEMBLED_REL, OVERLAY_REL, AssemblySpec
from scripts.sim.plot_extractions import validate_plot_png_basename, validate_plot_signal


@dataclass(frozen=True)
class MeasureSpec:
    """One named measure with optional bounds."""

    identifier: str
    min_value: float | None
    max_value: float | None
    op_node: str | None


@dataclass(frozen=True)
class PlotSpec:
    """Optional waveform PNG emitted under ``boards/<name>/sim/plots/`` (#59)."""

    png_basename: str
    signal: str


@dataclass(frozen=True)
class ScenarioSpec:
    """A named group of measures (one ngspice invocation per scenario v1)."""

    identifier: str
    measures: tuple[MeasureSpec, ...]


@dataclass(frozen=True)
class SimConfig:
    """Validated top-level config."""

    spec_version: int
    spice_engine: str
    netlist_path: Path
    config_dir: Path
    scenarios: tuple[ScenarioSpec, ...]
    assembly: AssemblySpec | None
    plots: tuple[PlotSpec, ...]


def _require_mapping(data: Any, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} must be a mapping")
    return data


def _load_measures(raw: Any, context: str) -> tuple[MeasureSpec, ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{context} must be a non-empty list")
    measures: list[MeasureSpec] = []
    for i, item in enumerate(raw):
        m = _require_mapping(item, f"{context}[{i}]")
        ident = m.get("id")
        if not isinstance(ident, str) or not ident.strip():
            raise ValueError(f"{context}[{i}] requires non-empty string id")
        min_v = m.get("min")
        max_v = m.get("max")
        min_f: float | None = float(min_v) if min_v is not None else None
        max_f: float | None = float(max_v) if max_v is not None else None
        if min_f is None and max_f is None:
            raise ValueError(f"{context}[{i}] needs at least one of min / max")
        raw_op = m.get("op_node")
        op_node_val: str | None = (
            raw_op.strip()
            if isinstance(raw_op, str) and raw_op.strip()
            else None
        )
        measures.append(
            MeasureSpec(
                identifier=ident.strip(),
                min_value=min_f,
                max_value=max_f,
                op_node=op_node_val,
            ),
        )
    return tuple(measures)


def _load_plots(root: dict[str, Any], context: str) -> tuple[PlotSpec, ...]:
    raw = root.get("plots")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{context}plots must be a list when present")
    out: list[PlotSpec] = []
    seen_names: set[str] = set()
    for i, item in enumerate(raw):
        m = _require_mapping(item, f"{context}plots[{i}]")
        fname = m.get("file")
        sig = m.get("signal")
        if not isinstance(fname, str):
            raise ValueError(f"{context}plots[{i}] requires string file")
        if not isinstance(sig, str):
            raise ValueError(f"{context}plots[{i}] requires string signal")
        png = validate_plot_png_basename(fname)
        if png in seen_names:
            raise ValueError(f"duplicate plots file: {png}")
        seen_names.add(png)
        out.append(
            PlotSpec(
                png_basename=png,
                signal=validate_plot_signal(sig),
            ),
        )
    return tuple(out)


def _parse_assembly(root: dict[str, Any], cfg_dir: Path) -> AssemblySpec:
    asm = root.get("assembly")
    if asm is None:
        raise ValueError("assembly block missing")
    am = _require_mapping(asm, "assembly")
    main_raw = am.get("main")
    if not isinstance(main_raw, str) or not main_raw.strip():
        raise ValueError("assembly.main must be a non-empty string path relative to sim.yml")
    inc_raw = am.get("includes", [])
    if inc_raw is None:
        inc_raw = []
    if not isinstance(inc_raw, list):
        raise ValueError("assembly.includes must be a list when present")
    includes_out: list[str] = []
    for i, item in enumerate(inc_raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"assembly.includes[{i}] must be a non-empty string")
        includes_out.append(item.strip())
    main_path = (cfg_dir / main_raw.strip()).resolve()
    if not main_path.is_file():
        raise ValueError(f"assembly.main not found: {main_path}")
    overlay_path = (cfg_dir / OVERLAY_REL).resolve()
    if not overlay_path.is_file():
        raise ValueError(f"overlay required at {overlay_path}")
    for i, rel in enumerate(includes_out):
        p = (cfg_dir / rel).resolve()
        if not p.is_file():
            raise ValueError(f"assembly.includes[{i}] not found: {p}")
    return AssemblySpec(main_rel=main_raw.strip(), includes_rel=tuple(includes_out))


def load_sim_config(config_path: Path) -> SimConfig:
    """Parse sim.yml next to fixtures or boards."""
    raw = yaml.safe_load(config_path.read_text())
    root = _require_mapping(raw, "root")
    spec_ver = root.get("spec_version")
    if spec_ver != 1:
        raise ValueError("spec_version must be 1 for this runner")

    engine = root.get("spice_engine")
    if engine != "ngspice":
        raise ValueError("spice_engine must be 'ngspice' for now")

    cfg_dir = config_path.parent.resolve()
    net_rel = root.get("netlist")
    has_net = isinstance(net_rel, str) and bool(net_rel.strip())
    has_asm = root.get("assembly") is not None

    if has_net and has_asm:
        raise ValueError("use either netlist or assembly, not both")
    if not has_net and not has_asm:
        raise ValueError("need netlist (single deck) or assembly (include chain)")

    assembly_spec: AssemblySpec | None = None
    net_path: Path
    if has_asm:
        assembly_spec = _parse_assembly(root, cfg_dir)
        net_path = (cfg_dir / ASSEMBLED_REL).resolve()
    else:
        netlist_str = root.get("netlist")
        if not isinstance(netlist_str, str) or not netlist_str.strip():
            raise ValueError("netlist must be a non-empty string path relative to the config file")
        net_path = (cfg_dir / netlist_str.strip()).resolve()
        if not net_path.is_file():
            raise ValueError(f"netlist not found: {net_path}")

    scenarios_raw = root.get("scenarios")
    if not isinstance(scenarios_raw, list) or not scenarios_raw:
        raise ValueError("scenarios must be a non-empty list")

    scenarios_out: list[ScenarioSpec] = []
    measure_ids: set[str] = set()
    for i, s in enumerate(scenarios_raw):
        sm = _require_mapping(s, f"scenarios[{i}]")
        sid = sm.get("id")
        if not isinstance(sid, str) or not sid.strip():
            raise ValueError(f"scenarios[{i}] requires non-empty string id")
        measures = _load_measures(sm.get("measures"), f"scenarios[{i}].measures")
        for mm in measures:
            if mm.identifier in measure_ids:
                raise ValueError(f"duplicate measure id across scenarios: {mm.identifier}")
            measure_ids.add(mm.identifier)
        scenarios_out.append(
            ScenarioSpec(identifier=sid.strip(), measures=measures),
        )

    plots_out = _load_plots(root, "root.")

    return SimConfig(
        spec_version=int(spec_ver),
        spice_engine=str(engine),
        netlist_path=net_path,
        config_dir=cfg_dir,
        scenarios=tuple(scenarios_out),
        assembly=assembly_spec,
        plots=plots_out,
    )
