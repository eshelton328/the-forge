"""Optional transient waveform PNGs via ngspice ``wrdata`` + matplotlib (#59)."""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path


_PLOT_OUT_RE = re.compile(r"^[a-zA-Z0-9._-]+\.png$")


def validate_plot_png_basename(filename: str) -> str:
    stripped = filename.strip()
    if not _PLOT_OUT_RE.fullmatch(stripped):
        raise ValueError(
            "plots[].file must be a simple *.png basename "
            f"(ASCII letters/digits ._- only): got {stripped!r}",
        )
    return stripped


def validate_plot_signal(signal: str) -> str:
    stripped = signal.strip()
    if not stripped:
        raise ValueError("plots[].signal must be a non-empty string")
    lowered = stripped.lower()
    if ";" in stripped:
        raise ValueError("plots[].signal must not contain ';'")
    for token in (".include", ".control", ".endc"):
        if token in lowered:
            raise ValueError(
                "plots[].signal looks like Spice meta — supply an expression such as v(/net)",
            )
    if "\n" in stripped or "\r" in stripped:
        raise ValueError("plots[].signal must be a single-line expression")
    return stripped


def strip_trailing_dot_end(deck_body: str) -> str:
    lines = deck_body.strip().splitlines()
    while lines and lines[-1].strip().lower() == ".end":
        lines.pop()
    return "\n".join(lines).rstrip() + "\n"


def build_plot_driver_deck(core_without_end: str, wr_commands: Sequence[tuple[str, str]]) -> str:
    """``.control`` runs after the netlist is parsed; ``run`` executes all analyses again."""
    ctl_lines = [".control", "run"]
    for data_rel_path, spice_signal in wr_commands:
        ctl_lines.append(f"wrdata {data_rel_path} {spice_signal}")
    ctl_lines.extend([".endc", ".end"])
    return core_without_end + "\n".join(ctl_lines) + "\n"


def parse_wrdata_two_column_table(text: str) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace("\t", " ").split()
        if len(parts) < 2:
            continue
        xs.append(float(parts[0]))
        ys.append(float(parts[1]))
    return xs, ys


def wrdata_ascii_to_png(
    *,
    wrdata_txt: Path,
    png_out: Path,
    title: str,
    signal_label: str,
) -> None:
    """Turn ngspice ``wrdata`` two-column ASCII into a PNG."""
    txt = wrdata_txt.read_text()
    times, vals = parse_wrdata_two_column_table(txt)
    if len(times) < 2:
        raise ValueError(f"wrdata {wrdata_txt} has too few samples for a plot ({len(times)})")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    png_out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=120)
    ax.plot(times, vals, color="#1f77b4", linewidth=1.2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(signal_label)
    ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(str(png_out))
    plt.close(fig)


def run_wrdata_extractions_then_pngs(
    *,
    sim_directory: Path,
    assembled_rel: Path,
    ngspice_exe: str,
    plot_pairs: Sequence[tuple[str, str]],
) -> tuple[str, ...]:
    """Run one ngspice batch for all ``wrdata`` targets, then render PNGs.

    ``plot_pairs`` items are ``(png_basename, spice_signal)``. Intermediate ``.txt`` lives under
    ``sim/plots/_data/<png_basename>.txt`` and is removed after each PNG is written.

    Returns paths relative to board root: ``sim/plots/<png>``.
    """
    if not plot_pairs:
        return ()

    assembled_path = (sim_directory / assembled_rel).resolve()
    if not assembled_path.is_file():
        raise FileNotFoundError(f"assembled deck missing: {assembled_path}")

    core = strip_trailing_dot_end(assembled_path.read_text())
    wr_commands: list[tuple[str, str]] = []
    for png_name, signal in plot_pairs:
        stem = Path(png_name).stem
        data_rel = f"plots/_data/{stem}.txt"
        wr_commands.append((data_rel, signal))

    driver_name = "_plot_extractions_driver.cir"
    driver_path = sim_directory / driver_name
    board_root = sim_directory.parent.resolve()

    (sim_directory / "plots" / "_data").mkdir(parents=True, exist_ok=True)

    driver_path.write_text(build_plot_driver_deck(core, wr_commands))

    try:
        proc = subprocess.run(
            [ngspice_exe, "-b", driver_name],
            cwd=str(sim_directory.resolve()),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "ngspice plot driver failed:\n" + (proc.stderr or proc.stdout or "(no output)"),
            )

        created: list[Path] = []
        for png_name, signal in plot_pairs:
            stem = Path(png_name).stem
            data_file = sim_directory / "plots" / "_data" / f"{stem}.txt"
            png_file = sim_directory / "plots" / png_name
            if not data_file.is_file():
                raise FileNotFoundError(f"ngspice did not write wrdata file: {data_file}")
            wrdata_ascii_to_png(
                wrdata_txt=data_file,
                png_out=png_file,
                title=png_name.replace("_", " ").replace("-", " "),
                signal_label=signal,
            )
            created.append(png_file)

        return tuple(p.resolve().relative_to(board_root).as_posix() for p in created)
    finally:
        if driver_path.is_file():
            driver_path.unlink()
        data_dir = sim_directory / "plots" / "_data"
        if data_dir.is_dir():
            shutil.rmtree(data_dir, ignore_errors=True)
