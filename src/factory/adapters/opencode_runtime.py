"""The agent runtime that runs an agent as one `opencode run` call and reads its JSON events."""

import json
import re
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
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
    ENTRY_DESCRIPTION,
    FINISH_MESSAGE,
    VERSION_TIME_LIMIT,
    CallEnd,
    Launch,
    LoginFiles,
    Starters,
    container_launch,
    denied_path,
    finished_run,
    login_argv,
    login_paths,
    login_used,
    read_call_end,
    resume_budget,
    run_environment,
    run_launch,
    since,
    state_directory_error,
    version_launch,
    version_printed,
)
from factory.adapters.process import (
    ProcessRequest,
    ProcessResult,
    Stream,
    run_process,
    run_streaming,
)
from factory.application.agent_runtime import AgentRuntime
from factory.application.containers import ContainerRuns
from factory.domain.agent_runs import (
    AgentDefinition,
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    PermissionDenial,
    TokenCounts,
    resumed_result,
)
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoints
from factory.domain.opencode_provider import provider_configuration, read_provider
from factory.domain.provider_limits import ProviderLimit, limit_in_text, named_wait

CONFIG_VARIABLE = "OPENCODE_CONFIG"
AGENT_PREFIX = "factory-"
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
# Tools of Claude Code that opencode has no counterpart for and that a run can do without.
LEFT_OUT_TOOLS: frozenset[str] = frozenset({"Skill"})
RESULT_OPEN = "<factory-result>"
RESULT_CLOSE = "</factory-result>"
DENIAL_PATTERN = re.compile(r"permission|denied", re.IGNORECASE)

_DECISION_LABEL = "decision:"
_ENTRY_LABEL = "entry:"
# opencode's own file tools name their file by this key.
_PATH_KEYS = ("filePath",)
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
    session_id: str | None = Field(default=None, alias="sessionID")
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

    cost: float
    tokens: _Tokens


