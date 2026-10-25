"""The stand-in `sudo` and the stand-in leftovers program of the runtimes' leftovers tests."""

import json
import os
import pwd
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from confine_support import read_records, write_script

# A user no test runs as, so that the runtime starts the program for it.
OTHER_USER = "factory-test-other"
LEFTOVERS_LINE = "factory-leftovers: 1 processes left after 50 rounds: 7"
SUDO_LINE = "sudo: a password is required"
SUDO_CALLS = "sudo-calls.jsonl"
PROGRAM_CALLS = "program-calls.jsonl"

# A `sudo` that records its arguments and working directory, refuses the agent's run when its
# plan says so, and otherwise runs what follows `--`.
SUDO_SCRIPT = r"""
import json
import os
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
record = {"arguments": arguments, "working_directory": os.getcwd()}
with (here / "sudo-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
plan = json.loads((here / "sudo-plan.json").read_text(encoding="utf-8"))
rest = arguments[arguments.index("--") + 1 :]
if plan["refusal"] and rest[0] not in (plan["program"], "/bin/sh"):
    sys.stderr.write(plan["refusal"])
    sys.exit(1)
os.execvp(rest[0], rest)
"""

# The leftovers program's stand-in: records its arguments, writes its planned standard error
# and exits with its planned status.
PROGRAM_SCRIPT = r"""
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
with (here / "program-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps({"arguments": sys.argv[1:]}) + "\n")
plan = json.loads((here / "program-plan.json").read_text(encoding="utf-8"))
sys.stderr.write(plan["stderr"])
sys.exit(plan["exit_status"])
"""


class SudoRecord(BaseModel):
    """One call the stand-in `sudo` saw: its arguments and its working directory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    working_directory: Path


class ProgramRecord(BaseModel):
    """One call the stand-in program saw: its arguments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]


def own_user() -> str:
    """The name of the user the tests run as."""
    return pwd.getpwuid(os.getuid()).pw_name


def write_program(directory: Path, *, exit_status: int = 0, stderr: str = "") -> Path:
    """Write the stand-in program into `directory`, exiting as planned; return its path."""
    path = write_script(directory / "leftovers", PROGRAM_SCRIPT)
    plan = {"exit_status": exit_status, "stderr": stderr}
    (directory / "program-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return path


def write_sudo(directory: Path, program: Path, *, refusal: str = "") -> Path:
    """Write the stand-in `sudo` into `directory`, refusing the run with `refusal` if given."""
    path = write_script(directory / "sudo", SUDO_SCRIPT)
    plan = {"refusal": refusal, "program": str(program)}
    (directory / "sudo-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return path


def sudo_records(directory: Path) -> list[SudoRecord]:
    """The calls the stand-in `sudo` in `directory` recorded, in order."""
    return read_records(directory / SUDO_CALLS, SudoRecord)


def program_calls(directory: Path) -> list[list[str]]:
    """The arguments of each call the stand-in program in `directory` recorded, in order."""
    return [record.arguments for record in read_records(directory / PROGRAM_CALLS, ProgramRecord)]


def kind(record: SudoRecord, program: Path) -> str:
    """`program` or `run`: what the `sudo` call of `record` started."""
    rest = record.arguments[record.arguments.index("--") + 1 :]
    if rest[0] == str(program):
        return "program"
    return "run"


def kinds(directory: Path, program: Path) -> list[str]:
    """What each `sudo` call recorded in `directory` started, in order."""
    return [kind(record, program) for record in sudo_records(directory)]
