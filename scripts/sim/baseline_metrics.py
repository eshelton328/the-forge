"""Optional committed baseline metrics for Spice report deltas (GitHub issue #58)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASELINE_FILENAME = "spice_metrics_baseline.json"
EXPECTED_BASELINE_VERSION = 1


def measure_key(scenario_id: str, measure_id: str) -> str:
    """Stable key for scenario + measure pairs (baseline JSON and deltas)."""
    return f"{scenario_id}::{measure_id}"


def parse_value_for_delta(value_str: str) -> float | None:
    """Parse simulated value from report cell content; `(missing)` is not a number."""
    s = value_str.strip()
    if s == "(missing)":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_baseline_file(path: Path) -> tuple[dict[str, float], str | None] | None:
    """Load baseline measures from JSON. Returns `(measures, ref)` or `None` if invalid."""
    raw_text = path.read_text()
    return parse_baseline_text(raw_text)


def parse_baseline_text(raw_text: str) -> tuple[dict[str, float], str | None] | None:
    """Parse baseline JSON text. Prints nothing; callers log errors."""
    try:
        data: Any = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    ver = data.get("baseline_version")
    if ver != EXPECTED_BASELINE_VERSION:
        return None
    raw_measures = data.get("measures")
    if not isinstance(raw_measures, dict):
        return None
    measures: dict[str, float] = {}
    for k, v in raw_measures.items():
        if not isinstance(k, str) or not k.strip():
            return None
        if not isinstance(v, (int, float)):
            return None
        measures[k.strip()] = float(v)
    ref_val = data.get("ref")
    ref: str | None
    if ref_val is None:
        ref = None
    elif isinstance(ref_val, str):
        ref = ref_val.strip() or None
    else:
        return None
    return measures, ref


def build_baseline_document(
    *,
    measures: dict[str, float],
    ref: str | None,
) -> str:
    """Serialize baseline JSON (pretty, trailing newline)."""
    doc = {
        "baseline_version": EXPECTED_BASELINE_VERSION,
        "measures": {k: measures[k] for k in sorted(measures.keys())},
    }
    if ref is not None:
        doc["ref"] = ref
    return json.dumps(doc, indent=2, sort_keys=False) + "\n"


def format_delta_cell(current: float | None, baseline: float | None) -> tuple[str, str]:
    """Return `(baseline_cell, delta_cell)` for markdown table."""
    if baseline is None:
        return "—", "—"
    bs = f"{baseline:.6g}"
    if current is None:
        return bs, "—"
    delta = current - baseline
    if delta == 0.0:
        ds = "0"
    else:
        ds = f"{delta:+.6g}"
    return bs, ds
