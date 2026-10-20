"""What the factory asks of an agent run and what it learns from one."""

from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    field_validator,
    model_validator,
)

from factory.domain.errors import AgentDefinitionMissing
from factory.domain.identifiers import Name, is_name

QUESTION = "question"

# The console script that confines a run's writes and then becomes the agent runtime.
CONFINE_COMMAND = "factory-confine"

# Claude Code ignores an agent file in print mode, so the runner applies these keys itself;
# any other key would read as if it did something and do nothing.
APPLIED_AGENT_KEYS: frozenset[str] = frozenset({"model", "tools", "effort", "budget_usd"})
KEY_NOT_APPLIED = "key not applied by the agent runtime"


def check_agent_name(name: str) -> None:
    """Raise `AgentDefinitionMissing` when `name` is not an agent name."""
    if not is_name(name):
        raise AgentDefinitionMissing(name, f"not an agent name: {name}")


# The agent's environment is built from these names alone, so nothing the factory process
# holds, its hosting-service token above all, reaches an agent run by accident.
ALLOWED_ENVIRONMENT_NAMES: frozenset[str] = frozenset(
    {"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TZ"}
)

EndReason = Literal["completed", "no_result", "time_limit", "budget", "died", "provider_limit"]
# The login a run's calls were handed: an API key, the subscription's token, or neither.
Login = Literal["api_key", "subscription", "none"]


def scrub_environment(source: Mapping[str, str]) -> dict[str, str]:
    """Return a new dict of the entries of `source` whose name is allowed for an agent run."""
    return {name: value for name, value in source.items() if name in ALLOWED_ENVIRONMENT_NAMES}


def _must_be_absolute(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError(f"path must be absolute, got {path}")
    return path


AbsolutePath = Annotated[Path, AfterValidator(_must_be_absolute)]


class AgentDefinition(BaseModel):
    """An agent: its name, model, tools, effort, budget per run and instructions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Name
    model: str
    tools: list[str]
    effort: str | None = None
    budget_usd: Annotated[Decimal, Field(gt=0)]
    instructions: str


class GuardSettings(BaseModel):
    """Where an agent may write: the root, write paths, protected paths and tool paths."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: AbsolutePath
    write_paths: list[str]
    protected_paths: list[str]
    tool_paths: list[str] = []


class AgentRunRequest(BaseModel):
    """One run of one agent: prompt, allowed decisions, limit, directory and environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent: AgentDefinition
    prompt: str
    allowed_decisions: list[str]
    time_limit: timedelta
    working_directory: AbsolutePath
    environment: dict[str, str] = {}
    guard: GuardSettings | None = None
    os_user: str | None = None
    resume_session: str | None = None

    @field_validator("allowed_decisions")
    @classmethod
    def _question_is_allowed_once_each(cls, decisions: list[str]) -> list[str]:
        # An agent that cannot finish must always be able to ask the human.
        if QUESTION not in decisions:
            raise ValueError(f"allowed decisions must contain {QUESTION!r}, got {decisions}")
        if len(set(decisions)) != len(decisions):
            raise ValueError(f"allowed decisions must not repeat, got {decisions}")
        return decisions

    @field_validator("time_limit")
    @classmethod
    def _time_limit_is_positive(cls, time_limit: timedelta) -> timedelta:
        if time_limit <= timedelta(0):
            raise ValueError(f"time limit must be positive, got {time_limit}")
        return time_limit

    @field_validator("resume_session")
    @classmethod
    def _resume_session_is_not_blank(cls, session: str | None) -> str | None:
        if session is not None and not session.strip():
            raise ValueError("a session to resume must not be blank")
        return session


class TokenCounts(BaseModel):
    """The tokens one run used, by kind."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input: NonNegativeInt
    output: NonNegativeInt
    cache_read: NonNegativeInt = 0
    cache_creation: NonNegativeInt = 0


class PermissionDenial(BaseModel):
    """A tool call the runtime refused during a run; `path` is the file it named, if any."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool: str
    detail: str
    path: str | None = None


class AgentRunResult(BaseModel):
    """How a run ended, its decision and entry, and its measures; `None` is unknown, never 0."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    end_reason: EndReason
    decision: str | None = None
    entry: str | None = None
    duration: timedelta
    model_duration: timedelta | None = None
    turns: NonNegativeInt | None = None
    tokens: TokenCounts | None = None
    cost_usd: Decimal | None = None
    permission_denials: list[PermissionDenial] = []
    login: Login | None = None
    session: str | None = None
    limit_wait: timedelta | None = None

    @model_validator(mode="after")
    def _decision_and_entry_only_when_completed(self) -> Self:
        completed = self.end_reason == "completed"
        for field, value in (("decision", self.decision), ("entry", self.entry)):
            if completed and value is None:
                raise ValueError(f"a completed run needs a {field}")
            if not completed and value is not None:
                raise ValueError(f"a run that ended by {self.end_reason} has no {field}")
        return self

    @model_validator(mode="after")
    def _limit_wait_only_when_limited(self) -> Self:
        if self.limit_wait is None:
            return self
        if self.end_reason != "provider_limit":
            raise ValueError(f"a run that ended by {self.end_reason} has no limit_wait")
        if self.limit_wait <= timedelta(0):
            raise ValueError(f"limit_wait must be positive, got {self.limit_wait}")
        return self

    @property
    def ok(self) -> bool:
        """Whether the run completed with a decision and an entry."""
        return self.end_reason == "completed"


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


def resumed_result(first: AgentRunResult, second: AgentRunResult) -> AgentRunResult:
    """The result of a run whose `first` call the `second` resumed: its answer, both calls' sums."""
    denials = [*first.permission_denials, *second.permission_denials]
    duration = first.duration + second.duration
    session = second.session if second.session is not None else first.session
    # R24: a resume the time limit ended has no measures, and the first call's alone are partial.
    if second.end_reason == "time_limit":
        return second.model_copy(
            update={"permission_denials": denials, "duration": duration, "session": session}
        )
    return second.model_copy(
        update={
            "session": session,
            "duration": duration,
            "model_duration": _add(first.model_duration, second.model_duration),
            "turns": _add(first.turns, second.turns),
            "cost_usd": _add(first.cost_usd, second.cost_usd),
            "tokens": _add_tokens(first.tokens, second.tokens),
            "permission_denials": denials,
        }
    )
