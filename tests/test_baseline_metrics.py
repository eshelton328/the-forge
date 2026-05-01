"""Tests for optional Spice baseline JSON (#58)."""

from __future__ import annotations

import json

from scripts.sim.baseline_metrics import (
    build_baseline_document,
    format_delta_cell,
    load_baseline_file,
    measure_key,
    parse_baseline_text,
    parse_value_for_delta,
)


def test_measure_key_stable() -> None:
    assert measure_key("s1", "m1") == "s1::m1"


def test_parse_value_for_delta() -> None:
    assert parse_value_for_delta("10") == 10.0
    assert parse_value_for_delta("10.25") == 10.25
    assert parse_value_for_delta("(missing)") is None
    assert parse_value_for_delta("nope") is None


def test_format_delta_cell() -> None:
    assert format_delta_cell(10.0, None) == ("—", "—")
    assert format_delta_cell(None, 10.0) == ("10", "—")
    assert format_delta_cell(10.0, 10.0) == ("10", "0")
    assert format_delta_cell(10.1, 10.0)[1].startswith("+")


def test_parse_baseline_text_round_trip() -> None:
    doc = build_baseline_document(
        measures={measure_key("a", "b"): 1.5},
        ref="r1",
    )
    loaded = parse_baseline_text(doc)
    assert loaded is not None
    measures, ref = loaded
    assert ref == "r1"
    assert measures[measure_key("a", "b")] == 1.5


def test_load_baseline_file(tmp_path) -> None:
    p = tmp_path / "b.json"
    p.write_text(
        json.dumps(
            {
                "baseline_version": 1,
                "measures": {"x::y": 3.0},
            },
        ),
    )
    loaded = load_baseline_file(p)
    assert loaded is not None
    measures, ref = loaded
    assert ref is None
    assert measures["x::y"] == 3.0


def test_rejects_wrong_version() -> None:
    assert parse_baseline_text('{"baseline_version": 2, "measures": {}}') is None


def test_rejects_bad_measures_type() -> None:
    assert parse_baseline_text('{"baseline_version": 1, "measures": []}') is None
