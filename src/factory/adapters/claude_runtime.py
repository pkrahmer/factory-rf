"""The agent runtime that runs an agent as one `claude -p` call under the operator's login."""

import json
import tempfile
import time
import uuid
from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
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

from factory.adapters.agent_launch import (
    CLEANUP_SCRIPT,
    CLEANUP_TIME_LIMIT,
    ENTRY_DESCRIPTION,
    FINISH_MESSAGE,
    LOGIN_PREFIX,
    LOGIN_SCRIPT,
    LOGIN_VARIABLE,
    RUN_FILE_MODE,
    SHELL_EXECUTABLE,
    SUDO_EXECUTABLE,
    VERSION_TIME_LIMIT,
    CallEnd,
    Launch,
    LoginFiles,
    Starters,
    cleanup_launch,
    confined_argv,
    denied_path,
    device_confinement,
    due_leftovers_launch,
    finished_run,
    leftovers_fault,
    login_argv,
    login_used,
    read_call_end,
    request_home,
    resume_budget,
    run_launch,
    since,
    state_directory_error,
    temporary_folder,
    version_printed,
)
from factory.adapters.process import ProcessRequest, ProcessResult, own_identity, run_process
from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import (
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    PermissionDenial,
    TokenCounts,
    resumed_result,
)
from factory.domain.confinement import DEVICE_FILES, DEVICE_FOLDERS, Confinement
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoints
from factory.domain.provider_limits import ProviderLimit, limit_in_text, named_wait

# These names moved to the shared launch module; earlier callers still import them here.
__all__ = [
    "CLEANUP_SCRIPT",
    "CLEANUP_TIME_LIMIT",
    "ENTRY_DESCRIPTION",
    "FINISH_MESSAGE",
    "LOGIN_PREFIX",
    "LOGIN_SCRIPT",
    "LOGIN_VARIABLE",
    "SHELL_EXECUTABLE",
    "SUDO_EXECUTABLE",
    "VERSION_TIME_LIMIT",
    "ClaudeCodeRuntime",
    "resume_budget",
]

# Without these, `claude` would keep its own memory and read git instructions the factory
# does not give, and Python the agent starts would leave bytecode in the working copy.
SWITCHES = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}
BUDGET_SUBTYPE = "error_max_budget_usd"
# Claude Code keeps its `.claude.json` in this folder rather than in the home's root, so a
# confined run keeps it inside the runtime's own folder, which the rules allow.
CONFIG_VARIABLE = "CLAUDE_CONFIG_DIR"
RUNTIME_FOLDER = ".claude"
# Where Claude Code keeps a login made by hand in the agent's home.
LOGIN_STATE_FILE = ".claude/.credentials.json"
_PATH_KEYS = ("file_path", "notebook_path")


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
    result: str | None = None


class _RunFiles(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    instructions: Path
    rules: Path
    temporary: Path

    @classmethod
    def of(cls, state_directory: Path, temporary_root: Path, session: str) -> "_RunFiles":
        return cls(
            instructions=state_directory / f"instructions-{session}.md",
            rules=state_directory / f"confine-{session}.json",
            temporary=temporary_folder(temporary_root, session),
        )

    def remove(self) -> None:
        for path in (self.instructions, self.rules):
            path.unlink(missing_ok=True)


_ZERO = timedelta(0)


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


def _session_arguments(request: AgentRunRequest, new_session: str) -> list[str]:
    if request.resume_session is not None:
        return ["--resume", request.resume_session]
    return ["--session-id", new_session]


def _arguments(request: AgentRunRequest, new_session: str, files: _RunFiles) -> list[str]:
    agent = request.agent
    arguments = ["-p", request.prompt, "--model", agent.model]
    if agent.effort is not None:
        arguments += ["--effort", agent.effort]
    arguments += ["--tools", ",".join(agent.tools), *_session_arguments(request, new_session)]
    arguments += ["--append-system-prompt-file", str(files.instructions)]
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


def _resume_arguments(arguments: list[str], budget: Decimal) -> list[str]:
    resumed = list(arguments)
    resumed[resumed.index("-p") + 1] = FINISH_MESSAGE
    # A call that already resumed a named session resumes it again as it is.
    if "--session-id" in resumed:
        resumed[resumed.index("--session-id")] = "--resume"
    resumed[resumed.index("--max-budget-usd") + 1] = format(resume_budget(budget), "f")
    return resumed


def _limit_text(process: ProcessResult, reply: _Reply | None, limit: ProviderLimit) -> str | None:
    """The error result or standard error line that holds the provider's limit, if one does."""
    # The agent's own text is never searched: only an error reply, or standard error without one.
    if reply is not None:
        refused = reply.is_error and reply.result is not None and limit_in_text(reply.result, limit)
        return reply.result if refused else None
    lines = process.stderr.splitlines()
    return next((line for line in lines if limit_in_text(line, limit)), None)


def _answered(request: AgentRunRequest, output: _StructuredOutput | None) -> bool:
    if output is None or output.decision not in request.allowed_decisions:
        return False
    return output.entry is not None and bool(output.entry.strip())


def _end_reason(
    request: AgentRunRequest,
    process: ProcessResult,
    reply: _Reply | None,
    limit_text: str | None,
) -> EndReason:
    if process.timed_out:
        return "time_limit"
    # `claude` may exit non-zero on a budget stop; the reply still says why it stopped.
    if reply is not None and reply.subtype == BUDGET_SUBTYPE:
        return "budget"
    if limit_text is not None:
        return "provider_limit"
    if process.exit_status != 0 or reply is None or reply.is_error:
        return "died"
    return "completed" if _answered(request, reply.structured_output) else "no_result"


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
            tool=denial.tool_name,
            detail=json.dumps(denial.tool_input, sort_keys=True),
            path=denied_path(denial.tool_input, _PATH_KEYS),
        )
        for denial in reply.permission_denials
    ]


