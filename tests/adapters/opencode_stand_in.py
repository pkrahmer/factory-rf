"""A stand-in for `opencode`: plays scripted steps of JSON events and records each call."""

import json
import sys
from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from adapters.claude_stand_in import STEPS, Step
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.kill_points import KillPoints
from factory.domain.provider_limits import ProviderLimit

CONFIG_MODES = "config-modes.jsonl"
SESSION = "ses_a"
MODELS = {"sonnet": "anthropic/claude-sonnet-5-5"}
TOKENS: Mapping[str, object] = {
    "input": 10,
    "output": 5,
    "reasoning": 2,
    "cache": {"read": 100, "write": 20},
}
# A stopped stand-in waits far longer than a stop may take, so a missed stop is plain.
WAIT_SECONDS = 30
BOUND_SECONDS = 20
RESUME_ENTRY = "Stopped at the budget."

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
    path.write_text(f"#!{sys.executable} -B\n{SCRIPT}", encoding="utf-8")
    path.chmod(0o755)
    return path


def write_agent_settings(folder: Path, text_of_file: str) -> Path:
    """Write `text_of_file` as `settings.json` in `folder`, created if missing; return its path."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "settings.json"
    path.write_text(text_of_file, encoding="utf-8")
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


def stand_in_runtime(  # noqa: PLR0913 - one parameter per setting a test varies
    tmp_path: Path,
    steps: list[Step],
    *,
    settings_file: Path | None = None,
    kill_points: KillPoints | None = None,
    provider_limit: ProviderLimit | None = None,
    stderr_first: str | None = None,
) -> OpencodeRuntime:
    """A runtime that calls the stand-in in `tmp_path / "bin"`, playing `steps`.

    With `stderr_first`, the runtime calls a wrapper that prints that line on standard error
    and then becomes the stand-in, since the stand-in itself writes standard error last.
    """
    executable = write_opencode(tmp_path / "bin", steps)
    if stderr_first is not None:
        executable = _stderr_first(tmp_path, executable, stderr_first)
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    return OpencodeRuntime(
        str(executable),
        state,
        kill_points,
        models=MODELS,
        settings_file=settings_file,
        provider_limit=provider_limit,
    )


def _stderr_first(tmp_path: Path, executable: Path, line: str) -> Path:
    wrapper = tmp_path / "wrapper" / "opencode"
    wrapper.parent.mkdir()
    wrapper.write_text(
        f"#!{sys.executable} -B\n"
        "import os\nimport sys\n"
        f"sys.stderr.write({line!r} + '\\n')\n"
        "sys.stderr.flush()\n"
        f"os.execv({str(executable)!r}, [{str(executable)!r}, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return wrapper


def budget_steps(*costs: float) -> list[str]:
    """The event lines of one step per cost, each a `step_start` and a `step_finish`."""
    lines: list[str] = []
    for index, cost in enumerate(costs):
        lines += [step_start(1000 * index), step_finish(1000 * index + 500, cost=cost)]
    return lines


def _without_session(line: str) -> str:
    return line.replace(f', "sessionID": "{SESSION}"', "")


def over_budget(*, with_session: bool = True) -> Step:
    """A first call whose steps of 0.4, 0.4 and 0.21 pass a budget of 1, then a long wait."""
    lines = budget_steps(0.4, 0.4, 0.21)
    if not with_session:
        lines = [_without_session(line) for line in lines]
    return Step(stdout_before_wait=stdout(*lines), wait_seconds=WAIT_SECONDS)


RESUME_REPLY = Step(
    stdout=stdout(
        step_start(10_000),
        text(result_text("question", RESUME_ENTRY), 10_200),
        step_finish(10_500, cost=0.1),
    )
)

REPLY_EVENTS = stdout(step_start(), text(result_text()), step_finish())
REPLY = Step(stdout=REPLY_EVENTS)
WAITING = Step(stdout_before_wait=stdout(step_start()), wait_seconds=WAIT_SECONDS)
