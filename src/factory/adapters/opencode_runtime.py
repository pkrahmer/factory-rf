"""The agent runtime that runs an agent as one `opencode run` call and reads its JSON events."""

import json
import re
import tempfile
import time
import uuid
from collections.abc import Mapping, Sequence
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    NonNegativeFloat,
    NonNegativeInt,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from factory.adapters.agent_launch import (
    CLEANUP_TIME_LIMIT,
    CONFINE_PREFIX,
    ENTRY_DESCRIPTION,
    RUN_FILE_MODE,
    SHELL_EXECUTABLE,
    SUDO_EXECUTABLE,
    SUDO_PREFIX,
    VERSION_TIME_LIMIT,
    LoginFiles,
    cleanup_argv,
    confined_argv,
    existing_devices,
    first_word,
    killed_at_limit,
    launch,
    line_starting,
    login_argv,
    login_refusal,
    login_used,
    run_confinement,
    temporary_folder,
    without_login,
)
from factory.adapters.process import (
    ProcessRequest,
    ProcessResult,
    Stream,
    run_process,
    run_streaming,
)
from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import (
    AgentDefinition,
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    PermissionDenial,
    TokenCounts,
)
from factory.domain.confinement import DEVICE_FILES, DEVICE_FOLDERS, Confinement
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoint, KillPoints

CONFIG_VARIABLE = "OPENCODE_CONFIG"
AGENT_PREFIX = "factory-"
# Where opencode keeps its sessions, logs and caches; its own configuration folder stays
# outside the rules, so an agent cannot rewrite what the next run is told.
RUNTIME_FOLDERS = (".local/share/opencode", ".local/state/opencode", ".cache/opencode")
SWITCHES = {"PYTHONDONTWRITEBYTECODE": "1"}
OPENCODE_TOOLS = (
    "bash",
    "edit",
    "write",
    "read",
    "grep",
    "glob",
    "list",
    "patch",
    "todowrite",
    "todoread",
    "webfetch",
    "task",
)
TOOL_NAMES = {
    "Bash": "bash",
    "Edit": "edit",
    "Write": "write",
    "Read": "read",
    "Grep": "grep",
    "Glob": "glob",
    "WebFetch": "webfetch",
    "Task": "task",
    "TodoWrite": "todowrite",
}
RESULT_OPEN = "<factory-result>"
RESULT_CLOSE = "</factory-result>"
DENIAL_PATTERN = re.compile(r"permission|denied", re.IGNORECASE)

_DECISION_LABEL = "decision:"
_ENTRY_LABEL = "entry:"
# opencode's own file tools name their file by this key.
_PATH_KEY = "filePath"
_BASH_DENIAL = re.compile(r"Bash\((?P<pattern>.*)\)")
_ZERO = timedelta(0)
_JSON = TypeAdapter[JsonValue](JsonValue)


def result_instructions(allowed_decisions: Sequence[str]) -> str:
    """The block the agent is told to end its final message with, naming `allowed_decisions`."""
    return (
        "End your final message with this block, and nothing after it:\n"
        f"{RESULT_OPEN}\n"
        f"{_DECISION_LABEL} <one of: {', '.join(allowed_decisions)}>\n"
        f"{_ENTRY_LABEL}\n"
        f"<{ENTRY_DESCRIPTION}>\n"
        f"{RESULT_CLOSE}"
    )


def parse_result_block(text: str, allowed_decisions: Sequence[str]) -> tuple[str, str] | None:
    """The decision and entry of the block that ends `text`, or `None` when it is not whole."""
    lines = text.rstrip().splitlines()
    if not lines or lines[-1] != RESULT_CLOSE:
        return None
    body = lines[:-1]
    if RESULT_OPEN not in body:
        return None
    opening = len(body) - 1 - body[::-1].index(RESULT_OPEN)
    block = body[opening + 1 :]
    if len(block) < 2 or not block[0].startswith(_DECISION_LABEL) or block[1] != _ENTRY_LABEL:
        return None
    decision = block[0].removeprefix(_DECISION_LABEL).strip()
    entry = "\n".join(block[2:]).strip()
    if decision not in allowed_decisions or not entry:
        return None
    return decision, entry


