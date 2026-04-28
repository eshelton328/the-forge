"""Load and validate sim.yml for the fixture runner (minimal schema, v1)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class MeasureSpec:
    """One named measure with optional bounds."""

    identifier: str
    min_value: float | None
    max_value: float | None


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
        measures.append(MeasureSpec(identifier=ident.strip(), min_value=min_f, max_value=max_f))
    return tuple(measures)


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

    net_rel = root.get("netlist")
    if not isinstance(net_rel, str) or not net_rel.strip():
        raise ValueError("netlist must be a non-empty string path relative to the config file")
    cfg_dir = config_path.parent.resolve()
    net_path = (cfg_dir / net_rel.strip()).resolve()
    if not net_path.exists():
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

    return SimConfig(
        spec_version=int(spec_ver),
        spice_engine=str(engine),
        netlist_path=net_path,
        config_dir=cfg_dir,
        scenarios=tuple(scenarios_out),
    )
