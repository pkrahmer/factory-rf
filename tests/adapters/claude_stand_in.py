"""A stand-in for `claude`: an executable that records each call and plays a scripted step."""

import json
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

CALLS = "calls.jsonl"
STEPS = "steps.json"
GIVEN = {"HOME": "/home/agent", "LANG": "C.UTF-8"}
REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)

SCRIPT = r"""
import json
import os
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
files = {}
for argument in arguments:
    try:
        if Path(argument).is_file():
            files[argument] = Path(argument).read_text(encoding="utf-8")
    except (OSError, ValueError):
        pass
calls = here / "calls.jsonl"
index = len(calls.read_text(encoding="utf-8").splitlines()) if calls.exists() else 0
record = {
    "arguments": arguments,
    "environment": dict(os.environ),
    "working_directory": os.getcwd(),
    "files": files,
}
with calls.open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
step = json.loads((here / "steps.json").read_text(encoding="utf-8"))[index]
for path, content in step["writes"].items():
    Path(path).write_text(content, encoding="utf-8")
sys.stdout.write(step["stdout_before_wait"])
sys.stdout.flush()
if step["wait_seconds"]:
    time.sleep(step["wait_seconds"])
sys.stdout.write(step["stdout"])
sys.stderr.write(step["stderr"])
sys.stdout.flush()
sys.exit(step["exit_status"])
"""


class Step(BaseModel):
    """What the stand-in does on one call: write files, print, wait, print, exit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    writes: dict[str, str] = {}
    stdout_before_wait: str = ""
    wait_seconds: float = 0
    stdout: str = ""
    stderr: str = ""
    exit_status: int = 0


class StandInCall(BaseModel):
    """What the stand-in saw on one call: its arguments, environment, directory and files."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    working_directory: Path
    files: dict[str, str]


def write_stand_in(directory: Path, steps: list[Step]) -> Path:
    """Write the stand-in into `directory`, to play `steps` one per call, and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / STEPS).write_text(
        json.dumps([step.model_dump() for step in steps]), encoding="utf-8"
    )
    path = directory / "claude"
    path.write_text(f"#!{sys.executable} -B\n{SCRIPT}", encoding="utf-8")
    path.chmod(0o755)
    return path


def read_calls(directory: Path) -> list[StandInCall]:
    """The calls the stand-in in `directory` recorded, in order; none when it was never called."""
    calls = directory / CALLS
    if not calls.exists():
        return []
    return [
        StandInCall.model_validate_json(line)
        for line in calls.read_text(encoding="utf-8").splitlines()
    ]


def claude_request(tmp_path: Path) -> AgentRunRequest:
    """A coder's request that works in `tmp_path / "work"` with a small given environment."""
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=30),
        working_directory=work,
        environment=GIVEN,
    )


def without_locale(environment: dict[str, str]) -> dict[str, str]:
    """`environment` without the `LC_CTYPE` a stand-in's Python adds in an empty environment."""
    return {name: value for name, value in environment.items() if name != "LC_CTYPE"}