# A negative timestamp, count or cost is no measure: such a line does not validate.
class _CacheTokens(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    read: NonNegativeInt = 0
    write: NonNegativeInt = 0


class _Tokens(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    input: NonNegativeInt
    output: NonNegativeInt
    reasoning: NonNegativeInt = 0
    cache: _CacheTokens = _CacheTokens()


class _Span(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    start: NonNegativeInt
    end: NonNegativeInt


class _ToolState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    status: str
    input: JsonValue = None
    error: str | None = None
    time: _Span | None = None


class _Part(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    type: str
    text: str | None = None
    tool: str | None = None
    state: _ToolState | None = None
    # A float as the JSON carries it; `Decimal(str(...))` keeps the digits it printed.
    cost: NonNegativeFloat | None = None
    tokens: _Tokens | None = None


class _ErrorData(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    message: str | None = None
    status_code: NonNegativeInt | None = Field(default=None, alias="statusCode")


class _Error(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    name: str | None = None
    data: _ErrorData | None = None


class _Event(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    type: Literal["step_start", "tool_use", "text", "step_finish", "error"]
    timestamp: NonNegativeInt
    part: _Part | None = None
    error: _Error | None = None

    @model_validator(mode="after")
    def _part_of_its_type(self) -> Self:
        part = self.part
        if self.type == "step_finish" and (
            part is None or part.cost is None or part.tokens is None
        ):
            raise ValueError("a step_finish needs a cost and tokens")
        if self.type == "tool_use" and (part is None or part.tool is None or part.state is None):
            raise ValueError("a tool_use needs a tool and a state")
        if self.type == "text" and (part is None or part.text is None):
            raise ValueError("a text needs a text")
        return self


class _Step(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: int
    cost: float
    tokens: _Tokens


class _RunFiles(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    config: Path
    rules: Path
    temporary: Path

    @classmethod
    def of(cls, state_directory: Path, temporary_root: Path, run: str) -> "_RunFiles":
        return cls(
            config=state_directory / f"opencode-{run}.json",
            rules=state_directory / f"confine-{run}.json",
            temporary=temporary_folder(temporary_root, run),
        )

    def remove(self) -> None:
        for path in (self.config, self.rules):
            path.unlink(missing_ok=True)


def _since(started: float) -> timedelta:
    return timedelta(seconds=time.monotonic() - started)


def _never_stop(_stream: Stream, _line: str) -> bool:
    return False


def _model(agent: AgentDefinition, models: Mapping[str, str]) -> str:
    if "/" in agent.model:
        return agent.model
    model = models.get(agent.model)
    if model is None:
        raise AgentRuntimeError(
            f"the opencode runtime has no model for {agent.model}: set FACTORY_OPENCODE_MODELS"
        )
    return model


def _tools(agent: AgentDefinition) -> dict[str, bool]:
    enabled = set()
    for tool in agent.tools:
        name = TOOL_NAMES.get(tool)
        if name is None:
            raise AgentRuntimeError(f"the opencode runtime has no tool for {tool}")
        enabled.add(name)
    return {name: name in enabled for name in OPENCODE_TOOLS}


def _deny_list(settings_file: Path) -> list[str]:
    try:
        text = settings_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentRuntimeError(f"cannot read the agent settings {settings_file}: {exc}") from exc
    missing = AgentRuntimeError(f"the agent settings {settings_file} hold no permissions.deny list")
    try:
        settings = _JSON.validate_json(text)
    except ValidationError as exc:
        raise missing from exc
    permissions = settings.get("permissions") if isinstance(settings, dict) else None
    deny = permissions.get("deny") if isinstance(permissions, dict) else None
    if not isinstance(deny, list) or not all(isinstance(entry, str) for entry in deny):
        raise missing
    return [entry for entry in deny if isinstance(entry, str)]


def _bash_permission(settings_file: Path | None) -> dict[str, str]:
    permission = {"*": "allow"}
    if settings_file is None:
        return permission
    for entry in _deny_list(settings_file):
        denial = _BASH_DENIAL.fullmatch(entry)
        if denial is not None:
            permission[denial["pattern"]] = "deny"
    return permission


def _configuration(request: AgentRunRequest, bash: dict[str, str]) -> str:
    agent = request.agent
    prompt = f"{agent.instructions}\n\n{result_instructions(request.allowed_decisions)}"
    configuration = {
        "autoupdate": False,
        "share": "disabled",
        "snapshot": False,
        "agent": {
            f"{AGENT_PREFIX}{agent.name}": {
                "mode": "primary",
                "prompt": prompt,
                "tools": _tools(agent),
                "permission": {"edit": "allow", "bash": bash},
            }
        },
    }
    return json.dumps(configuration)


def _events(stdout: str) -> list[_Event]:
    events = []
    for line in stdout.splitlines():
        try:
            events.append(_Event.model_validate_json(line))
        except ValidationError:
            continue
    return events


def _steps(events: Sequence[_Event]) -> list[_Step]:
    return [
        _Step(timestamp=event.timestamp, cost=event.part.cost, tokens=event.part.tokens)
        for event in events
        if event.type == "step_finish"
        and event.part is not None
        and event.part.cost is not None
        and event.part.tokens is not None
    ]


def _tokens(steps: Sequence[_Step]) -> TokenCounts:
    return TokenCounts(
        input=sum(step.tokens.input for step in steps),
        output=sum(step.tokens.output + step.tokens.reasoning for step in steps),
        cache_read=sum(step.tokens.cache.read for step in steps),
        cache_creation=sum(step.tokens.cache.write for step in steps),
    )


def _span_ms(event: _Event) -> int:
    span = None if event.part is None or event.part.state is None else event.part.state.time
    return 0 if span is None else span.end - span.start


def _model_ms(events: Sequence[_Event]) -> int:
    # "Before" and "between" go by line order, not by the timestamps.
    total = 0
    started: int | None = None
    tools = 0
    for event in events:
        if event.type == "step_start":
            started, tools = event.timestamp, 0
        elif event.type == "tool_use":
            tools += _span_ms(event)
        elif event.type == "step_finish" and started is not None:
            total += max(event.timestamp - started - tools, 0)
    return total


def _denied_path(tool_input: JsonValue) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    value = tool_input.get(_PATH_KEY)
    return value if isinstance(value, str) else None


def _denials(events: Sequence[_Event]) -> list[PermissionDenial]:
    denials = []
    for event in events:
        part = event.part
        if event.type != "tool_use" or part is None or part.tool is None or part.state is None:
            continue
        state = part.state
        if state.status != "error" or state.error is None or not DENIAL_PATTERN.search(state.error):
            continue
        denials.append(
            PermissionDenial(
                tool=part.tool,
                detail=json.dumps(state.input, sort_keys=True),
                path=_denied_path(state.input),
            )
        )
    return denials


def _answer(events: Sequence[_Event], allowed_decisions: Sequence[str]) -> tuple[str, str] | None:
    texts = [
        event.part.text
        for event in events
        if event.type == "text" and event.part is not None and event.part.text is not None
    ]
    return None if not texts else parse_result_block(texts[-1], allowed_decisions)


def _end_reason(
    process: ProcessResult, steps: Sequence[_Step], answer: tuple[str, str] | None
) -> EndReason:
    if process.timed_out:
        return "time_limit"
    if process.exit_status != 0 or not steps:
        return "died"
    if answer is None:
        return "no_result"
    return "completed"


def _result(request: AgentRunRequest, process: ProcessResult) -> AgentRunResult:
    # The duration is the whole run's, so `run` sets it once the call has ended.
    login = login_used(process.stderr)
    # A killed call's output is cut short, so whatever it printed is not its measure.
    if process.timed_out:
        return AgentRunResult(end_reason="time_limit", duration=_ZERO, login=login)
    events = _events(process.stdout)
    steps = _steps(events)
    answer = _answer(events, request.allowed_decisions)
    end_reason = _end_reason(process, steps, answer)
    completed = answer if end_reason == "completed" else None
    return AgentRunResult(
        end_reason=end_reason,
        decision=None if completed is None else completed[0],
        entry=None if completed is None else completed[1],
        duration=_ZERO,
        model_duration=timedelta(milliseconds=_model_ms(events)) if steps else None,
        turns=len(steps) if steps else None,
        tokens=_tokens(steps) if steps else None,
        cost_usd=sum((Decimal(str(step.cost)) for step in steps), Decimal(0)) if steps else None,
        permission_denials=_denials(events),
        login=login,
    )


def _has_usable_events(process: ProcessResult) -> bool:
    return bool(_events(process.stdout)) and not process.timed_out


def _sudo_refusal(request: AgentRunRequest, process: ProcessResult) -> str | None:
    if request.os_user is None or _has_usable_events(process):
        return None
    return line_starting(process.stderr, SUDO_PREFIX)


def _confine_refusal(process: ProcessResult) -> str | None:
    if _has_usable_events(process):
        return None
    return line_starting(process.stderr, CONFINE_PREFIX)


def _confinement(request: AgentRunRequest, temporary: Path) -> Confinement:
    devices = existing_devices(DEVICE_FOLDERS, DEVICE_FILES)
    return run_confinement(request, temporary, runtime_folders=RUNTIME_FOLDERS, devices=devices)


class OpencodeRuntime(AgentRuntime):
    """Runs an agent as an `opencode run` call, defined for the run from its agent file."""

    def __init__(
        self,
        executable: str,
        state_directory: Path,
        kill_points: KillPoints | None = None,
        *,
        models: Mapping[str, str] | None = None,
        settings_file: Path | None = None,
        version_time_limit: timedelta = VERSION_TIME_LIMIT,
        sudo_executable: str = SUDO_EXECUTABLE,
        api_login_file: Path | None = None,
        confine_executable: str | None = None,
        temporary_root: Path | None = None,
    ) -> None:
        """Call `executable`, keep a run's files in `state_directory`, reach `kill_points`.

        An agent's model alias is looked up in `models`; a model with a `/` is passed as it is.
        The shell commands the `Bash(...)` entries of `settings_file` deny are denied.
        A request with an operating-system user is started through `sudo_executable`.
        A run's call gets the key held in `api_login_file`, read by the call's own shell.
        With `confine_executable`, every call starts through it with the run's rules and
        its own temporary folder under `temporary_root`, the system's by default.
        """
        self._executable = executable
        self._state_directory = state_directory
        self._kill_points = kill_points
        self._models = {} if models is None else dict(models)
        self._settings_file = settings_file
        self._version_time_limit = version_time_limit
        self._sudo_executable = sudo_executable
        self._login_files = LoginFiles(api=api_login_file)
        self._confine_executable = confine_executable
        self._temporary_root = (
            Path(tempfile.gettempdir()) if temporary_root is None else temporary_root
        )

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` and turn the JSON events it prints into a result.

        A request the runtime cannot configure, a call that cannot be started, or files that
        cannot be written are `AgentRuntimeError`.
        """
        started = time.monotonic()
        model = _model(request.agent, self._models)
        configuration = _configuration(request, _bash_permission(self._settings_file))
        files = _RunFiles.of(self._state_directory, self._temporary_root, str(uuid.uuid4()))
        try:
            self._write_files(request, files, configuration)
            result = _result(request, self._call(request, files, model))
            result = result.model_copy(update={"duration": _since(started)})
            if self._kill_points is not None:
                self._kill_points.reach(KillPoint.AGENT_RUN)
            return result
        finally:
            files.remove()

    def version(self) -> str:
        """The version `opencode --version` prints, such as `1.19.3`.

        A call that cannot be started, fails, reaches its limit or prints nothing is
        `AgentRuntimeError`.
        """
        process = self._start(
            ProcessRequest(
                argv=[self._executable, "--version"],
                cwd=Path.cwd(),
                time_limit=self._version_time_limit,
            )
        )
        if process.timed_out or process.exit_status != 0:
            raise AgentRuntimeError(f"{self._executable} --version failed: {process.stderr}")
        version = first_word(process.stdout)
        if version is None:
            raise AgentRuntimeError(f"{self._executable} --version printed nothing")
        return version

    def _write_files(self, request: AgentRunRequest, files: _RunFiles, configuration: str) -> None:
        written = {files.config: configuration}
        if self._confine_executable is not None:
            written[files.rules] = _confinement(request, files.temporary).model_dump_json()
        try:
            for path, text in written.items():
                path.write_text(text, encoding="utf-8")
                path.chmod(RUN_FILE_MODE)
        except OSError as exc:
            raise AgentRuntimeError(
                f"cannot write the state directory {self._state_directory}: {exc}"
            ) from exc

    def _call(self, request: AgentRunRequest, files: _RunFiles, model: str) -> ProcessResult:
        process_request = self._process_request(request, files, model)
        process = self._start(process_request, streaming=True)
        if self._confine_executable is not None:
            self._remove_temporary_folder(request, files.temporary)
        killed = killed_at_limit(
            os_user=request.os_user,
            exit_status=process.exit_status,
            duration=process.duration,
            time_limit=request.time_limit,
        )
        if killed:
            # The inner kill ends the call as the factory's own would: read as its time limit.
            process = process.model_copy(update={"timed_out": True})
        refusal = _sudo_refusal(request, process)
        if refusal is not None:
            # A refused `sudo` is a misconfiguration of the machine, not a stalled agent.
            raise AgentRuntimeError(f"{self._sudo_executable} refused the agent run: {refusal}")
        self._check_confinement(process)
        self._check_login(process)
        return process

    def _check_confinement(self, process: ProcessResult) -> None:
        if self._confine_executable is None:
            return
        refusal = _confine_refusal(process)
        if refusal is not None:
            raise AgentRuntimeError(f"{self._confine_executable} refused the agent run: {refusal}")

    def _check_login(self, process: ProcessResult) -> None:
        if _events(process.stdout):
            return
        refusal = login_refusal(process.stderr, self._login_files)
        if refusal is not None:
            raise AgentRuntimeError(refusal)

    def _remove_temporary_folder(self, request: AgentRunRequest, temporary: Path) -> None:
        # Its status is not read: a folder left behind changes no run's result.
        removal = cleanup_argv(
            SHELL_EXECUTABLE,
            temporary,
            os_user=request.os_user,
            sudo_executable=self._sudo_executable,
        )
        self._start(
            ProcessRequest(
                argv=removal,
                cwd=request.working_directory,
                env={},
                time_limit=CLEANUP_TIME_LIMIT,
            )
        )

    def _opencode_argv(self, request: AgentRunRequest, model: str) -> list[str]:
        agent = f"{AGENT_PREFIX}{request.agent.name}"
        arguments = ["run", "--format", "json", "--auto", "--model", model, "--agent", agent]
        return [*login_argv(self._login_files), self._executable, *arguments, request.prompt]

    def _process_request(
        self, request: AgentRunRequest, files: _RunFiles, model: str
    ) -> ProcessRequest:
        # The login comes from the file or not at all, never from the request.
        given = without_login(request.environment)
        environment = {**given, CONFIG_VARIABLE: str(files.config), **SWITCHES}
        argv = confined_argv(
            self._opencode_argv(request, model), self._confine_executable, files.rules
        )
        started = launch(
            argv,
            environment,
            os_user=request.os_user,
            sudo_executable=self._sudo_executable,
            time_limit=request.time_limit,
        )
        return ProcessRequest(
            argv=started.argv,
            cwd=request.working_directory,
            env=started.env,
            time_limit=started.time_limit,
        )

    def _start(self, process_request: ProcessRequest, *, streaming: bool = False) -> ProcessResult:
        try:
            if streaming:
                return run_streaming(process_request, _never_stop)
            return run_process(process_request)
        except OSError as exc:
            program = process_request.argv[0]
            raise AgentRuntimeError(f"cannot start {program}: {exc}") from exc
