from pathlib import Path

import pytest

from scripts.validate_board import extract_components, extract_net_names, load_schematic_hierarchy


def test_reused_sheet_uses_each_instance_reference(tmp_path: Path) -> None:
    root = tmp_path / "board.kicad_sch"
    root.write_text('''(kicad_sch (uuid "root")
      (sheet (uuid "left") (property "Sheetfile" "child.kicad_sch"))
      (sheet (uuid "right") (property "Sheetfile" "child.kicad_sch")))''')
    (tmp_path / "child.kicad_sch").write_text('''(kicad_sch (uuid "child")
      (hierarchical_label "SENSE")
      (symbol (lib_id "Device:R") (property "Reference" "R?")
        (property "Value" "33k")
        (instances (project "board"
          (path "/root/left" (reference "R48"))
          (path "/root/right" (reference "R58"))))))''')
    tree = load_schematic_hierarchy(root)
    assert [c.reference for c in extract_components(tree)] == ["R48", "R58"]
    assert "SENSE" in extract_net_names(tree)


def test_missing_sheet_fails(tmp_path: Path) -> None:
    root = tmp_path / "board.kicad_sch"
    root.write_text('(kicad_sch (uuid "root") (sheet (uuid "s") (property "Sheetfile" "missing.kicad_sch")))')
    with pytest.raises(FileNotFoundError):
        load_schematic_hierarchy(root)


def test_recursive_sheet_fails(tmp_path: Path) -> None:
    root = tmp_path / "board.kicad_sch"
    root.write_text('(kicad_sch (uuid "root") (sheet (uuid "s") (property "Sheetfile" "board.kicad_sch")))')
    with pytest.raises(ValueError, match="recursive"):
        load_schematic_hierarchy(root)
