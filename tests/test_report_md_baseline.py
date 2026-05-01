"""Report markdown with optional baseline columns (#58)."""

from __future__ import annotations

from pathlib import Path

from scripts.sim.report_md import MeasureRowResult, render_report


def test_render_without_baseline_unchanged_shape() -> None:
    rows = (
        MeasureRowResult(
            measure_id="m1",
            scenario_id="s1",
            value_str="1",
            bounds_str="(unbounded)",
            passed=True,
            detail=None,
        ),
    )
    text = render_report(
        config_path=Path("sim.yml"),
        scenario_results=rows,
        ngspice_version="ngspice 1",
        netlist_path=Path("n.cir"),
        simulator_returncode=0,
    )
    assert "| Scenario | Measure | Value | Bounds | Result |" in text
    assert "SIM_BASELINE_COMPARE=false" in text
    assert "Baseline file" not in text


def test_render_with_baseline_columns() -> None:
    rows = (
        MeasureRowResult(
            measure_id="v_vin",
            scenario_id="vin_bias_op",
            value_str="10",
            bounds_str="min 9.99, max 10.01",
            passed=True,
            detail=None,
        ),
    )
    text = render_report(
        config_path=Path("boards/b/sim.yml"),
        scenario_results=rows,
        ngspice_version="ngspice 1",
        netlist_path=Path("assembled.cir"),
        simulator_returncode=0,
        baseline_measures={"vin_bias_op::v_vin": 10.0},
        baseline_relative_display="sim/spice_metrics_baseline.json",
        baseline_doc_ref="ref note",
    )
    assert "| Baseline file | `sim/spice_metrics_baseline.json` |" in text
    assert "| Baseline ref (documented) | `ref note` |" in text
    assert "| Scenario | Measure | Value | Baseline | Δ | Bounds | Result |" in text
    assert "| vin_bias_op | v_vin | 10 | 10 | 0 |" in text
    assert "SIM_BASELINE_COMPARE=true" in text
