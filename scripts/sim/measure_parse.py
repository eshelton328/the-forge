"""Parse ngspice stdout / stderr for .measure results (testable without ngspice)."""

from __future__ import annotations

import re


def parse_dc_op_node_voltage(log_text: str, node: str) -> float | None:
    """Read a node voltage from ngspice DC operating-point listing.

    Handles:

    - Numeric nets: ``V(2) …`` (batch output)
    - Named nets inside ``V()`` if ngspice prints them that way
    - KiCad-style power nets: ``/vin_2v_to_16v …`` (ngspice lowercases; leading ``/`` optional in ``node``)
    """
    if not node.strip():
        return None
    target = node.strip().lower()
    variants: set[str] = {target}
    if target.startswith("/"):
        variants.add(target[1:])
    else:
        variants.add(f"/{target}")

    for m in re.finditer(
        r"(?im)^\s*[Vv]\(\s*([^)]+?)\s*\)\s+([\d.eE+-]+)\s*$",
        log_text,
    ):
        raw = m.group(1).strip().lower()
        if raw in variants:
            return float(m.group(2))

    for m in re.finditer(
        r"(?im)^\s*([a-z_/][a-z0-9_/]*)\s+([\d.eE+-]+)\s*$",
        log_text,
    ):
        raw = m.group(1).strip().lower()
        if raw in variants:
            return float(m.group(2))
    return None


def parse_measure_value(log_text: str, measure_id: str) -> float | None:
    """Extract numeric value for a .measure name from combined ngspice output.

    Matches lines like ``v_n2 = 5.000000e+00`` (ngspice batch). First match wins.

    MIN/MAX/PP measures often append ``at=…``, ``from=…``, etc.; accept trailing text on the line.
    """
    if not measure_id.strip():
        return None
    # ngspice may left-pad; allow spaces around =
    pat = re.compile(
        rf"(?im)^{re.escape(measure_id)}\s*=\s*([\d.eE+-]+)",
        re.MULTILINE,
    )
    m = pat.search(log_text)
    if not m:
        return None
    return float(m.group(1))


def check_limits(
    value: float,
    min_value: float | None,
    max_value: float | None,
) -> tuple[bool, str | None]:
    """Return (ok, reason_if_fail)."""
    if min_value is not None and value < min_value:
        return False, f"{value} < min {min_value}"
    if max_value is not None and value > max_value:
        return False, f"{value} > max {max_value}"
    return True, None