def _result(
    request: AgentRunRequest, process: ProcessResult, session: str | None, limit: ProviderLimit
) -> AgentRunResult:
    # The duration is the whole run's, so `run` sets it once the last call has ended.
    duration = _ZERO
    reply = _parse_reply(process.stdout)
    limit_text = _limit_text(process, reply, limit)
    end_reason = _end_reason(request, process, reply, limit_text)
    login = login_used(process.stderr)
    limit_wait = (
        named_wait(limit_text)
        if end_reason == "provider_limit" and limit_text is not None
        else None
    )
    # A killed call's output is cut short, so whatever it printed is not its measure.
    if reply is None or process.timed_out:
        return AgentRunResult(
            end_reason=end_reason,
            duration=duration,
            login=login,
            session=session,
            limit_wait=limit_wait,
        )
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
        login=login,
        session=session,
        limit_wait=limit_wait,
    )


def _confinement(request: AgentRunRequest, temporary: Path) -> Confinement:
    return device_confinement(
        request,
        temporary,
        runtime_folders=[RUNTIME_FOLDER],
        device_folders=DEVICE_FOLDERS,
        device_files=DEVICE_FILES,
    )


def _request_of(started: Launch, cwd: Path) -> ProcessRequest:
    return ProcessRequest(
        argv=started.argv, cwd=cwd, env=started.env, time_limit=started.time_limit
    )


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
        confine_executable: str | None = None,
        temporary_root: Path | None = None,
        api_login_file: Path | None = None,
        provider_limit: ProviderLimit | None = None,
        leftovers: Sequence[str] | None = None,
    ) -> None:
        """Call `executable`, keep a run's files in `state_directory`, reach `kill_points`.

        A request with an operating-system user is started through `sudo_executable`.
        A run's calls get the key held in `api_login_file`, or else the token held in
        `login_file`, read by the call's own shell.
        With `confine_executable`, every call starts through it with the run's rules and
        its own temporary folder under `temporary_root`, the system's by default.
        A call refused by `provider_limit`, the default limit when `None`, ends `provider_limit`.
        Every call as another user is followed by `leftovers`, the program that ends that
        user's processes, when it is set.
        """
        self._executable = executable
        self._starters = Starters(
            sudo_executable=sudo_executable,
            confine_executable=confine_executable,
            leftovers=None if leftovers is None else list(leftovers),
            login_files=LoginFiles(subscription=login_file, api=api_login_file),
        )
        self._temporary_root = (
            Path(tempfile.gettempdir()) if temporary_root is None else temporary_root
        )
        self._state_directory = state_directory
        self._kill_points = kill_points
        self._version_time_limit = version_time_limit
        self._provider_limit = ProviderLimit() if provider_limit is None else provider_limit

    @property
    def sudo_executable(self) -> str:
        """The executable that starts a request as its operating-system user."""
        return self._starters.sudo_executable

    @property
    def confine_executable(self) -> str | None:
        """The wrapper every call starts through, or `None` when calls are not confined."""
        return self._starters.confine_executable

    @property
    def leftovers(self) -> list[str] | None:
        """The words that start the program ending the agent's leftover processes, or `None`."""
        return self._starters.leftovers

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` and turn the JSON it prints into a result.

        A request's `resume_session` is resumed; otherwise the run starts a new session.
        A budget stop resumes the session once within what is left of the time limit.
        A call that cannot be started, or whose files cannot be written, is `AgentRuntimeError`.
        """
        started = time.monotonic()
        # The run's files take a fresh id even when the session is resumed, so no run's files
        # meet another's.
        new_session = str(uuid.uuid4())
        session = request.resume_session or new_session
        files = _RunFiles.of(self._state_directory, self._temporary_root, new_session)
        self._make_state_directory()
        try:
            self._write_files(request, files)
            arguments = _arguments(request, new_session, files)
            process = self._call(request, files, arguments, request.time_limit)
            result = _result(request, process, session, self._provider_limit)
            if result.end_reason == "budget":
                result = self._resume(request, files, arguments, result, started)
            return finished_run(result, started, self._kill_points)
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
        process = self._start(process_request)
        return version_printed(
            self._executable,
            failed=process.timed_out or process.exit_status != 0,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    def _resume(
        self,
        request: AgentRunRequest,
        files: _RunFiles,
        arguments: list[str],
        first: AgentRunResult,
        started: float,
    ) -> AgentRunResult:
        left = request.time_limit - since(started)
        if left <= _ZERO:
            second = AgentRunResult(end_reason="time_limit", duration=_ZERO)
        else:
            resumed = _resume_arguments(arguments, request.agent.budget_usd)
            process = self._call(request, files, resumed, left)
            second = _result(request, process, first.session, self._provider_limit)
        return resumed_result(first, second)

    def _make_state_directory(self) -> None:
        try:
            self._state_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise self._state_error(exc) from exc

    def _state_error(self, exc: OSError) -> AgentRuntimeError:
        return state_directory_error(self._state_directory, exc)

    def _write_files(self, request: AgentRunRequest, files: _RunFiles) -> None:
        try:
            written = {files.instructions: request.agent.instructions}
            if self._starters.confine_executable is not None:
                written[files.rules] = _confinement(request, files.temporary).model_dump_json()
            for path, text in written.items():
                path.write_text(text, encoding="utf-8")
                path.chmod(RUN_FILE_MODE)
        except OSError as exc:
            raise self._state_error(exc) from exc

    def _call(
        self,
        request: AgentRunRequest,
        files: _RunFiles,
        arguments: list[str],
        time_limit: timedelta,
    ) -> ProcessResult:
        process = self._start(self._process_request(request, files, arguments, time_limit))
        leftovers_error = self._end_leftovers(request)
        if self._starters.confine_executable is not None:
            self._remove_temporary_folder(request, files.temporary)
        end = CallEnd(
            stderr=process.stderr,
            printed=_parse_reply(process.stdout) is not None,
            exit_status=process.exit_status,
            duration=process.duration,
            timed_out=process.timed_out,
        )
        timed_out = read_call_end(
            end, time_limit=time_limit, os_user=request.os_user, starters=self._starters
        )
        process = process.model_copy(update={"timed_out": timed_out})
        if leftovers_error is not None:
            raise AgentRuntimeError(leftovers_error)
        return process

    def _end_leftovers(self, request: AgentRunRequest) -> str | None:
        # The program's fault, or `None` when it ended them or was not due.
        started = due_leftovers_launch(self._starters, request.os_user, own_identity().user)
        if started is None:
            return None
        # From the root, so the program holds no folder of the run open.
        process = self._start(_request_of(started, Path("/")))
        return leftovers_fault(
            exit_status=process.exit_status, timed_out=process.timed_out, stderr=process.stderr
        )

    def _remove_temporary_folder(self, request: AgentRunRequest, temporary: Path) -> None:
        # Its status is not read: a folder left behind changes no run's result.
        removal = cleanup_launch(
            SHELL_EXECUTABLE,
            temporary,
            os_user=request.os_user,
            sudo_executable=self._starters.sudo_executable,
            time_limit=CLEANUP_TIME_LIMIT,
        )
        self._start(_request_of(removal, request.working_directory))

    def _claude_argv(self, arguments: list[str]) -> list[str]:
        return [*login_argv(self._starters.login_files), self._executable, *arguments]

    def _config_folder(self, request: AgentRunRequest) -> dict[str, str]:
        home = request_home(request)
        if self._starters.confine_executable is None or home is None:
            return {}
        return {CONFIG_VARIABLE: str(home / RUNTIME_FOLDER)}

    def _process_request(
        self,
        request: AgentRunRequest,
        files: _RunFiles,
        arguments: list[str],
        time_limit: timedelta,
    ) -> ProcessRequest:
        started = run_launch(
            request,
            confined_argv(
                self._claude_argv(arguments), self._starters.confine_executable, files.rules
            ),
            {**self._config_folder(request), **SWITCHES},
            sudo_executable=self._starters.sudo_executable,
            time_limit=time_limit,
        )
        return _request_of(started, request.working_directory)

    def _start(self, process_request: ProcessRequest) -> ProcessResult:
        try:
            return run_process(process_request)
        except OSError as exc:
            program = process_request.argv[0]
            raise AgentRuntimeError(f"cannot start {program}: {exc}") from exc
