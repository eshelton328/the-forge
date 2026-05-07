"""SIM metrics JSON sidecar serialization (#60); no ngspice."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.sim.metrics_json import (
    SIM_METRICS_SCHEMA_VERSION,
    build_metrics_json_document,
    metrics_sidecar_path,
)
from scripts.sim.report_md import MeasureRowResult


FROZEN_METRICS_TIME = "2026-05-05T12:00:00Z"


def test_metrics_sidecar_path_stem_suffix() -> None:
    md = Path("boards/b/docs/spice-report.md")
    assert metrics_sidecar_path(md) == Path("boards/b/docs/spice-report.metrics.json")


def test_build_metrics_without_baseline() -> None:
    rows = (
        MeasureRowResult(
            measure_id="m_div",
            scenario_id="s1",
            value_str="0.5",
            bounds_str="min 0.4, max 0.6",
            passed=True,
            detail=None,
            bounds_min=0.4,
            bounds_max=0.6,
        ),
    )
    raw = build_metrics_json_document(
        config_path=Path("sim/fixtures/x/sim.yml"),
        netlist_path=Path("sim/fixtures/x/deck.cir"),
        scenario_results=rows,
        ngspice_version="ngspice 44",
        simulator_returncode=0,
        kicad_cli_version="kicad-cli 9",
        kicad_docker_image=None,
        baseline_compare=False,
        baseline_relative_display=None,
        baseline_doc_ref=None,
        baseline_measures=None,
        waveform_pngs_rel=(),
        generated_at_override=FROZEN_METRICS_TIME,
    )
    parsed: dict[str, object] = json.loads(raw)
    assert parsed["metrics_schema_version"] == SIM_METRICS_SCHEMA_VERSION
    assert parsed["generated_at"] == FROZEN_METRICS_TIME
    assert parsed["pass"] is True
    assert parsed["exit_code_hint"] == 0
    assert parsed["baseline"] is None
    toolchain = parsed["toolchain"]
    assert isinstance(toolchain, dict)
    assert toolchain["baseline_compare_enabled"] is False
    assert toolchain["kicad_docker_image"] is None
    assert "waveform_pngs_rel" not in parsed
    m0 = parsed["measures"]
    assert isinstance(m0, list) and len(m0) == 1
    assert m0[0]["measure_id"] == "m_div"
    assert m0[0]["value_numeric"] == 0.5
    assert m0[0]["bounds_min"] == 0.4
    assert "measure_key" not in m0[0]


def test_build_metrics_with_baseline_columns_and_waveforms() -> None:
    rows = (
        MeasureRowResult(
            measure_id="v_vin",
            scenario_id="vin_bias_op",
            value_str="10",
            bounds_str="min 9",
            passed=True,
            detail=None,
            bounds_min=9.0,
            bounds_max=None,
        ),
    )
    baselines = {"vin_bias_op::v_vin": 9.5}
    raw = build_metrics_json_document(
        config_path=Path("boards/b/sim.yml"),
        netlist_path=Path("assembled.cir"),
        scenario_results=rows,
        ngspice_version="n",
        simulator_returncode=0,
        kicad_cli_version=None,
        kicad_docker_image="kicad/kicad:10@sha256:abc",
        baseline_compare=True,
        baseline_relative_display="sim/spice_metrics_baseline.json",
        baseline_doc_ref="main@deadbeef",
        baseline_measures=baselines,
        waveform_pngs_rel=("sim/plots/out.png",),
        generated_at_override=FROZEN_METRICS_TIME,
    )
    parsed = json.loads(raw)
    baseline = parsed["baseline"]
    assert isinstance(baseline, dict)
    assert baseline["baseline_file_rel"] == "sim/spice_metrics_baseline.json"
    assert baseline["doc_ref"] == "main@deadbeef"
    toolchain = parsed["toolchain"]
    assert isinstance(toolchain, dict)
    assert toolchain["baseline_compare_enabled"] is True
    assert toolchain["kicad_docker_image"] == "kicad/kicad:10@sha256:abc"
    m0_list = parsed["measures"]
    assert isinstance(m0_list, list)
    m0 = m0_list[0]
    assert m0["measure_key"] == "vin_bias_op::v_vin"
    assert m0["baseline_numeric"] == 9.5
    w = parsed["waveform_pngs_rel"]
    assert w == ["sim/plots/out.png"]


def test_missing_measure_value_numeric_is_null() -> None:
    rows = (
        MeasureRowResult(
            measure_id="x",
            scenario_id="s",
            value_str="(missing)",
            bounds_str="min 1",
            passed=False,
            detail="parse fail",
            bounds_min=1.0,
            bounds_max=None,
        ),
    )
    parsed = json.loads(
        build_metrics_json_document(
            config_path=Path("c/sim.yml"),
            netlist_path=Path("n.cir"),
            scenario_results=rows,
            ngspice_version="n",
            simulator_returncode=1,
            kicad_cli_version=None,
            kicad_docker_image=None,
            baseline_compare=False,
            baseline_relative_display=None,
            baseline_doc_ref=None,
            baseline_measures=None,
            generated_at_override=FROZEN_METRICS_TIME,
        ),
    )
    assert parsed["pass"] is False
    assert parsed["exit_code_hint"] == 1
    toolchain = parsed["toolchain"]
    assert isinstance(toolchain, dict)
    assert toolchain["simulator_exit_code"] == 1
    mm = parsed["measures"]
    assert isinstance(mm, list)
    assert mm[0]["value_numeric"] is None


def test_metrics_serializes_display_title_when_set() -> None:
    rows = (
        MeasureRowResult(
            measure_id="m1",
            scenario_id="scen",
            value_str="2",
            bounds_str="max 3",
            passed=True,
            detail=None,
            bounds_min=None,
            bounds_max=3.0,
            display_title="Human label",
            display_group="grp",
        ),
    )
    parsed = json.loads(
        build_metrics_json_document(
            config_path=Path("b/sim.yml"),
            netlist_path=Path("x.cir"),
            scenario_results=rows,
            ngspice_version="n",
            simulator_returncode=0,
            kicad_cli_version=None,
            kicad_docker_image=None,
            baseline_compare=False,
            baseline_relative_display=None,
            baseline_doc_ref=None,
            baseline_measures=None,
            generated_at_override=FROZEN_METRICS_TIME,
        ),
    )
    m = parsed["measures"]
    assert isinstance(m, list) and m[0]["display_title"] == "Human label"
    assert m[0]["display_group"] == "grp"


def test_json_sort_keys_is_stable_between_calls() -> None:
    rows = (
        MeasureRowResult(
            measure_id="m",
            scenario_id="s",
            value_str="1",
            bounds_str="(unbounded)",
            passed=True,
            detail=None,
        ),
    )
    a = build_metrics_json_document(
        config_path=Path("a/sim.yml"),
        netlist_path=Path("z.cir"),
        scenario_results=rows,
        ngspice_version="v",
        simulator_returncode=0,
        kicad_cli_version=None,
        kicad_docker_image=None,
        baseline_compare=False,
        baseline_relative_display=None,
        baseline_doc_ref=None,
        baseline_measures=None,
        generated_at_override=FROZEN_METRICS_TIME,
    )
    b = build_metrics_json_document(
        config_path=Path("a/sim.yml"),
        netlist_path=Path("z.cir"),
        scenario_results=rows,
        ngspice_version="v",
        simulator_returncode=0,
        kicad_cli_version=None,
        kicad_docker_image=None,
        baseline_compare=False,
        baseline_relative_display=None,
        baseline_doc_ref=None,
        baseline_measures=None,
        generated_at_override=FROZEN_METRICS_TIME,
    )
    assert a == b

