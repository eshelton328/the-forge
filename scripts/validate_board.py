#!/usr/bin/env python3
"""Board validation: checks design intent beyond ERC/DRC.

Parses the KiCad schematic directly (no external KiCad-specific library needed)
and validates against per-board rules declared in checks.yml.

Usage:  python scripts/validate_board.py boards/<name>
Output: JSON to stdout with validation results.
Exit:   0 = all pass or skipped, 1 = violations found, 2 = usage/parse error.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import yaml

# ── S-expression tokenizer & parser ──────────────────────────────────
#
# KiCad files are S-expressions: (tag arg1 arg2 (nested …) …).
# We represent them as nested Python lists whose first element is the tag.
# Quoted strings are unquoted during tokenization.

SExpr = Union[str, list["SExpr"]]


def _tokenize(text: str) -> list[str]:
    """Split KiCad S-expression text into tokens."""
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in "()":
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            tokens.append(text[i + 1 : j])
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and text[j] not in '() \t\n\r"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def _parse_tokens(tokens: list[str]) -> list[SExpr]:
    """Build nested-list tree from flat token stream."""
    stack: list[list[SExpr]] = [[]]
    for tok in tokens:
        if tok == "(":
            new: list[SExpr] = []
            stack[-1].append(new)
            stack.append(new)
        elif tok == ")":
            if len(stack) > 1:
                stack.pop()
        else:
            stack[-1].append(tok)
    return stack[0]


def parse_kicad_file(text: str) -> list[SExpr]:
    """Parse KiCad S-expression file content into a tree."""
    return _parse_tokens(_tokenize(text))


# ── Tree helpers ─────────────────────────────────────────────────────


def _tag(node: SExpr) -> str:
    if isinstance(node, list) and node and isinstance(node[0], str):
        return node[0]
    return ""


def _children(node: list[SExpr], tag: str) -> list[list[SExpr]]:
    """All direct children whose tag matches."""
    return [c for c in node if isinstance(c, list) and _tag(c) == tag]


def _child_value(node: list[SExpr], tag: str) -> str:
    """First string value of the first child matching *tag*."""
    for c in node:
        if isinstance(c, list) and _tag(c) == tag and len(c) > 1 and isinstance(c[1], str):
            return c[1]
    return ""


def _property_value(node: list[SExpr], key: str) -> str:
    """Value of a ``(property "<key>" "<value>" …)`` inside *node*."""
    for c in node:
        if (
            isinstance(c, list)
            and _tag(c) == "property"
            and len(c) > 2
            and c[1] == key
            and isinstance(c[2], str)
        ):
            return c[2]
    return ""


# ── Component / net extraction ───────────────────────────────────────


@dataclass
class Component:
    reference: str
    value: str
    footprint: str
    datasheet: str
    lib_id: str


def extract_components(root: list[SExpr]) -> list[Component]:
    """Return placed BOM components (excludes power symbols and flags)."""
    components: list[Component] = []
    for child in root:
        if not isinstance(child, list) or _tag(child) != "symbol":
            continue
        lib_id = _child_value(child, "lib_id")
        if not lib_id:
            continue
        ref = _property_value(child, "Reference")
        if ref.startswith("#"):
            continue
        components.append(
            Component(
                reference=ref,
                value=_property_value(child, "Value"),
                footprint=_property_value(child, "Footprint"),
                datasheet=_property_value(child, "Datasheet"),
                lib_id=lib_id,
            )
        )
    return components


def extract_net_names(root: list[SExpr]) -> set[str]:
    """Collect all named nets: local labels, global labels, and power symbols."""
    nets: set[str] = set()
    for child in root:
        if not isinstance(child, list):
            continue
        tag = _tag(child)
        if tag in ("label", "global_label") and len(child) > 1 and isinstance(child[1], str):
            nets.add(child[1])
        if tag == "symbol":
            lib_id = _child_value(child, "lib_id")
            if lib_id.startswith("power:"):
                val = _property_value(child, "Value")
                if val:
                    nets.add(val)
    return nets


# ── Validation checks ────────────────────────────────────────────────


@dataclass
class Violation:
    check: str
    message: str


def _parse_capacitance_uf(raw: str) -> float:
    """Best-effort parse of capacitance value strings to µF."""
    s = raw.strip().lower().replace("\u00b5", "u").replace("\u03bc", "u")
    m = re.match(r"^([\d.]+)\s*(u|n|p)?f?$", s)
    if not m:
        return 0.0
    num = float(m.group(1))
    unit = m.group(2) or "u"
    return num * {"u": 1.0, "n": 1e-3, "p": 1e-6}[unit]


def check_required_components(
    components: list[Component],
    rules: dict[str, dict[str, str] | None],
) -> list[Violation]:
    violations: list[Violation] = []
    by_ref = {c.reference: c for c in components}
    for ref, expected in rules.items():
        comp = by_ref.get(ref)
        if comp is None:
            violations.append(Violation("required_components", f"Missing required component {ref}"))
            continue
        if not expected:
            continue
        exp_val = expected.get("value", "")
        if exp_val and comp.value != exp_val:
            violations.append(
                Violation(
                    "required_components",
                    f"{ref}: expected value '{exp_val}', got '{comp.value}'",
                )
            )
        exp_fp = expected.get("footprint_lib", "")
        if exp_fp:
            fp_lib = comp.footprint.split(":")[0] if ":" in comp.footprint else ""
            if fp_lib != exp_fp:
                violations.append(
                    Violation(
                        "required_components",
                        f"{ref}: expected footprint lib '{exp_fp}', got '{fp_lib}'",
                    )
                )
    return violations


def check_required_nets(
    net_names: set[str],
    required: list[str],
) -> list[Violation]:
    return [
        Violation("required_nets", f"Missing required net '{net}'")
        for net in required
        if net not in net_names
    ]


def check_capacitor_budget(
    components: list[Component],
    budget: dict[str, dict[str, object]],
) -> list[Violation]:
    violations: list[Violation] = []
    by_ref = {c.reference: c for c in components}
    for group_name, group in budget.items():
        refs: list[str] = group.get("refs", [])  # type: ignore[union-attr]
        min_uf: float = float(group.get("min_total_uf", 0))  # type: ignore[union-attr]
        if min_uf <= 0:
            continue
        total = 0.0
        for ref in refs:
            comp = by_ref.get(ref)
            if comp is None:
                violations.append(
                    Violation("capacitor_budget", f"{group_name}: missing capacitor {ref}")
                )
                continue
            total += _parse_capacitance_uf(comp.value)
        if total < min_uf:
            violations.append(
                Violation(
                    "capacitor_budget",
                    f"{group_name}: total {total:.1f}\u00b5F < required {min_uf:.0f}\u00b5F"
                    f" (refs: {', '.join(refs)})",
                )
            )
    return violations


def _parse_resistance_ohms(raw: str) -> float:
    """Best-effort parse of resistance value strings to ohms."""
    s = raw.strip()
    s = s.replace("\u03a9", "").replace("\u03c9", "").replace("\u2126", "")  # Ω ω Ω
    s = s.lower().strip()
    s = re.sub(r"ohms?$", "", s).strip()
    m = re.match(r"^([\d.]+)\s*(k|m|meg)?$", s)
    if not m:
        return 0.0
    num = float(m.group(1))
    unit = m.group(2) or ""
    return num * {"": 1.0, "k": 1e3, "m": 1e6, "meg": 1e6}.get(unit, 1.0)


def check_voltage_divider(
    components: list[Component],
    rules: dict[str, object],
) -> list[Violation]:
    """Verify feedback divider produces expected output voltage.

    Uses: V_OUT = V_REF * (1 + R_upper / R_lower).
    """
    violations: list[Violation] = []
    by_ref = {c.reference: c for c in components}

    v_ref = float(rules.get("v_ref", 0))  # type: ignore[arg-type]
    expected_v = float(rules.get("expected_voltage", 0))  # type: ignore[arg-type]
    tolerance_pct = float(rules.get("tolerance_percent", 1.0))  # type: ignore[arg-type]
    upper_ref: str = rules.get("upper_ref", "")  # type: ignore[assignment]
    lower_ref: str = rules.get("lower_ref", "")  # type: ignore[assignment]

    if not all([v_ref, expected_v, upper_ref, lower_ref]):
        violations.append(
            Violation("voltage_divider", "incomplete config: need v_ref, expected_voltage, upper_ref, lower_ref")
        )
        return violations

    upper = by_ref.get(upper_ref)
    lower = by_ref.get(lower_ref)
    if upper is None:
        violations.append(Violation("voltage_divider", f"upper resistor {upper_ref} not found"))
        return violations
    if lower is None:
        violations.append(Violation("voltage_divider", f"lower resistor {lower_ref} not found"))
        return violations

    r_upper = _parse_resistance_ohms(upper.value)
    r_lower = _parse_resistance_ohms(lower.value)
    if r_lower == 0:
        violations.append(Violation("voltage_divider", f"{lower_ref} value '{lower.value}' parses to 0\u03a9"))
        return violations

    actual_v = v_ref * (1.0 + r_upper / r_lower)
    error_pct = abs(actual_v - expected_v) / expected_v * 100.0

    if error_pct > tolerance_pct:
        violations.append(
            Violation(
                "voltage_divider",
                f"V_OUT = {actual_v:.3f}V (expected {expected_v}V \u00b1{tolerance_pct}%)"
                f" from {upper_ref}={upper.value}, {lower_ref}={lower.value}, V_REF={v_ref}V",
            )
        )

    return violations


def check_bom_rules(
    components: list[Component],
    rules: dict[str, object],
) -> list[Violation]:
    violations: list[Violation] = []
    if rules.get("require_footprint"):
        for comp in components:
            if not comp.footprint or comp.footprint in ("", "~"):
                violations.append(
                    Violation("bom_rules", f"{comp.reference}: missing footprint")
                )
    if rules.get("no_duplicate_refs"):
        seen: dict[str, int] = {}
        for comp in components:
            seen[comp.reference] = seen.get(comp.reference, 0) + 1
        for ref, count in seen.items():
            if count > 1:
                violations.append(
                    Violation("bom_rules", f"Duplicate reference: {ref} (x{count})")
                )
    for ref in rules.get("require_datasheet_on", []):  # type: ignore[union-attr]
        comp = next((c for c in components if c.reference == ref), None)
        if comp and (not comp.datasheet or comp.datasheet in ("", "~")):
            violations.append(Violation("bom_rules", f"{ref}: missing datasheet URL"))
    return violations


# ── Orchestration ────────────────────────────────────────────────────

_CHECKERS = [
    ("required_components", check_required_components, lambda comps, nets: comps),
    ("required_nets", check_required_nets, lambda comps, nets: nets),
    ("capacitor_budget", check_capacitor_budget, lambda comps, nets: comps),
    ("voltage_divider", check_voltage_divider, lambda comps, nets: comps),
    ("bom_rules", check_bom_rules, lambda comps, nets: comps),
]


def validate_board(board_dir: Path) -> dict[str, object]:
    """Run all configured checks for *board_dir*. Returns JSON-serialisable dict."""
    checks_path = board_dir / "checks.yml"
    if not checks_path.exists():
        return {"board": board_dir.name, "skipped": True, "reason": "no checks.yml"}

    config: dict[str, object] = yaml.safe_load(checks_path.read_text()) or {}

    sch_file = board_dir / f"{board_dir.name}.kicad_sch"
    if not sch_file.exists():
        return {"board": board_dir.name, "checks": [], "error": f"schematic not found: {sch_file}"}

    tree = parse_kicad_file(sch_file.read_text())
    if not tree or not isinstance(tree[0], list):
        return {"board": board_dir.name, "checks": [], "error": "failed to parse schematic"}

    root = tree[0]
    components = extract_components(root)
    nets = extract_net_names(root)

    check_results: list[dict[str, object]] = []
    total_violations = 0

    for key, checker, data_selector in _CHECKERS:
        if key not in config:
            continue
        data = data_selector(components, nets)
        violations = checker(data, config[key])  # type: ignore[arg-type]
        total_violations += len(violations)
        check_results.append(
            {
                "category": key,
                "status": "fail" if violations else "pass",
                "violations": [{"message": v.message} for v in violations],
            }
        )

    return {
        "board": board_dir.name,
        "checks": check_results,
        "total_violations": total_violations,
        "passed": total_violations == 0,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <board-directory>", file=sys.stderr)
        sys.exit(2)

    board_dir = Path(sys.argv[1])
    if not board_dir.is_dir():
        print(f"Error: not a directory: {board_dir}", file=sys.stderr)
        sys.exit(2)

    result = validate_board(board_dir)
    json.dump(result, sys.stdout, indent=2)
    print()

    if result.get("error"):
        sys.exit(2)
    if result.get("skipped"):
        sys.exit(0)
    if not result.get("passed", True):
        sys.exit(1)


if __name__ == "__main__":
    main()
