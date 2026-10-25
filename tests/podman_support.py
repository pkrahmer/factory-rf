"""A stand-in `podman` that records each call, then plays its plan or runs the container's words."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from run_layout_support import read_records, write_script

IMAGE = "factory-stage:1"
CALLS = "podman-calls.jsonl"
PLAN = "podman-plan.json"

# Records its arguments, environment and working directory; then, when its arguments hold the
# planned image word, runs the words after it; otherwise prints its planned output, waits as
# planned and exits with the planned status (-9: kills itself with SIGKILL).
PODMAN_SCRIPT = r"""
import json
import os
import signal
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
with (here / "podman-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
plan = json.loads((here / "podman-plan.json").read_text(encoding="utf-8"))
if plan["image"] is not None and plan["image"] in arguments:
    rest = arguments[arguments.index(plan["image"]) + 1 :]
    os.execvp(rest[0], rest)
sys.stdout.write(plan["stdout"])
sys.stdout.flush()
sys.stderr.write(plan["stderr"])
sys.stderr.flush()
time.sleep(plan["wait_seconds"])
if plan["exit_status"] == -9:
    os.kill(os.getpid(), signal.SIGKILL)
sys.exit(plan["exit_status"])
"""


class PodmanPlan(BaseModel):
    """What the stand-in `podman` prints, how long it waits and how it exits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stdout: str = ""
    stderr: str = ""
    wait_seconds: float = 0
    exit_status: int = 0
    # When the arguments hold this word, the stand-in runs the words after it instead.
    image: str | None = None


class PodmanCall(BaseModel):
    """One call the stand-in `podman` saw."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    working_directory: Path


@dataclass(frozen=True)
class Podman:
    """The stand-in `podman` and the folder that holds its plan and its record."""

    path: Path
    folder: Path

    def plan(self, plan: PodmanPlan) -> None:
        """Make `plan` what the stand-in does on its next calls."""
        (self.folder / PLAN).write_text(plan.model_dump_json(), encoding="utf-8")

    def calls(self) -> list[PodmanCall]:
        """The calls it recorded, in order."""
        return read_records(self.folder / CALLS, PodmanCall)


def write_podman(folder: Path, plan: PodmanPlan | None = None) -> Podman:
    """Write the stand-in into `folder`, planned as `plan` (exit 0 silently by default)."""
    podman = Podman(path=write_script(folder / "podman", PODMAN_SCRIPT), folder=folder)
    podman.plan(PodmanPlan() if plan is None else plan)
    return podman
