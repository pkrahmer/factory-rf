"""A stand-in `sudo` that records each call, then runs it or exits as planned."""

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from confine_support import read_records, write_script

CALLS = "sudo-calls.jsonl"
PLAN = "sudo-plan.json"

# Records its arguments, environment and working directory; then, unless it starts the
# planned program, writes its planned warning and either exits as planned, after its
# planned wait, or runs what follows `--`.
SUDO_SCRIPT = r"""
import json
import os
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
record = {
    "arguments": arguments,
    "environment": dict(os.environ),
    "working_directory": os.getcwd(),
}
with (here / "sudo-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
plan = json.loads((here / "sudo-plan.json").read_text(encoding="utf-8"))
rest = arguments[arguments.index("--") + 1 :]
if rest[0] != plan["program"]:
    sys.stderr.write(plan["warning"])
    sys.stderr.flush()
    if plan["exit_status"] is not None:
        sys.stderr.write(plan["stderr"])
        time.sleep(plan["wait_seconds"])
        sys.exit(plan["exit_status"])
os.execvp(rest[0], rest)
"""


class SudoCall(BaseModel):
    """One call the stand-in `sudo` saw."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    working_directory: Path


@dataclass(frozen=True)
class Sudo:
    """The stand-in `sudo` and the folder that holds its plan and its record."""

    path: Path
    folder: Path

    def calls(self) -> list[SudoCall]:
        """The calls it recorded, in order."""
        return read_records(self.folder / CALLS, SudoCall)


def write_sudo(
    folder: Path,
    *,
    exit_status: int | None = None,
    stderr: str = "",
    warning: str = "",
    program: Path | None = None,
    wait_seconds: float = 0,
) -> Sudo:
    """Write the stand-in into `folder` and return it.

    It records each call, then runs `program` or what follows `--`, or exits as planned.
    """
    path = write_script(folder / "sudo", SUDO_SCRIPT)
    plan = {
        "exit_status": exit_status,
        "stderr": stderr,
        "warning": warning,
        "program": None if program is None else str(program),
        "wait_seconds": wait_seconds,
    }
    (folder / PLAN).write_text(json.dumps(plan), encoding="utf-8")
    return Sudo(path=path, folder=folder)
