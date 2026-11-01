"""The setup script's step `datasets`, run with stand-ins up to the delegation: the first base."""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from git_support import write_executable
from vm_support import REQUIRED, SYSTEM_PATH, in_order, run_setup, step_texts

POOL = "tank"
DATASET = f"{POOL}/factory/vm"
BASE = f"{DATASET}@base"
QUOTA = "30G"
WORK = "/srv/factory/vm/work"
FOUND = (
    f"setup: datasets: found {POOL}/factory and {DATASET} at {WORK} "
    f"with the quota {QUOTA} and its base"
)
MADE_BASE = f"made the first base {BASE}"

# Every command the steps before `delegation` call that would read or change the machine.
# `zfs allow -u` fails, so the run ends at the step `delegation` before anything is written.
_STAND_IN = """
import json, os, sys, tempfile
name = {name!r}
argv = sys.argv[1:]
with open({log!r}, "a", encoding="utf-8") as file:
    file.write(json.dumps({{"name": name, "argv": argv}}) + "\\n")
if name == "id":
    print(0)
elif name == "mktemp":
    handle, path = tempfile.mkstemp(dir={folder!r})
    os.close(handle)
    print(path)
elif name == "stat":
    print({owner!r})
elif name == "zfs" and argv[0] == "list":
    if argv[-1] not in {present!r}:
        sys.exit(1)
    print(argv[-1])
elif name == "zfs" and argv[0] == "get":
    print("lz4\\noff" if "compression,atime" in argv else {quota!r})
elif name == "zfs" and argv[0] == "allow" and "-u" in argv:
    sys.exit(1)
elif name == "zfs" and argv[0] == "snapshot" and {snapshot_fails!r}:
    sys.exit(1)
"""
STAND_INS = ("id", "mktemp", "dpkg-query", "grep", "zpool", "loginctl", "stat", "install", "zfs")


@dataclass(frozen=True)
class Machine:
    """What the stand-ins report: the datasets and base that exist, the quota and the owner."""

    dataset: bool
    base: bool
    quota: str = QUOTA
    owner: str = "factory:factory"
    snapshot_fails: bool = False


@dataclass(frozen=True)
class Run:
    """A run of the setup script: its result and the stand-ins' calls, oldest first."""

    result: ProcessResult
    calls: list[tuple[str, list[str]]]

    def zfs(self) -> list[list[str]]:
        """The arguments of each `zfs` call, oldest first."""
        return [argv for name, argv in self.calls if name == "zfs"]

    def datasets_lines(self) -> list[str]:
        """The lines the step `datasets` printed on standard output."""
        return [
            line for line in self.result.stdout.splitlines() if line.startswith("setup: datasets: ")
        ]


def _run(tmp_path: Path, machine: Machine) -> Run:
    stand_ins, scratch = tmp_path / "stand-ins", tmp_path / "scratch"
    stand_ins.mkdir()
    scratch.mkdir()
    log = tmp_path / "calls.jsonl"
    present = [f"{POOL}/factory"]
    present += [DATASET] if machine.dataset else []
    present += [BASE] if machine.base else []
    for name in STAND_INS:
        body = _STAND_IN.format(
            name=name,
            log=str(log),
            folder=str(scratch),
            owner=machine.owner,
            present=present,
            quota=machine.quota,
            snapshot_fails=machine.snapshot_fails,
        )
        write_executable(stand_ins, body, name)
    result = run_setup(tmp_path, REQUIRED, path=f"{stand_ins}:{SYSTEM_PATH}")
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    calls = [(record["name"], record["argv"]) for record in map(json.loads, lines)]
    return Run(result, calls)


@pytest.fixture
def made(tmp_path: Path) -> Run:
    """A run on a machine whose dataset is made by the step, without a base."""
    return _run(tmp_path, Machine(dataset=False, base=False, quota="none", owner="root:root"))


@pytest.fixture
def complete(tmp_path: Path) -> Run:
    """A run on a machine whose dataset, quota, owner and base are all in place."""
    return _run(tmp_path, Machine(dataset=True, base=True))


@pytest.mark.parametrize(
    "machine",
    [
        pytest.param(
            Machine(dataset=False, base=False, quota="none", owner="root:root"), id="made"
        ),
        pytest.param(Machine(dataset=True, base=False), id="existing"),
    ],
)
def test_a_missing_base_is_taken_once_and_named(tmp_path: Path, machine: Machine) -> None:
    run = _run(tmp_path, machine)

    assert [argv for argv in run.zfs() if argv[0] == "snapshot"] == [["snapshot", BASE]]
    assert any(MADE_BASE in line for line in run.datasets_lines()), run.result.stdout


def test_a_made_dataset_s_first_base_follows_its_create_quota_and_owner(
    made: Run, code: str
) -> None:
    calls = made.zfs()
    taken = calls.index(["snapshot", BASE])

    assert calls.index(["create", "-o", f"mountpoint={WORK}", DATASET]) < taken
    assert calls.index(["set", f"quota={QUOTA}", DATASET]) < taken
    assert in_order(step_texts(code)["datasets"], ["install -d -o factory", "zfs snapshot"])


def test_an_existing_base_is_left_alone_and_the_step_changes_nothing(complete: Run) -> None:
    calls = complete.zfs()

    assert [argv for argv in calls if argv[0] in ("snapshot", "create", "set")] == []
    assert [argv for name, argv in complete.calls if name == "install"] == []
    assert complete.datasets_lines() == [FOUND]


def test_the_first_base_is_taken_before_the_delegation(made: Run) -> None:
    calls = made.zfs()
    allows = [index for index, argv in enumerate(calls) if argv[0] == "allow"]

    assert allows != []
    assert calls.index(["snapshot", BASE]) < allows[0]


def test_the_step_s_closing_line_ends_with_its_base(complete: Run) -> None:
    lines = complete.datasets_lines()

    assert len(lines) == 1
    assert lines[0].endswith("and its base")


def test_a_failing_snapshot_stops_the_script_before_the_step_s_closing_line(
    tmp_path: Path,
) -> None:
    run = _run(tmp_path, Machine(dataset=True, base=False, snapshot_fails=True))

    assert ["snapshot", BASE] in run.zfs()
    assert run.result.exit_status != 0
    assert run.datasets_lines() == []
