#!/usr/bin/env python3
"""Migrate esp32s3-devkit J3: Connector USB symbol 14P -> 16P; restore stock PCB footprint naming."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path


def balanced_slice(s: str, open_paren_idx: int) -> tuple[int, int]:
    depth = 0
    i = open_paren_idx
    instr = False
    esc = False
    start = open_paren_idx
    while i < len(s):
        ch = s[i]
        if esc:
            esc = False
            i += 1
            continue
        if instr:
            if ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
            i += 1
            continue
        if ch == '"':
            instr = True
            i += 1
            continue
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth -= 1
            i += 1
            if depth == 0:
                return start, i
            continue
        i += 1
    raise ValueError("unbalanced parens")


def embedded_16p_block(connector_path: Path) -> str:
    lib = connector_path.read_text(encoding="utf-8")
    key = '(symbol "USB_C_Receptacle_USB2.0_16P"'
    p = lib.find(key)
    if p == -1:
        raise SystemExit(f"USB_C_Receptacle_USB2.0_16P not found in {connector_path}")
    o = lib.find("(", p)
    s, e = balanced_slice(lib, o)
    blob = lib[s:e]
    # One extra tab nests under schematic (lib_symbols) like other Connector:* embeds.
    indented = "\n".join("\t" + ln for ln in blob.splitlines())
    return indented.replace(
        '(symbol "USB_C_Receptacle_USB2.0_16P"',
        '(symbol "Connector:USB_C_Receptacle_USB2.0_16P"',
        1,
    )


def connector_sym_path(repo: Path) -> Path:
    env = os.environ.get("KICAD_CONNECTOR_SYM", "")
    if env:
        return Path(env)
    darwin = Path(
        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Connector.kicad_sym"
    )
    linux = Path("/usr/share/kicad/symbols/Connector.kicad_sym")
    for candidate in (darwin, linux):
        if candidate.exists():
            return candidate
    raise SystemExit(
        "Connector.kicad_sym not found. Install KiCad symbols or export "
        "KICAD_CONNECTOR_SYM=/path/to/Connector.kicad_sym"
    )


def replace_embedded_14p(sch: str, replacement: str) -> str:
    marker = '\t\t(symbol "Connector:USB_C_Receptacle_USB2.0_14P"'
    pos = sch.find(marker)
    if pos == -1:
        raise SystemExit("embedded Connector USB 14P definition not found")
    o = sch.find("(", pos)
    _, end = balanced_slice(sch, o)
    return sch[:pos] + replacement + sch[end:]


def replace_j3_placement(sch: str) -> str:
    needle = '\t(symbol\n\t\t(lib_id "Connector:USB_C_Receptacle_USB2.0_14P")\n'
    j3s = sch.find(needle)
    if j3s == -1:
        raise SystemExit('J3 (lib_id 14P) placement not found')
    open_j3 = sch.find("(", j3s)
    _, j3e = balanced_slice(sch, open_j3)

    pu = uuid.uuid4
    pin_uuids = {
        "A1": "fe78e264-d70a-4efb-bb06-979b25d95919",
        "A12": "ac0933eb-1421-4a99-b9df-5cbf576a4693",
        "B1": "e4272c27-85ff-40ff-ba30-5a4eba8e2ea6",
        "B6": "38071116-2ac1-4eee-b10a-8f5c4a60e547",
        "A6": "7ce8f404-6210-4675-af56-03b8ce01df07",
        "B7": "da7020b6-5711-4031-973a-45be3e5ccb01",
        "A7": "6d471dd2-d076-4c50-a06c-f9ba2eea4c54",
        "B5": "5d7bc1a9-79e9-484c-9a1d-8b7bdcf8cfb1",
        "A5": "d150ee5d-6dbc-41df-9010-4eb8ef7d4112",
        "B9": "89248f7d-14be-4ef2-a2b8-707a80056048",
        "B4": "26aa603c-02c5-4cc0-9e31-5e0192a520a1",
        "A9": "f38cb8c0-d431-4da5-a68a-677284885695",
        "A4": "4a1ae0a9-89bd-4c43-be49-08986ca96b74",
        "B12": "2bd53527-7388-4184-9630-bace951b6433",
        "A8": str(pu()),
        "B8": str(pu()),
        "SH": "03713008-29af-4e52-b5e3-272ba4b09d4a",
    }
    order = (
        "A1",
        "A4",
        "A5",
        "A6",
        "A7",
        "A8",
        "A9",
        "A12",
        "B1",
        "B4",
        "B5",
        "B6",
        "B7",
        "B8",
        "B9",
        "B12",
        "SH",
    )
    pins_txt = "".join(
        f'\t\t(pin "{nm}"\n\t\t\t(uuid "{pin_uuids[nm]}")\n\t\t)\n' for nm in order
    )
    blk = (
        '\t(symbol\n\t\t(lib_id "Connector:USB_C_Receptacle_USB2.0_16P")\n'
        '\t\t(at 152.4 130.81 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
        '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
        '\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
        '\t\t(uuid "7aeeb542-8ff8-4cc2-adec-48d0d55b553e")\n'
        '\t\t(property "Reference" "J3"\n\t\t\t(at 152.4 107.95 0)\n\t\t\t'
        '(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t'
        '(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
        '\t\t(property "Value" "USB_C_Receptacle_USB2.0_16P"\n\t\t\t'
        '(at 152.4 110.49 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
        '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
        '\t\t(property "Footprint" '
        '"Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"\n'
        '\t\t\t(at 156.21 130.81 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t'
        '(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
        '\t\t(property "Datasheet" '
        '"https://www.usb.org/sites/default/files/documents/usb_type-c.zip"\n'
        '\t\t\t(at 156.21 130.81 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t'
        '(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
        '\t\t(property "Description" '
        '"USB 2.0-only 16P Type-C Receptacle connector"\n'
        '\t\t\t(at 152.4 130.81 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n'
        '\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t'
        '(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
    )
    blk += pins_txt + (
        "\t\t(instances\n\t\t\t(project \"esp32s3-devkit\"\n"
        '\t\t\t\t(path "/7924bd8b-2498-4d76-899d-c0ad5a514485"\n'
        '\t\t\t\t\t(reference "J3")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n'
        "\t\t)\n\t)\n"
    )
    return sch[:j3s] + blk + sch[j3e:]


def insert_sbu_nc(sch: str) -> str:
    needle = "(at 167.64 118.11)"
    if needle in sch:
        return sch
    anchor = '\t(junction\n\t\t(at 238.76 54.61)'
    pos = sch.find(anchor)
    if pos == -1:
        raise SystemExit(f"NC insert anchor missing: {anchor!r}")
    block = (
        "\t(no_connect\n\t\t(at 167.64 118.11)\n\t\t(uuid "
        f'"{uuid.uuid4()}")\n\t)\n\t(no_connect\n\t\t(at 167.64 115.57)\n\t\t(uuid '
        f'"{uuid.uuid4()}")\n\t)\n'
    )
    return sch[:pos] + block + sch[pos:]


def patch_pcb(pcb: str) -> str:
    out = pcb.replace(
        '(footprint "HRO_TypeC_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"',
        '(footprint "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"',
        1,
    )
    out = out.replace('(pad "S1" thru_hole oval', '(pad "SH" thru_hole oval')
    old = """\t\t(units\n\t\t\t(unit\n\t\t\t\t(name "A")\n\t\t\t\t(pins "S1" "A1" "A12" "B1" "B12" "A4" "A9" "B4" "B9" "A5" "B5" "A7" "B7"\n\t\t\t\t\t"A6" "B6"\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"""  # noqa: E501
    new = """\t\t(units\n\t\t\t(unit\n\t\t\t\t(name "A")\n\t\t\t\t(pins "SH" "A1" "A4" "A5" "A6" "A7" "A8" "A9" "A12" "B1" "B4" "B5" "B6" "B7" "B8" "B9" "B12"\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"""  # noqa: E501
    if old not in out:
        raise SystemExit(
            'PCB J3 (units pins "S1" …) block not found — reconcile manually.'
        )
    return out.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    sch_path = repo / "boards/esp32s3-devkit/esp32s3-devkit.kicad_sch"
    pcb_path = repo / "boards/esp32s3-devkit/esp32s3-devkit.kicad_pcb"

    emb = embedded_16p_block(connector_sym_path(repo))
    txt = sch_path.read_text(encoding="utf-8")
    txt = replace_embedded_14p(txt, emb)
    txt = replace_j3_placement(txt)
    txt = insert_sbu_nc(txt)

    sch_path.write_text(txt, encoding="utf-8")
    pcb_path.write_text(
        patch_pcb(pcb_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    verified = sch_path.read_text(encoding="utf-8")
    if "Connector:USB_C_Receptacle_USB2.0_14P" in verified:
        raise SystemExit("sanity fail: 14P still referenced")
    print("updated:", sch_path.relative_to(repo), pcb_path.relative_to(repo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