class _RunFiles(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    config: Path

    @classmethod
    def of(cls, state_directory: Path, run: str) -> "_RunFiles":
        return cls(config=state_directory / f"opencode-{run}.json")

    def remove(self) -> None:
        self.config.unlink(missing_ok=True)


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
        if tool in LEFT_OUT_TOOLS:
            continue
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


def _provider_keys(provider_file: Path | None) -> dict[str, object]:
    if provider_file is None:
        return {}
    try:
        provider = read_provider(provider_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AgentRuntimeError(
            f"cannot use the opencode provider file {provider_file}: {exc}"
        ) from exc
    return provider_configuration(provider)


def _configuration(
    request: AgentRunRequest, bash: dict[str, str], provider_keys: Mapping[str, object]
) -> str:
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
        **provider_keys,
    }
    return json.dumps(configuration)


def _event(line: str) -> _Event | None:
    try:
        return _Event.model_validate_json(line)
    except ValidationError:
        return None


def _events(stdout: str) -> list[_Event]:
    events = (_event(line) for line in stdout.splitlines())
    return [event for event in events if event is not None]


def _limit_message(event: _Event, limit: ProviderLimit) -> str | None:
    """The message of an error event that shows `limit`, empty without one; else `None`."""
    data = None if event.error is None else event.error.data
    if event.type != "error" or data is None:
        return None
    message = data.message or ""
    if data.status_code == limit.status or limit_in_text(message, limit):
        return message
    return None


class _Watch:
    """Reads a call's lines as they stream and stops it past its budget or at a limit."""

    def __init__(self, budget: Decimal, limit: ProviderLimit) -> None:
        self._budget = budget
        self._limit = limit
        self._cost = Decimal(0)
        self.stopped_by: EndReason | None = None
        self.limit_text: str | None = None

    def on_line(self, stream: Stream, line: str) -> bool:
        """Read `line` of `stream`; True stops the call."""
        if stream == "stderr":
            if limit_in_text(line, self._limit):
                self._stop_at_limit(line)
        else:
            event = _event(line)
            if event is not None:
                self._read(event)
        return self.stopped_by is not None

    def _read(self, event: _Event) -> None:
        # Only an error event can be a limit: the agent's text and its tools' output name
        # whatever they like.
        limit_message = _limit_message(event, self._limit)
        if limit_message is not None:
            self._stop_at_limit(limit_message)
        elif event.type == "step_finish" and event.part is not None and event.part.cost is not None:
            self._cost += Decimal(str(event.part.cost))
            if self._cost > self._budget:
                self.stopped_by = "budget"

    def _stop_at_limit(self, text: str) -> None:
        self.stopped_by = "provider_limit"
        self.limit_text = text


def _steps(events: Sequence[_Event]) -> list[_Step]:
    return [
        _Step(cost=event.part.cost, tokens=event.part.tokens)
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
                path=denied_path(state.input, _PATH_KEYS),
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


def _session(events: Sequence[_Event], request: AgentRunRequest) -> str | None:
    named = (event.session_id for event in events if event.session_id is not None)
    return next(named, request.resume_session)


def _end_reason(
    process: ProcessResult,
    watch: _Watch,
    steps: Sequence[_Step],
    answer: tuple[str, str] | None,
) -> EndReason:
    if process.timed_out:
        return "time_limit"
    if watch.stopped_by is not None:
        return watch.stopped_by
    if process.exit_status != 0 or not steps:
        return "died"
    if answer is None:
        return "no_result"
    return "completed"


def _limit_wait(end_reason: EndReason, watch: _Watch) -> timedelta | None:
    if end_reason != "provider_limit" or watch.limit_text is None:
        return None
    return named_wait(watch.limit_text)


def _result(request: AgentRunRequest, process: ProcessResult, watch: _Watch) -> AgentRunResult:
    # The duration is the whole run's, so `run` sets it once the call has ended.
    login = login_used(process.stderr)
    events = _events(process.stdout)
    session = _session(events, request)
    # A killed call's output is cut short, so whatever it printed is not its measure.
    if process.timed_out:
        return AgentRunResult(end_reason="time_limit", duration=_ZERO, login=login, session=session)
    steps = _steps(events)
    answer = _answer(events, request.allowed_decisions)
    end_reason = _end_reason(process, watch, steps, answer)
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
        session=session,
        limit_wait=_limit_wait(end_reason, watch),
    )


def _request_of(started: Launch, cwd: Path) -> ProcessRequest:
    return ProcessRequest(
        argv=started.argv, cwd=cwd, env=started.env, time_limit=started.time_limit
    )


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
        api_login_file: Path | None = None,
        provider_limit: ProviderLimit | None = None,
        containers: ContainerRuns | None = None,
        extra_environment: Mapping[str, str] = {},
        ca_bundle: Path | None = None,
        provider_file: Path | None = None,
    ) -> None:
        """Call `executable`, keep a run's files in `state_directory`, reach `kill_points`.

        An agent's model alias is looked up in `models`; a model with a `/` is passed as it is.
        The shell commands the `Bash(...)` entries of `settings_file` deny are denied.
        A run's call gets the key held in `api_login_file`, read by the call's own shell.
        A call that shows `provider_limit`, the default limit when `None`, ends `provider_limit`.
        With `containers`, every call runs in a container, with `extra_environment` and with
        `ca_bundle` mounted read-only at its own path.
        The provider and small model of `provider_file` join every run's configuration.
        """
        self._containers = containers
        self._extra_environment = dict(extra_environment)
        self._bundle_files = [] if ca_bundle is None else [ca_bundle]
        self._executable = executable
        self._state_directory = state_directory
        self._kill_points = kill_points
        self._models = {} if models is None else dict(models)
        self._settings_file = settings_file
        self._version_time_limit = version_time_limit
        self._starters = Starters(login_files=LoginFiles(api=api_login_file))
        self._provider_limit = ProviderLimit() if provider_limit is None else provider_limit
        self._provider_file = provider_file

    @property
    def containers(self) -> ContainerRuns | None:
        """Where every call runs, or `None` when calls run on the host."""
        return self._containers

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` and turn the JSON events it prints into a result.

        A call is stopped once the cost of its steps passes its budget, or at once when it shows
        the provider limit. A budget stop of a known session resumes it once within what is
        left of the time limit. A request the runtime cannot configure, a call that cannot be
        started, or files that cannot be written are `AgentRuntimeError`.
        """
        started = time.monotonic()
        model = _model(request.agent, self._models)
        configuration = _configuration(
            request, _bash_permission(self._settings_file), _provider_keys(self._provider_file)
        )
        files = _RunFiles.of(self._state_directory, str(uuid.uuid4()))
        try:
            self._write_files(files, configuration)
            result = self._call(request, files, model, request.agent.budget_usd)
            if result.end_reason == "budget" and result.session is not None:
                result = self._resume(request, files, model, result, started)
            return finished_run(result, started, self._kill_points)
        finally:
            files.remove()

    def version(self) -> str:
        """The version `opencode --version` prints, such as `1.19.3`.

        A call that cannot be started, fails, reaches its limit or prints nothing is
        `AgentRuntimeError`.
        """
        started = version_launch(
            self._executable, containers=self._containers, time_limit=self._version_time_limit
        )
        process = self._start(_request_of(started, Path.cwd()))
        return version_printed(
            self._executable,
            failed=process.timed_out or process.exit_status != 0,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    def _write_files(self, files: _RunFiles, configuration: str) -> None:
        try:
            files.config.write_text(configuration, encoding="utf-8")
        except OSError as exc:
            raise state_directory_error(self._state_directory, exc) from exc

    def _resume(
        self,
        request: AgentRunRequest,
        files: _RunFiles,
        model: str,
        first: AgentRunResult,
        started: float,
    ) -> AgentRunResult:
        left = request.time_limit - since(started)
        if left <= _ZERO:
            second = AgentRunResult(end_reason="time_limit", duration=_ZERO)
        else:
            resume = request.model_copy(
                update={
                    "prompt": FINISH_MESSAGE,
                    "resume_session": first.session,
                    "time_limit": left,
                }
            )
            second = self._call(resume, files, model, resume_budget(request.agent.budget_usd))
        return resumed_result(first, second)

    def _call(
        self, request: AgentRunRequest, files: _RunFiles, model: str, budget: Decimal
    ) -> AgentRunResult:
        watch = _Watch(budget, self._provider_limit)
        process_request = self._process_request(request, files, model)
        process = self._start(process_request, watch.on_line)
        end = CallEnd(
            stderr=process.stderr,
            printed=bool(_events(process.stdout)),
            exit_status=process.exit_status,
            duration=process.duration,
            timed_out=process.timed_out,
        )
        timed_out = read_call_end(
            end,
            time_limit=request.time_limit,
            starters=self._starters,
            in_container=self._containers is not None,
        )
        process = process.model_copy(update={"timed_out": timed_out})
        return _result(request, process, watch)

    def _opencode_argv(self, request: AgentRunRequest, model: str) -> list[str]:
        agent = f"{AGENT_PREFIX}{request.agent.name}"
        arguments = ["run", "--format", "json", "--auto", "--model", model, "--agent", agent]
        if request.resume_session is not None:
            arguments += ["--session", request.resume_session]
        return [
            *login_argv(self._starters.login_files),
            self._executable,
            *arguments,
            request.prompt,
        ]

    def _process_request(
        self, request: AgentRunRequest, files: _RunFiles, model: str
    ) -> ProcessRequest:
        argv = self._opencode_argv(request, model)
        runtime_environment = {CONFIG_VARIABLE: str(files.config), **SWITCHES}
        if self._containers is None:
            started = run_launch(request, argv, runtime_environment, time_limit=request.time_limit)
        else:
            started = container_launch(
                self._containers,
                argv,
                # The factory's own names, PATH among them, never come from the host.
                {**self._extra_environment, **run_environment(request, runtime_environment)},
                files=[*login_paths(self._starters.login_files), files.config, *self._bundle_files],
                time_limit=request.time_limit,
            )
        return _request_of(started, request.working_directory)

    def _start(
        self,
        process_request: ProcessRequest,
        on_line: Callable[[Stream, str], bool] | None = None,
    ) -> ProcessResult:
        try:
            if on_line is not None:
                return run_streaming(process_request, on_line)
            return run_process(process_request)
        except OSError as exc:
            program = process_request.argv[0]
            raise AgentRuntimeError(f"cannot start {program}: {exc}") from exc
