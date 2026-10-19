"""A stand-in for `opencode`: plays scripted steps of JSON events and records each call."""

import json
import sys
from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from adapters.claude_stand_in import STEPS, Step
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

CONFIG_MODES = "config-modes.jsonl"
SESSION = "ses_a"
MODELS = {"sonnet": "anthropic/claude-sonnet-5-5"}
TOKENS: Mapping[str, object] = {
    "input": 10,
    "output": 5,
    "reasoning": 2,
    "cache": {"read": 100, "write": 20},
}

# Records its arguments, environment, directory and the text of the file `OPENCODE_CONFIG`
# names in the shape of `claude_stand_in.StandInCall`, and that file's mode beside it.
SCRIPT = r"""
import json
import os
import stat
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
files = {}
mode = None
config = os.environ.get("OPENCODE_CONFIG")
if config:
    try:
        files[config] = Path(config).read_text(encoding="utf-8")
        mode = stat.S_IMODE(Path(config).stat().st_mode)
    except OSError:
        pass
calls = here / "calls.jsonl"
index = len(calls.read_text(encoding="utf-8").splitlines()) if calls.exists() else 0
record = {
    "arguments": sys.argv[1:],
    "environment": dict(os.environ),
    "working_directory": os.getcwd(),
    "files": files,
}
with calls.open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
with (here / "config-modes.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(mode) + "\n")
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


def write_opencode(directory: Path, steps: list[Step]) -> Path:
    """Write the stand-in into `directory`, to play `steps` one per call, and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / STEPS).write_text(
        json.dumps([step.model_dump() for step in steps]), encoding="utf-8"
    )
    path = directory / "opencode"
    path.write_text(f"#!{sys.executable}\n{SCRIPT}", encoding="utf-8")
    path.chmod(0o755)
    return path


def read_config_modes(directory: Path) -> list[int | None]:
    """The mode of the configuration file at each call, `None` where there was none."""
    modes = directory / CONFIG_MODES
    if not modes.exists():
        return []
    return [json.loads(line) for line in modes.read_text(encoding="utf-8").splitlines()]


def _line(event: Mapping[str, object]) -> str:
    return json.dumps(event)


def step_start(timestamp: int = 1000) -> str:
    """The line of a `step_start` event."""
    return _line(
        {
            "type": "step_start",
            "timestamp": timestamp,
            "sessionID": SESSION,
            "part": {"type": "step-start"},
        }
    )


def tool_use(  # noqa: PLR0913 - one parameter per field of the event
    timestamp: int = 1500,
    *,
    tool: str = "bash",
    tool_input: object = None,
    status: str = "error",
    error: str | None = "permission denied by rule git push*",
    start: int = 1200,
    end: int = 1700,
) -> str:
    """The line of a `tool_use` event; its input is `{"command": "git push"}` unless given."""
    state: dict[str, object] = {
        "status": status,
        "input": {"command": "git push"} if tool_input is None else tool_input,
        "time": {"start": start, "end": end},
    }
    if error is not None:
        state["error"] = error
    else:
        state["output"] = ""
    return _line(
        {
            "type": "tool_use",
            "timestamp": timestamp,
            "sessionID": SESSION,
            "part": {"type": "tool", "tool": tool, "state": state},
        }
    )


def text(body: str, timestamp: int = 1900) -> str:
    """The line of a `text` event with `body`."""
    return _line(
        {
            "type": "text",
            "timestamp": timestamp,
            "sessionID": SESSION,
            "part": {"type": "text", "text": body},
        }
    )


def step_finish(
    timestamp: int = 2000,
    *,
    cost: float | None = 0.012,
    tokens: Mapping[str, object] | None = TOKENS,
) -> str:
    """The line of a `step_finish` event; a `None` cost or tokens leaves that key out."""
    part: dict[str, object] = {"type": "step-finish", "reason": "stop"}
    if cost is not None:
        part["cost"] = cost
    if tokens is not None:
        part["tokens"] = dict(tokens)
    return _line(
        {"type": "step_finish", "timestamp": timestamp, "sessionID": SESSION, "part": part}
    )


def error(
    message: str = "Precondition Required",
    *,
    name: str = "APIError",
    status_code: int = 428,
    timestamp: int = 2100,
) -> str:
    """The line of an `error` event."""
    return _line(
        {
            "type": "error",
            "timestamp": timestamp,
            "sessionID": SESSION,
            "error": {"name": name, "data": {"message": message, "statusCode": status_code}},
        }
    )


def result_text(decision: str = "doing", entry: str = "Built it.") -> str:
    """A final message that ends with a result block of `decision` and `entry`."""
    return f"Done.\n<factory-result>\ndecision: {decision}\nentry:\n{entry}\n</factory-result>"


def stdout(*lines: str) -> str:
    """The standard output of these event lines, one per line."""
    return "".join(f"{line}\n" for line in lines)


def opencode_request(
    work: Path,
    *,
    model: str = "sonnet",
    tools: tuple[str, ...] = ("Read", "Bash"),
    environment: Mapping[str, str] | None = None,
    time_limit: timedelta = timedelta(seconds=30),
    os_user: str | None = None,
) -> AgentRunRequest:
    """A coder's request with the prompt `Stage: doing` in `work`, which is made if missing."""
    work.mkdir(parents=True, exist_ok=True)
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model=model,
            tools=list(tools),
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=time_limit,
        working_directory=work,
        environment={"HOME": "/home/agent", "LANG": "C.UTF-8"}
        if environment is None
        else dict(environment),
        os_user=os_user,
    )
