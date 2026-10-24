"""Runs of the template's Makefile in a copy of it, with a stand-in `uv` on the `PATH`."""

import os
import re
import shutil
from datetime import timedelta
from pathlib import Path

from adapters.claude_stand_in import Step, write_stand_in
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from shipped_agents import ROOT

MAKEFILE = ROOT / "template" / "Makefile"

# An outer `make` passes its variables on through these; the run must see none of them.
DROPPED = {"MAKEFLAGS", "MFLAGS", "MAKELEVEL", "FEATURE", "SOURCE", "LAYERS"}


def makefile_lines() -> list[str]:
    """The lines of the template's Makefile."""
    return MAKEFILE.read_text(encoding="utf-8").splitlines()


def green_line(target: str) -> re.Pattern[str]:
    """The pattern of a target's last line when it passes."""
    return re.compile(rf"^{target}: green \(\d+\.\d s\)$")


def template_project(tmp_path: Path) -> Path:
    """A folder `project` in `tmp_path` that holds a copy of the template's Makefile."""
    folder = tmp_path / "project"
    folder.mkdir()
    shutil.copyfile(MAKEFILE, folder / "Makefile")
    return folder


def stand_in_uv(tmp_path: Path, steps: list[Step]) -> Path:
    """Writes a stand-in `uv` that answers with `steps` into `tmp_path / "bin"`."""
    path = write_stand_in(tmp_path / "bin", steps)
    path.rename(path.with_name("uv"))
    return tmp_path / "bin"


def run_make(tmp_path: Path, *args: str) -> ProcessResult:
    """Runs `make` in the project folder with the stand-in first on the `PATH`."""
    environment = {key: value for key, value in os.environ.items() if key not in DROPPED}
    environment["PATH"] = f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
    return run_process(
        ProcessRequest(
            argv=["make", *args],
            cwd=tmp_path / "project",
            env=environment,
            time_limit=timedelta(seconds=120),
            merge_stderr=True,
        )
    )
