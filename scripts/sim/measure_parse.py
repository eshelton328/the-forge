"""Parse ngspice stdout / stderr for .measure results (testable without ngspice)."""

from __future__ import annotations

import re


def parse_measure_value(log_text: str, measure_id: str) -> float | None:
    """Extract numeric value for a .measure name from combined ngspice output.

    Matches lines like ``v_n2 = 5.000000e+00`` (ngspice batch). First match wins.
    """
    if not measure_id.strip():
        return None
    # ngspice may left-pad; allow spaces around =
    pat = re.compile(
        rf"(?im)^{re.escape(measure_id)}\s*=\s*([\d.eE+-]+)\s*$",
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
