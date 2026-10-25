"""A stand-in `zfs` that records each call and answers by a plan keyed on its first argument."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.adapters.zfs_snapshots import ZfsSnapshots
from run_layout_support import read_records, write_script

CALLS = "zfs-calls.jsonl"
PLAN = "zfs-plan.json"
DATASET = "tank/factory/vm"
MOUNT_POINT = Path("/srv/factory/vm/work")

# Records its arguments, environment and working directory; then answers as planned for its
# first argument (nothing and exit status 0 when the plan has no answer for it).
ZFS_SCRIPT = r"""
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
with (here / "zfs-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
plan = json.loads((here / "zfs-plan.json").read_text(encoding="utf-8"))
answer = plan.get(arguments[0] if arguments else "", None)
if answer is None:
    sys.exit(0)
sys.stdout.write(answer["stdout"])
sys.stdout.flush()
sys.stderr.write(answer["stderr"])
sys.stderr.flush()
time.sleep(answer["sleep_seconds"])
sys.exit(answer["exit_status"])
"""


@dataclass(frozen=True)
class Answer:
    """What the stand-in prints and how it exits for one first argument."""

    stdout: str = ""
    stderr: str = ""
    exit_status: int = 0
    sleep_seconds: float = 0


class ZfsCall(BaseModel):
    """One call the stand-in `zfs` saw."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    working_directory: Path


@dataclass(frozen=True)
class Zfs:
    """The stand-in `zfs` and the folder that holds its plan and its record."""

    path: Path
    folder: Path

    def calls(self) -> list[ZfsCall]:
        """The calls it recorded, in order."""
        return read_records(self.folder / CALLS, ZfsCall)

    def arguments(self) -> list[list[str]]:
        """The arguments of each call, in order."""
        return [call.arguments for call in self.calls()]

    def command(self, *words: str) -> str:
        """The command a fault names for a call of the stand-in with `words`."""
        return " ".join([str(self.path), *words])


def write_zfs(folder: Path, plan: dict[str, Answer] | None = None) -> Zfs:
    """Write the stand-in into `folder` with `plan` and return it."""
    path = write_script(folder / "zfs", ZFS_SCRIPT)
    answers = {first: asdict(answer) for first, answer in (plan or {}).items()}
    (folder / PLAN).write_text(json.dumps(answers), encoding="utf-8")
    return Zfs(path=path, folder=folder)


def snapshots_on(zfs: Zfs) -> ZfsSnapshots:
    """The adapter of the test's dataset and mount point, run on the stand-in."""
    return ZfsSnapshots(DATASET, MOUNT_POINT, executable=str(zfs.path))
