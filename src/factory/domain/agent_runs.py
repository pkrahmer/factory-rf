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

from factory.domain.identifiers import Name

QUESTION = "question"

# The console script the Claude Code hook starts to judge a write.
GUARD_COMMAND = "factory-guard"

# The console script that confines a run's writes and then becomes the agent runtime.
CONFINE_COMMAND = "factory-confine"

# Claude Code ignores an agent file in print mode, so the runner applies these keys itself;
# any other key would read as if it did something and do nothing.
APPLIED_AGENT_KEYS: frozenset[str] = frozenset({"model", "tools", "effort", "budget_usd"})
KEY_NOT_APPLIED = "key not applied by the agent runtime"

# The agent's environment is built from these names alone, so nothing the factory process
# holds, its hosting-service token above all, reaches an agent run by accident.
ALLOWED_ENVIRONMENT_NAMES: frozenset[str] = frozenset(
    {"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TZ"}
)

EndReason = Literal["completed", "no_result", "time_limit", "budget", "died"]


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
    """Where an agent may write: root, write paths, paths no agent may touch, tools' folders."""

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


class TokenCounts(BaseModel):
    """The tokens one run used, by kind."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input: NonNegativeInt
    output: NonNegativeInt
    cache_read: NonNegativeInt = 0
    cache_creation: NonNegativeInt = 0


class PermissionDenial(BaseModel):
    """A tool call the runtime refused during a run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool: str
    detail: str


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

    @model_validator(mode="after")
    def _decision_and_entry_only_when_completed(self) -> Self:
        completed = self.end_reason == "completed"
        for field, value in (("decision", self.decision), ("entry", self.entry)):
            if completed and value is None:
                raise ValueError(f"a completed run needs a {field}")
            if not completed and value is not None:
                raise ValueError(f"a run that ended by {self.end_reason} has no {field}")
        return self

    @property
    def ok(self) -> bool:
        """Whether the run completed with a decision and an entry."""
        return self.end_reason == "completed"
