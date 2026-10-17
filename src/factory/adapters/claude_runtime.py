"""The agent runtime that runs an agent as one `claude -p` call under the operator's login."""

import json
import math
import shlex
import time
import uuid
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    JsonValue,
    NonNegativeFloat,
    NonNegativeInt,
    StrictBool,
    ValidationError,
)

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import (
    GUARD_COMMAND,
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    PermissionDenial,
    TokenCounts,
)
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoint, KillPoints

ENTRY_DESCRIPTION = (
    "your journal entry, without its number or your name: "
    "everything your instructions say the entry contains"
)

# Without these, `claude` would keep its own memory and read git instructions the factory
# does not give, and a Python hook would leave bytecode in the working copy.
SWITCHES = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}
GUARDED_TOOLS = "Edit|Write"
BUDGET_SUBTYPE = "error_max_budget_usd"
FINISH_MESSAGE = "Finish now: give your decision (question if the work is not done) and your entry."
MINIMUM_RESUME_BUDGET = Decimal("0.50")
VERSION_TIME_LIMIT = timedelta(seconds=30)
SUDO_EXECUTABLE = "/usr/bin/sudo"
SUDO_PREFIX = "sudo:"
TIMEOUT_EXECUTABLE = "timeout"
# The factory may not signal root's `sudo`, so the agent's own `timeout` kills at the limit;
# the factory's kill waits this much longer and fires only when the inner one did not.
SUDO_GRACE = timedelta(seconds=30)
# `timeout --signal=KILL` exits 128 + 9; `subprocess` reports a death by SIGKILL as -9.
KILL_STATUSES = frozenset({137, -9})
# The agent reads a run's files through its group and must not rewrite its own guard.
RUN_FILE_MODE = 0o640
CENT = Decimal("0.01")
# Claude Code's name for a token made by `claude setup-token`.
LOGIN_VARIABLE = "CLAUDE_CODE_OAUTH_TOKEN"
SHELL_EXECUTABLE = "/bin/sh"
LOGIN_PREFIX = "factory-login:"
# Run by the call's own shell, as the user the call runs as, so the factory never holds the
# token and it stands in no process's arguments. A shell variable cannot hold a zero byte, so
# the ASCII check counts the bytes left once the allowed ones are deleted.
LOGIN_SCRIPT = f"""\
login_file=$1
shift
if [ ! -e "$login_file" ]; then
    unset {LOGIN_VARIABLE}
    exec "$@"
fi
if [ ! -f "$login_file" ] || ! cat -- "$login_file" >/dev/null 2>&1; then
    printf '%s\\n' '{LOGIN_PREFIX} cannot be read' >&2
    exit 1
fi
other_bytes=$(LC_ALL=C tr -d '!-~ \\t\\r\\n' <"$login_file" 2>/dev/null | wc -c)
if [ $other_bytes -ne 0 ]; then
    printf '%s\\n' '{LOGIN_PREFIX} not ASCII text' >&2
    exit 1
fi
login=$(LC_ALL=C tr -d ' \\t\\r\\n' <"$login_file" 2>/dev/null)
if [ -z "$login" ]; then
    unset {LOGIN_VARIABLE}
    exec "$@"
fi
export {LOGIN_VARIABLE}="$login"
exec "$@"
"""


# A negative count or cost is no measure: such a reply does not parse, so the call is `died`.
class _Usage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    cache_read_input_tokens: NonNegativeInt = 0
    cache_creation_input_tokens: NonNegativeInt = 0


