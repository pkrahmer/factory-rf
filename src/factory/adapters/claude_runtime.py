"""The agent runtime that runs an agent as one `claude -p` call under the operator's login."""

import json
import shlex
import time
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, JsonValue, StrictBool, ValidationError

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.domain.agent_runs import (
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
GUARD_COMMAND = "factory-guard"
GUARDED_TOOLS = "Edit|Write"


class _Usage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


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
    num_turns: int | None = None
    # A float as the JSON carries it; `Decimal(str(...))` keeps the digits it printed.
    total_cost_usd: float | None = None
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


def _end_reason(
    request: AgentRunRequest, process: ProcessResult, reply: _Reply | None
) -> EndReason:
    if process.timed_out:
        return "time_limit"
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


def _result(
    request: AgentRunRequest, process: ProcessResult, duration: timedelta
) -> AgentRunResult:
    reply = _parse_reply(process.stdout)
    end_reason = _end_reason(request, process, reply)
    # A killed call's output is cut short, so whatever it printed is not its measure.
    if reply is None or process.timed_out:
        return AgentRunResult(end_reason=end_reason, duration=duration)
    output = reply.structured_output if end_reason == "completed" else None
    cost = None if reply.total_cost_usd is None else Decimal(str(reply.total_cost_usd))
    return AgentRunResult(
        end_reason=end_reason,
        decision=None if output is None else output.decision,
        entry=None if output is None else output.entry,
        duration=duration,
        turns=reply.num_turns,
        tokens=_tokens(reply.usage),
        cost_usd=cost,
        permission_denials=_denials(reply),
    )


class ClaudeCodeRuntime:
    """Runs an agent as one `claude -p` call, with only the environment the request gives."""

    def __init__(
        self, executable: str, state_directory: Path, kill_points: KillPoints | None = None
    ) -> None:
        """Call `executable`, keep a run's files in `state_directory`, reach `kill_points`."""
        self._executable = executable
        self._state_directory = state_directory
        self._kill_points = kill_points

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` as one call and turn the JSON it prints into a result.

        A call that cannot be started, or whose files cannot be written, is `AgentRuntimeError`.
        """
        started = time.monotonic()
        session = str(uuid.uuid4())
        files = _RunFiles.of(self._state_directory, session)
        self._make_state_directory()
        try:
            self._write_files(request, files)
            process = self._call(request, _arguments(request, session, files))
            result = _result(request, process, timedelta(seconds=time.monotonic() - started))
            if self._kill_points is not None:
                self._kill_points.reach(KillPoint.AGENT_RUN)
            return result
        finally:
            files.remove()

    def _make_state_directory(self) -> None:
        try:
            self._state_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise self._state_error(exc) from exc

    def _state_error(self, exc: OSError) -> AgentRuntimeError:
        return AgentRuntimeError(f"cannot write the state directory {self._state_directory}: {exc}")

    def _write_files(self, request: AgentRunRequest, files: _RunFiles) -> None:
        try:
            files.instructions.write_text(request.agent.instructions, encoding="utf-8")
            if request.guard is not None:
                files.guard.write_text(request.guard.model_dump_json(), encoding="utf-8")
                files.hooks.write_text(_hook_settings(files.guard), encoding="utf-8")
        except OSError as exc:
            raise self._state_error(exc) from exc

    def _call(self, request: AgentRunRequest, arguments: list[str]) -> ProcessResult:
        process_request = ProcessRequest(
            argv=[self._executable, *arguments],
            cwd=request.working_directory,
            env={**request.environment, **SWITCHES},
            time_limit=request.time_limit,
        )
        try:
            return run_process(process_request)
        except OSError as exc:
            raise AgentRuntimeError(f"cannot start {self._executable}: {exc}") from exc