class _Denial(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    tool_name: str
    tool_input: JsonValue = None


class _StructuredOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    decision: str | None = None
    entry: str | None = None


class _Reply(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    subtype: str
    is_error: StrictBool
    num_turns: NonNegativeInt | None = None
    duration_api_ms: NonNegativeInt | None = None
    # A float as the JSON carries it; `Decimal(str(...))` keeps the digits it printed.
    total_cost_usd: NonNegativeFloat | None = None
    usage: _Usage | None = None
    permission_denials: list[_Denial] = []
    structured_output: _StructuredOutput | None = None


class _RunFiles(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    instructions: Path
    guard: Path
    hooks: Path

    @classmethod
    def of(cls, state_directory: Path, session: str) -> "_RunFiles":
        return cls(
            instructions=state_directory / f"instructions-{session}.md",
            guard=state_directory / f"guard-{session}.json",
            hooks=state_directory / f"hooks-{session}.json",
        )

    def remove(self) -> None:
        for path in (self.instructions, self.guard, self.hooks):
            path.unlink(missing_ok=True)


_ZERO = timedelta(0)


def _since(started: float) -> timedelta:
    return timedelta(seconds=time.monotonic() - started)


def _parse_reply(stdout: str) -> _Reply | None:
    try:
        return _Reply.model_validate_json(stdout)
    except ValidationError:
        return None


def _decision_schema(request: AgentRunRequest) -> str:
    schema = {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": request.allowed_decisions},
            "entry": {"type": "string", "description": ENTRY_DESCRIPTION},
        },
        "required": ["decision", "entry"],
        "additionalProperties": False,
    }
    return json.dumps(schema)


def _hook_settings(guard_file: Path) -> str:
    command = f"{GUARD_COMMAND} --settings {shlex.quote(str(guard_file))}"
    hook = {"type": "command", "command": command}
    return json.dumps({"hooks": {"PreToolUse": [{"matcher": GUARDED_TOOLS, "hooks": [hook]}]}})


def _arguments(request: AgentRunRequest, session: str, files: _RunFiles) -> list[str]:
    agent = request.agent
    arguments = ["-p", request.prompt, "--model", agent.model]
    if agent.effort is not None:
        arguments += ["--effort", agent.effort]
    arguments += ["--tools", ",".join(agent.tools), "--session-id", session]
    arguments += ["--append-system-prompt-file", str(files.instructions)]
    if request.guard is not None:
        arguments += ["--settings", str(files.hooks)]
    arguments += [
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
        "--strict-mcp-config",
        "--max-budget-usd",
        format(agent.budget_usd, "f"),
        "--output-format",
        "json",
        "--json-schema",
        _decision_schema(request),
    ]
    return arguments


def resume_budget(budget: Decimal) -> Decimal:
    """The budget of a call that resumes a session its budget stopped: a quarter, at least 0.50."""
    quarter = (budget / 4).quantize(CENT, rounding=ROUND_HALF_UP)
    return max(quarter, MINIMUM_RESUME_BUDGET)


def _resume_arguments(arguments: list[str], budget: Decimal) -> list[str]:
    resumed = list(arguments)
    resumed[resumed.index("-p") + 1] = FINISH_MESSAGE
    resumed[resumed.index("--session-id")] = "--resume"
    resumed[resumed.index("--max-budget-usd") + 1] = format(resume_budget(budget), "f")
    return resumed


def _end_reason(
    request: AgentRunRequest, process: ProcessResult, reply: _Reply | None
) -> EndReason:
    if process.timed_out:
        return "time_limit"
    # `claude` may exit non-zero on a budget stop; the reply still says why it stopped.
    if reply is not None and reply.subtype == BUDGET_SUBTYPE:
        return "budget"
    if process.exit_status != 0 or reply is None or reply.is_error:
        return "died"
    output = reply.structured_output
    if output is None or output.decision not in request.allowed_decisions:
        return "no_result"
    if output.entry is None or not output.entry.strip():
        return "no_result"
    return "completed"


def _tokens(usage: _Usage | None) -> TokenCounts | None:
    if usage is None or usage.input_tokens is None or usage.output_tokens is None:
        return None
    return TokenCounts(
        input=usage.input_tokens,
        output=usage.output_tokens,
        cache_read=usage.cache_read_input_tokens,
        cache_creation=usage.cache_creation_input_tokens,
    )


def _denials(reply: _Reply) -> list[PermissionDenial]:
    return [
        PermissionDenial(
            tool=denial.tool_name, detail=json.dumps(denial.tool_input, sort_keys=True)
        )
        for denial in reply.permission_denials
    ]


def _result(request: AgentRunRequest, process: ProcessResult) -> AgentRunResult:
    # The duration is the whole run's, so `run` sets it once the last call has ended.
    duration = _ZERO
    reply = _parse_reply(process.stdout)
    end_reason = _end_reason(request, process, reply)
    # A killed call's output is cut short, so whatever it printed is not its measure.
    if reply is None or process.timed_out:
        return AgentRunResult(end_reason=end_reason, duration=duration)
    output = reply.structured_output if end_reason == "completed" else None
    cost = None if reply.total_cost_usd is None else Decimal(str(reply.total_cost_usd))
    api_ms = reply.duration_api_ms
    model_duration = None if api_ms is None else timedelta(milliseconds=api_ms)
    return AgentRunResult(
        end_reason=end_reason,
        decision=None if output is None else output.decision,
        entry=None if output is None else output.entry,
        duration=duration,
        model_duration=model_duration,
        turns=reply.num_turns,
        tokens=_tokens(reply.usage),
        cost_usd=cost,
        permission_denials=_denials(reply),
    )


def _add[T: (int, Decimal, timedelta)](first: T | None, second: T | None) -> T | None:
    if first is None:
        return second
    if second is None:
        return first
    return first + second


def _add_tokens(first: TokenCounts | None, second: TokenCounts | None) -> TokenCounts | None:
    if first is None:
        return second
    if second is None:
        return first
    return TokenCounts(
        input=first.input + second.input,
        output=first.output + second.output,
        cache_read=first.cache_read + second.cache_read,
        cache_creation=first.cache_creation + second.cache_creation,
    )


def _resumed_result(first: AgentRunResult, second: AgentRunResult) -> AgentRunResult:
    denials = [*first.permission_denials, *second.permission_denials]
    # R24: a resume the time limit ended has no measures, and the first call's alone are partial.
    if second.end_reason == "time_limit":
        return second.model_copy(update={"permission_denials": denials})
    return second.model_copy(
        update={
            "model_duration": _add(first.model_duration, second.model_duration),
            "turns": _add(first.turns, second.turns),
            "cost_usd": _add(first.cost_usd, second.cost_usd),
            "tokens": _add_tokens(first.tokens, second.tokens),
            "permission_denials": denials,
        }
    )


def _sudo_line(stderr: str) -> str | None:
    for line in stderr.splitlines():
        if line.startswith(SUDO_PREFIX):
            return line
    return None


def _login_refusal(process: ProcessResult) -> str | None:
    if _parse_reply(process.stdout) is not None:
        return None
    for line in process.stderr.splitlines():
        if line.startswith(LOGIN_PREFIX):
            return line.removeprefix(LOGIN_PREFIX).strip()
    return None


def _sudo_refusal(request: AgentRunRequest, process: ProcessResult) -> str | None:
    if request.os_user is None:
        return None
    if _parse_reply(process.stdout) is not None and not process.timed_out:
        return None
    return _sudo_line(process.stderr)


def _killed_at_limit(
    request: AgentRunRequest, process: ProcessResult, time_limit: timedelta
) -> bool:
    if request.os_user is None or process.exit_status not in KILL_STATUSES:
        return False
    return process.duration >= time_limit


def _limit_argument(time_limit: timedelta) -> str:
    return f"{math.ceil(time_limit.total_seconds())}s"


def _first_word(output: str) -> str | None:
    for line in output.splitlines():
        if line.strip():
            return line.split()[0]
    return None


class ClaudeCodeRuntime(AgentRuntime):
    """Runs an agent as a `claude -p` call, with only the environment the request gives.

    A call stopped by its budget is resumed once to get the agent's decision and entry.
    """

    def __init__(
        self,
        executable: str,
        state_directory: Path,
        kill_points: KillPoints | None = None,
        *,
        version_time_limit: timedelta = VERSION_TIME_LIMIT,
        sudo_executable: str = SUDO_EXECUTABLE,
        login_file: Path | None = None,
    ) -> None:
        """Call `executable`, keep a run's files in `state_directory`, reach `kill_points`.

        A request with an operating-system user is started through `sudo_executable`.
        A run's calls get the token held in `login_file`, read by the call's own shell.
        """
        self._executable = executable
        self._login_file = login_file
        self._sudo_executable = sudo_executable
        self._state_directory = state_directory
        self._kill_points = kill_points
        self._version_time_limit = version_time_limit

    @property
    def sudo_executable(self) -> str:
        """The executable that starts a request as its operating-system user."""
        return self._sudo_executable

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` and turn the JSON it prints into a result.

        A budget stop resumes the session once within what is left of the time limit.
        A call that cannot be started, or whose files cannot be written, is `AgentRuntimeError`.
        """
        started = time.monotonic()
        session = str(uuid.uuid4())
        files = _RunFiles.of(self._state_directory, session)
        self._make_state_directory()
        try:
            self._write_files(request, files)
            arguments = _arguments(request, session, files)
            result = _result(request, self._call(request, arguments, request.time_limit))
            if result.end_reason == "budget":
                result = self._resume(request, arguments, result, started)
            result = result.model_copy(update={"duration": _since(started)})
            if self._kill_points is not None:
                self._kill_points.reach(KillPoint.AGENT_RUN)
            return result
        finally:
            files.remove()

    def version(self) -> str:
        """The version `claude --version` prints, such as `2.1.289`.

        A call that cannot be started, fails, reaches its limit or prints nothing is
        `AgentRuntimeError`.
        """
        process_request = ProcessRequest(
            argv=[self._executable, "--version"],
            cwd=Path.cwd(),
            time_limit=self._version_time_limit,
        )
        try:
            process = run_process(process_request)
        except OSError as exc:
            raise AgentRuntimeError(f"cannot start {self._executable}: {exc}") from exc
        if process.timed_out or process.exit_status != 0:
            raise AgentRuntimeError(f"{self._executable} --version failed: {process.stderr}")
        version = _first_word(process.stdout)
        if version is None:
            raise AgentRuntimeError(f"{self._executable} --version printed nothing")
        return version

    def _resume(
        self,
        request: AgentRunRequest,
        arguments: list[str],
        first: AgentRunResult,
        started: float,
    ) -> AgentRunResult:
        left = request.time_limit - _since(started)
        if left <= _ZERO:
            second = AgentRunResult(end_reason="time_limit", duration=_ZERO)
        else:
            resumed = _resume_arguments(arguments, request.agent.budget_usd)
            second = _result(request, self._call(request, resumed, left))
        return _resumed_result(first, second)

    def _make_state_directory(self) -> None:
        try:
            self._state_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise self._state_error(exc) from exc

    def _state_error(self, exc: OSError) -> AgentRuntimeError:
        return AgentRuntimeError(f"cannot write the state directory {self._state_directory}: {exc}")

    def _write_files(self, request: AgentRunRequest, files: _RunFiles) -> None:
        try:
            written = {files.instructions: request.agent.instructions}
            if request.guard is not None:
                written[files.guard] = request.guard.model_dump_json()
                written[files.hooks] = _hook_settings(files.guard)
            for path, text in written.items():
                path.write_text(text, encoding="utf-8")
                path.chmod(RUN_FILE_MODE)
        except OSError as exc:
            raise self._state_error(exc) from exc

    def _call(
        self, request: AgentRunRequest, arguments: list[str], time_limit: timedelta
    ) -> ProcessResult:
        process = self._start(self._process_request(request, arguments, time_limit))
        if _killed_at_limit(request, process, time_limit):
            # The inner kill ends the call as the factory's own would: read as its time limit.
            process = process.model_copy(update={"timed_out": True})
        refusal = _sudo_refusal(request, process)
        if refusal is not None:
            # A refused `sudo` is a misconfiguration of the machine, not a stalled agent.
            raise AgentRuntimeError(f"{self._sudo_executable} refused the agent run: {refusal}")
        self._check_login(process)
        return process

    def _check_login(self, process: ProcessResult) -> None:
        if self._login_file is None:
            return
        reason = _login_refusal(process)
        if reason is not None:
            raise AgentRuntimeError(
                f"cannot read the agent's login file {self._login_file}: {reason}"
            )

    def _claude_argv(self, arguments: list[str]) -> list[str]:
        claude = [self._executable, *arguments]
        if self._login_file is None:
            return claude
        login = [SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", str(self._login_file)]
        return [*login, *claude]

    def _process_request(
        self, request: AgentRunRequest, arguments: list[str], time_limit: timedelta
    ) -> ProcessRequest:
        # The login comes from the file or not at all, never from the request.
        given = {
            name: value for name, value in request.environment.items() if name != LOGIN_VARIABLE
        }
        environment = {**given, **SWITCHES}
        argv = self._claude_argv(arguments)
        if request.os_user is None:
            return ProcessRequest(
                argv=argv, cwd=request.working_directory, env=environment, time_limit=time_limit
            )
        # `env -i` drops whatever `sudo` keeps, so the agent sees the request's environment alone.
        assignments = [f"{name}={value}" for name, value in environment.items()]
        sudo = [self._sudo_executable, "-n", "-u", request.os_user, "--"]
        timeout = [TIMEOUT_EXECUTABLE, "--signal=KILL", _limit_argument(time_limit)]
        return ProcessRequest(
            argv=[*sudo, *timeout, "env", "-i", *assignments, *argv],
            cwd=request.working_directory,
            env={},
            time_limit=time_limit + SUDO_GRACE,
        )

    def _start(self, process_request: ProcessRequest) -> ProcessResult:
        try:
            return run_process(process_request)
        except OSError as exc:
            program = process_request.argv[0]
            raise AgentRuntimeError(f"cannot start {program}: {exc}") from exc
